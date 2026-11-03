"""Cálculo de referencia INDEPENDIENTE (no es el código del sistema) de:
turnos, ráfagas, registro por turno, latencia hasta la siguiente intervención
y sensibilidad a la SEGMENTACIÓN (huecos de sesión y separación de ráfagas).

Aplica las secciones 1 a 3 de docs/definiciones_operativas.md. No fija un número
de versión: el historial de git indica qué versión del documento rige para cada
commit, y los parámetros usados se imprimen siempre en el bloque PARAMETROS.

Uso: python3 -I tools/referencia/ref_latency.py CHAT.txt [detalle]

El lector (`load`) NO es el parser del sistema: solo acepta el formato de los chats sintéticos y
rechaza (ReferenceLoadError) cualquier línea que no pueda clasificar, sin anexarla ni descartarla.
"""
import re, sys, statistics as st
from datetime import datetime

LINE = re.compile(r'^(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}) - ([^:]+): (.*)$')

# ---- Parámetros (espejo de config.yaml; los cambios se hacen en AMBOS sitios) ----
BURST_S = 300                  # segmentation.burst_max_gap_seconds (experimental)
SESSION_GAPS_H = (2, 6, 12)    # segmentation.sensitivity_session_gap_hours; 6 h es el inicial
BURST_GRID_S = (120, 300, 600) # robustness.segmentation.burst_max_gap_seconds (rejilla)
DEFAULT_GAP_H = 6


def params_block():
    return ('PARAMETROS (segmentación): hueco de sesión en horas = %s (inicial %s; la sesión se corta '
            'cuando el silencio SUPERA el hueco); ráfaga = intervalo <= %s s; rejilla de ráfaga = %s s; '
            'latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco'
            % (list(SESSION_GAPS_H), DEFAULT_GAP_H, BURST_S, list(BURST_GRID_S)))


class ReferenceLoadError(Exception):
    """El archivo contiene líneas que el lector de referencia no puede clasificar.
    El mensaje lista número de línea y motivo; nunca el contenido de la línea."""


# Orden de fecha del lector de referencia: parámetro EXPLÍCITO, no un valor por defecto del
# sistema (el contrato v0.2 prohíbe elegir DMY/MDY por defecto). Los tres chats sintéticos
# se escribieron en DD/MM/AAAA; el chat 00 es ambiguo por sus datos y solo se lee así por
# indicación (equivale a date_order_hint=dmy).
DATE_ORDER = 'dmy'

# Misma forma de encabezado que usan los tres chats de la Fase 0 (formato Android 24 h sin coma).
HEADER = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4}) (\d{1,2}):(\d{2}) - ([^:]+): (.*)$')
# "Aspecto de timestamp": fecha n/n/n al inicio y una hora h:m en los primeros 40 caracteres.
TS_LIKE = re.compile(r'^\[?\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}')
TS_HOUR = re.compile(r'\d{1,2}:\d{2}')
TS_WINDOW = 40
# Avisos del sistema reconocidos por el lector de referencia (solo el que traen los chats de la Fase 0).
# Un encabezado con fecha y hora SIN "Autor:" que no esté aquí se reporta como anomalía.
SYSTEM_HEADER = re.compile(r'^(\d{1,2})/(\d{1,2})/(\d{4}) (\d{1,2}):(\d{2}) - (Los mensajes y las llamadas están cifrados.*)$')


def _parse_header(m):
    a, b, y, hh, mm = int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5])
    day, month = (a, b) if DATE_ORDER == 'dmy' else (b, a)
    return datetime(y, month, day, hh, mm)       # ValueError si la fecha u hora no existe


def load_checked(path):
    """Devuelve (mensajes, anomalias, avisos_sistema). Cada línea física termina en un mensaje de
    persona, un aviso del sistema, una continuación, en blanco, o en `anomalias` con (línea, motivo).
    Nada se descarta ni se anexa sin clasificar. Una línea con aspecto de timestamp que no sea un
    encabezado válido NO se anexa al mensaje anterior y deja de haber mensaje abierto hasta el
    siguiente encabezado. Los avisos del sistema no son mensajes de persona: se devuelven aparte."""
    text = open(path, encoding='utf-8').read().lstrip('\ufeff')
    out, anomalies, system = [], [], []
    cur, had_header = None, False                 # cur: dict del mensaje o aviso abierto
    for n, raw in enumerate(text.replace('\r\n', '\n').split('\n'), 1):
        if not raw.strip():
            continue
        m = HEADER.match(raw)
        sm = None if m else SYSTEM_HEADER.match(raw)
        if m or sm:
            try:
                ts = _parse_header(m or sm)
            except ValueError:
                anomalies.append((n, 'TIMESTAMP_INVALID')); cur = None
                continue
            had_header = True
            if m:
                cur = {'ts': ts, 'who': m[6], 'txt': m[7], 'line': n}; out.append(cur)
            else:
                cur = {'ts': ts, 'txt': sm[6], 'line': n}; system.append(cur)
            continue
        if TS_LIKE.match(raw) and TS_HOUR.search(raw[:TS_WINDOW]):
            anomalies.append((n, 'TIMESTAMP_LIKE_UNRECOGNIZED')); cur = None
        elif cur is not None:
            cur['txt'] += '\n' + raw              # continuación legítima del mensaje o aviso abierto
        else:
            anomalies.append((n, 'ORPHAN_AFTER_UNPROCESSED' if had_header else 'ORPHAN_BEFORE_FIRST_MESSAGE'))
    return out, anomalies, system


def load(path):
    """Lectura estricta para los cálculos de referencia: si hay una sola línea sin clasificar,
    se rechaza el archivo (no se calcula sobre datos incompletos)."""
    msgs, anomalies, _system = load_checked(path)
    if anomalies:
        det = ', '.join('línea %d: %s' % a for a in anomalies[:20])
        raise ReferenceLoadError('%d línea(s) sin clasificar (%s)%s' % (
            len(anomalies), det, ' …' if len(anomalies) > 20 else ''))
    return msgs


def minutes(a, b):
    return (b - a).total_seconds() / 60


def build(msgs, gap_h, burst_s=BURST_S):
    """Devuelve lista de turnos; cada turno = dict con índices de mensajes y sesión."""
    sess = 0
    turns = []
    for i, m in enumerate(msgs):
        if i > 0 and minutes(msgs[i-1]['ts'], m['ts']) > gap_h * 60:
            sess += 1
        if turns and turns[-1]['who'] == m['who'] and turns[-1]['sess'] == sess:
            turns[-1]['idx'].append(i)
        else:
            turns.append({'who': m['who'], 'sess': sess, 'idx': [i]})
    for t in turns:
        ts = [msgs[i]['ts'] for i in t['idx']]
        gaps = [minutes(a, b) for a, b in zip(ts, ts[1:])]
        t['first'], t['last'] = ts[0], ts[-1]
        t['elapsed'] = minutes(ts[0], ts[-1])
        t['n'] = len(ts)
        t['silences'] = gaps
        t['bursts'] = 1 + sum(1 for g in gaps if g * 60 > burst_s)
        t['in_burst_min'] = sum(g for g in gaps if g * 60 <= burst_s)
    return turns


def latencies(msgs, turns, gap_h):
    res = []
    for t in turns:
        j = t['idx'][-1] + 1
        if j >= len(msgs):
            res.append((t, 'sin_respuesta_observada', None, None, None)); continue
        nxt = msgs[j]
        if nxt['who'] == t['who']:
            res.append((t, 'sin_intervencion_previa_a_su_nuevo_turno', None, None, None)); continue
        lat = minutes(t['last'], nxt['ts'])
        res.append((t, 'con_intervencion', lat, nxt['who'], lat <= gap_h * 60))
    return res


def med(xs):
    return st.median(xs) if xs else None


def summary(msgs, gap_h):
    turns = build(msgs, gap_h)
    L = latencies(msgs, turns, gap_h)
    out = {'sesiones': turns[-1]['sess'] + 1, 'turnos': len(turns), 'por_autor': {}}
    for who in sorted({m['who'] for m in msgs}):
        mine = [x for x in L if x[3] == who]
        allv = [x[2] for x in mine]
        win = [x[2] for x in mine if x[4]]
        btw = [x[2] for x in mine if not x[4]]
        out['por_autor'][who] = {
            'n': len(allv), 'mediana_general': med(allv),
            'n_dentro': len(win), 'mediana_dentro': med(win),
            'n_entre': len(btw), 'mediana_entre': med(btw),
            'prop_dentro': round(len(win) / len(allv), 3) if allv else None,
        }
    allL = [x for x in L if x[1] == 'con_intervencion']
    a = [x[2] for x in allL]; w = [x[2] for x in allL if x[4]]; b = [x[2] for x in allL if not x[4]]
    out['agregado'] = {'n': len(a), 'mediana_general': med(a), 'n_dentro': len(w), 'mediana_dentro': med(w),
                       'n_entre': len(b), 'mediana_entre': med(b), 'prop_dentro': round(len(w) / len(a), 3) if a else None}
    states = {}
    for t, s, *_ in L:
        states.setdefault(s, []).append(t['first'].strftime('%d/%m %H:%M') + ' ' + t['who'])
    out['estados'] = states
    out['turnos_por_autor'] = {who: sum(1 for t in turns if t['who'] == who) for who in sorted({m['who'] for m in msgs})}
    out['turnos_resumen'] = turns
    out['L'] = L
    return out


def burst_sensitivity(msgs, gap_h=DEFAULT_GAP_H):
    """Ráfagas totales y turnos con más de una ráfaga para cada separación de ráfaga de la rejilla."""
    res = {}
    for bs in BURST_GRID_S:
        turns = build(msgs, gap_h, bs)
        res[bs] = (sum(t['bursts'] for t in turns), sum(1 for t in turns if t['bursts'] > 1), len(turns))
    return res


def fmt(x):
    return '-' if x is None else (f'{x:.3f}'.rstrip('0').rstrip('.') if isinstance(x, float) else str(x))


if __name__ == '__main__':
    try:
        msgs = load(sys.argv[1])
    except ReferenceLoadError as e:
        sys.exit('RECHAZADO: %s' % e)
    print(params_block())
    print('mensajes:', len(msgs))
    for g in SESSION_GAPS_H:
        s = summary(msgs, g)
        tp = s['turnos_por_autor']; tt = sum(tp.values())
        print(f"\n== hueco {g} h: sesiones={s['sesiones']} turnos={s['turnos']} por autor={tp} "
              f"(% {({k: round(100 * v / tt, 1) for k, v in tp.items()})})")
        for who, d in s['por_autor'].items():
            print(' ', who, {k: fmt(v) for k, v in d.items()})
        print('  AGREGADO', {k: fmt(v) for k, v in s['agregado'].items()})
        for k, v in s['estados'].items():
            if k != 'con_intervencion':
                print('  estado', k, len(v), v)
    print('\n== sensibilidad de la separación de ráfaga (hueco de sesión %s h): ráfagas totales / turnos con >1 ráfaga / turnos'
          % DEFAULT_GAP_H)
    for bs, (nb, nm, nt) in burst_sensitivity(msgs).items():
        print(f'  ráfaga <= {bs} s: {nb} ráfagas, {nm} turnos con más de una ráfaga, {nt} turnos')
    print('  (la separación de ráfaga no afecta a las latencias ni a los estados de turno: solo a las ráfagas)')
    if len(sys.argv) > 2:
        s = summary(msgs, DEFAULT_GAP_H)
        print('\n  -- turnos (6 h, ráfaga %s s) con más de un mensaje:' % BURST_S)
        for t in s['turnos_resumen']:
            if t['n'] > 1:
                print('   ', t['who'], t['first'].strftime('%d/%m %H:%M'), '->', t['last'].strftime('%H:%M'),
                      'elapsed', fmt(t['elapsed']), 'msgs', t['n'], 'ráfagas', t['bursts'],
                      'silencios', [fmt(x) for x in t['silences']], 'en_ráfagas', fmt(t['in_burst_min']))
        print('  -- latencias por turno (6 h):')
        for t, state, lat, who, within in s['L']:
            print('   ', t['who'], t['first'].strftime('%d/%m %H:%M'), '->', t['last'].strftime('%d/%m %H:%M'),
                  state, fmt(lat), who or '', 'dentro' if within else ('entre' if within is False else ''))

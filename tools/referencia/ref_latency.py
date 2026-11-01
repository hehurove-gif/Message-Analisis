"""Cálculo de referencia INDEPENDIENTE (no es el código del sistema) de:
turnos, ráfagas, registro por turno y latencia hasta la siguiente intervención.
Implementa literalmente docs/definiciones_operativas.md v0.3."""
import re, sys, statistics as st
from datetime import datetime

LINE = re.compile(r'^(\d{2}/\d{2}/\d{4}) (\d{2}:\d{2}) - ([^:]+): (.*)$')
BURST_S = 300

def load(path):
    out = []
    for raw in open(path, encoding='utf-8').read().split('\n'):
        m = LINE.match(raw)
        if m:
            out.append({'ts': datetime.strptime(m[1] + ' ' + m[2], '%d/%m/%Y %H:%M'), 'who': m[3], 'txt': m[4]})
        elif raw.strip() and out and not re.match(r'^\d{2}/\d{2}/\d{4} ', raw):
            out[-1]['txt'] += '\n' + raw
    return out

def minutes(a, b):
    return (b - a).total_seconds() / 60

def build(msgs, gap_h):
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
        t['bursts'] = 1 + sum(1 for g in gaps if g * 60 > BURST_S)
        t['in_burst_min'] = sum(g for g in gaps if g * 60 <= BURST_S)
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
    allL=[x for x in L if x[1]=='con_intervencion']
    a=[x[2] for x in allL]; w=[x[2] for x in allL if x[4]]; b=[x[2] for x in allL if not x[4]]
    out['agregado']={'n':len(a),'mediana_general':med(a),'n_dentro':len(w),'mediana_dentro':med(w),'n_entre':len(b),'mediana_entre':med(b),'prop_dentro':round(len(w)/len(a),3) if a else None}
    states = {}
    for t, s, *_ in L:
        states.setdefault(s, []).append(t['first'].strftime('%d/%m %H:%M') + ' ' + t['who'])
    out['estados'] = states
    out['turnos_resumen'] = turns
    out['L'] = L
    return out

def fmt(x):
    return '-' if x is None else (f'{x:.3f}'.rstrip('0').rstrip('.') if isinstance(x, float) else str(x))

if __name__ == '__main__':
    msgs = load(sys.argv[1])
    print('mensajes:', len(msgs))
    for g in (2, 6, 12):
        s = summary(msgs, g)
        print(f"\n== hueco {g} h: sesiones={s['sesiones']} turnos={s['turnos']}")
        for who, d in s['por_autor'].items():
            print(' ', who, {k: fmt(v) for k, v in d.items()})
        print('  AGREGADO', {k: fmt(v) for k, v in s['agregado'].items()})
        for k, v in s['estados'].items():
            if k != 'con_intervencion':
                print('  estado', k, len(v), v)
        if g == 6 and len(sys.argv) > 2:
            print('  -- turnos (6 h) con más de un mensaje:')
            for t in s['turnos_resumen']:
                if t['n'] > 1:
                    print('   ', t['who'], t['first'].strftime('%d/%m %H:%M'), '->', t['last'].strftime('%H:%M'),
                          'elapsed', fmt(t['elapsed']), 'msgs', t['n'], 'ráfagas', t['bursts'],
                          'silencios', [fmt(x) for x in t['silences']], 'en_ráfagas', fmt(t['in_burst_min']))
            print('  -- latencias por turno (6 h):')
            for t, state, lat, who, within in s['L']:
                print('   ', t['who'], t['first'].strftime('%d/%m %H:%M'), '->', t['last'].strftime('%d/%m %H:%M'),
                      state, fmt(lat), who or '', 'dentro' if within else ('entre' if within is False else ''))

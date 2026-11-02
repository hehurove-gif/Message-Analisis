"""Cálculo de referencia INDEPENDIENTE (no es el código del sistema) de:
balance de participación (cada unidad por separado), frecuencia de eventos candidatos,
sensibilidad de la RECURRENCIA, sensibilidad de los INDICADORES (variantes de inclusión)
y latencia del interlocutor según el tipo de turno.

Aplica las secciones 1 a 5 de docs/definiciones_operativas.md. No fija un número de
versión: los parámetros usados se imprimen siempre en el bloque PARAMETROS.

Las pruebas de sensibilidad se separan por familia y NO se cruzan entre sí:
  - recurrencia: mínimo de eventos x mínimo de periodos x granularidad (semana, mes)
  - segmentación: huecos de sesión y ráfagas (ver ref_latency.py)
  - indicadores: variantes de inclusión de candidatos (P, S1, S2)
"Robusto" solo se aplica a lo efectivamente probado y las configuraciones que el chat no
permite probar (menos periodos disponibles que el mínimo) se marcan "no evaluable".
La especificidad provisional del CSV se cuenta aparte: NO pondera ni altera ninguna métrica.
Robustez ante parámetros NO equivale a validez científica.

Uso: python3 -I tools/referencia/ref_indicadores.py CHAT.txt ETIQUETAS.csv
"""
import csv, os, sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_latency as R

# ---- Parámetros (espejo de config.yaml; los cambios se hacen en AMBOS sitios) ----
MIN_EVENTS_GRID = (2, 3, 4, 5)         # robustness.recurrence.min_events
MIN_PERIODS_GRID = (1, 2, 3)           # robustness.recurrence.min_distinct_periods
MIN_TURNS_LATENCY = 20                 # data_sufficiency.min_turns_for_response_time
VARIANTES = {
    'P  (principal: indicador_candidato)': lambda r: r['clase_evento'] == 'indicador_candidato',
    'S1 (P + calidez_no_especifica)': lambda r: r['clase_evento'] in ('indicador_candidato', 'calidez_no_especifica'),
    'S2 (P sin candidatos ambiguo=si)': lambda r: r['clase_evento'] == 'indicador_candidato' and r.get('ambiguo') != 'si',
}


def week(d): return d.isocalendar()[:2]          # semana ISO: lunes a domingo
def month(d): return (d.year, d.month)           # mes calendario
GRANULARIDADES = {'semana': week, 'mes': month}
PLURAL = {'semana': 'semanas', 'mes': 'meses'}
SINGULAR = {'semana': 'semana', 'mes': 'mes'}


def params_block():
    return ('PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; '
            'evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos %s x min_periodos %s; '
            'una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; '
            'variantes: %s; columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, '
            'categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; '
            'mínimo de turnos para comparar latencias: %d'
            % (list(MIN_EVENTS_GRID), list(MIN_PERIODS_GRID), '; '.join(VARIANTES), MIN_TURNS_LATENCY))


def load_labels(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            r['ts'] = datetime.strptime(r['fecha_hora'], '%Y-%m-%d %H:%M')
            rows.append(r)
    return rows


def window_periods(msgs, key):
    d0, d1 = msgs[0]['ts'].date(), msgs[-1]['ts'].date()
    return {key(d0 + timedelta(days=i)) for i in range((d1 - d0).days + 1)}


def words_and_days(msgs):
    words, days = Counter(), defaultdict(set)
    for m in msgs:
        days[m['who']].add(m['ts'].date()); days['_todos'].add(m['ts'].date())
        if m['txt'].strip() != '<Multimedia omitido>':
            words[m['who']] += len(m['txt'].split())
    span = (msgs[-1]['ts'].date() - msgs[0]['ts'].date()).days + 1
    return words, days, span


def shares(d):
    t = sum(d.values())
    return {k: f'{v} ({100 * v / t:.1f} %)' for k, v in sorted(d.items())}


def grid_status(event_dates, key, available):
    """Devuelve (cumple, no_cumple, no_evaluable, detalle_no_evaluable) en la rejilla de recurrencia."""
    periods = {key(d) for d in event_dates}
    c = n = e = 0; ne_detail = set()
    for me in MIN_EVENTS_GRID:
        for mp in MIN_PERIODS_GRID:
            if len(available) < mp:
                e += 1; ne_detail.add(mp)
            elif len(event_dates) >= me and len(periods) >= mp:
                c += 1
            else:
                n += 1
    return c, n, e, sorted(ne_detail), len(periods)


def main(chat, labels):
    msgs = R.load(chat); L = load_labels(labels)
    print(R.params_block()); print(params_block())
    authors = sorted({m['who'] for m in msgs})

    # ---- Balance de participación: cada unidad por separado, sin índice compuesto ----
    print('\n== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)')
    print('  mensajes:', shares(Counter(m['who'] for m in msgs)))
    w, days, span = words_and_days(msgs)
    print('  palabras (mensajes de texto; separadas por espacios):', shares(w))
    for g in R.SESSION_GAPS_H:
        s = R.summary(msgs, g)
        print(f'  turnos con hueco {g} h:', shares(s['turnos_por_autor']))
    print('  días con mensajes (frecuencia observable): %d de %d; por persona %s; mensajes por día activo %.2f'
          % (len(days['_todos']), span, {k: len(v) for k, v in days.items() if k != '_todos'}, len(msgs) / len(days['_todos'])))

    # ---- Familia RECURRENCIA, por variante de indicadores (las variantes NO se cruzan con la segmentación) ----
    print('\n== SENSIBILIDAD DE LA RECURRENCIA (rejilla %d x %d por granularidad)' % (len(MIN_EVENTS_GRID), len(MIN_PERIODS_GRID)))
    avail = {g: window_periods(msgs, k) for g, k in GRANULARIDADES.items()}
    print('  periodos disponibles en la ventana del chat:', {g: len(v) for g, v in avail.items()})
    for vname, fn in VARIANTES.items():
        rows = [r for r in L if fn(r)]
        if not rows:
            continue
        print(f'  -- variante {vname}: eventos por autor {dict(Counter(r["autor"] for r in rows))}')
        for a in sorted({r['autor'] for r in rows}):
            ev = [r['ts'].date() for r in rows if r['autor'] == a]
            per_week = Counter(week(d) for d in ev)
            print(f'     {a}: por semana ISO', {f'S{s}': c for (y, s), c in sorted(per_week.items())})
            for g, k in GRANULARIDADES.items():
                c, n, e, ne, p = grid_status(ev, k, avail[g])
                nota = f'; no evaluable: min_periodos {ne} (la ventana solo tiene {len(avail[g])} {SINGULAR[g] if len(avail[g]) == 1 else PLURAL[g]})' if e else ''
                print(f'        {g}: {len(ev)} eventos en {p} periodos -> cumple {c}, no cumple {n}, no evaluable {e} (de 12){nota}')

    # ---- Familia INDICADORES: especificidad como dimensión separada, categorías y latencia por tipo de turno ----
    if L and 'categoria_respuesta' in L[0]:
        print('\n== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)')
        for vname, fn in VARIANTES.items():
            rows = [r for r in L if fn(r)]
            print(f'  {vname}: frecuencia={len(rows)}; especificidad provisional (anotación cualitativa)='
                  f'{dict(Counter(r["especificidad_provisional"] for r in rows))}')
        pre = [r for r in L if VARIANTES['P  (principal: indicador_candidato)'](r)]
        print('  categorías de respuesta (P):', dict(Counter(r['categoria_respuesta'] for r in pre)))
        print('  secundarias (P):', dict(Counter(r['categoria_secundaria'] for r in pre if r['categoria_secundaria'])))
        decl = {(r['ts'], r['autor']) for r in L if r['clase_evento'] == 'declaracion_explicita'}
        autor = pre[0]['autor']
        print('\n== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO DE %s (mínimo para comparar: %d turnos)' % (autor, MIN_TURNS_LATENCY))
        for vname, fn in VARIANTES.items():
            cand = {(r['ts'], r['autor']) for r in L if fn(r)}
            for gap in R.SESSION_GAPS_H:
                if gap != R.DEFAULT_GAP_H and not vname.startswith('P '):
                    continue
                turns = R.build(msgs, gap); Ls = R.latencies(msgs, turns, gap)
                cat = {'candidatos': [], 'declaracion': [], 'resto': []}; sin_prev = 0
                for t, state, lat, who2, within in Ls:
                    if t['who'] != autor: continue
                    keys = {(msgs[i]['ts'], msgs[i]['who']) for i in t['idx']}
                    k = 'candidatos' if keys & cand else ('declaracion' if keys & decl else 'resto')
                    if state == 'con_intervencion': cat[k].append((lat, within))
                    elif k == 'candidatos': sin_prev += 1
                print(f'  {vname} | hueco {gap} h | candidatos sin intervención previa: {sin_prev}')
                for k, v in cat.items():
                    a = [x for x, _ in v]; wn = [x for x, y in v if y]; bt = [x for x, y in v if not y]
                    suf = 'suficiente' if len(a) >= MIN_TURNS_LATENCY else 'insuficiente'
                    print(f'     {k:12} n={len(a):2} ({suf}) general={R.fmt(R.med(a))} dentro={R.fmt(R.med(wn))}(n={len(wn)}) entre={R.fmt(R.med(bt))}(n={len(bt)})')
                if gap == R.DEFAULT_GAP_H:
                    print('        latencias candidatos:', sorted(round(x) for x, _ in cat['candidatos']))
                    print('        latencias resto     :', sorted(round(x) for x, _ in cat['resto']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

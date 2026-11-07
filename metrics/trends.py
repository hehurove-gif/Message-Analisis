"""Evolución temporal (Fase 4, provisional): las métricas existentes por periodo (mes; semana ISO como opción).

Series por periodo (todas se refieren a A; la de B es el complemento o su propia columna):
  mensajes_A          proporción de mensajes de persona escritos por A
  palabras_A          proporción de palabras sustantivas de A
  desarrollados_A     proporción de A entre los turnos desarrollados (umbral de turn_content)
  inicia_dia_A        proporción de días lógicos del periodo que abre A
  cierra_A            proporción de sesiones (sin la última del chat) cuyo último turno sin respuesta es de A
                      (necesita >= min_events sesiones en el periodo)
  multimedia_A/B      proporción de los mensajes de cada uno que son multimedia omitida
  dias_activos        días lógicos con mensajes / días del periodo (frecuencia de contacto, §7)
  latencia_A/B        mediana de minutos que tarda cada uno dentro de la sesión (latencia <= hueco)
El periodo de un turno o de una latencia es el de su primer mensaje / de la intervención. Un periodo con menos de
`data_sufficiency.min_events_per_period_for_trend` mensajes (o latencias, para su serie) queda `None`.

CAMBIO SOSTENIDO (config `temporal`): línea base = mediana de los primeros `rolling_window_periods` periodos con
datos; mediana móvil de la misma ventana. Hay cambio cuando la mediana móvil se aleja de la base más que el umbral
durante `sustained_change_min_periods` periodos seguidos. Umbral: proporciones -> diferencia ABSOLUTA
`share_deviation_abs`; latencias -> diferencia RELATIVA `deviation_ratio` Y al menos `latency_min_change_minutes` (con resolución
de minuto y medianas de 0–2 min, pasar de 0 a 1 no es un cambio; con base 0 solo cuenta la diferencia absoluta). Valores experimentales.
Primer y último periodo con < `edge_period_min_active_days` de días activos = `parcial`: se muestran, no cuentan.
`desde` = primer periodo en que la MEDIANA MÓVIL cruza el umbral: va con retraso (≈ media ventana) respecto
al cambio real; mira la tabla de periodos para ubicarlo. Describe cuándo cambia una cifra; no explica por qué ni interpreta interés."""
import statistics
from collections import defaultdict
from datetime import date, datetime, timedelta

import yaml

from metrics.latency import turn_latencies
from metrics.text_units import DEFAULT_ACKS, substantive_words
from metrics.turn_content import classify_turn
from segmentation.sessions import build_sessions
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns

SHARE_SERIES = ('mensajes_A', 'palabras_A', 'desarrollados_A', 'inicia_dia_A', 'cierra_A', 'dias_activos',
                'multimedia_A', 'multimedia_B')
LAT_SERIES = ('latencia_A', 'latencia_B')


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    t, tc = raw.get('temporal', {}), raw.get('turn_content', {})
    return {'gran': t.get('default_granularity', 'month'), 'win': t.get('rolling_window_periods', 4),
            'n_seq': t.get('sustained_change_min_periods', 3), 'ratio': t.get('deviation_ratio', 0.5),
            'abs': t.get('share_deviation_abs', 0.15), 'lat_min': t.get('latency_min_change_minutes', 5),
            'edge_min': t.get('edge_period_min_active_days', 0.5),
            'min_ev': raw.get('data_sufficiency', {}).get('min_events_per_period_for_trend', 5),
            'day_start': raw.get('habits', {}).get('day_start_hour', 5),
            'acks': tc.get('acknowledgements', DEFAULT_ACKS), 'dev': tc.get('developed_min_words', 15),
            'gap': raw.get('segmentation', {}).get('session_gap_hours', 6)}


def period_key(day, gran):
    if gran == 'week':
        y, w, _ = day.isocalendar()
        return f'{y}-W{w:02d}'
    return f'{day.year}-{day.month:02d}'


def _period_days(key, gran):
    if gran == 'week':
        return 7
    y, m = map(int, key.split('-'))
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return (nxt - date(y, m, 1)).days


def _all_periods(first, last, gran):
    keys, d = [], first
    while d <= last:
        k = period_key(d, gran)
        if not keys or keys[-1] != k:
            keys.append(k)
        d += timedelta(days=1)
    return keys


def _share(num, den, min_ev, n):
    return round(num / den, 3) if den and n >= min_ev else None


def sustained_change(values, win, n_seq, thr, relative, min_abs=0):
    """{'detectado', 'desde', 'direccion', 'base'} sobre una lista de valores (None = sin datos)."""
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    if len(pts) < win + n_seq:
        return {'detectado': None, 'motivo': 'periodos_insuficientes'}
    base = statistics.median(v for _, v in pts[:win])
    run, start, sign = 0, None, 0
    for j in range(win, len(pts)):
        roll = statistics.median(v for _, v in pts[j - win + 1:j + 1])
        dev = (roll - base) / base if relative and base else roll - base
        s = (dev > thr) - (dev < -thr)
        if relative and abs(roll - base) < min_abs:   # base 0 o cambios de 1-2 min: ruido de la resolución por minuto
            s = 0
        if relative and not base and abs(roll - base) >= min_abs:
            s = 1 if roll > base else -1
        if s and s == sign:
            run += 1
        elif s:
            run, start, sign = 1, pts[j][0], s
        else:
            run, sign = 0, 0
        if run >= n_seq:
            return {'detectado': True, 'desde_indice': start, 'direccion': 'sube' if sign > 0 else 'baja',
                    'base': round(base, 3)}
    return {'detectado': False, 'base': round(base, 3)}


def trends(messages, granularity=None, cfg_path=None):
    c = _cfg(cfg_path)
    gran = granularity or c['gran']
    people = [m for m in messages if m.tipo in PERSON_TYPES and m.timestamp_local]
    names = sorted({m.participante for m in people})
    if len(names) != 2:
        raise ValueError('la evolución espera exactamente 2 participantes')
    a, b = names
    lday = lambda ts: (datetime.fromisoformat(ts) - timedelta(hours=c['day_start'])).date()   # noqa: E731
    msgs, words, days, opener = defaultdict(lambda: defaultdict(int)), defaultdict(lambda: defaultdict(int)), \
        defaultdict(set), defaultdict(lambda: defaultdict(int))
    media = defaultdict(lambda: defaultdict(int))
    first_of_day = {}
    for m in people:
        d = lday(m.timestamp_local)
        k = period_key(d, gran)
        msgs[k][m.participante] += 1
        media[k][m.participante] += m.tipo == 'media'
        if m.tipo == 'texto':
            words[k][m.participante] += len(substantive_words(m.texto, c['acks']))
        days[k].add(d)
        first_of_day.setdefault(d, m.participante)
    for d, who in first_of_day.items():
        opener[period_key(d, gran)][who] += 1
    pos = {m.seq: i for i, m in enumerate(people)}
    dev = defaultdict(lambda: defaultdict(int))
    for t in build_turns(people, session_gap_hours=c['gap']):
        ms = people[pos[t.seq_primero]:pos[t.seq_ultimo] + 1]
        if classify_turn(ms, c['acks'], c['dev'])[0] == 'desarrollado':
            dev[period_key(lday(t.primer_ts), gran)][t.participante] += 1
    closes = defaultdict(lambda: defaultdict(int))
    for se in build_sessions(build_turns(people, session_gap_hours=c['gap'])):
        if not se.es_ultima:
            closes[period_key(lday(se.ultimo_ts), gran)][se.ultimo_mensaje] += 1
    lat = defaultdict(lambda: defaultdict(list))
    seq_ts = {m.seq: m.timestamp_local for m in people}
    turns = {t.index: t for t in build_turns(people, session_gap_hours=c['gap'])}
    for r in turn_latencies(messages, c['gap'], cfg_path):
        if r['estado'] == 'con_intervencion' and r['dentro_de_sesion']:
            t = turns[r['turno']]
            k = period_key(lday(seq_ts[t.seq_ultimo]), gran)
            lat[k][r['interviene']].append(r['latencia_minutos'])

    keys = _all_periods(lday(people[0].timestamp_local), lday(people[-1].timestamp_local), gran)
    rows = []
    for k in keys:
        n = sum(msgs[k].values())
        rows.append({'periodo': k, 'mensajes': n,
                     'mensajes_A': _share(msgs[k][a], n, c['min_ev'], n),
                     'palabras_A': _share(words[k][a], sum(words[k].values()), c['min_ev'], n),
                     'desarrollados_A': _share(dev[k][a], sum(dev[k].values()), c['min_ev'], n),
                     'inicia_dia_A': _share(opener[k][a], len(days[k]), c['min_ev'], n),
                     'cierra_A': _share(closes[k][a], sum(closes[k].values()), c['min_ev'], sum(closes[k].values())),
                     **{f'multimedia_{x}': _share(media[k][p], msgs[k][p], c['min_ev'], msgs[k][p])
                        for x, p in (('A', a), ('B', b))},
                     'dias_activos': round(len(days[k]) / _period_days(k, gran), 3),
                     **{f'latencia_{p}': (statistics.median(lat[k][p]) if len(lat[k][p]) >= c['min_ev'] else None)
                        for p in (a, b)}})
    # Primer/último periodo incompletos (el chat empieza o termina a mitad): se muestran, pero no entran en la base
    # ni en la detección de cambios, porque sus proporciones salen de pocos días.
    for r in rows:
        r['parcial'] = False
    for r in (rows[0], rows[-1]):
        if r['dias_activos'] < c['edge_min']:
            r['parcial'] = True
    usable = lambda r, s: None if r['parcial'] else r[s]   # noqa: E731
    changes = {}
    for s in SHARE_SERIES + LAT_SERIES:
        ch = sustained_change([usable(r, s) for r in rows], c['win'], c['n_seq'],
                              c['ratio'] if s in LAT_SERIES else c['abs'], s in LAT_SERIES,
                              c['lat_min'] if s in LAT_SERIES else 0)
        if ch.get('detectado'):
            ch['desde'] = rows[ch.pop('desde_indice')]['periodo']
        changes[s] = ch
    return {'granularidad': gran, 'periodos': rows, 'cambios_sostenidos': changes,
            'parametros': {k: c[k] for k in ('win', 'n_seq', 'ratio', 'abs', 'lat_min', 'min_ev', 'gap')},
            'nota': 'describe cuándo cambia una cifra; no explica por qué ni interpreta interés'}

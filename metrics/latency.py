"""Latencia hasta la siguiente intervención del interlocutor (Fase 3.2; definiciones v0.6 §3).

Para cada turno de X: el mensaje inmediatamente posterior del chat, si es de Y, es su "siguiente intervención".
Latencia = tiempo entre el ÚLTIMO mensaje del turno de X y esa intervención; se asigna a quien interviene (Y).
Sin ventana máxima y sin depender de la sesión. Que Y escriba después NO demuestra que responda a lo anterior
(respuesta semántica = otra cosa, Fase 6). Estados de cada turno, mutuamente excluyentes:
  con_intervencion                             hay latencia
  sin_intervencion_previa_a_su_nuevo_turno     el siguiente mensaje es del MISMO autor (otra sesión): sin latencia,
                                               fuera de las medianas, no es indiferencia ni rechazo; depende del hueco
  sin_respuesta_observada                      no hay mensaje posterior (fin de los datos): límite de los datos
  con_intervencion_fuera_de_orden              (extra) el timestamp de la intervención es ANTERIOR al del turno: no se
                                               reordena ni se inventa una latencia; se cuenta aparte, fuera de las medianas
Se reportan SIEMPRE: mediana general, dentro de sesión (<= hueco), entre sesiones (> hueco) y su proporción;
además los percentiles de config (general y dentro de sesión). Cada cifra lleva su n y la suficiencia de datos;
también por subgrupo (dentro/entre), porque una "mediana" de 1 o 2 latencias no describe nada.

RESOLUCIÓN: WhatsApp exporta con precisión de minuto, así que una latencia de 0 significa "en el mismo minuto"
(no instantánea) y las medianas son enteras. Por eso se agrega `distribucion`: proporción acumulada de latencias
<= cada corte de `latency.buckets_minutes` (config). Es descriptiva: no distingue rapidez de interés.

LECTURA de `por_participante_que_interviene`: la latencia de X es cuánto tarda X en escribir después de que
termina un turno del otro. A/B son etiquetas por orden de primera aparición (ver metrics/participants.py)."""
import statistics
from datetime import datetime

import yaml

from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns

STATES = ('con_intervencion', 'sin_intervencion_previa_a_su_nuevo_turno', 'sin_respuesta_observada',
          'con_intervencion_fuera_de_orden')


DEFAULT_BUCKETS = [0, 1, 5, 15, 60]


def _raw(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _cfg(path=None):
    raw = _raw(path)
    return (raw.get('latency', {}).get('percentiles', [75, 90]),
            raw.get('data_sufficiency', {}).get('min_turns_for_response_time', 20),
            raw.get('segmentation', {}).get('session_gap_hours', 6))


def _buckets(path=None):
    return sorted(_raw(path).get('latency', {}).get('buckets_minutes', DEFAULT_BUCKETS))


def _bucket_label(b):
    return 'mismo_minuto' if b == 0 else f'hasta_{b:g}_min'


def distribution(values, buckets):
    """Proporción ACUMULADA de latencias <= cada corte (minutos); None sin datos."""
    if not values:
        return {_bucket_label(b): None for b in buckets}
    return {_bucket_label(b): round(sum(1 for v in values if v <= b) / len(values), 3) for b in buckets}


def _suf(n, min_turns):
    return 'suficiente' if n >= min_turns else 'insuficiente'


def _resolution(messages):
    precs = {m.precision for m in messages if m.tipo in PERSON_TYPES}
    return 'segundo' if precs == {'segundo'} else 'minuto'


def _round(x):
    return None if x is None else round(x, 2)


def percentile(values, p):
    """Interpolación lineal entre rangos (método 'inclusive'); None si no hay datos."""
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def _minutes(a, b):
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60


def turn_latencies(messages, session_gap_hours=None, cfg_path=None):
    """Lista de dicts por turno: turno, estado, latencia (min), interviene, dentro_de_sesion."""
    _p, _m, default_gap = _cfg(cfg_path)
    gap_h = default_gap if session_gap_hours is None else session_gap_hours
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    pos = {m.seq: i for i, m in enumerate(people)}
    out = []
    for t in build_turns(people, session_gap_hours=gap_h):
        j = pos[t.seq_ultimo] + 1
        row = {'turno': t.index, 'participante': t.participante, 'latencia_minutos': None, 'interviene': None,
               'dentro_de_sesion': None}
        if j >= len(people):
            row['estado'] = 'sin_respuesta_observada'
        elif people[j].participante == t.participante:
            row['estado'] = 'sin_intervencion_previa_a_su_nuevo_turno'
        else:
            lat = _minutes(t.ultimo_ts, people[j].timestamp_local)
            row['interviene'] = people[j].participante
            if lat < 0:
                row['estado'] = 'con_intervencion_fuera_de_orden'
            else:
                row.update(estado='con_intervencion', latencia_minutos=lat, dentro_de_sesion=lat <= gap_h * 60)
        out.append(row)
    return out


def _stats(rows, percentiles, min_turns=20, buckets=None):
    allv = [r['latencia_minutos'] for r in rows]
    win = [r['latencia_minutos'] for r in rows if r['dentro_de_sesion']]
    btw = [r['latencia_minutos'] for r in rows if r['dentro_de_sesion'] is False]
    med = lambda xs: statistics.median(xs) if xs else None   # noqa: E731
    return {'n': len(allv), 'mediana_general': med(allv),
            **{f'p{p}_general': _round(percentile(allv, p)) for p in percentiles},
            'n_dentro': len(win), 'mediana_dentro': med(win),
            **{f'p{p}_dentro': _round(percentile(win, p)) for p in percentiles},
            'suficiencia_dentro': _suf(len(win), min_turns),
            'n_entre': len(btw), 'mediana_entre': med(btw), 'suficiencia_entre': _suf(len(btw), min_turns),
            'proporcion_dentro': round(len(win) / len(allv), 3) if allv else None,
            'distribucion': distribution(allv, buckets if buckets is not None else DEFAULT_BUCKETS)}


def latency_summary(messages, session_gap_hours=None, cfg_path=None):
    percentiles, min_turns, default_gap = _cfg(cfg_path)
    buckets = _buckets(cfg_path)
    gap_h = default_gap if session_gap_hours is None else session_gap_hours
    rows = turn_latencies(messages, gap_h, cfg_path)
    names = sorted({r['participante'] for r in rows})
    ok = [r for r in rows if r['estado'] == 'con_intervencion']
    por = {}
    for n in names:                                  # la latencia se asigna a quien interviene
        mine = [r for r in ok if r['interviene'] == n]
        por[n] = {**_stats(mine, percentiles, min_turns, buckets), 'suficiencia_de_datos': _suf(len(mine), min_turns)}
    resolution = _resolution(messages)
    return {'hueco_horas': gap_h, 'unidad': 'minutos', 'resolucion': resolution, 'n_turnos': len(rows),
            'estados': {s: sum(1 for r in rows if r['estado'] == s) for s in STATES},
            'agregado': _stats(ok, percentiles, min_turns, buckets), 'por_participante_que_interviene': por,
            'nota': ('latencia de X = minutos que tarda X en escribir tras el turno del otro; '
                     + ('0 = en el mismo minuto (la exportación no trae segundos); ' if resolution == 'minuto' else '')
                     + 'no prueba respuesta a lo anterior ni interés')}


def latency_sensitivity(messages, gaps=None, cfg_path=None):
    """El resumen con varios huecos (los estados dependen del hueco)."""
    cfg_gaps = _raw(cfg_path).get('segmentation', {}).get('sensitivity_session_gap_hours', [2, 6, 12])
    return {g: latency_summary(messages, g, cfg_path) for g in (gaps or cfg_gaps)}


def latency_from_result(result, **kwargs):
    if not result.analysis_enabled:
        raise ValueError('el análisis no está habilitado: ' + ', '.join(result.pending_requirements or ['importación no aceptada']))
    return latency_sensitivity(result.messages, **kwargs)

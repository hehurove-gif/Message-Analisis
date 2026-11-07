"""Ritmo de la conversación (Fase 3, provisional): sesiones, continuidad de días y fragmentación.

SESIONES (hueco de config): duración transcurrida (mediana, p90; no es actividad efectiva), turnos y mensajes por
sesión, y quién deja el último turno sin respuesta antes de que la sesión se corte ("cierra"; excluye la última del
chat, que es fin de los datos). Cerrar no significa terminar la conversación a propósito.
CONTINUIDAD (días lógicos, `habits.day_start_hour`): días activos / días del rango, racha más larga de días
seguidos con mensajes, racha al final de los datos, pausa más larga y días en que
escribe SOLO uno (sin ningún mensaje del otro ese día lógico; no implica que lo ignore: puede no haber leído) (días sin mensajes entre dos días activos).
FRAGMENTACIÓN por participante: mensajes por turno y mensajes por ráfaga (`burst_max_gap_seconds`): quién parte lo
que dice en varios mensajes cortos. Hábito de escritura (§9.3), no una actitud. Solo números."""
import statistics
from datetime import datetime, timedelta

import yaml

from metrics.latency import percentile
from segmentation.sessions import build_sessions
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return (raw.get('segmentation', {}).get('session_gap_hours', 6), raw.get('habits', {}).get('day_start_hour', 5),
            raw.get('data_sufficiency', {}).get('min_sessions_for_initiative', 10))


def _med(xs):
    return statistics.median(xs) if xs else None


def _r(x, n=1):
    return None if x is None else round(x, n)


def rhythm(messages, session_gap_hours=None, cfg_path=None):
    gap, day_start, min_sess = _cfg(cfg_path)
    gap = gap if session_gap_hours is None else session_gap_hours
    people = [m for m in messages if m.tipo in PERSON_TYPES and m.timestamp_local]
    names = sorted({m.participante for m in people})
    turns = build_turns(people, session_gap_hours=gap)
    sess = build_sessions(turns)
    dur = [s.duracion_minutos for s in sess]
    closes = {n: sum(1 for s in sess if not s.es_ultima and s.ultimo_mensaje == n) for n in names}
    n_close = sum(closes.values())

    who_by_day = {}
    for m in people:
        who_by_day.setdefault((datetime.fromisoformat(m.timestamp_local) - timedelta(hours=day_start)).date(),
                              set()).add(m.participante)
    days = sorted(who_by_day)
    solo = {n: sum(1 for w in who_by_day.values() if w == {n}) for n in names}
    span = (days[-1] - days[0]).days + 1 if days else 0
    best = run = 1 if days else 0
    pause = 0
    for a, b in zip(days, days[1:]):
        d = (b - a).days
        run = run + 1 if d == 1 else 1
        best, pause = max(best, run), max(pause, d - 1)

    frag = {}
    for n in names:
        mine = [t for t in turns if t.participante == n]
        mpt = [t.n_mensajes for t in mine]
        mpb = [t.n_mensajes / t.n_rafagas for t in mine]
        frag[n] = {'mensajes_por_turno_mediana': _med(mpt), 'mensajes_por_turno_p90': _r(percentile(mpt, 90)),
                   'proporcion_turnos_de_un_mensaje': round(sum(x == 1 for x in mpt) / len(mpt), 3) if mpt else None,
                   'mensajes_por_rafaga_media': round(sum(mpb) / len(mpb), 2) if mpb else None}
    return {'hueco_horas': gap,
            'sesiones': {'n': len(sess), 'duracion_minutos_mediana': _r(_med(dur)),
                         'duracion_minutos_p90': _r(percentile(dur, 90)),
                         'turnos_por_sesion_mediana': _med([s.n_turnos for s in sess]),
                         'mensajes_por_sesion_mediana': _med([s.n_mensajes for s in sess]),
                         'cierra': closes,
                         'proporcion_cierra': {n: (round(v / n_close, 3) if n_close else None) for n, v in closes.items()},
                         'suficiencia_de_datos': 'suficiente' if len(sess) >= min_sess else 'insuficiente'},
            'continuidad': {'dias_activos': len(days), 'dias_del_rango': span,
                            'proporcion_dias_activos': round(len(days) / span, 3) if span else None,
                            'racha_mas_larga_dias': best, 'racha_al_final_dias': run if days else 0,
                            'pausa_mas_larga_dias': pause,
                            'dias_ambos': sum(1 for w in who_by_day.values() if len(w) == 2),
                            'dias_solo_uno': solo},
            'fragmentacion': frag,
            'nota': 'duración transcurrida, no actividad; cerrar la sesión no implica intención; hábitos de escritura'}

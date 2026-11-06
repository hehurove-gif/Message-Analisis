"""Sesiones y eventos de sesión (Fase 2, paso 2; definiciones operativas v0.6, sección 2).

SESIÓN: criterio operativo (silencio > session_gap_hours corta). NO se asume que sea una separación real de
conversaciones. Se registran por separado, sin atribuir intención:
  - reanudación: autor del primer turno de una sesión (salvo la primera del chat, que es el inicio de los datos);
  - último mensaje de la sesión: autor de su último turno (salvo la última del chat, que es el fin de los datos).
La sensibilidad repite todo con varios huecos (2, 6 y 12 h) y marca si la conclusión es frágil. "robusto" aquí
solo significa estable ante ese parámetro: no es validez científica ni prueba de interés de nadie."""
import os
from dataclasses import dataclass
from datetime import datetime

import yaml

from .turns import DEFAULT_CONFIG_PATH, build_turns


@dataclass(frozen=True)
class Session:
    index: int
    primer_ts: str
    ultimo_ts: str
    n_mensajes: int
    n_turnos: int
    reanuda: str                       # participante del primer turno
    ultimo_mensaje: str                # participante del último turno
    es_primera: bool                   # inicio de los datos, no una reanudación
    es_ultima: bool                    # fin de los datos, no un cierre observado
    silencio_previo_minutos: float | None
    duracion_minutos: float            # transcurrida (no actividad efectiva)

    def __repr__(self):
        return f'Session(index={self.index}, n_turnos={self.n_turnos})'


def _minutes(a, b):
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60


def build_sessions(turns):
    """Tupla de Session a partir de los turnos (que ya llevan su índice de sesión)."""
    by = {}
    for t in turns:
        by.setdefault(t.sesion, []).append(t)
    keys = sorted(by)
    out, prev_last = [], None
    for pos, k in enumerate(keys):
        ts = by[k]
        first, last = ts[0].primer_ts, ts[-1].ultimo_ts
        out.append(Session(
            index=k, primer_ts=first, ultimo_ts=last, n_mensajes=sum(t.n_mensajes for t in ts), n_turnos=len(ts),
            reanuda=ts[0].participante, ultimo_mensaje=ts[-1].participante,
            es_primera=pos == 0, es_ultima=pos == len(keys) - 1,
            silencio_previo_minutos=None if prev_last is None else _minutes(prev_last, first),
            duracion_minutos=_minutes(first, last)))
        prev_last = last
    return tuple(out)


def _load_cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return (raw.get('segmentation', {}).get('sensitivity_session_gap_hours', [2, 6, 12]),
            raw.get('data_sufficiency', {}).get('min_sessions_for_initiative', 10))


def _leader(counts):
    (a, na), (b, nb) = sorted(counts.items())[:2]
    return 'empate' if na == nb else (a if na > nb else b)


def summarize(sessions, participantes):
    """Conteos de reanudaciones y últimos mensajes, sin interpretarlos."""
    rean = {p: sum(1 for s in sessions if not s.es_primera and s.reanuda == p) for p in participantes}
    ult = {p: sum(1 for s in sessions if not s.es_ultima and s.ultimo_mensaje == p) for p in participantes}
    return {'n_sesiones': len(sessions), 'reanudaciones': rean, 'ultimos_mensajes': ult,
            'mayor_reanudador': _leader(rean), 'mayor_ultimo_mensaje': _leader(ult)}


def sensitivity(messages, gaps=None, cfg_path=None, burst_max_gap_seconds=None):
    """Resumen por hueco de sesión + fragilidad. Devuelve dict serializable (sin texto de mensajes)."""
    cfg_gaps, min_sessions = _load_cfg(cfg_path)
    gaps = list(gaps or cfg_gaps)
    people = sorted({m.participante for m in messages if m.participante})
    if len(people) != 2:
        raise ValueError('la segmentación espera exactamente 2 participantes')
    per_gap = {}
    for g in gaps:
        sess = build_sessions(build_turns(messages, session_gap_hours=g,
                                          burst_max_gap_seconds=burst_max_gap_seconds))
        r = summarize(sess, people)
        r['suficiencia_de_datos'] = 'suficiente' if len(sess) >= min_sessions else 'insuficiente'
        per_gap[g] = r

    def stable(key):
        vals = {per_gap[g][key] for g in gaps}
        return len(vals) == 1 and 'empate' not in vals

    return {'participantes': people, 'huecos_horas': gaps, 'por_hueco': per_gap,
            'robustez': {'reanudaciones': 'robusto' if stable('mayor_reanudador') else 'sensible_a_umbrales',
                         'ultimos_mensajes': 'robusto' if stable('mayor_ultimo_mensaje') else 'sensible_a_umbrales'},
            'nota': 'robusto = misma dirección con todos los huecos probados; no es validez ni interpretación'}


def sensitivity_from_result(result, **kwargs):
    """Solo con el análisis habilitado (igual que los turnos)."""
    if not result.analysis_enabled:
        raise ValueError('el análisis no está habilitado: ' + ', '.join(result.pending_requirements or ['importación no aceptada']))
    return sensitivity(result.messages, **kwargs)

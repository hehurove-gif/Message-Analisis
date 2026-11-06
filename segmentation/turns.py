"""Turnos conversacionales (Fase 2, paso 1; definiciones operativas v0.6, sección 1).

TURNO: mensajes consecutivos del mismo participante hasta que interviene el otro, dentro de una misma sesión.
RÁFAGA: mensajes consecutivos del mismo autor con intervalo <= burst_max_gap_seconds (no es frontera de turno).
SESIÓN (solo su corte, aquí): el silencio entre dos mensajes consecutivos SUPERA session_gap_hours. Con el
intervalo exactamente igual al umbral la sesión continúa.

Entrada: mensajes del parser (en orden de origen). Solo cuentan los de persona (texto, media, deleted); los
`system` no pertenecen a ningún participante y se omiten. No se reordena nada por timestamp: si un mensaje
retrocede en el tiempo, su intervalo es negativo, nunca provoca un corte de sesión y el turno queda marcado
`tiene_fuera_de_orden` para que las métricas lo traten con cuidado.

No calcula métricas ni latencias: solo segmenta y conserva el registro por turno (config `turn_record_fields`).
Los parámetros salen de config.yaml (`segmentation`); nada está fijo aquí."""
import os
from dataclasses import dataclass
from datetime import datetime

import yaml

PERSON_TYPES = ('texto', 'media', 'deleted')
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')


@dataclass(frozen=True)
class SegmentationConfig:
    session_gap_hours: float = 6
    burst_max_gap_seconds: float = 300


def load_segmentation_config(path=None) -> SegmentationConfig:
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        seg = (yaml.safe_load(f) or {}).get('segmentation', {})
    return SegmentationConfig(session_gap_hours=seg.get('session_gap_hours', 6),
                              burst_max_gap_seconds=seg.get('burst_max_gap_seconds', 300))


@dataclass(frozen=True)
class Turn:
    index: int                           # 1, 2, … en orden de origen
    participante: str
    sesion: int                          # índice de sesión (0, 1, …) según el hueco usado
    seq_primero: int                     # `seq` del primer y último mensaje del turno
    seq_ultimo: int
    n_mensajes: int
    primer_ts: str                       # ISO local, tal como lo entrega el parser
    ultimo_ts: str
    minutos_transcurridos: float         # último - primero: NO es actividad efectiva
    n_rafagas: int
    silencios_minutos: tuple             # intervalos entre mensajes consecutivos del turno
    minutos_dentro_de_rafagas: float
    tiene_fuera_de_orden: bool

    def __repr__(self):                  # sin contenido de mensajes
        return f'Turn(index={self.index}, participante={self.participante}, n={self.n_mensajes})'


def _minutes(a, b):
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60


def build_turns(messages, session_gap_hours=None, burst_max_gap_seconds=None, cfg=None):
    """Tupla de Turn. `messages`: secuencia de Message del parser; todos los de persona deben tener
    `timestamp_local` (si el orden de fecha no se resolvió no hay segmentación posible)."""
    cfg = cfg or load_segmentation_config()
    gap_h = cfg.session_gap_hours if session_gap_hours is None else session_gap_hours
    burst_s = cfg.burst_max_gap_seconds if burst_max_gap_seconds is None else burst_max_gap_seconds

    people = [m for m in messages if m.tipo in PERSON_TYPES]
    if any(m.timestamp_local is None or m.participante is None for m in people):
        raise ValueError('hay mensajes de persona sin timestamp normalizado o sin participante')

    groups, session = [], 0                          # cada grupo: (participante, sesión, [mensajes])
    for i, m in enumerate(people):
        if i > 0 and _minutes(people[i - 1].timestamp_local, m.timestamp_local) > gap_h * 60:
            session += 1                             # corta solo cuando el silencio SUPERA el umbral
        if groups and groups[-1][0] == m.participante and groups[-1][1] == session:
            groups[-1][2].append(m)
        else:
            groups.append((m.participante, session, [m]))

    turns = []
    for k, (who, sess, ms) in enumerate(groups, 1):
        gaps = tuple(_minutes(a.timestamp_local, b.timestamp_local) for a, b in zip(ms, ms[1:]))
        turns.append(Turn(
            index=k, participante=who, sesion=sess, seq_primero=ms[0].seq, seq_ultimo=ms[-1].seq,
            n_mensajes=len(ms), primer_ts=ms[0].timestamp_local, ultimo_ts=ms[-1].timestamp_local,
            minutos_transcurridos=_minutes(ms[0].timestamp_local, ms[-1].timestamp_local),
            n_rafagas=1 + sum(1 for g in gaps if g * 60 > burst_s), silencios_minutos=gaps,
            minutos_dentro_de_rafagas=sum(g for g in gaps if g * 60 <= burst_s),
            tiene_fuera_de_orden=any(g < 0 for g in gaps)))
    return tuple(turns)


def turns_from_result(result, **kwargs):
    """Segmenta una importación SOLO si el análisis está habilitado (tipo de conversación confirmado por el
    usuario y pérdidas resueltas o aceptadas). Nunca se segmenta una importación rechazada o pendiente."""
    if not result.analysis_enabled:
        raise ValueError('el análisis no está habilitado: ' + ', '.join(result.pending_requirements or ['importación no aceptada']))
    return build_turns(result.messages, **kwargs)

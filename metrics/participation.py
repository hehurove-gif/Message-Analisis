"""Balance de participación (Fase 3.1; definiciones v0.6 §5 y config `participation`).

Cada unidad se reporta POR SEPARADO: mensajes, turnos y palabras. No hay etiqueta única de "equilibrio" ni
índice compuesto, y esto NO es reciprocidad (que todavía no tiene definición operativa): que los turnos estén
parejos no demuestra una relación recíproca.
Palabras = fragmentos separados por espacios en mensajes de tipo `texto` (los `media` y `deleted` no aportan palabras).
Los mensajes `system` no pertenecen a nadie y no cuentan. Solo cuenta lo que el parser entregó."""
import os
from collections import Counter

import yaml

from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns


def _min_messages(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('data_sufficiency', {}).get('min_messages_for_any_metric', 30)


def _shares(values):
    total = sum(values.values())
    return {k: (round(v / total, 4) if total else None) for k, v in sorted(values.items())}


def participation(messages, session_gap_hours=None, cfg_path=None):
    people_msgs = [m for m in messages if m.tipo in PERSON_TYPES]
    names = sorted({m.participante for m in people_msgs})
    if len(names) != 2:
        raise ValueError('la participación espera exactamente 2 participantes')

    msgs, words, by_type, days = Counter(), Counter(), {n: Counter() for n in names}, {n: set() for n in names}
    for m in people_msgs:
        msgs[m.participante] += 1
        by_type[m.participante][m.tipo] += 1
        days[m.participante].add(m.timestamp_local[:10])
        if m.tipo == 'texto':
            words[m.participante] += len(m.texto.split())
    turns = Counter(t.participante for t in build_turns(people_msgs, session_gap_hours=session_gap_hours))

    por = {n: {'mensajes': msgs[n], 'turnos': turns[n], 'palabras': words[n],
               'mensajes_por_tipo': {t: by_type[n].get(t, 0) for t in PERSON_TYPES},
               'dias_con_mensajes': len(days[n])} for n in names}
    return {
        'participantes': names, 'por_participante': por,
        'proporciones': {'mensajes': _shares(msgs), 'turnos': _shares(turns), 'palabras': _shares(words)},
        'suficiencia_de_datos': 'suficiente' if len(people_msgs) >= _min_messages(cfg_path) else 'insuficiente',
        'nota': 'cada unidad por separado; sin índice compuesto; no es reciprocidad',
    }


def participation_from_result(result, **kwargs):
    """Solo con el análisis habilitado (como la segmentación)."""
    if not result.analysis_enabled:
        raise ValueError('el análisis no está habilitado: ' + ', '.join(result.pending_requirements or ['importación no aceptada']))
    return participation(result.messages, **kwargs)

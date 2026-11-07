"""Hábitos temporales (Fase 3, provisional): CUÁNDO escribe cada participante.

Cuenta MENSAJES de persona por hora local del timestamp (0–23), por día de la semana y por franja del día
(config `habits.day_parts`). Hora local = la del teléfono que exportó; no se corrige zona horaria y, si las
personas viven en zonas distintas, la hora del otro está desplazada. Descriptivo: escribir de madrugada no
significa nada por sí solo. Proporciones dentro de cada participante (suman 1 por participante)."""
from collections import Counter
from datetime import datetime

import yaml

from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES

DAYS = ('lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom')
DEFAULT_PARTS = {'madrugada': [0, 6], 'manana': [6, 12], 'tarde': [12, 19], 'noche': [19, 24]}


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return (raw.get('habits', {}).get('day_parts', DEFAULT_PARTS),
            raw.get('data_sufficiency', {}).get('min_messages_for_any_metric', 30))


def _part(hour, parts):
    for name, (lo, hi) in parts.items():
        if lo <= hour < hi:
            return name
    return 'sin_franja'


def _props(counter, keys):
    total = sum(counter.values())
    return {k: (round(counter.get(k, 0) / total, 3) if total else None) for k in keys}


def habits(messages, cfg_path=None):
    parts, min_msgs = _cfg(cfg_path)
    people = [m for m in messages if m.tipo in PERSON_TYPES and m.timestamp_local]
    names = sorted({m.participante for m in people})
    por = {}
    for n in names:
        dts = [datetime.fromisoformat(m.timestamp_local) for m in people if m.participante == n]
        hours, days = Counter(d.hour for d in dts), Counter(DAYS[d.weekday()] for d in dts)
        franjas = Counter(_part(d.hour, parts) for d in dts)
        por[n] = {'n_mensajes': len(dts),
                  'por_hora': {h: hours.get(h, 0) for h in range(24)},
                  'hora_mas_frecuente': hours.most_common(1)[0][0] if hours else None,
                  'proporcion_por_franja': _props(franjas, list(parts)),
                  'proporcion_por_dia': _props(days, DAYS),
                  'suficiencia_de_datos': 'suficiente' if len(dts) >= min_msgs else 'insuficiente'}
    return {'unidad': 'mensajes', 'franjas_horas': parts, 'por_participante': por,
            'nota': 'hora local del teléfono que exportó; descriptivo, no interpreta disponibilidad ni interés'}

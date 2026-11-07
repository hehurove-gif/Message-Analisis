"""Guía de participantes: cómo saber quién es A y quién es B SIN imprimir nombres.

REGLA DE ETIQUETAS (parsers/anonymize.py + importer): A = autor del PRIMER mensaje de persona que aparece en el
archivo; B = el siguiente autor distinto. Es solo orden de aparición en lo exportado:
  - NO indica quién exportó el chat (el TXT de WhatsApp no lo marca),
  - NO indica quién inició la relación (el historial exportado puede empezar a la mitad),
  - con otra exportación del mismo chat (más corta o más larga) A y B pueden invertirse.
Para ubicarlos, la guía da el número de LÍNEA y la fecha del primer y último mensaje de cada etiqueta: abre tu
archivo en esa línea (en local) y verás el nombre. Con `yo` (A o B) se agrega el rol "yo"/"otra_persona" para que
los reportes se lean sin traducir etiquetas. Nunca sale texto ni nombre."""
from segmentation.turns import PERSON_TYPES

RULE = ('A = autor del primer mensaje de persona del archivo; B = el siguiente autor distinto. '
        'No indica quién exportó ni quién inició la relación.')


def participant_guide(messages, yo=None):
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    por = {}
    for m in people:
        p = por.setdefault(m.participante, {'primer_mensaje_linea': m.linea_inicial,
                                            'primer_mensaje_fecha': m.timestamp_local})
        p['ultimo_mensaje_linea'], p['ultimo_mensaje_fecha'] = m.linea_inicial, m.timestamp_local
    por = dict(sorted(por.items()))
    out = {'regla': RULE, 'por_participante': por}
    if yo is not None:
        if yo not in por:
            raise ValueError(f'--yo {yo}: esa etiqueta no existe (hay {", ".join(por)})')
        out['roles'] = {k: ('yo' if k == yo else 'otra_persona') for k in por}
    return out


def role_name(label, guide):
    """'A (yo)' / 'B (otra_persona)' si hay roles; si no, la etiqueta tal cual."""
    r = guide.get('roles', {}).get(label)
    return f'{label} ({r})' if r else label

"""Herramienta de revisión: agrupa avisos sin catalogar por forma y lista retrocesos, sin texto ni nombres."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from revisar_avisos_y_orden_local import out_of_order, resumen, uncatalogued  # noqa: E402

from parsers import parse_text  # noqa: E402

T = ('5/13/26, 9:00 AM - Ana: hola\n'
     '5/13/26, 9:01 AM - Aviso raro del sistema\n'
     '5/13/26, 9:02 AM - Otro raro del sistema\n'
     '5/13/26, 9:03 AM - Beto: que tal\n'
     '5/13/26, 8:03 AM - Ana: ya\n')


def test_agrupa_y_ubica_sin_texto():
    ms = parse_text(T, date_order_hint='mdy').messages
    av = uncatalogued(ms)
    assert sum(g['n'] for g in av) == 2 and av[0]['lineas'][0] in (2, 3)
    oo = out_of_order(ms)
    assert oo == [{'linea': 5, 'fecha': '2026-05-13T08:03', 'retrocede_min': 60, 'mismo_autor': False}]
    txt = resumen(ms)
    assert 'exactamente 60 min: 1' in txt
    for w in ('Ana', 'Beto', 'raro', 'Otro', 'hola'):
        assert w not in txt

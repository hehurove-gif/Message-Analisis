"""Herramienta de revisión manual de sesiones: solo números, líneas correctas y coherencia con la segmentación."""
import os
import sys

from parsers import parse_text
from tests.synth_chats import build_text

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
import sesiones_para_revisar_local as S  # noqa: E402


def test_revision_de_sesiones_sintetica():
    text = build_text(seed=4, months=3)
    msgs = parse_text(text, date_order_hint='dmy').messages
    r = S.review(msgs, n=5, lo=4, hi=14)
    assert 1 <= len(r['sesiones_elegidas']) <= 5
    lines = text.split('\n')
    for s in r['sesiones_elegidas']:
        a, b = s['lineas']
        assert a <= b and 4 <= s['turnos'] <= 14 and len(s['detalle']) == s['turnos']
        assert s['detalle'][0]['quien'] == s['abre'] and s['detalle'][-1]['quien'] == s['cierra']
        assert s['detalle'][-1]['min_hasta_que_interviene_el_otro'] is None
        assert lines[a - 1][:2].isdigit() and lines[b - 1][:2].isdigit()    # son líneas de encabezado de mensaje
        assert all(t['quien'] != u['quien'] for t, u in zip(s['detalle'], s['detalle'][1:]))   # los turnos alternan
    out = S.render(r)
    assert 'Ana' not in out and 'Beto' not in out and 'hoy' not in out

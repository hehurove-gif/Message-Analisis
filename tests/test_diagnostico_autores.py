"""El diagnóstico de autores no imprime nombres ni contenido (datos ficticios)."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import diagnostico_autores_local as D  # noqa: E402

CHAT = ('1/5/26, 9:10 AM - Zoilo Peñaloza: secreto-1234\n'
        '1/5/26, 9:11 AM - Zoilo Peñaloza: otro\n'
        '1/6/26, 9:12 AM - +52 55 1234 5678: hola\n'
        '1/7/26, 9:13 AM - Brígida Ñúñez: ok\n'
        '1/7/26, 9:14 AM - Brígida cambió algo raro\n')


def test_diagnostico_sin_nombres_ni_contenido():
    out = D.diagnose(CHAT)
    blob = json.dumps(out, ensure_ascii=False)
    for s in ('Zoilo', 'Peñaloza', 'Brígida', 'secreto', 'hola', '1234', '5678'):
        assert s not in blob
    assert [a['mensajes'] for a in out['autores']] == [2, 1, 1]
    assert [a['parece_telefono'] for a in out['autores']] == [False, True, False]
    assert out['avisos_sin_catalogar_por_forma']


def test_formato_no_reconocido():
    assert D.diagnose('nada\n') == {'error': 'FORMAT_NOT_RECOGNIZED'}


def test_forma_de_linea_sin_contenido():
    shapes = D.line_shapes(CHAT, 3)
    assert [x['linea'] for x in shapes] == [2, 3, 4]
    blob = json.dumps(shapes, ensure_ascii=False)
    for s in ('Zoilo', 'Brígida', 'hola', '5678', 'otro'):
        assert s not in blob
    assert D.line_shapes(CHAT, 1)[0]['linea'] == 1

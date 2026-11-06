"""probar_orden_fecha_local: distingue el orden con evidencia cronológica, no elige y no imprime contenido."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import probar_orden_fecha_local as P  # noqa: E402

# Todos los componentes <= 12: el parser bloquea. En orden dmy son fechas crecientes (3/4, 5/4, 10/4, 2/5).
DMY = ''.join(f'{d}, 9:00 AM - {a}: secreto-{i}\n' for i, (d, a) in enumerate(
    [('3/4/26', 'Zoilo'), ('3/4/26', 'Brígida'), ('5/4/26', 'Zoilo'), ('10/4/26', 'Brígida'), ('2/5/26', 'Zoilo')]))
# Mismas cifras, pero cronológicas en orden mdy (3/4, 4/5, 4/10, 5/2 => mar 4, abr 5, abr 10, may 2)
MDY = ''.join(f'{d}, 9:00 AM - {a}: secreto-{i}\n' for i, (d, a) in enumerate(
    [('3/4/26', 'Zoilo'), ('4/5/26', 'Brígida'), ('4/10/26', 'Zoilo'), ('5/2/26', 'Brígida')]))
AMBOS = '3/4/26, 9:00 AM - Zoilo: a\n3/4/26, 9:05 AM - Brígida: b\n'


def probar(tmp_path, texto):
    p = tmp_path / 'c.txt'
    p.write_text(texto, encoding='utf-8')
    return P.probe(str(p))


def test_distingue_dmy(tmp_path):
    res = probar(tmp_path, DMY)
    assert res['dmy']['timestamps_fuera_de_orden'] == 0 and res['mdy']['timestamps_fuera_de_orden'] > 0
    assert P.veredicto(res) == {**P.veredicto(res), 'distingue': True, 'mas_cronologico': 'dmy'}


def test_distingue_mdy(tmp_path):
    res = probar(tmp_path, MDY)
    assert res['mdy']['timestamps_fuera_de_orden'] == 0 and res['dmy']['timestamps_fuera_de_orden'] > 0
    assert P.veredicto(res)['mas_cronologico'] == 'mdy'


def test_no_distingue_si_la_cronologia_no_ayuda(tmp_path):
    assert P.veredicto(probar(tmp_path, AMBOS))['distingue'] is False


def test_el_parser_sigue_bloqueando_sin_pista(tmp_path):
    from parsers import parse_file
    p = tmp_path / 'c.txt'
    p.write_text(DMY, encoding='utf-8')
    assert parse_file(str(p)).report['decision_importacion'] == 'blocked_pending_confirmation'


def test_solo_numeros_y_fechas(tmp_path, capsys):
    p = tmp_path / 'c.txt'
    p.write_text(DMY, encoding='utf-8')
    P.main([str(p)])
    raw = capsys.readouterr().out
    assert json.loads(raw)['veredicto']['distingue'] is True
    for s in ('Zoilo', 'Brígida', 'secreto'):
        assert s not in raw


def test_se_niega_a_leer_dentro_del_repo():
    with pytest.raises(SystemExit):
        P.main([os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp', 'A01_android24_coma_es.txt')])

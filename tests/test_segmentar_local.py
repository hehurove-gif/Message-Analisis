"""segmentar_local: exige confirmación explícita, imprime solo conteos y rechaza archivos dentro del repo."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import segmentar_local as S  # noqa: E402

CHAT = ('5/13/26, 9:00 AM - Zoilo Peñaloza: secreto-1234\n5/13/26, 9:01 AM - Brígida Ñúñez: ok\n'
        '5/14/26, 9:00 PM - Zoilo Peñaloza: hola de nuevo\n5/14/26, 9:05 PM - Brígida Ñúñez: sí\n')


def correr(tmp_path, capsys, *args):
    p = tmp_path / 'chat.txt'
    p.write_text(CHAT, encoding='utf-8')
    S.main([str(p), *args])
    return capsys.readouterr().out


def test_sin_confirmacion_no_segmenta(tmp_path, capsys):
    out = json.loads(correr(tmp_path, capsys))
    assert out['analisis_habilitado'] is False and 'turnos' not in out
    assert out['requisitos_pendientes'] == ['CONFIRMAR_TIPO_CONVERSACION']


def test_con_confirmacion_entrega_solo_conteos(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--confirmo-individual')
    out = json.loads(raw)
    assert out['turnos']['n_turnos'] == 4 and out['sesiones']['participantes'] == ['A', 'B']
    for s in ('Zoilo', 'Brígida', 'secreto', 'hola'):
        assert s not in raw


def test_se_niega_a_leer_dentro_del_repo():
    with pytest.raises(SystemExit):
        S.main([os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp', 'A01_android24_coma_es.txt')])


def test_retroceso_entre_turnos_se_cuenta():
    """El siguiente turno (otro autor) empieza ANTES de que termine el anterior: no es un retroceso dentro de un turno."""
    from parsers import parse_text
    import segmentar_local as S
    t = ('18/01/2026, 10:44 - Ana: hola\n18/01/2026, 10:36 - Beto: ya\n18/01/2026, 10:54 - Ana: ok\n')
    r = S.resumen_turnos(parse_text(t, date_order_hint='dmy').messages)
    assert r['pares_de_turnos_fuera_de_orden'] == 1 and r['turnos_con_fuera_de_orden'] == 0

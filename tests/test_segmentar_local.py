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

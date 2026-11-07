"""metricas_local: exige confirmación, imprime solo números y no lee dentro del repo."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import metricas_local as M  # noqa: E402

CHAT = ('5/13/26, 9:00 AM - Zoilo Peñaloza: secreto-1234\n5/13/26, 9:01 AM - Brígida Ñúñez: ok\n'
        '5/14/26, 9:00 PM - Zoilo Peñaloza: hola de nuevo\n5/14/26, 9:05 PM - Brígida Ñúñez: sí\n')


def correr(tmp_path, capsys, *args):
    p = tmp_path / 'chat.txt'
    p.write_text(CHAT, encoding='utf-8')
    M.main([str(p), *args])
    return capsys.readouterr().out


def test_sin_confirmacion_no_calcula(tmp_path, capsys):
    out = json.loads(correr(tmp_path, capsys))
    assert out['analisis_habilitado'] is False and 'participacion' not in out


def test_con_confirmacion_solo_numeros(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--confirmo-individual')
    out = json.loads(raw)
    assert out['participacion']['por_participante']['A']['mensajes'] == 2 and set(out['latencias']) == {'2', '6', '12'}
    for s in ('Zoilo', 'Brígida', 'secreto', 'hola'):
        assert s not in raw


def test_se_niega_a_leer_dentro_del_repo():
    with pytest.raises(SystemExit):
        M.main([os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp', 'A01_android24_coma_es.txt')])


def test_incluye_guia_habitos_y_estilo_sin_texto(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--confirmo-individual', '--yo', 'B')
    out = json.loads(raw)
    assert out['participantes']['roles'] == {'A': 'otra_persona', 'B': 'yo'}
    assert out['participantes']['por_participante']['A']['primer_mensaje_linea'] == 1
    assert set(out) >= {'habitos', 'estilo'}
    for s in ('Zoilo', 'Brígida', 'secreto', 'hola'):
        assert s not in raw


def test_resumen_legible_sin_texto(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--confirmo-individual', '--yo', 'A', '--resumen')
    assert 'Quién es quién' in raw and 'A (yo)' in raw and 'B (otra_persona)' in raw and 'Latencia' in raw
    for s in ('Zoilo', 'Brígida', 'secreto', 'hola'):
        assert s not in raw


def test_resumen_sin_confirmacion(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--resumen')
    assert 'análisis: NO' in raw


def test_resumen_incluye_contenido_de_turnos(tmp_path, capsys):
    raw = correr(tmp_path, capsys, '--confirmo-individual', '--resumen')
    assert 'Contenido de turnos' in raw and 'inicia el día' in raw and 'risa' in raw


def test_comparar_local_sin_nombres(tmp_path, capsys):
    import comparar_local as C
    d = tmp_path / 'exp'
    d.mkdir()
    (d / 'Chat de WhatsApp con Zoilo.txt').write_text(CHAT, encoding='utf-8')
    (d / 'Chat de WhatsApp con Brígida.txt').write_text(CHAT, encoding='utf-8')
    C.main([str(d), '--confirmo-individual'])
    raw = capsys.readouterr().out
    assert raw.count('\n0 ') + raw.count('\n1 ') == 2 and 'p90 lat A/B' in raw
    for s in ('Zoilo', 'Brígida', 'secreto', 'Chat de'):
        assert s not in raw
    C.main([str(d)])
    assert 'NO:' in capsys.readouterr().out

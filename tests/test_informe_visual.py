import json
import os
import sys

import pytest

sys.path.insert(0, 'tools')
import informe_local as il  # noqa: E402
import informe_visual_local as iv  # noqa: E402

T = ('14/03/2025, 08:00 - Ana <b>: buenos dias, mi amor secreto\n14/03/2025, 08:05 - Beto: gracias, buen dia\n'
     '14/03/2025, 23:00 - Beto: te quiero mucho\n14/03/2025, 23:01 - Ana <b>: perdon por lo de ayer\n'
     '15/03/2025, 08:00 - Ana <b>: ánimo\n15/03/2025, 09:00 - Beto: jaja gracias 😂\n')


def hacer(tmp_path, extra=()):
    d = tmp_path / 'exp'
    d.mkdir()
    (d / 'chat.txt').write_text(T, encoding='utf-8')
    il.main([str(d), '--confirmo-individual', '--hint', '0=dmy', '--etiqueta', 'v', *extra])
    inf = d / 'informes'
    return d, next(p for p in inf.iterdir() if p.suffix == '.json'), inf


def test_html_desde_informe_local(tmp_path, capsys):
    d, j, inf = hacer(tmp_path, ['--html'])
    capsys.readouterr()
    h = next(p for p in inf.iterdir() if p.suffix == '.html').read_text(encoding='utf-8')
    assert 'cdn.tailwindcss.com' in h and '<svg' in h and 'Chat 0' in h and 'Beto' in h
    assert 'secreto' not in h and 'buenos dias' not in h              # nunca texto de mensajes
    assert 'Ana &lt;b&gt;' in h and 'Ana <b>' not in h               # los nombres se escapan
    assert 'Observaciones descriptivas' in h and 'contiene nombres' in h


def test_anonimo_no_lleva_nombres(tmp_path, capsys):
    d, j, inf = hacer(tmp_path, ['--html', '--anonimo'])
    capsys.readouterr()
    h = next(p for p in inf.iterdir() if p.suffix == '.html').read_text(encoding='utf-8')
    assert 'Beto' not in h and 'Ana' not in h and 'A × B' in h and 'contiene nombres' not in h


def test_desde_json_y_formato_antiguo(tmp_path, capsys):
    d, j, inf = hacer(tmp_path)
    foto = json.load(open(j, encoding='utf-8'))
    out = foto['archivos']['0']['out']
    for k in ('lexico_serie', 'nombres', 'nombres_completos'):         # un informe viejo no los trae
        out.pop(k, None)
    viejo = tmp_path / 'viejo.json'
    viejo.write_text(json.dumps(foto), encoding='utf-8')
    iv.main([str(viejo)])
    capsys.readouterr()
    h = (tmp_path / 'viejo.html').read_text(encoding='utf-8')
    assert 'A × B' in h and 'Léxico por periodo' not in h


def test_chat_no_analizado_y_privacidad(tmp_path):
    foto = {'meta': {'etiqueta': 'x', 'fecha': 'hoy'},
            'archivos': {'0': {'kb': '1', 'out': {'analisis_habilitado': False, 'importacion': 'rejected', 'requisitos_pendientes': ['x']}}}}
    h = iv.render(foto)
    assert 'No se analizó' in h
    repo = os.path.dirname(os.path.dirname(os.path.abspath(iv.__file__)))
    with pytest.raises(SystemExit):
        iv.main([os.path.join(repo, 'config.yaml'), '--salida', str(tmp_path / 'a.html')])
    j = tmp_path / 'i.json'
    j.write_text(json.dumps(foto), encoding='utf-8')
    with pytest.raises(SystemExit):
        iv.main([str(j), '--salida', os.path.join(repo, 'salida.html')])


def test_utilidades():
    assert iv.minutos(30) == '30 min' and iv.minutos(120) == '2.0 h' and iv.minutos(None) == '—'
    assert iv.periodo_corto('2025-03') == 'mar 25' and iv.periodo_corto('2025-W07') == '2025 s07'
    assert iv.corto('x' * 40).endswith('…') and len(iv.corto('x' * 40)) == 26

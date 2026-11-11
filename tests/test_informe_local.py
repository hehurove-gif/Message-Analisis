import json
import os
import sys

import pytest

sys.path.insert(0, 'tools')
import informe_local as il  # noqa: E402

T = ('14/03/2025, 08:00 - Ana: buenos dias, mi amor\n14/03/2025, 08:05 - Beto: gracias, buen dia\n'
     '14/03/2025, 23:00 - Beto: te quiero mucho\n14/03/2025, 23:01 - Ana: perdon por lo de ayer\n'
     '15/03/2025, 08:00 - Ana: ánimo\n15/03/2025, 09:00 - Beto: jaja gracias 😂\n')


def carpeta(tmp_path):
    d = tmp_path / 'exp'
    d.mkdir()
    (d / 'b_chat.txt').write_text(T, encoding='utf-8')
    (d / 'A_chat.txt').write_text(T.replace('mi amor', 'tigre'), encoding='utf-8')
    (d / 'salida.local.txt').write_text('no soy un chat', encoding='utf-8')
    return d


def test_orden_y_filtro(tmp_path):
    d = carpeta(tmp_path)
    assert [os.path.basename(f) for f in il.archivos_de(str(d))] == ['A_chat.txt', 'b_chat.txt']   # sin .local.txt


def test_informe_y_comparacion(tmp_path, capsys):
    d = carpeta(tmp_path)
    args = [str(d), '--confirmo-individual', '--hint', '0=dmy', '--hint', '1=dmy', '--anonimo']
    il.main(args + ['--etiqueta', 'inicio'])
    (d / 'lexicon_local.yaml').write_text('apodos: ["tigre"]\n', encoding='utf-8')   # el léxico cambia entre inicio y final
    il.main(args + ['--etiqueta', 'final'])
    capsys.readouterr()
    inf = sorted((d / 'informes').iterdir())
    nombres = [p.name for p in inf]
    assert sum(n.endswith('.md') for n in nombres) == 2 and sum(n.endswith('.json') for n in nombres) == 2
    md = next(p for p in inf if p.name.startswith('informe_inicio') and p.suffix == '.md').read_text(encoding='utf-8')
    assert '## Tabla comparativa' in md and '### Léxico (mensajes con evento)' in md and '| categoría |' in md
    assert 'A_chat' not in md and 'b_chat' not in md and 'Ana' not in md and 'Beto' not in md
    md2 = next(p for p in inf if p.name.startswith('informe_final') and p.suffix == '.md').read_text(encoding='utf-8')
    assert 'tigre' not in md2 and '(local)' in md2        # el léxico local nunca se imprime
    j0 = next(p for p in inf if p.name.startswith('informe_inicio') and p.suffix == '.json')
    j1 = next(p for p in inf if p.name.startswith('informe_final') and p.suffix == '.json')
    foto = json.load(open(j1, encoding='utf-8'))
    assert foto['meta']['etiqueta'] == 'final' and set(foto['archivos']) == {'0', '1'}
    il.main(['--comparar', str(j0), str(j1)])
    txt = capsys.readouterr().out
    assert '# Comparación' in txt and 'Archivo 0' in txt and 'lexico' in txt and '→' in txt
    assert (d / 'informes' / 'comparacion_inicio_vs_final.md').exists()
    assert 'tigre' not in txt


def test_solo_y_privacidad(tmp_path):
    d = carpeta(tmp_path)
    il.main([str(d), '--confirmo-individual', '--hint', '0=dmy', '--hint', '1=dmy', '--solo', '1', '--etiqueta', 'x', '--anonimo'])
    foto = json.load(open(next(p for p in (d / 'informes').iterdir() if p.suffix == '.json'), encoding='utf-8'))
    assert list(foto['archivos']) == ['1']
    with pytest.raises(SystemExit):
        il.main([il.ROOT, '--confirmo-individual'])
    with pytest.raises(SystemExit):
        il.main([str(d), '--confirmo-individual', '--salida', il.ROOT + '/inf'])
    with pytest.raises(SystemExit):
        il.main(['--comparar', il.ROOT + '/a.json', il.ROOT + '/b.json'])


def test_nombres_en_lugar_de_A_B(tmp_path, capsys):
    d = carpeta(tmp_path)
    args = [str(d), '--confirmo-individual', '--hint', '0=dmy', '--hint', '1=dmy']
    il.main(args + ['--etiqueta', 'n1'])
    plantilla = json.load(open(d / 'nombres_local.json', encoding='utf-8'))
    assert plantilla == {'Ana': 'Ana', 'Beto': 'Beto'}
    plantilla['Beto'] = 'Betito'                                    # nombre corto elegido por el usuario
    (d / 'nombres_local.json').write_text(json.dumps(plantilla), encoding='utf-8')
    il.main(args + ['--etiqueta', 'n2'])
    capsys.readouterr()
    md = next(p for p in (d / 'informes').iterdir() if p.name.startswith('informe_n2') and p.suffix == '.md').read_text(encoding='utf-8')
    assert 'Ana × Betito' in md and 'Ana_a_Betito' in md and 'Betito_a_Ana' in md
    assert 'A_a_B' not in md and 'CONTIENE nombres' in md
    j = json.load(open(next(p for p in (d / 'informes').iterdir() if p.name.startswith('informe_n2') and p.suffix == '.json'), encoding='utf-8'))
    assert j['archivos']['0']['out']['nombres'] == {'A': 'Ana', 'B': 'Betito'}      # el análisis sigue con A/B; los nombres son solo etiquetas


def test_comparar_ignora_nombres(tmp_path, capsys):
    d = carpeta(tmp_path)
    args = [str(d), '--confirmo-individual', '--hint', '0=dmy', '--hint', '1=dmy']
    il.main(args + ['--anonimo', '--etiqueta', 'ini'])
    il.main(args + ['--etiqueta', 'fin'])
    capsys.readouterr()
    inf = sorted((d / 'informes').iterdir())
    j0 = next(p for p in inf if 'informe_ini' in p.name and p.suffix == '.json')
    j1 = next(p for p in inf if 'informe_fin' in p.name and p.suffix == '.json')
    il.main(['--comparar', str(j0), str(j1)])
    txt = capsys.readouterr().out
    assert 'Ana' not in txt and 'Beto' not in txt

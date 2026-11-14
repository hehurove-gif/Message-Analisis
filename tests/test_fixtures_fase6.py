"""Fase 6, paso 3: los fixtures sintéticos 03 a 08 son coherentes con sus etiquetas y la referencia independiente."""
import csv
import os
import subprocess
import sys
from collections import Counter

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYN = os.path.join(ROOT, 'data', 'synthetic')
# fixture -> eventos P esperados por autor (clase indicador_candidato), declaraciones y límites
ESPERADO = {
    '03_romantico_reciproco': ({'Mateo': 10, 'Valeria': 9}, 3, 0),
    '04_amistad_calida': ({}, 0, 0),
    '05_ambiguo': ({'Ricardo': 12}, 0, 0),
    '06_limite_con_alcance': ({'Ernesto': 7}, 0, 2),
    '07_falsos_positivos_contexto': ({}, 0, 0),
    '08_datos_insuficientes': ({'Hugo': 3, 'Daniela': 1}, 0, 0),
}


def rows(name):
    with open(os.path.join(SYN, name + '.etiquetas.csv'), encoding='utf-8') as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize('name', sorted(ESPERADO))
def test_archivos_y_conteos(name):
    for ext in ('.txt', '.etiquetas.csv', '.esperado.md'):
        assert os.path.getsize(os.path.join(SYN, name + ext)) > 0, name + ext
    p, decl, limites = ESPERADO[name]
    r = rows(name)
    assert dict(Counter(x['autor'] for x in r if x['clase_evento'] == 'indicador_candidato')) == p
    assert sum(x['clase_evento'] == 'declaracion_explicita' for x in r) == decl
    assert sum(x['categoria_respuesta'].startswith('limite_interpersonal') for x in r) == limites


@pytest.mark.parametrize('name', sorted(ESPERADO))
def test_la_referencia_independiente_corre(name):
    base = os.path.join(SYN, name)
    out = subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools', 'referencia', 'ref_indicadores.py'),
                          base + '.txt', base + '.etiquetas.csv'], capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    assert 'PARAMETROS (indicadores)' in out.stdout


@pytest.mark.parametrize('name', sorted(ESPERADO))
def test_latencias_del_csv_coinciden_con_el_txt(name):
    """latencia = del último mensaje del turno del autor a la siguiente intervención del otro; dentro si <= 6 h."""
    from datetime import datetime
    msgs = []
    with open(os.path.join(SYN, name + '.txt'), encoding='utf-8') as f:
        for line in f.read().splitlines()[1:]:
            d, rest = line.split(' - ', 1)
            who, _ = rest.split(': ', 1)
            msgs.append((datetime.strptime(d, '%d/%m/%Y %H:%M'), who))
    for r in rows(name):
        if not r['latencia_siguiente_intervencion_min']:
            continue
        t = datetime.strptime(r['fecha_hora'], '%Y-%m-%d %H:%M')
        i = next(k for k, (ts, w) in enumerate(msgs) if ts == t and w == r['autor'])
        j = i
        while j + 1 < len(msgs) and msgs[j + 1][1] == r['autor']:
            j += 1
        k = next(x for x in range(j + 1, len(msgs)) if msgs[x][1] != r['autor'])
        lat = int((msgs[k][0] - msgs[j][0]).total_seconds() // 60)
        assert str(lat) == r['latencia_siguiente_intervencion_min'], (name, r['fecha_hora'])
        assert r['sesion_hueco_6h'] == ('dentro' if lat <= 360 else 'entre')


def test_categorias_de_respuesta_estan_en_config():
    import yaml
    cfg = yaml.safe_load(open(os.path.join(ROOT, 'config.yaml'), encoding='utf-8'))['romantic_interest']
    validas = set(cfg['response_categories'])
    for name in ESPERADO:
        for r in rows(name):
            if r['categoria_respuesta']:
                assert r['categoria_respuesta'] in validas, (name, r['categoria_respuesta'])

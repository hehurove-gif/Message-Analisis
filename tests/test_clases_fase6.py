"""Fase 6, paso 2: lexicon/clases_fase6.yaml cubre todas las reglas del léxico y solo usa clases válidas."""
import os

import pytest
import yaml

from nlp.lexicon import load_lexicon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASES = yaml.safe_load(open(os.path.join(ROOT, 'lexicon', 'clases_fase6.yaml'), encoding='utf-8'))
LEX = load_lexicon()
VALIDAS = set(CLASES['clases_validas'])
ESPECIFICIDAD = {'baja', 'media', 'alta', None}


def test_cada_regla_tiene_clase():
    sin_clase = {r.id for r in LEX.rules} - set(CLASES['reglas'])
    assert not sin_clase, f'reglas sin clase: {sorted(sin_clase)}'


def test_no_hay_clases_de_reglas_inexistentes():
    sobran = set(CLASES['reglas']) - {r.id for r in LEX.rules}
    assert not sobran, f'clases de reglas que no existen: {sorted(sobran)}'


def test_clases_validas_son_las_de_definiciones():
    assert VALIDAS == {'linea_base', 'calidez_no_especifica', 'indicador_candidato', 'declaracion_explicita', 'no_candidato'}


@pytest.mark.parametrize('seccion', ['reglas', 'categorias_sin_regla', 'reglas_nuevas_previstas'])
def test_entradas_bien_formadas(seccion):
    for rid, e in CLASES[seccion].items():
        assert e['clase'] in VALIDAS, rid
        assert e.get('especificidad') in ESPECIFICIDAD, rid
        assert isinstance(e.get('ambiguo'), bool), rid
        if 'sube_a' in e:
            assert e['sube_a']['clase'] in VALIDAS, rid


def test_sin_indicadores_ni_declaraciones_sin_especificidad():
    for rid, e in CLASES['reglas'].items():
        if e['clase'] in ('indicador_candidato', 'declaracion_explicita'):
            assert e['especificidad'] is not None, rid


def test_reglas_previstas_no_estan_ya_en_el_lexico():
    assert not set(CLASES['reglas_nuevas_previstas']) & {r.id for r in LEX.rules}


def test_categorias_de_emoji_cubiertas():
    # emoji_otro no viene de una regla: debe tener clase propia
    assert 'emoji_otro' in CLASES['categorias_sin_regla']


def test_decision_1_te_quiero_y_te_amo():
    r = CLASES['reglas']
    assert r['afecto.te_quiero.v1']['clase'] == 'calidez_no_especifica'
    assert r['afecto.te_amo.v1']['clase'] == 'indicador_candidato' and r['afecto.te_amo.v1']['ambiguo'] is True
    assert r['afecto.te_extrano.v1']['ambiguo'] is True
    assert r['apodo.fuerte.v1']['clase'] == 'indicador_candidato'

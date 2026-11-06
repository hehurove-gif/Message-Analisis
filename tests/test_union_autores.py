"""Autor con prefijo + nombre de otro autor: se reporta como posible alias, nunca se une solo.
La unión es una decisión explícita del usuario (merge_authors). Datos ficticios."""
import json

import pytest

from parsers import parse_text

CHAT = ('5/13/26, 9:10 AM - Ana Pérez: hola\n'
        '5/13/26, 9:11 AM - Beto 🔥- Ruiz: qué tal\n'
        '5/13/26, 9:12 AM - Beto 🔥- Ruiz: otro\n'
        '5/13/26, 9:13 AM - Ab9 PM - Beto 🔥- Ruiz: IMG-20260105-WA0001.jpg (file attached)\n'
        '5/13/26, 9:14 AM - Ana Pérez: ok\n')


def test_sin_decision_se_rechaza_y_se_reporta_el_alias():
    res = parse_text(CHAT)
    rep = res.report
    assert rep['decision_importacion'] == 'rejected' and res.messages is None
    assert rep['participantes_detectados'] == 3
    assert rep['autores_alias_sospechosos'] == [{'etiqueta': 'C', 'posible_de': 'B', 'mensajes': 1, 'lineas': [4]}]
    assert 'AUTHOR_ALIAS_SUSPECTED' in rep['advertencias']
    blob = json.dumps(rep, ensure_ascii=False)
    assert 'Beto' not in blob and 'Ana' not in blob


def test_union_explicita_permite_importar_sin_cambiar_el_contenido():
    res = parse_text(CHAT, merge_authors={'C': 'B'})
    rep = res.report
    assert res.accepted and rep['participantes_detectados'] == 2
    assert rep['estado_tipo_conversacion'] == 'pending_confirmation'    # sigue sin declararse individual
    assert rep['autores_unidos'] == [{'de': 'C', 'a': 'B', 'mensajes': 1, 'lineas': [4]}]
    assert 'AUTHORS_MERGED_BY_USER' in rep['advertencias']
    assert [m.participante for m in res.messages] == ['A', 'B', 'B', 'B', 'A']
    assert res.messages[3].media_kind == 'imagen'
    assert res.analysis_enabled is False and res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION']


@pytest.mark.parametrize('merge', [{'Z': 'B'}, {'C': 'C'}, {'C': 'B', 'B': 'A'}])
def test_uniones_invalidas(merge):
    with pytest.raises(ValueError) as e:
        parse_text(CHAT, merge_authors=merge)
    assert 'Beto' not in str(e.value)


def test_tres_autores_sin_parecido_no_se_marcan_como_alias():
    res = parse_text('5/13/26, 9:10 AM - Ana: a\n5/13/26, 9:11 AM - Beto: b\n5/13/26, 9:12 AM - Caro: c\n')
    assert res.report['autores_alias_sospechosos'] == [] and not res.accepted


def test_aceptar_alias_sospechosos_es_opcional_y_queda_registrado():
    assert parse_text(CHAT).accepted is False                     # por defecto no se une nada
    res = parse_text(CHAT, accept_suspected_aliases=True)
    assert res.accepted and res.report['participantes_detectados'] == 2
    assert res.report['autores_unidos'] == [{'de': 'C', 'a': 'B', 'mensajes': 1, 'lineas': [4]}]
    assert 'AUTHORS_MERGED_BY_USER' in res.report['advertencias']
    assert res.analysis_enabled is False


def test_aceptar_alias_sospechosos_no_une_autores_sin_parecido():
    res = parse_text('5/13/26, 9:10 AM - Ana: a\n5/13/26, 9:11 AM - Beto: b\n5/13/26, 9:12 AM - Caro: c\n',
                     accept_suspected_aliases=True)
    assert not res.accepted and res.report['autores_unidos'] == []

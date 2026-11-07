"""Guía de participantes: A = primer autor del archivo; da líneas y fechas, nunca nombres ni texto."""
import pytest

from metrics.participants import participant_guide, role_name
from parsers import parse_text

T = ('5/13/26, 9:00 AM - Zoilo: hola\n5/13/26, 9:01 AM - Brígida: ok\n'
     '5/13/26, 9:02 AM - Brígida: otra\n5/14/26, 9:00 AM - Zoilo: adiós\n')


def test_a_es_el_primer_autor_y_da_lineas():
    g = participant_guide(parse_text(T).messages)
    assert g['por_participante']['A'] == {'primer_mensaje_linea': 1, 'primer_mensaje_fecha': '2026-05-13T09:00:00',
                                          'ultimo_mensaje_linea': 4, 'ultimo_mensaje_fecha': '2026-05-14T09:00:00'}
    assert g['por_participante']['B']['primer_mensaje_linea'] == 2 and 'roles' not in g
    assert 'Zoilo' not in str(g) and 'hola' not in str(g)


def test_roles_con_yo():
    g = participant_guide(parse_text(T).messages, yo='B')
    assert g['roles'] == {'A': 'otra_persona', 'B': 'yo'} and role_name('B', g) == 'B (yo)'
    with pytest.raises(ValueError):
        participant_guide(parse_text(T).messages, yo='C')

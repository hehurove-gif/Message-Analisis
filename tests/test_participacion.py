"""Participación (Fase 3.1): coincide con la referencia independiente y no inventa índices compuestos."""
import os
import sys

import pytest

from metrics.participation import participation, participation_from_result
from parsers import parse_file, parse_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
import ref_indicadores as RI  # noqa: E402
import ref_latency as R  # noqa: E402

SYN = os.path.join(ROOT, 'data', 'synthetic')
CHATS = [('00_escenarios_validacion', 'dmy'), ('01_amistad_equilibrada', None),
         ('02_interes_romantico_unilateral', None)]


@pytest.mark.parametrize('nombre,hint', CHATS)
def test_coincide_con_la_referencia(nombre, hint):
    res = parse_file(os.path.join(SYN, nombre + '.txt'), date_order_hint=hint)
    out = participation(res.messages, session_gap_hours=6)
    ref_msgs = R.load(os.path.join(SYN, nombre + '.txt'))
    words, days, _span = RI.words_and_days(ref_msgs)
    turns = R.build(ref_msgs, 6)
    lab = res.anonymization_map()
    for who in {m['who'] for m in ref_msgs}:
        mine = out['por_participante'][lab[who]]
        assert mine['mensajes'] == sum(1 for m in ref_msgs if m['who'] == who)
        assert mine['turnos'] == sum(1 for t in turns if t['who'] == who)
        assert mine['palabras'] == words[who]
        assert mine['dias_con_mensajes'] == len(days[who])


def test_no_hay_indice_compuesto_ni_etiqueta_de_equilibrio():
    out = participation(parse_file(os.path.join(SYN, '01_amistad_equilibrada.txt')).messages)
    texto = str(out).lower()
    assert 'equilibr' not in texto.replace('sin índice', '') and 'indice' not in texto.replace('sin índice compuesto', '')
    assert set(out['proporciones']) == {'mensajes', 'turnos', 'palabras'}


def test_media_y_eliminados_no_aportan_palabras_y_system_no_cuenta():
    chat = ('5/13/26, 9:00 AM - Ana: uno dos tres\n5/13/26, 9:01 AM - Beto: <Media omitted>\n'
            '5/13/26, 9:02 AM - Ana: You deleted this message\n5/13/26, 9:03 AM - Beto: cuatro cinco\n'
            '5/13/26, 9:04 AM - Messages and calls are end-to-end encrypted.\n')
    out = participation(parse_text(chat).messages)
    assert out['por_participante']['A']['palabras'] == 3 and out['por_participante']['B']['palabras'] == 2
    assert out['por_participante']['A']['mensajes'] == 2 and out['por_participante']['B']['mensajes'] == 2
    assert out['suficiencia_de_datos'] == 'insuficiente'


def test_requiere_dos_participantes_y_analisis_habilitado():
    with pytest.raises(ValueError):
        participation([])
    res = parse_file(os.path.join(SYN, '01_amistad_equilibrada.txt'))
    with pytest.raises(ValueError):
        participation_from_result(res)
    assert participation_from_result(res.confirm_individual())['participantes'] == ['A', 'B']

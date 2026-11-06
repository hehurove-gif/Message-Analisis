"""Sesiones (Fase 2.2): coinciden con el lector de referencia y la sensibilidad marca lo frágil."""
import os
import sys

import pytest

from parsers import parse_file, parse_text
from segmentation.sessions import build_sessions, sensitivity, sensitivity_from_result
from segmentation.turns import build_turns

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
import ref_latency as R  # noqa: E402

SYN = os.path.join(ROOT, 'data', 'synthetic')
CHATS = [('00_escenarios_validacion', 'dmy'), ('01_amistad_equilibrada', None),
         ('02_interes_romantico_unilateral', None)]


def importar(nombre, hint):
    return parse_file(os.path.join(SYN, nombre + '.txt'), date_order_hint=hint)


@pytest.mark.parametrize('nombre,hint', CHATS)
@pytest.mark.parametrize('gap', [2, 6, 12])
def test_sesiones_coinciden_con_la_referencia(nombre, hint, gap):
    res = importar(nombre, hint)
    sess = build_sessions(build_turns(res.messages, session_gap_hours=gap))
    ref_msgs = R.load(os.path.join(SYN, nombre + '.txt'))
    ref_turns = R.build(ref_msgs, gap)
    labels = res.anonymization_map()
    by = {}
    for t in ref_turns:
        by.setdefault(t['sess'], []).append(t)
    assert len(sess) == len(by)
    for s, k in zip(sess, sorted(by)):
        assert s.reanuda == labels[by[k][0]['who']] and s.ultimo_mensaje == labels[by[k][-1]['who']]
        assert s.n_turnos == len(by[k]) and s.n_mensajes == sum(t['n'] for t in by[k])
        assert s.primer_ts == by[k][0]['first'].isoformat() and s.ultimo_ts == by[k][-1]['last'].isoformat()


def test_primera_y_ultima_no_cuentan_como_reanudacion_ni_cierre():
    res = importar(*CHATS[0])
    sess = build_sessions(build_turns(res.messages, session_gap_hours=6))
    assert len(sess) == 7 and sess[0].es_primera and sess[-1].es_ultima
    assert sess[0].silencio_previo_minutos is None and all(s.silencio_previo_minutos > 360 for s in sess[1:])
    r = sensitivity(res.messages)['por_hueco'][6]
    assert sum(r['reanudaciones'].values()) == 6 and sum(r['ultimos_mensajes'].values()) == 6


def test_chat_00_es_fragil_ante_el_hueco():
    s = sensitivity(importar(*CHATS[0]).messages)
    assert s['huecos_horas'] == [2, 6, 12]
    assert s['robustez']['reanudaciones'] == 'sensible_a_umbrales'
    assert s['por_hueco'][6]['suficiencia_de_datos'] == 'insuficiente'      # 7 sesiones < 10


def test_empate_nunca_es_robusto():
    texto = ('5/13/26, 9:00 AM - Ana: a\n5/13/26, 9:01 AM - Beto: b\n5/14/26, 9:00 AM - Beto: c\n'
             '5/14/26, 9:01 AM - Ana: d\n')
    s = sensitivity(parse_text(texto).messages, gaps=[6])
    assert s['por_hueco'][6]['reanudaciones'] == {'A': 0, 'B': 1}
    texto2 = texto + '5/15/26, 9:00 AM - Ana: e\n5/15/26, 9:01 AM - Beto: f\n'
    s2 = sensitivity(parse_text(texto2).messages, gaps=[6, 12])
    assert s2['por_hueco'][6]['mayor_reanudador'] == 'empate' and s2['robustez']['reanudaciones'] == 'sensible_a_umbrales'


def test_requiere_dos_participantes():
    with pytest.raises(ValueError):
        sensitivity(parse_text('5/13/26, 9:00 AM - Ana: a\n').messages or [])


def test_solo_con_analisis_habilitado():
    res = importar(*CHATS[1])
    with pytest.raises(ValueError):
        sensitivity_from_result(res)
    assert sensitivity_from_result(res.confirm_individual())['participantes'] == ['A', 'B']

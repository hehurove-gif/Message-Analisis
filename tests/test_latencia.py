"""Latencia (Fase 3.2): coincide con ref_latency.summary en los tres chats con 2, 6 y 12 h, y cumple los
ejemplos de las definiciones v0.6 §3."""
import os
import sys

import pytest

from metrics.latency import latency_from_result, latency_summary, percentile, turn_latencies
from parsers import parse_file, parse_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
import ref_latency as R  # noqa: E402

SYN = os.path.join(ROOT, 'data', 'synthetic')
CHATS = [('00_escenarios_validacion', 'dmy'), ('01_amistad_equilibrada', None),
         ('02_interes_romantico_unilateral', None)]


@pytest.mark.parametrize('nombre,hint', CHATS)
@pytest.mark.parametrize('gap', [2, 6, 12])
def test_coincide_con_la_referencia(nombre, hint, gap):
    res = parse_file(os.path.join(SYN, nombre + '.txt'), date_order_hint=hint)
    mine = latency_summary(res.messages, gap)
    ref = R.summary(R.load(os.path.join(SYN, nombre + '.txt')), gap)
    a, ra = mine['agregado'], ref['agregado']
    for k_m, k_r in [('n', 'n'), ('mediana_general', 'mediana_general'), ('n_dentro', 'n_dentro'),
                     ('mediana_dentro', 'mediana_dentro'), ('n_entre', 'n_entre'),
                     ('mediana_entre', 'mediana_entre'), ('proporcion_dentro', 'prop_dentro')]:
        assert a[k_m] == pytest.approx(ra[k_r]) if ra[k_r] is not None else a[k_m] is None
    lab = res.anonymization_map()
    for who, r in ref['por_autor'].items():
        m = mine['por_participante_que_interviene'][lab[who]]
        assert (m['n'], m['n_dentro'], m['n_entre']) == (r['n'], r['n_dentro'], r['n_entre'])
        assert m['mediana_general'] == r['mediana_general'] or m['mediana_general'] == pytest.approx(r['mediana_general'])
    for estado, lista in ref['estados'].items():
        assert mine['estados'][estado] == len(lista)


def test_cifras_conocidas_chat_00():
    res = parse_file(os.path.join(SYN, '00_escenarios_validacion.txt'), date_order_hint='dmy')
    a = latency_summary(res.messages, 6)['agregado']
    assert (a['mediana_general'], a['mediana_dentro'], a['n_dentro'], a['mediana_entre'], a['n_entre']) == \
        (375, 17.5, 4, 600, 4)


def msgs(texto):
    return parse_text(texto).messages


def test_ejemplos_de_las_definiciones():
    # A escribe 10:00, 10:00 y 10:01; B interviene 10:03: latencia de B = 2 min (dentro de sesión)
    r = turn_latencies(msgs('5/13/26, 10:00 AM - Ana: a\n5/13/26, 10:00 AM - Ana: b\n5/13/26, 10:01 AM - Ana: c\n'
                            '5/13/26, 10:03 AM - Beto: d\n'))
    assert (r[0]['latencia_minutos'], r[0]['interviene'], r[0]['dentro_de_sesion']) == (2, 'B', True)
    # A 23:30, B 08:00 del día siguiente: 510 min, entre sesiones, sin ventana máxima
    r = turn_latencies(msgs('5/13/26, 11:30 PM - Ana: a\n5/14/26, 8:00 AM - Beto: b\n'), 6)
    assert (r[0]['latencia_minutos'], r[0]['dentro_de_sesion']) == (510, False)


def test_estados_sin_latencia():
    t = '5/13/26, 9:00 AM - Ana: a\n5/14/26, 9:00 AM - Ana: b\n5/14/26, 9:05 AM - Beto: c\n'
    r = turn_latencies(msgs(t), 6)
    assert [x['estado'] for x in r] == ['sin_intervencion_previa_a_su_nuevo_turno', 'con_intervencion',
                                         'sin_respuesta_observada']
    assert r[0]['latencia_minutos'] is None and r[1]['latencia_minutos'] == 5 and r[2]['latencia_minutos'] is None


def test_el_estado_depende_del_hueco():
    t = '5/13/26, 9:00 AM - Ana: a\n5/13/26, 1:00 PM - Ana: b\n5/13/26, 1:05 PM - Beto: c\n'
    # con 6 h, los dos mensajes de Ana son un solo turno; con 2 h son turnos de sesiones distintas
    assert [x['estado'] for x in turn_latencies(msgs(t), 6)] == ['con_intervencion', 'sin_respuesta_observada']
    assert [x['estado'] for x in turn_latencies(msgs(t), 2)] == [
        'sin_intervencion_previa_a_su_nuevo_turno', 'con_intervencion', 'sin_respuesta_observada']


def test_fuera_de_orden_no_inventa_latencia():
    r = turn_latencies(msgs('5/13/26, 9:10 AM - Ana: a\n5/13/26, 9:05 AM - Beto: b\n5/13/26, 9:20 AM - Ana: c\n'))
    assert r[0]['estado'] == 'con_intervencion_fuera_de_orden' and r[0]['latencia_minutos'] is None
    s = latency_summary(msgs('5/13/26, 9:10 AM - Ana: a\n5/13/26, 9:05 AM - Beto: b\n'))
    assert s['agregado']['n'] == 0 and s['estados']['con_intervencion_fuera_de_orden'] == 1


def test_percentiles():
    assert percentile([], 75) is None and percentile([5], 90) == 5
    assert percentile([1, 2, 3, 4], 50) == 2.5 and percentile([1, 2, 3, 4], 75) == 3.25


def test_suficiencia_y_candado():
    res = parse_file(os.path.join(SYN, '01_amistad_equilibrada.txt'))
    with pytest.raises(ValueError):
        latency_from_result(res)
    out = latency_from_result(res.confirm_individual())
    assert set(out) == {2, 6, 12}
    assert all(v['suficiencia_de_datos'] in ('suficiente', 'insuficiente')
               for v in out[6]['por_participante_que_interviene'].values())

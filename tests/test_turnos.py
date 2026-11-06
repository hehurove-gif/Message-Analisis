"""Turnos (Fase 2.1): coinciden con el lector de referencia independiente en los tres chats de la Fase 0
y cumplen las reglas de borde de las definiciones v0.6."""
import os
import sys

import pytest

from parsers import parse_text, parse_file
from segmentation.turns import build_turns, turns_from_result

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
def test_coincide_con_el_lector_de_referencia(nombre, hint, gap):
    res = importar(nombre, hint)
    mine = build_turns(res.messages, session_gap_hours=gap)
    ref_msgs = R.load(os.path.join(SYN, nombre + '.txt'))
    ref = R.build(ref_msgs, gap)
    assert len(mine) == len(ref)
    for t, r in zip(mine, ref):
        assert (t.n_mensajes, t.sesion, t.n_rafagas) == (r['n'], r['sess'], r['bursts'])
        assert t.primer_ts == r['first'].isoformat() and t.ultimo_ts == r['last'].isoformat()
        assert t.minutos_transcurridos == pytest.approx(r['elapsed'])
        assert t.silencios_minutos == pytest.approx(tuple(r['silences']))
        assert t.minutos_dentro_de_rafagas == pytest.approx(r['in_burst_min'])


def test_cifras_conocidas_de_la_fase_0():
    t0 = build_turns(importar(*CHATS[0]).messages, session_gap_hours=6)
    assert len(t0) == 11 and len({t.sesion for t in t0}) == 7
    t1 = build_turns(importar(*CHATS[1]).messages)
    assert len(t1) == 56 and sorted([sum(t.participante == p for t in t1) for p in 'AB']) == [28, 28]
    t2 = build_turns(importar(*CHATS[2]).messages)
    assert len(t2) == 63 and sorted([sum(t.participante == p for t in t2) for p in 'AB']) == [30, 33]


def msgs(lines):
    texto = '\n'.join(f'5/13/26, {h} - {a}: x' for h, a in lines) + '\n'
    return parse_text(texto, accept_suspected_aliases=False).messages


def test_borde_de_sesion_igual_al_umbral_continua():
    m = msgs([('9:00 AM', 'Ana'), ('3:00 PM', 'Ana'), ('9:01 PM', 'Ana'), ('9:02 PM', 'Beto')])
    t = build_turns(m, session_gap_hours=6)
    assert [x.sesion for x in t] == [0, 1, 1]               # 6 h exactas: misma sesión; 6 h 1 min: corta
    assert [x.n_mensajes for x in t] == [2, 1, 1]


def test_borde_de_rafaga_igual_al_umbral_continua():
    m = msgs([('9:00 AM', 'Ana'), ('9:05 AM', 'Ana'), ('9:11 AM', 'Ana'), ('9:12 AM', 'Beto')])
    t = build_turns(m, burst_max_gap_seconds=300)
    assert t[0].n_mensajes == 3 and t[0].n_rafagas == 2     # 5 min exactos = misma ráfaga; 6 min = nueva
    assert t[0].minutos_dentro_de_rafagas == 5 and t[0].minutos_transcurridos == 11


def test_mismo_autor_tras_cambio_de_sesion_es_otro_turno():
    m = msgs([('9:00 AM', 'Ana'), ('9:05 AM', 'Beto'), ('9:10 PM', 'Beto')])
    assert [(t.participante, t.sesion) for t in build_turns(m)] == [('A', 0), ('B', 0), ('B', 1)]


def test_sistema_se_omite_y_no_rompe_el_turno():
    texto = ('5/13/26, 9:00 AM - Ana: a\n5/13/26, 9:01 AM - Messages and calls are end-to-end encrypted.\n'
             '5/13/26, 9:02 AM - Ana: b\n5/13/26, 9:03 AM - Beto: c\n')
    res = parse_text(texto)
    assert any(m.tipo == 'system' for m in res.messages)
    assert [t.n_mensajes for t in build_turns(res.messages)] == [2, 1]


def test_fuera_de_orden_no_corta_ni_reordena():
    m = msgs([('9:10 AM', 'Ana'), ('9:05 AM', 'Ana'), ('9:20 AM', 'Beto')])
    t = build_turns(m)
    assert t[0].n_mensajes == 2 and t[0].tiene_fuera_de_orden and t[0].silencios_minutos == (-5.0,)
    assert [x.seq for x in m] == sorted(x.seq for x in m)


def test_no_segmenta_sin_analisis_habilitado():
    res = importar(*CHATS[1])
    with pytest.raises(ValueError):
        turns_from_result(res)                               # falta confirmar el tipo de conversación
    assert len(turns_from_result(res.confirm_individual())) == 56


def test_no_segmenta_con_fecha_ambigua():
    res = parse_text('1/5/26, 9:00 AM - Ana: a\n1/5/26, 9:01 AM - Beto: b\n')
    assert res.messages is None                              # bloqueada: no hay mensajes que segmentar


def test_repr_sin_contenido():
    t = build_turns(msgs([('9:00 AM', 'Ana'), ('9:01 AM', 'Beto')]))
    assert 'Ana' not in repr(t) and 'Beto' not in repr(t)

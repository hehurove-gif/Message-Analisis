"""Criterios de salida de las Fases 3 y 4 con chats sintéticos largos (tests/synth_chats.py).

FASE 3 — los resultados del sistema coinciden con el lector de referencia INDEPENDIENTE (tools/referencia/ref_latency.py,
que no comparte código con el sistema) en turnos, sesiones, latencias y participación. No sustituye la revisión manual
de 5 sesiones reales (docs/reporte_pruebas_fase_3_4.md §3), que solo puede hacer el usuario en local.
FASE 4 — el detector de cambio sostenido marca el enfriamiento sintético y no lanza falsas alarmas en el chat equilibrado."""
import os
import re
import sys

import pytest

from metrics.latency import latency_summary
from metrics.participation import participation
from metrics.trends import trends
from parsers import parse_text
from tests.synth_chats import build_chat, build_text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
import ref_latency as R  # noqa: E402

GAP = 6


def _ref(tmp_path, text):
    p = tmp_path / 'chat.txt'
    # el lector de referencia espera el encabezado sin coma ('05/10/2026 09:00 - '); mismo contenido y horas
    p.write_text(re.sub(r'(?m)^(\d\d/\d\d/\d{4}), ', r'\1 ', text), encoding='utf-8')
    return R.load(str(p))


@pytest.mark.parametrize('kw', [{'seed': 1}, {'seed': 2, 'cool_from_month': 5}, {'seed': 3, 'months': 4}])
def test_fase3_sistema_coincide_con_referencia(tmp_path, kw):
    text = build_text(**kw)
    msgs = _ref(tmp_path, text)
    first = msgs[0]['who']                                   # el sistema nombra A al primero que aparece
    ab = {first: 'A', next(m['who'] for m in msgs if m['who'] != first): 'B'}
    ref = R.summary(msgs, GAP)
    sysm = parse_text(text, date_order_hint='dmy').messages
    lat, part = latency_summary(sysm), participation(sysm)

    assert lat['n_turnos'] == ref['turnos']
    assert part['por_participante']['A']['turnos'] == ref['turnos_por_autor'][first]
    assert part['por_participante']['A']['mensajes'] == sum(m['who'] == first for m in msgs)
    assert part['por_participante']['B']['mensajes'] == sum(m['who'] != first for m in msgs)
    ag = lat['agregado']
    for k_sys, k_ref in (('n', 'n'), ('mediana_general', 'mediana_general'), ('n_dentro', 'n_dentro'),
                         ('mediana_dentro', 'mediana_dentro'), ('n_entre', 'n_entre'), ('mediana_entre', 'mediana_entre')):
        assert ag[k_sys] == ref['agregado'][k_ref], k_sys
    for who, tag in ab.items():
        s, r = lat['por_participante_que_interviene'][tag], ref['por_autor'][who]
        assert (s['n'], s['n_dentro'], s['n_entre']) == (r['n'], r['n_dentro'], r['n_entre']), tag
        assert (s['mediana_general'], s['mediana_dentro'], s['mediana_entre']) == \
               (r['mediana_general'], r['mediana_dentro'], r['mediana_entre']), tag


@pytest.mark.parametrize('seed', range(1, 9))
def test_fase4_chat_equilibrado_sin_falsas_alarmas(seed):
    r = trends(build_chat(seed))
    detectados = {k: v for k, v in r['cambios_sostenidos'].items() if v.get('detectado')}
    assert detectados == {}, detectados


@pytest.mark.parametrize('seed', range(1, 6))
def test_fase4_detecta_el_enfriamiento(seed):
    r = trends(build_chat(seed, cool_from_month=5))
    ch = r['cambios_sostenidos']
    assert ch['dias_activos']['detectado'] and ch['dias_activos']['direccion'] == 'baja'
    assert ch['dias_activos']['desde'] in ('2025-06', '2025-07', '2025-08')      # con retraso de ≈ media ventana
    assert any(ch[s].get('detectado') and ch[s]['direccion'] == 'sube' for s in ('latencia_A', 'latencia_B'))
    base = [p['dias_activos'] for p in r['periodos'][:4]]
    fin = [p['dias_activos'] for p in r['periodos'][-3:]]
    assert min(base) > max(fin)                                                   # la cifra cruda también lo muestra

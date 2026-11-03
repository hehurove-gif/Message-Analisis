"""Parser de WhatsApp contra los fixtures (cada .txt con su .esperado.json) y las 10 invariantes del
contrato v0.2. Los fixtures son SIMULADOS: que estas pruebas pasen no demuestra compatibilidad con
exportaciones reales de WhatsApp (ver docs/limitaciones_y_formatos_pendientes.md)."""
import glob
import json
import os

import pytest

from parsers import parse_bytes, parse_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp')
FIXTURES = sorted(glob.glob(os.path.join(FIX, '*.txt')))
IDS = [os.path.basename(p)[:-4] for p in FIXTURES]
NO_COMPARAR = {'fixture', 'origen', 'notas', 'mensajes_esperados', 'mapa_anonimizacion_esperado',
               'limitacion_conocida'}


def expected(path):
    with open(path[:-4] + '.esperado.json', encoding='utf-8') as f:
        return json.load(f)


def decoded_lines(path):
    """Líneas del archivo calculadas de forma independiente del parser."""
    with open(path, 'rb') as f:
        text = f.read().decode('utf-8').lstrip('﻿')
    lines = text.replace('\r\n', '\n').split('\n')
    if lines and lines[-1] == '':
        lines.pop()
    return lines


@pytest.fixture(params=FIXTURES, ids=IDS)
def case(request):
    path = request.param
    return path, expected(path), parse_file(path)


# ---------- fixture vs .esperado.json ----------

def test_reporte_coincide_con_esperado(case):
    path, exp, res = case
    rep = res.to_report_dict()
    for k, v in exp.items():
        if k in NO_COMPARAR:
            continue
        assert rep.get(k) == v, f'{k} difiere en {os.path.basename(path)}'


def test_mensajes_coinciden_con_esperado(case):
    _, exp, res = case
    if exp.get('mensajes_esperados') is None:
        assert res.messages is None
    else:
        assert [m.to_dict() for m in res.messages] == exp['mensajes_esperados']


def test_mapa_de_anonimizacion(case):
    _, exp, res = case
    if 'mapa_anonimizacion_esperado' in exp:
        assert res.anonymization_map() == exp['mapa_anonimizacion_esperado']


# ---------- invariantes del contrato ----------

def test_inv1_toda_linea_tiene_una_disposicion(case):
    path, _, res = case
    rep = res.report
    if rep['lineas_totales'] is None:          # F04: no hubo texto decodificado
        return
    d = rep['lineas_por_disposicion']
    assert sum(d.values()) == rep['lineas_totales'] == len(decoded_lines(path))


def test_inv2_todo_encabezado_produce_un_mensaje(case):
    _, _, res = case
    rep = res.report
    if rep['lineas_por_disposicion'] is None:
        return
    assert rep['lineas_por_disposicion']['encabezado'] == sum(rep['mensajes_por_tipo'].values())
    if res.messages is not None:
        assert len(res.messages) == sum(rep['mensajes_por_tipo'].values())


def test_inv3_mensajes_system_sin_participante(case):
    _, _, res = case
    for m in res.messages or ():
        assert (m.participante is None) == (m.tipo == 'system')


def test_inv4_seq_consecutivo(case):
    _, _, res = case
    assert [m.seq for m in res.messages or ()] == list(range(1, len(res.messages or ()) + 1))


def test_inv5_rangos_no_se_solapan(case):
    _, _, res = case
    prev = 0
    for m in res.messages or ():
        assert m.linea_inicial <= m.linea_final
        assert m.linea_inicial > prev
        prev = m.linea_final


def test_inv6_ninguna_linea_desaparece(case):
    path, _, res = case
    rep = res.report
    if rep['lineas_totales'] is None:
        return
    lines = decoded_lines(path)
    unproc = {x['linea'] for x in rep['lineas_no_procesadas']}
    assert len(unproc) == len(rep['lineas_no_procesadas']) == rep['lineas_por_disposicion']['no_procesada']
    assert all(x['motivo'] for x in rep['lineas_no_procesadas'])
    nonblank = {i for i, t in enumerate(lines, 1) if t.strip()}
    if res.messages is None:
        # rechazo o bloqueo: no hay mensajes, pero la cuenta de líneas sigue cuadrando
        d = rep['lineas_por_disposicion']
        assert d['en_blanco'] == len(lines) - len(nonblank)
        return
    in_msgs = set()
    for m in res.messages:
        in_msgs |= {i for i in range(m.linea_inicial, m.linea_final + 1) if i in nonblank}
    assert not (in_msgs & unproc), 'una línea no procesada quedó dentro de un mensaje'
    assert in_msgs | unproc == nonblank, 'hay líneas no vacías sin mensaje ni motivo'


def test_inv7_orden_de_origen(case):
    _, _, res = case
    lines = [(m.linea_inicial, m.seq) for m in res.messages or ()]
    assert lines == sorted(lines)               # nunca se reordena por timestamp


def test_inv8_anonimizacion_fuera_del_reporte(case):
    _, _, res = case
    blob = json.dumps(res.to_report_dict(), ensure_ascii=False) + repr(res)
    for name in res.anonymization_map():
        assert name not in blob
    for m in res.messages or ():
        if len(m.texto) >= 8:                  # textos cortos ('A', 'ok') coincidirían por azar
            assert m.texto not in blob and m.texto not in repr(m)
    assert 'mapa_anonimizacion' not in blob


def test_inv9_fechas_ambiguas_no_se_normalizan_sin_pista(case):
    path, _, res = case
    if res.report['orden_fecha'] == 'ambiguo':
        assert res.report['decision_importacion'] == 'blocked_pending_confirmation'
        assert res.messages is None and res.report['rango_fechas'] is None
    for m in res.messages or ():
        assert (m.timestamp_local is None) == (res.report['orden_fecha'] == 'ambiguo')


def test_inv10_grupos_no_se_aprueban_automaticamente(case):
    _, _, res = case
    rep = res.report
    if rep['estado_tipo_conversacion'].startswith('rejected'):
        assert rep['decision_importacion'] == 'rejected' and res.messages is None
        with pytest.raises(ValueError):
            res.confirm_individual()
    # el parser nunca declara que la conversación sea individual ni habilita el análisis
    assert rep['analisis_habilitado'] is False and res.analysis_enabled is False
    assert rep['estado_tipo_conversacion'] in {
        'rejected_more_than_two_participants', 'rejected_fewer_than_two_participants',
        'rejected_possible_group', 'pending_confirmation', 'not_evaluated'}


# ---------- casos específicos ----------

def fx(name):
    return os.path.join(FIX, name + '.txt')


def test_f03_formato_mixto_con_empate():
    res = parse_file(fx('F03_formato_mixto_empate'))
    assert res.report['advertencias'] == ['FORMAT_AMBIGUOUS']
    assert res.messages is None and res.report['decision_importacion'] == 'rejected'


def test_f04_bytes_utf8_invalidos():
    res = parse_file(fx('F04_bytes_utf8_invalidos'))
    assert res.report['advertencias'] == ['ENCODING_ERROR'] and res.messages is None


def test_bytes_invalidos_en_memoria():
    res = parse_bytes(b'14/10/2026, 09:10 - Ana: hola \xe9\xff\n')
    assert res.report['advertencias'] == ['ENCODING_ERROR']


def test_d07_pendiente_de_revision_y_sin_analisis_automatico():
    res = parse_file(fx('D07_lineas_desconocidas'))
    rep = res.report
    assert res.accepted and rep['estado_calidad'] == 'pendiente_revision_calidad'
    assert rep['procesamiento_completo'] is False and 'UNPROCESSED_LINES' in rep['advertencias']
    assert 'REVISAR_LINEAS_NO_PROCESADAS' in rep['requisitos_analisis']
    assert len(res.messages) == 5                       # los reconocidos sí se importan
    confirmed = res.confirm_individual()
    assert confirmed.analysis_enabled is False          # confirmar el tipo no resuelve las pérdidas


def test_d07_solo_se_habilita_aceptando_expresamente_cada_perdida():
    res = parse_file(fx('D07_lineas_desconocidas')).confirm_individual()
    lines = [x['linea'] for x in res.report['lineas_no_procesadas']]
    assert res.accept_losses(lines[:-1]).analysis_enabled is False       # parcial: no basta
    ok = res.accept_losses(lines)
    assert ok.analysis_enabled is True
    assert ok.to_report_dict()['perdidas_aceptadas'] == sorted(lines)
    assert ok.to_report_dict()['procesamiento_completo'] is False        # la pérdida sigue registrada
    with pytest.raises(ValueError):
        res.accept_losses([2])                                           # línea reconocida, no una pérdida


def test_archivo_limpio_requiere_confirmar_tipo_para_habilitar_analisis():
    res = parse_file(fx('A01_android24_coma_es'))
    assert res.analysis_enabled is False and res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION']
    assert res.confirm_individual().analysis_enabled is True


def test_c01_bloquea_y_c02_rechaza():
    c01, c02 = parse_file(fx('C01_fecha_ambigua')), parse_file(fx('C02_fecha_orden_contradictorio'))
    assert c01.report['decision_importacion'] == 'blocked_pending_confirmation' and c01.messages is None
    assert c02.report['decision_importacion'] == 'rejected' and c02.messages is None


def test_c01_se_resuelve_solo_con_pista_explicita():
    res = parse_file(fx('C01_fecha_ambigua'), date_order_hint='dmy')
    assert res.report['orden_fecha'] == 'dmy_por_indicacion' and res.accepted
    assert res.messages[0].timestamp_local == '2026-10-03T' + res.messages[0].timestamp_local[11:]
    mdy = parse_file(fx('C01_fecha_ambigua'), date_order_hint='mdy')
    assert mdy.messages[0].timestamp_local.startswith('2026-03-10')
    assert mdy.messages[0].timestamp_original == res.messages[0].timestamp_original


def test_pista_no_pisa_la_evidencia_de_los_datos():
    # A01 tiene un día > 12: el orden queda resuelto por dato aunque la pista diga lo contrario
    res = parse_file(fx('A01_android24_coma_es'), date_order_hint='mdy')
    assert res.report['orden_fecha'].endswith('_resuelto_por_dato')


def test_contenido_original_conserva_marcas_rtl_y_normalizado_es_aparte():
    res = parse_file(fx('D01_invisibles_bom'))
    originales = ''.join(m.texto for m in res.messages)
    assert '‎' in originales or '‏' in originales
    for m in res.messages:
        assert not set(m.texto_normalizado) & {'‎', '‏', '﻿', ' '}


def test_timestamp_original_conserva_u202f():
    res = parse_file(fx('A03_android12_es_nnbsp'))
    assert any(' ' in m.timestamp_original for m in res.messages)


SINTETICOS = [('00_escenarios_validacion', 'dmy'), ('01_amistad_equilibrada', None),
              ('02_interes_romantico_unilateral', None)]


@pytest.mark.parametrize('nombre,hint', SINTETICOS)
def test_chats_sinteticos_coinciden_con_el_lector_de_referencia(nombre, hint):
    import sys
    sys.path.insert(0, os.path.join(ROOT, 'tools', 'referencia'))
    import ref_latency as R
    path = os.path.join(ROOT, 'data', 'synthetic', nombre + '.txt')
    res = parse_file(path, date_order_hint=hint)
    assert res.accepted and res.report['lineas_no_procesadas'] == []
    ref = R.load(path)
    mine = [m for m in res.messages if m.tipo != 'system']
    assert len(mine) == len(ref)
    labels = res.anonymization_map()
    for a, b in zip(mine, ref):
        assert a.timestamp_local == b['ts'].isoformat()
        assert a.participante == labels[b['who']]
        assert a.texto == b['txt'] and a.linea_inicial == b['line']


def test_chat_00_sin_pista_queda_bloqueado():
    res = parse_file(os.path.join(ROOT, 'data', 'synthetic', '00_escenarios_validacion.txt'))
    assert res.report['decision_importacion'] == 'blocked_pending_confirmation'

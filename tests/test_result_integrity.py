"""Integridad de ImportResult: el reporte público no puede alterar las decisiones internas, y la confirmación
de tipo solo procede sobre importaciones aceptadas y pendientes de confirmación."""
import os

import pytest

from parsers import parse_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(ROOT, 'tests', 'fixtures', 'whatsapp')


def fx(name, **kw):
    return parse_file(os.path.join(FIX, name + '.txt'), **kw)


def test_modificar_el_reporte_publico_no_habilita_el_analisis():
    res = fx('A01_android24_coma_es')
    assert res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION']
    rep = res.report
    rep['requisitos_analisis'].clear()                       # lista anidada
    rep['requisitos_analisis'].append('OTRO')
    rep['decision_importacion'] = 'accepted'                 # campos
    rep['estado_tipo_conversacion'] = 'pending_confirmation'
    rep['lineas_no_procesadas'].append({'linea': 1, 'motivo': 'X'})
    rep['advertencias'] = []
    assert res.analysis_enabled is False
    assert res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION']
    assert res.report['requisitos_analisis'] == ['CONFIRMAR_TIPO_CONVERSACION']
    assert res.report['lineas_no_procesadas'] == []


def test_modificar_to_report_dict_no_altera_el_resultado():
    res = fx('D07_lineas_desconocidas')
    d = res.to_report_dict()
    d['requisitos_analisis'].clear()
    d['analisis_habilitado'] = True
    d['lineas_no_procesadas'].clear()
    d['decision_importacion'] = 'rejected'
    assert res.analysis_enabled is False and res.accepted
    assert res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION', 'REVISAR_LINEAS_NO_PROCESADAS']
    assert res.to_report_dict()['analisis_habilitado'] is False
    assert len(res.report['lineas_no_procesadas']) == 9


def test_cada_acceso_al_reporte_es_una_copia_nueva():
    res = fx('A01_android24_coma_es')
    assert res.report is not res.report and res.report == res.report
    assert res.report['requisitos_analisis'] is not res.report['requisitos_analisis']


def test_el_reporte_de_origen_no_queda_enlazado():
    from parsers.results import ImportResult
    original = {'decision_importacion': 'accepted', 'estado_tipo_conversacion': 'pending_confirmation',
                'requisitos_analisis': ['CONFIRMAR_TIPO_CONVERSACION'], 'lineas_no_procesadas': [],
                'estado_calidad': 'x'}
    res = ImportResult(_report=original, messages=())
    original['requisitos_analisis'].clear()
    assert res.pending_requirements == ['CONFIRMAR_TIPO_CONVERSACION']


def test_el_analisis_solo_se_habilita_con_las_acciones_explicitas():
    res = fx('D07_lineas_desconocidas')
    lines = [x['linea'] for x in res.report['lineas_no_procesadas']]
    assert res.analysis_enabled is False
    assert res.confirm_individual().analysis_enabled is False       # falta resolver pérdidas
    assert res.accept_losses(lines).analysis_enabled is False       # falta confirmar el tipo
    assert res.confirm_individual().accept_losses(lines).analysis_enabled is True
    assert res.accept_losses(lines).confirm_individual().analysis_enabled is True
    # el resultado original sigue sin cambios (los objetos son inmutables)
    assert res.analysis_enabled is False and res.to_report_dict()['perdidas_aceptadas'] == []


def test_no_se_puede_reasignar_el_estado_interno():
    res = fx('A01_android24_coma_es')
    with pytest.raises(Exception):
        res._confirmed = True
    with pytest.raises(Exception):
        res.report = {}


def test_repr_y_reportes_no_exponen_el_mapa():
    res = fx('A01_android24_coma_es')
    nombres = list(res.anonymization_map())
    blob = repr(res) + str(res.report) + str(res.to_report_dict()) + repr(res.messages)
    assert nombres and all(n not in blob for n in nombres)
    assert '_anonymization' not in blob and 'mapa' not in blob.lower().replace('mapa_anonimizacion_esperado', '')


# ---- confirm_individual ----

def test_confirmar_sobre_c01_bloqueado_falla():
    res = fx('C01_fecha_ambigua')
    assert res.report['decision_importacion'] == 'blocked_pending_confirmation'
    assert res.report['estado_tipo_conversacion'] == 'pending_confirmation'    # el tipo sí está pendiente...
    with pytest.raises(ValueError):                                             # ...pero no está aceptada
        res.confirm_individual()
    assert res.pending_requirements == ['INDICAR_ORDEN_FECHA'] and res.analysis_enabled is False


@pytest.mark.parametrize('nombre', ['E01_tres_autores', 'E02_dos_autores_eventos_grupo', 'E05_un_solo_autor',
                                    'C02_fecha_orden_contradictorio', 'F01_formato_no_reconocido',
                                    'F02_archivo_vacio', 'F03_formato_mixto_empate',
                                    'F04_bytes_utf8_invalidos'])
def test_confirmar_sobre_rechazados_falla(nombre):
    res = fx(nombre)
    assert res.report['decision_importacion'] == 'rejected'
    with pytest.raises(ValueError) as e:
        res.confirm_individual()
    assert 'Zoilo' not in str(e.value)
    assert res.analysis_enabled is False


def test_c01_con_pista_si_admite_confirmacion():
    res = fx('C01_fecha_ambigua', date_order_hint='dmy')
    assert res.accepted and res.confirm_individual().analysis_enabled is True


def test_confirmar_aceptada_conserva_el_comportamiento():
    res = fx('A01_android24_coma_es').confirm_individual()
    assert res.to_report_dict()['tipo_conversacion_confirmado'] is True and res.analysis_enabled is True

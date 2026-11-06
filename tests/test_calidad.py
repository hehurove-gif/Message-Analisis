"""Estado de calidad: una importación aceptada con avisos sin catalogar, fuera de orden o uniones de autores
NO es 'sin_observaciones_de_calidad'. Las líneas fuera de orden se reportan por número de línea."""
import os

from parsers import parse_file, parse_text

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures', 'whatsapp')


def test_fuera_de_orden_da_observaciones_y_lista_lineas():
    rep = parse_file(os.path.join(FIX, 'D04_fuera_de_orden.txt')).report
    assert rep['estado_calidad'] == 'con_observaciones' and rep['procesamiento_completo'] is True
    assert len(rep['lineas_fuera_de_orden']) == rep['timestamps_fuera_de_orden'] > 0


def test_archivo_limpio_sigue_sin_observaciones():
    rep = parse_file(os.path.join(FIX, 'A01_android24_coma_es.txt')).report
    assert rep['estado_calidad'] == 'sin_observaciones_de_calidad' and rep['lineas_fuera_de_orden'] == []


def test_union_de_autores_deja_observaciones():
    chat = ('5/13/26, 9:10 AM - Ana: hola\n5/13/26, 9:11 AM - Beto - Zeta: x\n5/13/26, 9:12 AM - Zeta: y\n')
    rep = parse_text(chat, accept_suspected_aliases=True).report
    assert rep['decision_importacion'] == 'accepted' and rep['estado_calidad'] == 'con_observaciones'


def test_lineas_no_procesadas_siguen_pendientes_de_revision():
    rep = parse_file(os.path.join(FIX, 'D07_lineas_desconocidas.txt')).report
    assert rep['estado_calidad'] == 'pendiente_revision_calidad'

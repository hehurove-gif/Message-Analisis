"""Fase 6, paso 4: reglas nuevas del léxico (ejemplos inventados). ≥ 6 positivos y ≥ 6 negativos por regla.
Las reglas .v1 anteriores no se tocan: sus conteos de la Fase 5 siguen igual."""
import pytest

from nlp.lexicon import detect, load_lexicon

LEX = load_lexicon()


def hits(text, rule_id):
    h, _ = detect(text, LEX)
    return {f for r, f, _ in h if r.id == rule_id}


POS = {
    'declaracion.romantica.v1': ['me gustas', 'oye, me gustas mucho', 'estoy enamorado de ti', 'estoy enamorada de ti', 'me enamoré de ti',
                                 'siento algo por ti', 'creo que siento cosas por ti', 'estoy muy enamorada de ti'],
    'declaracion.propuesta_pareja.v1': ['¿quieres ser mi novia?', 'quieres ser mi novio', '¿quieres ser mi pareja?', '¿quieres que seamos novios?',
                                        'quieres que seamos pareja', '¿te gustaría ser mi novia?'],
    'vida_sentimental.v1': ['¿tienes novio?', '¿tienes novia?', 'oye, ¿tienes pareja?', '¿andas saliendo con alguien?', '¿estás saliendo con alguien?',
                            '¿estás soltera?', '¿eres soltero?', '¿te gusta alguien?', '¿sales con alguien?'],
    'verse.plan_ampliado.v1': ['¿vamos tú y yo el sábado?', 'salimos los dos', 'podríamos salir a cenar', 'podríamos vernos pronto', 'déjame invitarte a comer',
                               'quiero invitarte al cine', '¿te gustaría salir el viernes?', 'una cita contigo'],
    'apodo.adjetivo_vocativo.v1': ['buenas noches, linda', 'buenos días hermosa', 'hola, guapo', 'descansa, preciosa', 'cuídate, bonita',
                                   'buenas tardes guapa', 'adiós, lindo'],
}
NEG = {
    'declaracion.romantica.v1': ['me gusta tu idea', 'me gustan los tacos', 'estoy enamorado de esa canción', 'siento algo raro en la pierna',
                                 'me gustaría ir al cine', 'qué gustas de comer', 'te gustas mucho jaja'],
    'declaracion.propuesta_pareja.v1': ['quieres ser mi amigo', '¿quieres ser mi compañero de equipo?', 'quieres una pareja de baile', 'quiero ser mejor',
                                        '¿quieres que seamos puntuales?', 'te gustaría ser doctora'],
    'vida_sentimental.v1': ['tengo novio', 'mi hermana tiene novia', '¿tienes pareja de baile?', 'estoy soltera', '¿tienes tarea?',
                            '¿tienes pareja para el proyecto?', 'sales con tu mamá'],
    'verse.plan_ampliado.v1': ['vamos a la escuela', 'podríamos revisar el proyecto', 'gracias por invitarme', 'te invitaron a la fiesta', 'una cita médica',
                               'podríamos mejorar el reporte', 'no podemos salir'],
    'apodo.adjetivo_vocativo.v1': ['qué linda foto', 'ella es muy linda', 'buenos días, hermosa mañana', 'hola, qué bonita casa', 'tu hermana es guapa',
                                   'buenas noches a todos', 'ese es un lindo detalle'],
}


@pytest.mark.parametrize('rid', sorted(POS))
def test_positivos(rid):
    assert len(POS[rid]) >= 6
    for t in POS[rid]:
        assert 'afirmativa' in hits(t, rid), (rid, t)


@pytest.mark.parametrize('rid', sorted(NEG))
def test_negativos(rid):
    assert len(NEG[rid]) >= 6
    for t in NEG[rid]:
        assert 'afirmativa' not in hits(t, rid), (rid, t)


def test_negada_y_pregunta_se_cuentan_aparte():
    assert hits('no me gustas', 'declaracion.romantica.v1') == {'negada'}
    assert hits('¿te gusta alguien?', 'vida_sentimental.v1') == {'afirmativa'}      # la pregunta cuenta: ES la pregunta íntima
    assert hits('¿quieres ser mi novia?', 'declaracion.propuesta_pareja.v1') == {'afirmativa'}


def test_adjetivo_vocativo_es_ambiguo():
    r = next(r for r in LEX.rules if r.id == 'apodo.adjetivo_vocativo.v1')
    assert r.ambiguo and r.categoria == 'apodo_carinoso'


def test_las_reglas_v1_anteriores_siguen_igual():
    # un cumplido físico no se convierte en apodo; el apodo fuerte sigue sin ser ambiguo
    assert not hits('te ves hermosa hoy', 'apodo.adjetivo_vocativo.v1')
    assert next(r for r in LEX.rules if r.id == 'apodo.fuerte.v1').ambiguo is False
    assert next(r for r in LEX.rules if r.id == 'apodo.general.v1').ambiguo is True


def test_ids_unicos_y_con_version():
    ids = [r.id for r in LEX.rules]
    assert len(ids) == len(set(ids))
    nuevas = ['declaracion.romantica.v1', 'declaracion.propuesta_pareja.v1', 'vida_sentimental.v1', 'verse.plan_ampliado.v1',
              'apodo.adjetivo_vocativo.v1']
    assert all(i in ids for i in nuevas)

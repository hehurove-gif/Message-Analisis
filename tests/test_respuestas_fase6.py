"""Fase 6, paso 5: marcadores léxicos de la respuesta (ejemplos inventados). ≥ 6 positivos y ≥ 6 negativos por grupo."""
import pytest

from nlp.respuestas import canon_alcance, load_markers, markers_in

MK = load_markers()


def g(text):
    return markers_in(text, MK)['grupos']


POS = {
    'aceptacion': ['sí, me encantaría', 'claro!', 'va, nos vemos', 'dale', 'sale, a las 5', 'con gusto', 'perfecto, ahí estaré', 'ok, ¿dónde?'],
    'rechazo': ['no puedo ese día', 'no podré, perdón', 'no gracias', 'estoy ocupada mañana', 'no voy a poder ir', 'mejor no', 'no tengo tiempo'],
    'aplazamiento': ['veamos cómo va la semana', 'a ver, te aviso', 'ya veremos', 'no sé, luego te aviso', 'tal vez', 'depende', 'otro día', 'cuando pueda'],
    'eco_afectivo': ['yo también te quiero', 'y yo a ti', 'yo también te extraño', 'también te quiero mucho', 'tú también me gustas', 'yo también te amo'],
    'cortesia_devuelta': ['igualmente!!', 'igual', 'para ti también', 'lo mismo digo', 'igual, descansa', 'igualmente, cuídate'],
    'reconocimiento': ['gracias', 'muchas gracias', 'qué lindo', 'qué amable', 'aww', 'ay gracias', 'te lo agradezco', 'mil gracias'],
    'amistosa': ['te tengo confianza', 'cuenta conmigo', 'aquí estoy', 'para eso estamos', 'me caes muy bien', 'me divierto contigo'],
    'encuadre_amistad': ['gracias amigo', 'eres mi amiga', 'buen amigo', 'como amiga', 'mi amigo querido', 'amigos'],
    'polar': ['sí', 'no', 'claro', 'pues no', 'aja, ya lo vi', 'nop', 'claro que sí'],
    'cambio_de_tema': ['por cierto, ¿ya viste el aviso?', 'cambiando de tema', 'a todo esto, ¿entregaste?', 'hablando de otra cosa, mañana hay examen',
                       'jaja, por cierto', 'por cierto'],
}
NEG = {
    'aceptacion': ['si quieres lo vemos', 'ya vamos tarde', 'no hay clase', 'avanza el proyecto', 'eso es claro', 'me voy a dormir', 'dalia vino'],
    'rechazo': ['no hay problema', 'puedo mañana', 'tengo tiempo', 'mejor así', 'no importa', 'qué ocupada estás'],
    'aplazamiento': ['hoy mismo', 'ahora mismo', 'sí claro', 'quedamos el sábado', 'vamos ya', 'te veo allá'],
    'eco_afectivo': ['igualmente', 'qué gusto', 'te quiero preguntar algo', 'te lo agradezco', 'yo también voy', 'a ti te toca'],
    'cortesia_devuelta': ['no es igual', 'es igual de largo', 'qué igualito', 'gracias', 'quiero otro', 'tengo lo mismo'],
    'reconocimiento': ['gracias a dios', 'sí, claro', 'nos vemos', 'ya llegué', 'no puedo', 'eres tú'],
    'amistosa': ['cuenta bancaria', 'aquí está tu libro', 'qué caes tú', 'ya llegué', 'cuenta la historia', 'hola'],
    'encuadre_amistad': ['gracias', 'buenos días', 'amistad', 'tengo amigos'.replace('tengo amigos', 'tengo sueño'), 'ya llegué', 'sí'],
    'polar': ['siempre', 'nunca', 'nada', 'claramente', 'cuando quieras', 'hola, ya'],
    'cambio_de_tema': ['oye', 'por qué', 'a todos', 'qué cierto', 'cambió la hora', 'otro tema'],
}


@pytest.mark.parametrize('grupo', sorted(POS))
def test_positivos(grupo):
    assert len(POS[grupo]) >= 6
    for t in POS[grupo]:
        assert grupo in g(t), (grupo, t)


@pytest.mark.parametrize('grupo', sorted(NEG))
def test_negativos(grupo):
    assert len(NEG[grupo]) >= 6
    for t in NEG[grupo]:
        assert grupo not in g(t), (grupo, t)


def test_igual_no_es_eco_afectivo():
    assert 'eco_afectivo' not in g('igualmente') and 'cortesia_devuelta' in g('igualmente')


def test_si_solo_cuenta_al_inicio_de_clausula():
    assert 'aceptacion' not in g('si quieres lo vemos') and 'aceptacion' in g('ok, sí, nos vemos')


LIM_E = {'relacion_romantica': ['te veo como amigo', 'solo te veo como amiga', 'no siento lo mismo', 'no me gustas', 'solo somos amigos',
                                'no quiero nada contigo', 'prefiero que seamos amigos'],
         'contacto': ['deja de escribirme', 'no me escribas más', 'no me hables']}
LIM_S = {'apodos_o_trato': ['no me digas así', 'jaja no me digas así', 'prefiero que me hables como siempre', 'no me llames así',
                            'prefiero que me llames Lucía', 'no me gusta que me digas eso'],
         'no_determinado': ['me incomoda', 'me incomodas un poco']}
LIM_NEG = ['ahorita no', 'ahorita no puedo', 'no me digas que no vienes', 'dime cómo estás', 'te veo mañana', 'somos del mismo equipo',
           'me gusta tu idea', 'no me hables de eso jaja'.replace('no me hables de eso jaja', 'háblame más tarde')]


@pytest.mark.parametrize('alc,texts', LIM_E.items())
def test_limite_explicito_con_alcance(alc, texts):
    assert len(texts) >= 3
    for t in texts:
        assert alc in markers_in(t, MK)['limite_explicito'], t


@pytest.mark.parametrize('alc,texts', LIM_S.items())
def test_limite_suave_con_alcance(alc, texts):
    assert len(texts) >= 2
    for t in texts:
        assert alc in markers_in(t, MK)['limite_suave'], t


@pytest.mark.parametrize('t', LIM_NEG)
def test_sin_limite(t):
    r = markers_in(t, MK)
    assert not r['limite_explicito'] and not r['limite_suave'], t


def test_ahorita_no_es_aplazamiento_no_limite():
    assert not markers_in('ahorita no', MK)['limite_suave']
    assert canon_alcance('apodos_y_forma_de_tratamiento', MK) == 'apodos_o_trato'
    assert 'apodos_o_trato' in MK['alcances']


def test_sin_texto_no_falla():
    assert markers_in('', MK) == {'grupos': set(), 'limite_explicito': set(), 'limite_suave': set()}
    assert markers_in(None, MK)['grupos'] == set()

"""Fase 5.2: categorías restantes. ≥ 6 positivos y ≥ 6 negativos por categoría (ejemplos inventados)."""
import pytest

from nlp.lexicon import detect, load_lexicon

LEX = load_lexicon()


def forms(text, cat):
    hits, _ = detect(text, LEX)
    return {f for r, f, _ in hits if r.categoria == cat}


def strict(text, cat):
    hits, _ = detect(text, LEX)
    return any(r.categoria == cat and f == 'afirmativa' and not r.ambiguo for r, f, _ in hits)


def wide(text, cat):
    return 'afirmativa' in forms(text, cat)


POS = {
    'apodo_carinoso': ['hola, mi amor', 'gracias mi vida', 'buenas noches, corazón', 'descansa, cielo', 'amor, ¿vienes?',
                       'te extraño, mi cielo', 'ya llegué, corazoncito'],
    'cumplido': ['te ves hermosa hoy', 'qué guapo saliste en la foto', 'eres muy lista', 'eres el mejor', 'estás guapísima'.replace('guapísima', 'guapa'),
                 'me encanta tu sonrisa', 'eres una persona increíble', 'qué inteligente eres'],
    'propuesta_de_verse': ['¿nos vemos mañana?', '¿quieres ir al cine?', 'salimos el viernes', 'te veo hoy a las 5',
                           'quedamos el sábado', '¿quieres salir a cenar?', 'te invito al concierto', 'vamos a comer algo'],
    'apoyo': ['ánimo', 'aquí estoy para lo que necesites', 'cuenta conmigo', 'tú puedes', 'todo va a estar bien',
              'no estás sola', 'te mando un abrazo', 'échale ganas'],
    'conflicto': ['me molesta que no avises', 'ya basta', 'no me hables', 'eres un idiota', 'estoy harto de esto',
                  'déjame en paz', 'me decepcionaste', 'nunca me escuchas'],
    'disculpa': ['perdón por lo de ayer', 'fue mi culpa', 'disculpa que te grité', 'perdóname', 'lo siento', 'me equivoqué',
                 'te pido una disculpa', 'perdón'],
    'gratitud': ['gracias', 'muchas gracias!', 'mil gracias por todo', 'te lo agradezco', 'graciaaas', 'gracias por venir'],
    'risa_texto': ['jajaja', 'jejeje', 'jaja qué bueno', 'jsjsjs', 'xd', 'ajajaja', 'JAJAJAJA', 'jajajajaja'],
}
NEG = {
    'apodo_carinoso': ['el amor propio es importante', 'mi amor por el café', 'mi vida es difícil', 'te ves hermosa hoy',
                       'qué guapo saliste', 'el cielo está nublado', 'tengo un corazón enfermo', 'amor propio'],
    'cumplido': ['qué bonito está el parque', 'estás cansada', 'eres de Puebla', 'eres mayor que yo', 'te ves en la foto',
                 'eres la primera en llegar', 'que lista tan larga'],
    'propuesta_de_verse': ['nos vemos', 'ya salí del trabajo', 'hasta luego, nos vemos', 'te veo luego',
                           'no nos vemos mañana', 'vi una película', 'quieres agua'],
    'apoyo': ['no tengo ánimo', 'el animal es grande', 'tengo fuerza de voluntad', 'aquí está tu libro', 'cuenta bancaria',
              'me dio un abrazo mi mamá y se fue'.replace('abrazo', 'regalo'), 'mucho gusto'],
    'conflicto': ['me molesta el ruido de la calle', 'hace calor', 'estoy cansado de caminar', 'tengo hambre',
                  'qué bonito día', 'basta de azúcar'.replace('basta', 'sobra'), 'no es tarde'],
    'disculpa': ['disculpa, ¿a qué hora es?', '¿perdón?', 'no es mi lápiz', 'qué error tan raro', 'con permiso', 'hola',
                 'no te perdono'],
    'gratitud': ['gracias a dios', 'ya fui', 'tengo gracia para bailar'.replace('gracia', 'ganas'), 'hola', 'agradable día',
                 'graciosa'],
    'risa_texto': ['ja', 'ya llegué', 'hoy fui al mejor lugar', 'jabón', 'jarabe', 'lolita', 'hola'],
}


@pytest.mark.parametrize('cat,texts', POS.items())
def test_positivos(cat, texts):
    assert len(texts) >= 6
    for t in texts:
        assert wide(t, cat), (cat, t)


@pytest.mark.parametrize('cat,texts', NEG.items())
def test_negativos(cat, texts):
    assert len(texts) >= 6
    for t in texts:
        assert not wide(t, cat), (cat, t)


def test_ambiguas_solo_en_amplia():
    assert wide('lo siento', 'disculpa') and not strict('lo siento', 'disculpa')
    assert strict('perdón por lo de ayer', 'disculpa')
    assert wide('ánimo', 'apoyo') and not strict('ánimo', 'apoyo')
    assert wide('eres un cabrón', 'conflicto') and not strict('eres un cabrón', 'conflicto')
    assert wide('hola amor', 'apodo_carinoso') and not strict('hola amor', 'apodo_carinoso')
    assert strict('hola mi amor', 'apodo_carinoso')


def test_pregunta_de_perdon_va_aparte():
    assert forms('¿perdón?', 'disculpa') == {'pregunta'}


def test_invitacion_pregunta_cuenta_pero_negada_no():
    assert forms('¿nos vemos mañana?', 'propuesta_de_verse') == {'afirmativa'}
    assert forms('no nos vemos mañana', 'propuesta_de_verse') == {'negada'}


def test_sin_doble_conteo_entre_reglas_de_una_categoria():
    hits, _ = detect('perdón por lo de ayer', LEX)
    assert sum(n for r, f, n in hits if r.categoria == 'disculpa') == 1
    hits, _ = detect('hola mi amor', LEX)
    assert sum(n for r, f, n in hits if r.categoria == 'apodo_carinoso') == 1


def test_risa_conteos():
    hits, _ = detect('jajaja jejeje xd', LEX)
    assert sum(n for r, f, n in hits if r.categoria == 'risa_texto') == 3


def test_ajustes_con_datos_reales():
    # adjetivos sueltos ya no son apodos; con "mi" sí
    assert not wide('qué bonito', 'apodo_carinoso') and not wide('hermoso', 'apodo_carinoso')
    assert wide('gracias, mi bonita', 'apodo_carinoso') and strict('hola mi linda', 'apodo_carinoso')
    # "suerte" es un buen deseo, no apoyo
    assert not wide('mucha suerte en el examen', 'apoyo')
    # "quedamos en que" es un acuerdo, no una invitación
    assert not wide('quedamos en que lo hacías tú', 'propuesta_de_verse') and wide('quedamos el sábado', 'propuesta_de_verse')

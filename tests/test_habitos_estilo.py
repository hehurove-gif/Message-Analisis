"""Hábitos (hora/día/franja) y estilo (longitud, preguntas, emoji, mayúsculas): cifras conocidas, sin texto."""
from metrics.habits import habits
from metrics.style import is_question, is_uppercase, style
from parsers import parse_text

T = ('5/13/26, 1:00 AM - Ana: ¿cómo estás?\n5/13/26, 9:00 AM - Beto: bien 😊\n'
     '5/13/26, 9:01 AM - Beto: OYE MIRA\n5/16/26, 8:00 PM - Ana: cuándo vienes\n'
     '5/16/26, 8:05 PM - Beto: <Multimedia omitido>\n')


def test_habitos():
    h = habits(parse_text(T).messages)['por_participante']
    a, b = h['A'], h['B']
    assert a['por_hora'][1] == 1 and a['por_hora'][20] == 1 and a['n_mensajes'] == 2
    assert a['proporcion_por_franja'] == {'madrugada': 0.5, 'manana': 0.0, 'tarde': 0.0, 'noche': 0.5}
    assert a['proporcion_por_dia']['mie'] == 0.5 and a['proporcion_por_dia']['sab'] == 0.5   # 13/5/26 = miércoles
    assert b['hora_mas_frecuente'] == 9 and b['suficiencia_de_datos'] == 'insuficiente'


def test_estilo():
    s = style(parse_text(T).messages)['por_participante']
    assert s['A']['proporcion_preguntas'] == 1.0 and s['A']['palabras_mediana'] == 2
    b = s['B']
    assert (b['n_texto'], b['proporcion_con_emoji'], b['proporcion_mayusculas']) == (2, 0.5, 0.5)
    assert b['proporcion_media'] == round(1 / 3, 3)
    assert 'Ana' not in str(s) and 'estás' not in str(s)


def test_reglas_sueltas():
    assert is_question('Por qué no') and is_question('ok?') and not is_question('que bien')
    assert is_uppercase('HOLA!!') and not is_uppercase('OK') and not is_uppercase('Hola')

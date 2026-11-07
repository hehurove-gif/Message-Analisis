"""Contenido de turnos, risas, pausas largas e inicio del día: cifras conocidas y sin texto en la salida."""
from metrics.habits import habits
from metrics.latency import latency_summary
from metrics.style import style
from metrics.text_units import has_laugh, is_laugh_token, substantive_words
from metrics.turn_content import turn_content
from parsers import parse_text

LARGO = 'te cuento que hoy fui al centro a comprar los libros que faltaban y además pasé por la casa de mi tía'
T = (f'5/13/26, 9:00 AM - Ana: {LARGO}\n5/13/26, 9:01 AM - Beto: ok\n'
     f'5/13/26, 9:02 AM - Ana: y tú qué hiciste\n5/13/26, 9:03 AM - Beto: JAJAJA 👍\n'
     f'5/13/26, 9:04 AM - Ana: <Multimedia omitido>\n5/13/26, 9:05 AM - Beto: nada, fui a trabajar\n'
     f'5/14/26, 8:00 AM - Beto: buenos días\n5/14/26, 8:30 AM - Ana: hola\n')


def test_risas_y_palabras_sustantivas():
    assert all(is_laugh_token(x) for x in ['jaja', 'JAJAJA', 'jeje', 'haha', 'jsjsjs', 'xD'])
    assert not is_laugh_token('hola') and has_laugh('ok jaja')
    assert substantive_words('ok jajaja 👍 nos vemos mañana?') == ['nos', 'vemos', 'mañana']


def test_clasificacion_de_turnos():
    tc = turn_content(parse_text(T).messages)
    a, b = tc['por_participante']['A'], tc['por_participante']['B']
    assert (a['turnos_desarrollado'], a['turnos_breve'], a['turnos_minimo']) == (1, 2, 1)   # 'y tú qué…' es pregunta
    assert (b['turnos_minimo'], b['turnos_breve']) == (2, 2)
    p = tc['proporciones_entre_participantes']
    assert p['turnos']['A'] == 0.5 and p['turnos_desarrollados']['A'] == 1.0
    assert 'Ana' not in str(tc) and 'centro' not in str(tc)


def test_mayusculas_no_cuentan_risas():
    b = style(parse_text(T).messages)['por_participante']['B']
    assert b['proporcion_mayusculas'] == 0.0 and b['proporcion_con_risa'] == 0.25
    assert b['proporcion_solo_minimo'] == 0.5


def test_inicia_y_cierra_el_dia():
    h = habits(parse_text(T).messages)['por_participante']
    assert (h['A']['inicia_el_dia'], h['B']['inicia_el_dia']) == (1, 1)
    assert (h['A']['cierra_el_dia'], h['B']['cierra_el_dia']) == (1, 1)
    assert h['B']['hora_mediana_al_iniciar_el_dia'] == 8.0


def test_pausas_largas():
    s = latency_summary(parse_text('1/13/26, 9:00 AM - Ana: a\n3/20/26, 9:00 AM - Beto: b\n'
                                   '3/20/26, 9:01 AM - Ana: c\n').messages)
    assert s['pausas_largas']['n'] == 1 and s['pausas_largas']['maxima_dias'] == 66.0
    assert s['pausas_largas']['por_participante_que_retoma'] == {'A': 0, 'B': 1}


def test_config_acuses_son_texto():
    from metrics.turn_content import _cfg
    acks, dev, _ = _cfg()
    assert all(isinstance(a, str) for a in acks) and 'no' in acks and dev == 15

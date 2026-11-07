"""Saludos y despedidas: conteo, quién lo dice primero y si el otro corresponde."""
from metrics.greetings import greetings
from parsers import parse_text

T = ('14/03/2025, 08:00 - Ana: Buenos días!\n14/03/2025, 08:05 - Beto: buen dia\n'
     '14/03/2025, 23:00 - Beto: buenas noches, descansa\n14/03/2025, 23:01 - Ana: igual\n'
     '15/03/2025, 08:00 - Ana: buenos dias\n15/03/2025, 09:00 - Beto: hola\n'
     '15/03/2025, 23:30 - Ana: Buenas noches\n15/03/2025, 23:31 - Beto: buenas noches\n')


def test_saludos():
    g = greetings(parse_text(T, date_order_hint='dmy').messages)['por_clase']
    assert g['manana']['mensajes'] == {'A': 2, 'B': 1}
    assert g['manana']['dias_lo_dice_primero'] == {'A': 2, 'B': 0} and g['manana']['proporcion_dias_A'] == 1.0
    assert g['manana']['el_otro_corresponde']['A'] == 0.5
    assert g['noche']['dias_lo_dice_primero'] == {'A': 1, 'B': 1}
    assert g['noche']['el_otro_corresponde'] == {'A': 1.0, 'B': 0.0}
    assert 'Ana' not in str(g)

"""Ritmo: sesiones, continuidad de días y fragmentación con un chat sintético mínimo."""
from metrics.rhythm import rhythm
from parsers import parse_text

T = ('14/03/2025, 10:00 - Ana: hola\n14/03/2025, 10:00 - Ana: cómo vas\n14/03/2025, 10:05 - Beto: bien\n'
     '15/03/2025, 10:00 - Beto: oye\n15/03/2025, 10:30 - Ana: dime\n'
     '16/03/2025, 10:00 - Ana: ya\n'
     '20/03/2025, 10:00 - Beto: volví\n20/03/2025, 10:01 - Ana: va\n')


def test_ritmo():
    r = rhythm(parse_text(T, date_order_hint='dmy').messages)
    s, c, f = r['sesiones'], r['continuidad'], r['fragmentacion']
    assert s['n'] == 4 and s['cierra'] == {'A': 2, 'B': 1}      # la última sesión es fin de los datos, no cierre
    assert (c['dias_activos'], c['dias_del_rango'], c['racha_mas_larga_dias'], c['pausa_mas_larga_dias']) == (4, 7, 3, 3)
    assert c['racha_al_final_dias'] == 1
    assert c['dias_solo_uno'] == {'A': 1, 'B': 0} and c['dias_ambos'] == 3
    assert f['A']['mensajes_por_turno_mediana'] == 1 and f['A']['proporcion_turnos_de_un_mensaje'] == 0.75
    assert 'hola' not in str(r) and 'Ana' not in str(r)

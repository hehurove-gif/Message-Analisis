"""Correspondencia formal (R1–R4) con conversaciones sintéticas generadas aquí: simétrica, asimétrica e insuficiente."""
from datetime import datetime, timedelta

from metrics.correspondence import correspondence, spearman, turn_pairs
from parsers import parse_text

T0 = datetime(2026, 3, 2, 9, 0)


def _w(n, q=False):
    txt = ' '.join(f'palabra{i}' for i in range(n)) if n else 'ok'
    return txt + ('?' if q else '')


def _chat(turns):
    """turns: lista de (autor, texto, día). Un minuto entre turnos; cada día nuevo = sesión nueva."""
    out, last_day, t = [], None, T0
    for who, txt, day in turns:
        t = T0 + timedelta(days=day) if day != last_day else t + timedelta(minutes=1)
        last_day = day
        out.append(f"{t.month}/{t.day}/{t.year % 100}, {t.strftime('%I:%M %p').lstrip('0')} - {who}: {txt}")
    return parse_text('\n'.join(out) + '\n', date_order_hint='mdy').messages


def _tri(i, top=30):
    k = i % (2 * top)
    return 1 + (k if k < top else 2 * top - k)


def simetrica(rounds=90):
    turns = []
    for i in range(rounds):
        turns.append(('Ana', _w(_tri(2 * i), q=i % 3 == 0), i // 10))
        turns.append(('Beto', _w(_tri(2 * i + 1), q=i % 3 == 1), i // 10))
    return _chat(turns)


def asimetrica(rounds=150):
    """B contesta 'ok' a las preguntas y a los turnos desarrollados de A; A siempre contesta con contenido."""
    turns = []
    for i in range(rounds):
        n, q = _tri(2 * i), i % 3 == 0
        turns.append(('Ana', _w(n, q), i // 10))
        turns.append(('Beto', 'ok' if q or n >= 15 else _w(18 if i % 2 else 3 + i % 5, q=i % 4 < 2), i // 10))
    return _chat(turns)


def test_spearman():
    assert spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0
    assert spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert spearman([1, 2], [1, 2]) is None and spearman([1, 1, 1], [1, 2, 3]) is None


def test_pares_excluyen_otra_sesion():
    ms = _chat([('Ana', 'hola qué tal', 0), ('Beto', 'bien gracias', 0), ('Ana', 'sigues ahí', 1)])
    assert len(turn_pairs(ms, 6)) == 1              # el turno del día siguiente no responde al anterior


def test_simetrica():
    r = correspondence(simetrica())
    assert r['pares_misma_sesion'] >= 170
    assert r['R1_extension']['A_a_B']['rho'] > 0.9 and r['R1_extension']['B_a_A']['rho'] > 0.9
    for k in ('R1_extension', 'R2_preguntas', 'R3_desarrollados'):
        assert r[k]['etiqueta'] == 'simetrica', k


def test_asimetrica_hacia_B():
    r = correspondence(asimetrica())
    assert r['R2_preguntas']['A_a_B']['con_pregunta'] == 0.0      # B nunca da contenido a una pregunta de A
    assert r['R2_preguntas']['etiqueta'] == 'asimetrica_hacia_B'   # B recibe más correspondencia de la que da
    assert r['R3_desarrollados']['A_a_B']['tras_desarrollado']['minimo'] == 1.0
    assert r['R3_desarrollados']['etiqueta'] in ('asimetrica_hacia_B', 'sensible_a_umbrales')
    assert r['R3_desarrollados']['etiqueta_central'] == 'asimetrica_hacia_B'


def test_insuficiente():
    r = correspondence(simetrica(rounds=10))
    assert all(r[k]['etiqueta'] == 'insuficiente' for k in ('R1_extension', 'R2_preguntas', 'R3_desarrollados'))


def test_r4_y_sin_texto():
    r = correspondence(simetrica())
    assert set(r['R4_iniciativa']['reanudaciones']) == {2, 6, 12}
    assert r['R4_iniciativa']['inicia_dia'] == {'A': 9, 'B': 0}
    assert 'palabra0' not in str(r) and 'Ana' not in str(r) and 'interés' in r['nota']


def test_nivel_por_direccion():
    r = correspondence(simetrica())
    assert r['R1_extension']['A_a_B']['nivel'] == 'presente'
    a = correspondence(asimetrica())['R2_preguntas']
    assert a['A_a_B']['nivel'] == 'inversa' and a['B_a_A']['nivel'] == 'baja_o_nula'

"""Evolución temporal: series por mes y cambio sostenido con chats sintéticos."""
from datetime import datetime, timedelta

from metrics.trends import sustained_change, trends
from parsers import parse_text


def _chat(months=8, switch=4):
    """Cada día: alguien abre y el otro contesta. Hasta `switch` meses abre Ana; después abre Beto."""
    out, d = [], datetime(2025, 1, 1, 10, 0)
    while d < datetime(2025, 1, 1) + timedelta(days=30 * months):
        first, second = (('Ana', 'Beto') if (d - datetime(2025, 1, 1)).days < 30 * switch else ('Beto', 'Ana'))
        for i, who in enumerate((first, second, first, second)):
            t = d + timedelta(minutes=i * 2)
            out.append(f"{t.day}/{t.month}/{t.year}, {t.strftime('%H:%M')} - {who}: hola que tal todo bien {i}")
        d += timedelta(days=1)
    return parse_text('\n'.join(out) + '\n', date_order_hint='dmy').messages


def test_sustained_change_unit():
    r = sustained_change([0.8] * 4 + [0.2] * 6, 4, 3, 0.15, False)
    assert r['detectado'] and r['direccion'] == 'baja'
    assert sustained_change([0.5] * 10, 4, 3, 0.15, False)['detectado'] is False
    assert sustained_change([0.5] * 5, 4, 3, 0.15, False)['detectado'] is None


def test_detecta_cambio_de_quien_abre_el_dia():
    r = trends(_chat())
    assert r['granularidad'] == 'month' and r['periodos'][0]['periodo'] == '2025-01'
    assert r['periodos'][0]['inicia_dia_A'] == 1.0 and r['periodos'][-1]['inicia_dia_A'] == 0.0
    ch = r['cambios_sostenidos']['inicia_dia_A']
    assert ch['detectado'] and ch['direccion'] == 'baja'
    assert r['cambios_sostenidos']['mensajes_A']['detectado'] is False      # los mensajes siguen 50/50
    assert r['periodos'][0]['dias_activos'] == 1.0


def test_semanal_y_sin_texto():
    r = trends(_chat(months=3), granularity='week')
    assert r['periodos'][0]['periodo'].startswith('2025-W')
    assert 'hola' not in str(r) and 'Ana' not in str(r)


def test_latencia_base_cero_no_es_cambio():
    """Caso real: medianas 0 -> 1 min con resolución por minuto no deben marcar 'sube'."""
    assert sustained_change([0, 0, 0, 0, 1, 1, 1, 2, 1], 4, 3, 0.5, True, 5)['detectado'] is False
    assert sustained_change([0, 0, 0, 0, 9, 9, 9, 9, 9], 4, 3, 0.5, True, 5)['detectado'] is True
    assert sustained_change([10, 10, 10, 10, 13, 13, 13, 13], 4, 3, 0.5, True, 5)['detectado'] is False



def test_periodos_parciales_en_orillas():
    txt = '\n'.join(['1/1/2025, 10:00 - Ana: hola', '1/1/2025, 10:01 - Beto: hola'] +
                     [f'{d}/2/2025, 10:00 - Ana: hola' for d in range(1, 29)] + ['1/3/2025, 10:00 - Beto: hola']) + '\n'
    rows = trends(parse_text(txt, date_order_hint='dmy').messages)['periodos']
    assert [r['parcial'] for r in rows] == [True, False, True]

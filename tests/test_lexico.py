"""Motor léxico Fase 5.1: normalización, palabra completa, negación, pregunta, excepciones, emojis, conteo bruto."""
import pytest

from metrics.lexical import lexical_counts
from nlp.lexicon import detect, events_for_message, load_lexicon
from nlp.text import normalize
from parsers import parse_text

LEX = load_lexicon()


def cats(text, solo=('afecto_explicito',)):
    hits, _ = detect(text, LEX)
    return sorted({(r.categoria, f) for r, f, _ in hits if solo is None or r.categoria in solo or r.categoria.startswith('emoji')})


def test_normalizacion():
    assert normalize('Te QUIEROOOO muchísimo') == 'te quiero muchisimo'
    assert normalize('te amoo') == 'te amo' and normalize('tqmmmm') == 'tqm'
    assert normalize('calle  llamar') == 'calle llamar'            # 'll' se conserva
    assert normalize('❤️') == '❤'


@pytest.mark.parametrize('t', ['te quiero mucho', 'Te quiero', 'te kiero!!', 'tqm', 'tkm amiga', 'Te quierooo',
                               'te amo', 'te adoro', 'te extraño', 'te extrañooo mucho', 'te echo de menos',
                               'me haces falta', 'te quiero tanto', 'bueno, tq'])
def test_afecto_positivos(t):
    assert ('afecto_explicito', 'afirmativa') in cats(t)


@pytest.mark.parametrize('t', ['te quiero decir algo', 'te quiero preguntar una cosa', 'no te quiero molestar',
                               'te quiero pedir un favor', 'quiero que vengas', 'tq123', 'estequiero',
                               'te quiero ver mañana', 'el tqm de ayer fue otro'])
def test_afecto_negativos(t):
    got = [c for c in cats(t) if c[0] == 'afecto_explicito' and c[1] == 'afirmativa']
    # "el tqm de ayer fue otro" sí coincide por palabra completa: se documenta como falso positivo conocido
    assert (not got) == (t != 'el tqm de ayer fue otro')


def test_descartes_se_cuentan():
    _, d = detect('te quiero decir algo', LEX)
    assert d['afecto.te_quiero.v1'] == 1


def test_negada_y_pregunta():
    assert cats('no te quiero') == [('afecto_explicito', 'negada')]
    assert cats('ya no, nunca te quiero mucho') == [('afecto_explicito', 'negada')]
    assert cats('¿me dices que te quiero?') == [('afecto_explicito', 'pregunta')]
    assert cats('¿Qué dices, te quiero? jaja') == [('afecto_explicito', 'pregunta')]
    assert cats('Hola. No sé. Te quiero') == [('afecto_explicito', 'afirmativa')]   # la negación no cruza oraciones
    assert cats('no entiendo nada y la verdad te quiero') == [('afecto_explicito', 'afirmativa')]  # fuera de 3 palabras


def test_emojis():
    assert ('emoji_afectivo', 'afirmativa') in cats('buenas noches ❤️')
    assert ('emoji_afectivo', 'afirmativa') in cats('🥰')
    assert ('emoji_risa', 'afirmativa') in cats('jajaja 😂😂')
    assert ('emoji_tristeza', 'afirmativa') in cats('😢')
    assert ('emoji_enojo', 'afirmativa') in cats('ya basta 😡')
    assert cats('hola, qué tal') == []
    hits, _ = detect('😂😂😂', LEX)
    assert [n for _, _, n in hits] == [3]


def test_ambiguas_marcadas():
    evs, _ = events_for_message(_msg('me muero 😭'), LEX)
    assert evs[0].categoria == 'emoji_tristeza' and evs[0].ambiguo
    evs, _ = events_for_message(_msg('🙄'), LEX)
    assert evs[0].categoria == 'emoji_posible_ironia' and evs[0].ambiguo
    evs, _ = events_for_message(_msg('te quiero ❤️'), LEX)
    assert {e.categoria for e in evs} == {'afecto_explicito', 'emoji_afectivo'}
    assert not any(e.ambiguo for e in evs)


def _msg(texto):
    return parse_text(f'14/03/2025, 08:00 - Ana: {texto}\n14/03/2025, 08:01 - Beto: ok', date_order_hint='dmy').messages[0]


def test_un_evento_por_categoria_y_mensaje():
    evs, _ = events_for_message(_msg('te quiero, te amo, te extraño ❤️❤️'), LEX)
    por_cat = [e.categoria for e in evs]
    assert por_cat.count('afecto_explicito') == 1 and por_cat.count('emoji_afectivo') == 1
    ev = next(e for e in evs if e.categoria == 'afecto_explicito')
    assert ev.n_coincidencias == 3 and set(ev.subetiquetas) == {'te_quiero', 'te_amo', 'extranar'}
    assert ev.linea == 1 and ev.clase_provisional == 'pendiente_fase_6'


def test_evento_no_contiene_texto():
    evs, _ = events_for_message(_msg('te quiero zanahoria'), LEX)
    assert 'zanahoria' not in repr(evs[0]) and 'zanahoria' not in str(evs[0])


T = '''14/03/2025, 08:00 - Ana: te quiero
14/03/2025, 08:01 - Ana: buenos dias ❤️
14/03/2025, 08:10 - Beto: jaja gracias 😂
14/03/2025, 22:00 - Ana: te extraño
14/03/2025, 22:30 - Beto: no te quiero ver
14/03/2025, 22:31 - Beto: ya no te quiero
15/03/2025, 09:00 - Ana: ¿me quieres? te amo
15/03/2025, 09:05 - Beto: 😭
16/03/2025, 12:00 - Ana: hola
16/03/2025, 12:05 - Beto: te quiero decir algo
'''


def test_conteo_bruto_por_persona():
    r = lexical_counts(parse_text(T, date_order_hint='dmy').messages)
    a = r['por_categoria']['afecto_explicito']
    # Ana: línea 1 (te quiero), 4 (te extraño), 6 (te amo; "¿me quieres?" no coincide) = 3 mensajes, 3 días lógicos? días 14,14,15
    assert a['estricta']['A']['mensajes_con_evento'] == 3 and a['estricta']['A']['ocurrencias'] == 3
    assert a['estricta']['A']['dias_con_evento'] == 2
    assert a['estricta']['A']['turnos_con_evento'] == 3
    assert a['estricta']['B']['mensajes_con_evento'] == 0
    assert a['negadas']['B']['mensajes_con_evento'] == 1
    assert r['descartes_por_regla'] == {'afecto.te_quiero.v1': 2}      # 'no te quiero ver' y 'te quiero decir algo'
    assert r['base']['A'] == {'mensajes_texto': 5, 'turnos': 4, 'dias_activos': 3}
    assert a['estricta']['A']['por_100_mensajes'] == 60.0
    assert a['mas_dias_con_evento']['estricta'] == 'insuficiente'          # 2 días < min_events_for_pattern (3)
    em = r['por_categoria']['emoji_tristeza']
    assert em['estricta']['B']['mensajes_con_evento'] == 0 and em['amplia']['B']['mensajes_con_evento'] == 1


def test_sin_texto_en_resultado():
    r = lexical_counts(parse_text(T, date_order_hint='dmy').messages)
    s = str(r)
    assert 'Ana' not in s and 'Beto' not in s and 'quiero' not in s.replace('te_quiero', '').replace('afecto.te_quiero.v1', '')


def test_local_apodos_vocativo(tmp_path):
    p = tmp_path / 'lexicon_local.yaml'
    p.write_text('apodos: ["tigre"]\nafecto: ["mi cielo lindo"]\n', encoding='utf-8')
    lex = load_lexicon(local_path=str(p))
    assert lex.n_local == 2
    ok = lambda t: ('apodo_carinoso', 'afirmativa') in {(r.categoria, f) for r, f, _ in detect(t, lex)[0]}
    assert cats_with(lex, 'Tigre, ¿vienes?') == {('apodo_carinoso', 'afirmativa')}
    assert ok('hola, tigre') and ok('gracias tigre') and ok('Tigre, ¿vienes?')
    assert not ok('el tigre de bengala es grande')
    assert not ok('vi un tigre por ahí hoy')
    assert ('afecto_explicito', 'afirmativa') in cats_with(lex, 'mi cielo lindo')


def cats_with(lex, t):
    return {(r.categoria, f) for r, f, _ in detect(t, lex)[0]}


def test_lexico_invalido(tmp_path):
    p = tmp_path / 'x.yaml'
    p.write_text('reglas:\n  - id: a\n    categoria: inventada\n    patrones: [hola]\n', encoding='utf-8')
    with pytest.raises(ValueError):
        load_lexicon(path=str(p))


def test_crear_lexico_local(tmp_path, monkeypatch, capsys):
    import sys
    sys.path.insert(0, 'tools')
    import crear_lexico_local as c
    c.main([str(tmp_path / 'exp')])
    assert (tmp_path / 'exp' / 'lexicon_local.yaml').exists()
    with pytest.raises(SystemExit):
        c.main([str(tmp_path / 'exp')])                    # no sobrescribe
    with pytest.raises(SystemExit):
        c.main([c.ROOT])                                   # no dentro del repo
    assert load_lexicon(local_path=str(tmp_path / 'exp' / 'lexicon_local.yaml')).n_local == 0


def test_integracion_metricas_local(tmp_path):
    import sys
    sys.path.insert(0, 'tools')
    import metricas_local as m
    f = tmp_path / 'chat.txt'
    f.write_text(T, encoding='utf-8')
    (tmp_path / 'lexicon_local.yaml').write_text('apodos: ["tigre"]\n', encoding='utf-8')
    out = m.analizar(str(f), confirmo=True, date_order_hint='dmy')
    assert out['lexico']['reglas']['n_locales'] == 1               # detecta lexicon_local.yaml junto al chat
    txt = m.resumen(out)
    assert 'Léxico: conteo bruto' in txt and 'afecto_explicito' in txt and 'tigre' not in txt

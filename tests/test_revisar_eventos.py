import csv
import json
import sys

import pytest

sys.path.insert(0, 'tools')
import revisar_eventos_local as rv  # noqa: E402
from metrics.validation import allocate, label_category, load_cfg, sample_size, wilson  # noqa: E402
from nlp.lexicon import load_lexicon  # noqa: E402
from parsers import parse_text  # noqa: E402


def chat(n_gracias=40, n_perdon=6, n_otros=200):
    L, d = [], 1
    for i in range(n_gracias):
        L.append(f'{(i % 27) + 1:02d}/03/2025, 10:{i % 60:02d} - {"Ana" if i % 3 else "Beto"}: gracias por todo {i}')
    for i in range(n_perdon):
        L.append(f'{(i % 27) + 1:02d}/04/2025, 11:{i:02d} - Ana: perdon por lo de ayer')
    for i in range(n_otros):
        L.append(f'{(i % 27) + 1:02d}/05/2025, 12:{i % 60:02d} - {"Ana" if i % 2 else "Beto"}: hoy llueve {i}')
    return '\n'.join(L)


def test_tamano_de_muestra():
    assert [sample_size(n) for n in (1, 10, 30, 100, 500, 2000)] == [1, 10, 24, 50, 81, 92]
    assert sample_size(5) == 5 and sample_size(0) == 0


def test_wilson_y_etiquetas():
    lo, hi = wilson(8, 10)
    assert 0.48 < lo < 0.50 and 0.94 < hi < 0.95 and wilson(0, 0) == (None, None)
    cfg = load_cfg()
    assert label_category(9, 9, cfg) == 'no_validada'              # menos de min_events revisados
    assert label_category(40, 36, cfg) == 'valida'
    assert label_category(40, 24, cfg) == 'baja_precision'


def test_reparto_proporcional():
    a = allocate({'a': 80, 'b': 15, 'c': 5}, 20)
    assert a == {'a': 16, 'b': 3, 'c': 1} and sum(a.values()) == 20
    assert allocate({'a': 3, 'b': 2}, 99) == {'a': 3, 'b': 2}      # nunca más que el estrato
    b = allocate({'a': 100, 'b': 1, 'c': 1}, 2)
    assert min(b.values()) >= 1 and sum(b.values()) == 3          # mínimo 1 por estrato


def test_muestreo_reproducible_y_sin_texto():
    msgs = parse_text(chat(), date_order_hint='dmy').messages
    lex, cfg = load_lexicon(), load_cfg()
    r1, m1 = rv.muestrear(msgs, lex, cfg, seed=7)
    r2, m2 = rv.muestrear(msgs, lex, cfg, seed=7)
    assert [x['linea_inicial'] for x in r1] == [x['linea_inicial'] for x in r2] and m1 == m2
    assert m1['categorias']['gratitud']['poblacion'] == 40 and m1['categorias']['gratitud']['muestra'] == 29
    assert m1['categorias']['disculpa']['poblacion'] == 6 and m1['categorias']['disculpa']['muestra'] == 6  # N<10: todos
    assert all(x['texto'] == '' for x in r1)
    assert m1['sin_evento']['muestra'] == min(m1['sin_evento']['poblacion'], 300)
    con, _ = rv.muestrear(msgs, lex, cfg, seed=7, con_texto=True)
    assert any('gracias' in x['texto'] for x in con)


def test_flujo_completo(tmp_path, capsys):
    f = tmp_path / 'c.txt'
    f.write_text(chat(), encoding='utf-8')
    out = tmp_path / 'rev'
    rv.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', str(out)])
    hoja = out / rv.CSV_NAME
    rows = list(csv.DictReader(open(hoja, encoding='utf-8-sig', newline='')))
    # el revisor marca: gratitud todo correcto; disculpa 4 correcto y 2 incorrecto; recuperación: todo ok menos 1
    n_esc = 0
    for r in rows:
        if r['categoria'] == 'gratitud':
            r['veredicto'] = 'c'
        elif r['categoria'] == 'disculpa':
            r['veredicto'] = 'c' if int(r['id']) % 3 else 'i'
        elif r['tipo'] == 'sin_evento':
            r['veredicto'] = 'escapo' if n_esc == 0 else 'ok'
            n_esc += 1
    with open(hoja, 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=rv.FIELDS)
        w.writeheader()
        w.writerows(rows)
    capsys.readouterr()
    rv.main(['--resumir', str(hoja)])
    txt = capsys.readouterr().out
    assert 'gratitud: eventos 40, muestra 29, revisados 29 (c 29, i 0, a 0) precisión 1.00' in txt and '-> valida' in txt
    assert 'disculpa' in txt and 'no_validada' in txt                 # 6 revisados < 10
    assert 'Recuperación: de' in txt and '1 tenían una expresión no detectada' in txt
    assert 'ayer' not in txt and 'llueve' not in txt
    with pytest.raises(SystemExit):                                   # no sobrescribe una hoja con veredictos
        rv.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', str(out)])


def test_no_dentro_del_repo(tmp_path):
    f = tmp_path / 'c.txt'
    f.write_text(chat(), encoding='utf-8')
    with pytest.raises(SystemExit):
        rv.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', rv.ROOT + '/rev'])
    with pytest.raises(SystemExit):
        rv.main([rv.ROOT + '/README.md', '--salida', str(tmp_path / 'x')])
    with pytest.raises(SystemExit):
        rv.main(['--resumir', rv.ROOT + '/x.csv'])


def test_acotar_categorias_y_recuperacion(tmp_path, capsys):
    f = tmp_path / 'c.txt'
    f.write_text(chat(), encoding='utf-8')
    rv.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', str(tmp_path / 'r'),
             '--categorias', 'disculpa', '--recuperacion', '20'])
    rows = list(csv.DictReader(open(tmp_path / 'r' / rv.CSV_NAME, encoding='utf-8-sig', newline='')))
    assert {r['categoria'] for r in rows if r['tipo'] == 'evento'} == {'disculpa'}
    assert sum(r['tipo'] == 'sin_evento' for r in rows) == 20
    meta = json.load(open(tmp_path / 'r' / rv.META_NAME, encoding='utf-8'))
    assert list(meta['categorias']) == ['disculpa'] and meta['solo_categorias'] == ['disculpa']

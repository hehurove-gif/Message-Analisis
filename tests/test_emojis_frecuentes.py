import sys

import pytest

sys.path.insert(0, 'tools')
import emojis_frecuentes_local as ef  # noqa: E402
from nlp.lexicon import load_lexicon  # noqa: E402
from parsers import parse_text  # noqa: E402

T = ('14/03/2025, 08:00 - Ana: hola 😂😂 ❤️\n14/03/2025, 08:01 - Beto: jaja 😂\n'
     '14/03/2025, 08:02 - Beto: 🦄 y 😭\n')


def test_conteo_y_categorias():
    msgs = parse_text(T, date_order_hint='dmy').messages
    por_msj, ocurr = ef.contar(msgs)
    assert por_msj['😂']['A'] == 1 and por_msj['😂']['B'] == 1 and ocurr['😂'] == 3
    lex = load_lexicon()
    assert ef.categoria_de('🦄', lex) == ['emoji_otro']
    assert ef.categoria_de('😭', lex) == ['emoji_tristeza*']
    assert ef.categoria_de('😂', lex) == ['emoji_risa']


def test_no_lee_ni_escribe_dentro_del_repo(tmp_path):
    with pytest.raises(SystemExit):
        ef.main([ef.ROOT + '/README.md'])
    f = tmp_path / 'c.txt'
    f.write_text(T, encoding='utf-8')
    with pytest.raises(SystemExit):
        ef.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', ef.ROOT + '/x.txt'])


def test_salida_utf8(tmp_path):
    f = tmp_path / 'c.txt'
    f.write_text(T, encoding='utf-8')
    out = tmp_path / 's.txt'
    ef.main([str(f), '--confirmo-individual', '--date-order-hint', 'dmy', '--salida', str(out)])
    txt = out.read_text(encoding='utf-8')
    assert '🦄' in txt and 'emoji_otro' in txt and 'U+1F602' in txt and 'hola' not in txt

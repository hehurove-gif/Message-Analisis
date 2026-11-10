"""Frecuencia de emojis de una exportación, por participante y por categoría del léxico (solo en tu máquina).

    python tools/emojis_frecuentes_local.py RUTA --confirmo-individual [--date-order-hint dmy] [--top 40] [--salida ARCHIVO]

Sirve para ver qué emojis hay en el chat que ninguna categoría cubre y decidir si añadirlos al léxico. Imprime
cada emoji con su punto de código (por si la consola no lo muestra), cuántos mensajes lo contienen por persona y
la categoría que lo cubre. No imprime texto de mensajes. `--salida` escribe en UTF-8 (recomendado en Windows)."""
import argparse
import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from nlp.lexicon import load_lexicon  # noqa: E402
from nlp.text import normalize  # noqa: E402
from parsers import parse_file  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402

EMOJI = re.compile('[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿←-⇿⤀-⥿〰〽]')


def contar(messages):
    """{emoji: Counter(persona -> mensajes que lo contienen)} y {emoji: ocurrencias totales}."""
    por_msj, ocurr = {}, Counter()
    for m in messages:
        if m.tipo != 'texto' or not m.participante:
            continue
        found = EMOJI.findall(m.texto)
        for e in found:
            ocurr[e] += 1
        for e in set(found):
            por_msj.setdefault(e, Counter())[m.participante] += 1
    return por_msj, ocurr


def categoria_de(emoji, lex):
    e = normalize(emoji)
    return sorted({f"{r.categoria}{'*' if r.ambiguo else ''}" for r in lex.rules if any(x and x in e for x in r.emojis)}) or ['SIN_CATEGORIA']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--top', type=int, default=40)
    ap.add_argument('--salida')
    a = ap.parse_args(argv)
    real = os.path.realpath(a.ruta)
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio.')
    if a.salida and is_inside(os.path.realpath(a.salida), os.path.realpath(ROOT)):
        sys.exit('Por privacidad la salida no se escribe dentro del repositorio.')
    res = parse_file(real, date_order_hint=a.date_order_hint)
    if res.accepted and a.confirmo_individual:
        res = res.confirm_individual()
    if not res.analysis_enabled:
        sys.exit('Análisis no habilitado: ' + ', '.join(res.pending_requirements or ['importación no aceptada']))
    lex = load_lexicon(local_path=os.path.join(os.path.dirname(real), 'lexicon_local.yaml'))
    por_msj, ocurr = contar(res.messages)
    names = sorted({m.participante for m in res.messages if m.participante})
    rows = sorted(por_msj, key=lambda e: -sum(por_msj[e].values()))[:a.top]
    out = [f'Emojis distintos: {len(por_msj)}; mensajes con emoji: ' + ' / '.join(
        f"{n} {sum(1 for m in res.messages if m.tipo == 'texto' and m.participante == n and EMOJI.search(m.texto))}" for n in names),
        '(* = regla ambigua; SIN_CATEGORIA = ninguna categoría lo cubre)',
        'emoji  codepoints        ' + '  '.join(f'msj {n}' for n in names) + '  ocurr.  categoría']
    for e in rows:
        cp = ' '.join(f'U+{ord(c):04X}' for c in e)
        out.append(f"{e}  {cp:<16} " + '  '.join(f'{por_msj[e].get(n, 0):>5}' for n in names)
                   + f'  {ocurr[e]:>6}  ' + ','.join(categoria_de(e, lex)))
    txt = '\n'.join(out)
    if a.salida:
        with open(a.salida, 'w', encoding='utf-8') as f:
            f.write(txt + '\n')
        print('Escrito:', a.salida)
    else:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        print(txt)


if __name__ == '__main__':
    main()

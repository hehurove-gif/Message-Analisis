#!/usr/bin/env python3
"""Contrasta UNA exportación real propia con el parser, en local y sin salida de contenido privado.

Uso:  python tools/validar_exportacion_local.py RUTA_AL_TXT [--date-order-hint dmy|mdy] [--formas N]

- Solo LEE el archivo; no escribe nada ni usa la red.
- Imprime únicamente el reporte de calidad (números, códigos y números de línea).
- `--formas N` muestra la FORMA enmascarada de hasta N líneas no procesadas (dígitos → 9, letras → a,
  caracteres especiales como U+XXXX): sirve para ver qué formato no se reconoció sin ver el contenido.
- Se niega a leer archivos dentro del repositorio, para que una conversación privada no acabe en git.
"""
import argparse
import json
import os
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from parsers import parse_file  # noqa: E402


def mask(line, limit=60):
    out = []
    for ch in line[:limit]:
        if ch.isdigit():
            out.append('9')
        elif ch.isalpha():
            out.append('a')
        elif ch in ' \t' or (ch.isprintable() and ch.isascii()):
            out.append(ch)
        elif ch.isalnum() or unicodedata.category(ch).startswith(('S', 'P')) and ch.isprintable() and ord(ch) < 0x2000:
            out.append('?')
        else:
            out.append('<U+%04X>' % ord(ch))
    return ''.join(out)


def is_inside(path, root, pm=os.path):
    """¿`path` está dentro de `root`? Ambos deben venir ya resueltos (realpath). Rutas en unidades distintas
    (Windows: `commonpath` lanza ValueError) son externas al repositorio. `pm` permite probar con `ntpath`."""
    path, root = pm.normcase(pm.normpath(path)), pm.normcase(pm.normpath(root))
    try:
        return pm.commonpath([path, root]) == root
    except ValueError:            # unidades distintas, o mezcla de rutas absolutas y relativas
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--formas', type=int, default=0, metavar='N')
    ap.add_argument('--unir', action='append', default=[], metavar='C=B',
                    help='decisión EXPLÍCITA: trata al autor con la etiqueta C como el autor B (etiquetas del reporte)')
    a = ap.parse_args(argv)

    real = os.path.realpath(a.ruta)      # resuelve enlaces simbólicos que terminen dentro del repositorio
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')

    merge = dict(x.split('=', 1) for x in a.unir) if a.unir else None
    res = parse_file(real, date_order_hint=a.date_order_hint, merge_authors=merge)
    print(json.dumps(res.to_report_dict(), ensure_ascii=False, indent=2))
    if a.formas:
        with open(real, 'rb') as f:
            lines = f.read().decode('utf-8', errors='replace').lstrip('﻿').replace('\r\n', '\n').split('\n')
        print('\nFormas enmascaradas de líneas no procesadas:')
        for item in res.report['lineas_no_procesadas'][:a.formas]:
            print('  línea %d [%s]: %s' % (item['linea'], item['motivo'], mask(lines[item['linea'] - 1])))


if __name__ == '__main__':
    main()

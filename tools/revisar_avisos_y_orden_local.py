#!/usr/bin/env python3
"""Ubica en UNA exportación propia los avisos del sistema sin catalogar y los timestamps fuera de orden, SIN imprimir
contenido: solo números de línea, fechas, minutos y la FORMA enmascarada (letras -> a, dígitos -> 9).

Uso:  python tools/revisar_avisos_y_orden_local.py RUTA [--date-order-hint dmy|mdy] [--max N]

Avisos: se agrupan por forma enmascarada; para cada grupo, cuántos hay y en qué líneas. Abre TU archivo en esas
líneas (en local) y dime el texto GENÉRICO del aviso (p. ej. "Bloqueaste a este contacto"), sin nombres: con eso
se agrega al catálogo de parsers/patterns.py con un fixture sintético.
Fuera de orden: cada par de mensajes de persona consecutivos donde el segundo es ANTERIOR al primero: línea,
fecha y cuántos minutos retrocede. Un retroceso de exactamente 60 min sugiere cambio de horario (hipótesis).
Solo LEE el archivo; no escribe ni usa red; se niega a leer archivos dentro del repositorio."""
import argparse
import os
import sys
from collections import defaultdict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import parse_file, patterns  # noqa: E402
from validar_exportacion_local import is_inside, mask  # noqa: E402

PERSON = ('texto', 'media', 'deleted')


def uncatalogued(messages):
    groups = defaultdict(list)
    for m in messages:
        if m.tipo == 'system' and patterns.classify_notice(m.texto) is None and not patterns.is_known_notice_text(m.texto):
            groups[mask(m.texto.split('\n')[0])].append(m.linea_inicial)
    return sorted(({'forma': k, 'n': len(v), 'lineas': v} for k, v in groups.items()), key=lambda g: -g['n'])


def out_of_order(messages):
    people = [m for m in messages if m.tipo in PERSON and m.timestamp_local]
    out = []
    for a, b in zip(people, people[1:]):
        d = (datetime.fromisoformat(b.timestamp_local) - datetime.fromisoformat(a.timestamp_local)).total_seconds() / 60
        if d < 0:
            out.append({'linea': b.linea_inicial, 'fecha': b.timestamp_local[:16], 'retrocede_min': round(-d),
                        'mismo_autor': a.participante == b.participante})
    return out


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--max', type=int, default=10, help='líneas a listar por grupo (por defecto 10)')
    a = ap.parse_args(argv)
    real = os.path.realpath(a.ruta)
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    res = parse_file(real, date_order_hint=a.date_order_hint)
    print(resumen(res.messages, a.max))


def resumen(messages, mx=10):
    av, oo = uncatalogued(messages), out_of_order(messages)
    lines = [f'== Avisos del sistema sin catalogar: {sum(g["n"] for g in av)} en {len(av)} formas ==']
    for i, g in enumerate(av):
        more = f' (+{g["n"] - mx})' if g['n'] > mx else ''
        lines.append(f'  [{i}] n={g["n"]}  forma: {g["forma"]}\n      líneas: {", ".join(map(str, g["lineas"][:mx]))}{more}')
    lines += ['', f'== Timestamps fuera de orden: {len(oo)} ==']
    if oo:
        c60 = sum(1 for x in oo if x['retrocede_min'] == 60)
        lines.append(f'  retroceden exactamente 60 min: {c60} (posible cambio de horario; hipótesis)')
        for x in oo[:mx * 3]:
            lines.append(f"  línea {x['linea']}  {x['fecha']}  retrocede {x['retrocede_min']} min"
                         f"  {'mismo autor' if x['mismo_autor'] else 'cambio de autor'}")
    lines += ['', 'Solo líneas, fechas y formas enmascaradas; ningún texto ni nombre.']
    return '\n'.join(lines)


if __name__ == '__main__':
    main()

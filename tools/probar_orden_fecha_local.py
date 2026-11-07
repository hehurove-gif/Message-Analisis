#!/usr/bin/env python3
"""Prueba AMBOS órdenes de fecha (dmy y mdy) sobre una exportación propia y muestra la evidencia, sin elegir.

Uso:  python tools/probar_orden_fecha_local.py RUTA

Cuando ninguna fecha del archivo tiene un componente > 12, los dos órdenes son válidos en todos los mensajes y
el parser bloquea la importación (no adivina). Un chat exportado está en orden cronológico: con el orden correcto
casi no hay retrocesos de timestamp; con el equivocado suelen aparecer muchos. Esta herramienta cuenta los
retrocesos y el rango resultante con cada orden. Es una PISTA, no una prueba: la decisión es tuya y se aplica
volviendo a ejecutar el validador con --date-order-hint. Imprime solo números y fechas (nada de texto de
mensajes ni nombres). Solo lee el archivo; se niega a leer dentro del repositorio."""
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import parse_file  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402

ORDERS = ('dmy', 'mdy')


_FECHA = re.compile(r'(?m)^[\u200e\u200f\ufeff]*\[?(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})')


def campos(text):
    """Distribución de los dos primeros campos numéricos de la fecha de cada línea que empieza con una fecha:
    {'primer_campo': {valor: cantidad}, 'segundo_campo': {...}}. Solo números."""
    f = _FECHA.findall(text)
    a, b = Counter(int(x[0]) for x in f), Counter(int(x[1]) for x in f)
    return {'lineas_con_fecha': len(f), 'primer_campo': dict(sorted(a.items())),
            'segundo_campo': dict(sorted(b.items()))}


def lectura_de_campos(c):
    """Frases sobre qué campo puede ser el día y cuál el mes, según su variedad. Evidencia, no decisión."""
    out = []
    for nombre in ('primer_campo', 'segundo_campo'):
        vals = c[nombre]
        out.append(f'{nombre}: {len(vals)} valores distintos entre {min(vals)} y {max(vals)}' if vals else f'{nombre}: sin datos')
    n1, n2 = len(c['primer_campo']), len(c['segundo_campo'])
    if n1 and n2 and n1 != n2:
        raro = 'primer_campo' if n1 < n2 else 'segundo_campo'
        otro = 'segundo_campo' if raro == 'primer_campo' else 'primer_campo'
        out.append(f'{raro} varía menos que {otro}. Un DÍA del mes suele recorrer muchos valores en un chat largo; '
                   f'un MES recorre como máximo 12. Si {otro} es el día, el mes es {raro}')
    return out


def probe(path):
    out = {}
    for h in ORDERS:
        rep = parse_file(path, date_order_hint=h).report
        r = rep['rango_fechas']
        dias = None
        if r:
            dias = (datetime.fromisoformat(r['ultimo']) - datetime.fromisoformat(r['primero'])).days
        out[h] = {'orden_fecha': rep['orden_fecha'], 'decision_importacion': rep['decision_importacion'],
                  'timestamps_fuera_de_orden': rep['timestamps_fuera_de_orden'],
                  'rango_fechas': r, 'dias_de_rango': dias}
    return out


def veredicto(res):
    """Compara retrocesos. Nunca decide: solo dice si la cronología distingue los órdenes."""
    a, b = (res[h]['timestamps_fuera_de_orden'] for h in ORDERS)
    if a == b:
        return {'distingue': False, 'detalle': 'ambos órdenes tienen los mismos retrocesos: la cronología no ayuda'}
    mejor = ORDERS[0] if a < b else ORDERS[1]
    return {'distingue': True, 'mas_cronologico': mejor,
            'detalle': f'{mejor} tiene menos retrocesos ({min(a, b)} frente a {max(a, b)}). Es una pista: confírmala '
                       'con lo que sabes del chat y vuelve a ejecutar con --date-order-hint'}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit(__doc__)
    real = os.path.realpath(argv[0])
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    res = probe(real)
    with open(real, 'rb') as f:
        c = campos(f.read().decode('utf-8', errors='replace'))
    print(json.dumps({'por_orden': res, 'veredicto': veredicto(res), 'campos_de_fecha': c,
                      'lectura_de_campos': lectura_de_campos(c)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

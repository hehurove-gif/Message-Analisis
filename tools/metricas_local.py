#!/usr/bin/env python3
"""Participación y latencias de UNA exportación propia, en local, imprimiendo solo números (sin contenido).

Uso:  python tools/metricas_local.py RUTA --confirmo-individual [--date-order-hint dmy|mdy]
                                     [--aceptar-alias-sospechosos | --unir C=B] [--aceptar-perdidas L1,L2]

Igual que segmentar_local: sin --confirmo-individual el análisis queda deshabilitado. Solo LEE el archivo,
no escribe ni usa red, y se niega a leer archivos dentro del repositorio. Los resultados son observaciones
descriptivas: no interpretan interés, cercanía ni reciprocidad."""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics.latency import latency_sensitivity  # noqa: E402
from metrics.participation import participation  # noqa: E402
from parsers import parse_file  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--aceptar-alias-sospechosos', action='store_true')
    ap.add_argument('--unir', action='append', default=[], metavar='C=B')
    ap.add_argument('--aceptar-perdidas', default='', metavar='L1,L2')
    a = ap.parse_args(argv)

    real = os.path.realpath(a.ruta)
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    merge = dict(x.split('=', 1) for x in a.unir) if a.unir else None
    res = parse_file(real, date_order_hint=a.date_order_hint, merge_authors=merge,
                     accept_suspected_aliases=a.aceptar_alias_sospechosos)
    if res.accepted and a.confirmo_individual:
        res = res.confirm_individual()
    if res.accepted and a.aceptar_perdidas:
        res = res.accept_losses([int(x) for x in a.aceptar_perdidas.split(',')])
    out = {'importacion': res.report['decision_importacion'], 'estado_calidad': res.report['estado_calidad'],
           'analisis_habilitado': res.analysis_enabled, 'requisitos_pendientes': res.pending_requirements}
    if res.analysis_enabled:
        out['participacion'] = participation(res.messages)
        out['latencias'] = latency_sensitivity(res.messages)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

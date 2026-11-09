#!/usr/bin/env python3
"""Segmenta (turnos y sesiones) UNA exportación propia en local; imprime solo conteos, sin contenido.

Uso:  python tools/segmentar_local.py RUTA --confirmo-individual [--date-order-hint dmy|mdy]
                                      [--aceptar-alias-sospechosos | --unir C=B] [--aceptar-perdidas L1,L2]

Nada se habilita por sí solo: sin --confirmo-individual (tu declaración de que el chat es individual) el
análisis queda deshabilitado y la herramienta solo lo informa. Con líneas no procesadas hay que aceptar
expresamente cada una con --aceptar-perdidas. Solo LEE el archivo; no escribe nada ni usa la red; se niega
a leer archivos dentro del repositorio."""
import argparse
import json
import os
import statistics
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics.participants import participant_guide  # noqa: E402
from parsers import parse_file  # noqa: E402
from segmentation.sessions import sensitivity  # noqa: E402
from segmentation.turns import build_turns  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402


def resumen_turnos(messages, gap_h=6):
    turns = build_turns(messages, session_gap_hours=gap_h)
    per = Counter(t.participante for t in turns)
    return {'hueco_horas': gap_h, 'n_turnos': len(turns), 'turnos_por_participante': dict(sorted(per.items())),
            'mensajes_por_turno_mediana': statistics.median(t.n_mensajes for t in turns),
            'mensajes_por_turno_maximo': max(t.n_mensajes for t in turns),
            'turnos_con_fuera_de_orden': sum(t.tiene_fuera_de_orden for t in turns),
            # retroceso ENTRE turnos de distinto autor (el siguiente empieza antes de que termine el anterior)
            'pares_de_turnos_fuera_de_orden': sum(y.primer_ts < x.ultimo_ts for x, y in zip(turns, turns[1:]))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--aceptar-alias-sospechosos', action='store_true')
    ap.add_argument('--unir', action='append', default=[], metavar='C=B')
    ap.add_argument('--aceptar-perdidas', default='', metavar='L1,L2')
    ap.add_argument('--yo', choices=['A', 'B'], help='cuál etiqueta eres tú (A = quien escribe primero en el archivo)')
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
        out['participantes'] = participant_guide(res.messages, yo=a.yo)
        out['turnos'] = resumen_turnos(res.messages)
        out['sesiones'] = sensitivity(res.messages)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

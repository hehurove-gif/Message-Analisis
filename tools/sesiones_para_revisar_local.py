#!/usr/bin/env python3
"""Elige N sesiones de UNA exportación propia para revisarlas A MANO contra el sistema (criterio de salida de la Fase 3).

Uso:  python tools/sesiones_para_revisar_local.py RUTA --confirmo-individual [--date-order-hint dmy|mdy] [-n 5]
                                                  [--min-turnos 4] [--max-turnos 14]

Imprime SOLO números (nada de texto ni nombres): para cada sesión elegida, el rango de líneas del TXT donde está y,
turno por turno, quién es (A/B), cuántos mensajes tiene, hora de su primer y último mensaje y los minutos hasta que
interviene el otro. Abre el TXT en esas líneas, cuenta tú los turnos (mensajes seguidos del mismo autor), quién abre,
quién cierra y los minutos entre el último mensaje de un turno y el primero del siguiente, y compara con esta salida.
Las sesiones se eligen repartidas a lo largo del chat y con entre --min-turnos y --max-turnos turnos (comprobables a
mano). Hueco de sesión: el de config. Solo LEE el archivo; no escribe ni usa red; se niega a leer dentro del repo."""
import argparse
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import parse_file  # noqa: E402
from segmentation.sessions import build_sessions  # noqa: E402
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402


def _gap():
    import yaml
    with open(DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        return (yaml.safe_load(f) or {}).get('segmentation', {}).get('session_gap_hours', 6)


def _mins(a, b):
    return round((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 60, 1)


def pick(sessions, n, lo, hi):
    """n sesiones comprobables a mano, repartidas por el chat (índices equiespaciados entre las candidatas)."""
    cand = [s for s in sessions if lo <= s.n_turnos <= hi and not s.es_primera and not s.es_ultima]
    if len(cand) <= n:
        return cand
    return [cand[round(i * (len(cand) - 1) / (n - 1))] for i in range(n)] if n > 1 else [cand[len(cand) // 2]]


def review(messages, n=5, lo=4, hi=14, gap=None):
    gap = gap or _gap()
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    pos = {m.seq: i for i, m in enumerate(people)}
    turns = build_turns(people, session_gap_hours=gap)
    sessions = build_sessions(turns)
    out = []
    for s in pick(sessions, n, lo, hi):
        ts = [t for t in turns if t.sesion == s.index]
        first_line = people[pos[ts[0].seq_primero]].linea_inicial
        last_line = people[pos[ts[-1].seq_ultimo]].linea_inicial
        rows = []
        for i, t in enumerate(ts):
            nxt = ts[i + 1] if i + 1 < len(ts) else None
            rows.append({'turno': i + 1, 'quien': t.participante, 'mensajes': t.n_mensajes,
                         'primer_ts': t.primer_ts[:16], 'ultimo_ts': t.ultimo_ts[:16],
                         'min_hasta_que_interviene_el_otro': _mins(t.ultimo_ts, nxt.primer_ts) if nxt else None})
        out.append({'sesion': s.index, 'lineas': [first_line, last_line], 'turnos': len(ts), 'mensajes': s.n_mensajes,
                    'abre': s.reanuda, 'cierra': s.ultimo_mensaje,
                    'silencio_previo_min': None if s.silencio_previo_minutos is None else round(s.silencio_previo_minutos, 1),
                    'detalle': rows})
    return {'hueco_horas': gap, 'sesiones_totales': len(sessions), 'sesiones_elegidas': out}


def render(r):
    lines = [f"Hueco de sesión {r['hueco_horas']} h; {r['sesiones_totales']} sesiones en el chat. "
             f"Revisa estas {len(r['sesiones_elegidas'])} a mano (solo números):", '']
    for i, s in enumerate(r['sesiones_elegidas'], 1):
        lines.append(f"[{i}] sesión {s['sesion']}: líneas {s['lineas'][0]}–{s['lineas'][1]} | {s['turnos']} turnos, "
                     f"{s['mensajes']} mensajes | abre {s['abre']}, cierra {s['cierra']} | silencio previo "
                     f"{s['silencio_previo_min']} min")
        for t in s['detalle']:
            nx = '—' if t['min_hasta_que_interviene_el_otro'] is None else f"{t['min_hasta_que_interviene_el_otro']:g} min"
            lines.append(f"     turno {t['turno']:>2}: {t['quien']} {t['mensajes']:>2} msj  {t['primer_ts']} → "
                         f"{t['ultimo_ts']}  | tarda el otro: {nx}")
        lines.append('')
    return '\n'.join(lines)


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--aceptar-alias-sospechosos', action='store_true')
    ap.add_argument('-n', type=int, default=5)
    ap.add_argument('--min-turnos', type=int, default=4)
    ap.add_argument('--max-turnos', type=int, default=14)
    a = ap.parse_args(argv)
    real = os.path.realpath(a.ruta)
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    res = parse_file(real, date_order_hint=a.date_order_hint, accept_suspected_aliases=a.aceptar_alias_sospechosos)
    if res.accepted and a.confirmo_individual:
        res = res.confirm_individual()
    if not res.analysis_enabled:
        sys.exit('Análisis no habilitado: ' + ', '.join(res.pending_requirements or ['importación no aceptada']))
    print(render(review(res.messages, a.n, a.min_turnos, a.max_turnos)))


if __name__ == '__main__':
    main()

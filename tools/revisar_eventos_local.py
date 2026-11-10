"""Validación manual de la capa léxica (Fase 5.4): elige una MUESTRA de eventos y una de mensajes sin evento,
para que los revises a mano, y luego calcula la precisión por categoría y por regla.

  1) Generar la hoja de revisión (en tu carpeta de exportaciones, nunca dentro del repo):
       python tools/revisar_eventos_local.py RUTA --confirmo-individual [--date-order-hint dmy] --salida CARPETA [--con-texto] [--semilla 1]
     Crea  revision_eventos.local.csv  (para rellenar) y  revision_eventos.local.meta.json  (solo conteos).
     Por defecto la hoja NO contiene texto de mensajes: solo línea, persona, categoría, regla y expresión; abre la
     línea en tu .txt. Con --con-texto la hoja incluye el texto del mensaje (opcional; el archivo queda solo en tu máquina).
  2) Rellena la columna `veredicto`:  eventos:  c = correcto, i = incorrecto, a = ambiguo (no se puede saber)
                                      sin_evento:  ok = no había expresión, escapo = había una expresión no detectada
  3) Resumir (solo números; es seguro pegar la salida):
       python tools/revisar_eventos_local.py --resumir CARPETA/revision_eventos.local.csv

Tamaño de la muestra por categoría: n = N·96/(96+N−1) (margen ±10 % al 95 %, población finita), repartida entre
reglas y participantes. Los emojis no se revisan (la coincidencia es exacta; su significado no se valida aquí)."""
import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from metrics.validation import (allocate, draw, label_category, load_cfg, sample_size, systematic,  # noqa: E402
                                wilson)
from nlp.lexicon import events_for_message, load_lexicon  # noqa: E402
from parsers import parse_file  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402

CSV_NAME, META_NAME = 'revision_eventos.local.csv', 'revision_eventos.local.meta.json'
FIELDS = ['id', 'tipo', 'linea_inicial', 'linea_final', 'participante', 'categoria', 'regla', 'expresion',
          'variante', 'texto', 'veredicto', 'nota']
OK_EVENT = {'c': 'c', 'correcto': 'c', 'i': 'i', 'incorrecto': 'i', 'a': 'a', 'ambiguo': 'a'}
OK_RECALL = {'ok': 'ok', 'no': 'ok', 'n': 'ok', 'escapo': 'escapo', 'si': 'escapo', 's': 'escapo'}


def muestrear(messages, lex, cfg, seed=1, con_texto=False):
    """Devuelve (filas, meta). Solo eventos afirmativos de categorías de texto (no emoji_*)."""
    by_cat = defaultdict(list)                        # categoría -> [(msg, evento)]
    sin_evento = []
    for m in messages:
        if m.tipo != 'texto' or not m.participante:
            continue
        evs, _ = events_for_message(m, lex)
        aff = [e for e in evs if e.forma == 'afirmativa' and not e.categoria.startswith('emoji')]
        for e in aff:
            by_cat[e.categoria].append((m, e))
        if not aff:
            sin_evento.append(m)
    rows, meta = [], {'semilla': seed, 'categorias': {}, 'sin_evento': {'poblacion': len(sin_evento)},
                      'con_texto': con_texto}
    n_id = 0

    def row(tipo, m, e=None):
        nonlocal n_id
        n_id += 1
        return {'id': n_id, 'tipo': tipo, 'linea_inicial': m.linea_inicial, 'linea_final': m.linea_final,
                'participante': m.participante, 'categoria': e.categoria if e else '', 'regla': '+'.join(e.reglas) if e else '',
                'expresion': ' | '.join(x for x, _ in e.expresiones) if e else '',
                'variante': ('amplia' if e.ambiguo else 'estricta') if e else '',
                'texto': m.texto if con_texto else '', 'veredicto': '', 'nota': ''}

    for cat in sorted(by_cat):
        items = by_cat[cat]
        N = len(items)
        strata = defaultdict(list)
        for m, e in items:
            strata['+'.join(e.reglas) + '/' + m.participante].append((m, e))
        n = N if N < cfg['min_events'] else sample_size(N, cfg['n0'])
        alloc = allocate({k: len(v) for k, v in strata.items()}, n)
        for k in sorted(strata):
            for m, e in draw(strata[k], alloc[k], seed, f'{cat}:{k}'):
                rows.append(row('evento', m, e))
        meta['categorias'][cat] = {'poblacion': N, 'muestra': sum(alloc.values()),
                                   'estratos': {k: [len(strata[k]), alloc[k]] for k in sorted(strata)}}
    k = min(len(sin_evento), cfg['recall_max_messages'])
    for m in systematic(sin_evento, k, seed):
        rows.append(row('sin_evento', m))
    meta['sin_evento']['muestra'] = k
    return rows, meta


def resumir(path, cfg=None):
    cfg = cfg or load_cfg()
    meta = json.load(open(path.replace('.csv', '.meta.json'), encoding='utf-8'))
    with open(path, encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    ev = defaultdict(list)
    rec = []
    for r in rows:
        v = (r['veredicto'] or '').strip().lower()
        if r['tipo'] == 'evento':
            ev[r['categoria']].append((r['regla'], OK_EVENT.get(v)))
        else:
            rec.append(OK_RECALL.get(v))
    out = ['Validación de la capa léxica (precisión = correctos / revisados; ambiguos cuentan como no correctos)']
    for cat, info in meta['categorias'].items():
        lst = ev.get(cat, [])
        rev = [v for _, v in lst if v]
        c = Counter(rev)
        n = len(rev)
        lo, hi = wilson(c['c'], n)
        lab = label_category(n, c['c'], cfg) if n else 'sin_revisar'
        ci = f' IC95 [{lo:.2f}-{hi:.2f}]' if n else ''
        out.append(f"  {cat}: eventos {info['poblacion']}, muestra {info['muestra']}, revisados {n} "
                   f"(c {c['c']}, i {c['i']}, a {c['a']}) precisión {c['c'] / n:.2f}{ci} -> {lab}" if n else
                   f"  {cat}: eventos {info['poblacion']}, muestra {info['muestra']}, revisados 0 -> sin_revisar")
        by_rule = defaultdict(list)
        for rule, v in lst:
            if v:
                by_rule[rule].append(v)
        for rule, vs in sorted(by_rule.items()):
            cc = Counter(vs)
            flag = ''
            if len(vs) >= cfg['min_reviewed_rule'] and cc['c'] / len(vs) < cfg['drop_point']:
                flag = '  <- REVISAR/ELIMINAR regla'
            out.append(f"      {rule}: {len(vs)} revisados, c {cc['c']} i {cc['i']} a {cc['a']} "
                       f"({cc['c'] / len(vs):.2f}){flag}")
    got = [v for v in rec if v]
    if got:
        miss = got.count('escapo')
        lo, hi = wilson(miss, len(got))
        pop = meta['sin_evento']['poblacion']
        out.append(f"Recuperación: de {len(got)} mensajes sin evento revisados, {miss} tenían una expresión no detectada "
                   f"({miss / len(got):.1%}, IC95 [{lo:.1%}-{hi:.1%}]) sobre {pop} mensajes sin evento")
    else:
        out.append('Recuperación: sin revisar')
    return '\n'.join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta', nargs='?')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--salida', help='carpeta donde crear la hoja (fuera del repo)')
    ap.add_argument('--con-texto', action='store_true')
    ap.add_argument('--semilla', type=int, default=1)
    ap.add_argument('--resumir', metavar='CSV')
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if a.resumir:
        if is_inside(os.path.realpath(a.resumir), os.path.realpath(ROOT)):
            sys.exit('Por privacidad la hoja de revisión no se lee dentro del repositorio.')
        print(resumir(a.resumir))
        return
    if not a.ruta or not a.salida:
        sys.exit('Indica RUTA y --salida CARPETA (o --resumir CSV).')
    real = os.path.realpath(a.ruta)
    out_dir = os.path.realpath(a.salida)
    if is_inside(real, os.path.realpath(ROOT)) or is_inside(out_dir, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se lee ni se escribe dentro del repositorio.')
    res = parse_file(real, date_order_hint=a.date_order_hint)
    if res.accepted and a.confirmo_individual:
        res = res.confirm_individual()
    if not res.analysis_enabled:
        sys.exit('Análisis no habilitado: ' + ', '.join(res.pending_requirements or ['importación no aceptada']))
    lex = load_lexicon(local_path=os.path.join(os.path.dirname(real), 'lexicon_local.yaml'))
    rows, meta = muestrear(res.messages, lex, load_cfg(), seed=a.semilla, con_texto=a.con_texto)
    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(out_dir, CSV_NAME)
    if os.path.exists(dest):
        sys.exit(f'Ya existe {CSV_NAME} en esa carpeta; no se sobrescribe (puede tener tus veredictos). Bórralo o usa otra carpeta.')
    with open(dest, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(out_dir, META_NAME), 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print('Creado:', dest)
    print('Eventos a revisar por categoría (población → muestra):')
    for cat, i in meta['categorias'].items():
        print(f"  {cat}: {i['poblacion']} → {i['muestra']}")
    print(f"Mensajes sin evento: {meta['sin_evento']['poblacion']} → {meta['sin_evento']['muestra']}")
    print('Texto de mensajes en la hoja:', 'SÍ (--con-texto)' if a.con_texto else 'no (abre cada línea en tu .txt)')


if __name__ == '__main__':
    main()

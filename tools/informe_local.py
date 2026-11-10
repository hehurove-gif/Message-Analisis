#!/usr/bin/env python3
r"""Informe completo de TODOS tus chats con un solo comando, y comparación entre dos informes (inicio vs final).

1) Generar un informe (analiza cada .txt de la carpeta salvo los *.local.txt, los mismos que `$archivos`):
     python tools/informe_local.py CARPETA --confirmo-individual [--hint 4=dmy] [--alias N] [--solo 0,1] [--etiqueta inicio]
   Escribe en CARPETA\informes\ (fuera del repo):
     informe_<etiqueta>_<fecha>.md    informe legible: tabla comparativa, léxico por archivo y resumen completo por archivo
     informe_<etiqueta>_<fecha>.json  "foto" de todos los números (para comparar después)
   Solo números e índices (0, 1, …): ningún nombre de archivo, de persona ni texto de mensajes.
   Cada informe registra la versión del código (commit) y la huella del léxico y de la configuración usados.

2) Comparar dos informes (qué cambió entre el inicio y el final):
     python tools/informe_local.py --comparar ANTES.json DESPUES.json [--max 40]
   Escribe comparacion_<antes>_vs_<despues>.md junto al informe DESPUÉS y lo imprime."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from comparar_local import COLS, fila, tabla  # noqa: E402
from metricas_local import analizar, resumen  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402


def archivos_de(carpeta):
    """Chats de la carpeta: .txt que NO terminan en .local.txt, orden sin distinguir mayúsculas (como $archivos)."""
    return [os.path.join(carpeta, f) for f in sorted((f for f in os.listdir(carpeta)
            if f.lower().endswith('.txt') and not f.lower().endswith('.local.txt')), key=lambda f: (f.casefold(), f))]


def _huella(*rutas):
    h = hashlib.sha1()
    for r in rutas:
        with open(r, 'rb') as f:
            h.update(f.read())
    return h.hexdigest()[:8]


def _git():
    try:
        c = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        d = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, timeout=10).stdout.strip()
        return (c or 'desconocido') + (' (con cambios sin guardar)' if d else '')
    except Exception:
        return 'desconocido'


def tabla_lexico(out):
    """Tabla Markdown del conteo léxico (mensajes con evento por persona, variante estricta y amplia)."""
    lx = out['lexico']
    names = list(lx['base'])
    head = ['categoría'] + [f'estricta {n}' for n in names] + [f'amplia {n}' for n in names] + [f'días estr. {n}' for n in names] + ['robustez']
    rows = []
    for cat, d in lx['por_categoria'].items():
        rows.append([cat] + [str(d['estricta'][n]['mensajes_con_evento']) for n in names]
                    + [str(d['amplia'][n]['mensajes_con_evento']) for n in names]
                    + [str(d['estricta'][n]['dias_con_evento']) for n in names] + [d['robustez_indicadores']])
    base = ' · '.join(f"{n}: {v['mensajes_texto']} msj de texto, {v['turnos']} turnos, {v['dias_activos']} días" for n, v in lx['base'].items())
    return f'_Base — {base}_\n\n' + md_tabla(head, rows)


def md_tabla(head, rows):
    esc = lambda x: str(x).replace('|', '\\|')   # noqa: E731
    return '\n'.join(['| ' + ' | '.join(esc(h) for h in head) + ' |', '|' + '|'.join('---' for _ in head) + '|']
                     + ['| ' + ' | '.join(esc(c) for c in r) + ' |' for r in rows])


def generar(a):
    carpeta = os.path.realpath(a.carpeta)
    sal = os.path.realpath(a.salida or os.path.join(carpeta, 'informes'))
    if is_inside(carpeta, os.path.realpath(ROOT)) or is_inside(sal, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se lee ni se escribe dentro del repositorio.')
    files = archivos_de(carpeta)
    if not files:
        sys.exit('No hay chats .txt en esa carpeta.')
    hints = {int(k): v for k, v in (x.split('=', 1) for x in a.hint)}
    solo = {int(x) for x in a.solo.split(',')} if a.solo else None
    ahora = datetime.now()
    sello = ahora.strftime('%Y-%m-%d_%H%M')
    etiqueta = a.etiqueta or 'informe'
    meta = {'etiqueta': etiqueta, 'fecha': ahora.strftime('%Y-%m-%d %H:%M'), 'commit': _git(),
            'huella_lexico': _huella(os.path.join(ROOT, 'lexicon', 'es_mx.yaml')),
            'huella_config': _huella(os.path.join(ROOT, 'config.yaml'))}
    outs, filas, trozos = {}, [], []
    for i, f in enumerate(files):
        if solo is not None and i not in solo:
            continue
        kb = str(round(os.path.getsize(f) / 1024))
        print(f'[{i}] analizando ({kb} KB)…', flush=True)
        out = analizar(f, confirmo=a.confirmo_individual, date_order_hint=hints.get(i), aceptar_alias=i in a.alias,
                       yo=None)
        outs[str(i)] = {'kb': kb, 'out': out}
        filas.append(fila(i, out, kb))
        if out['analisis_habilitado']:
            trozos.append(f"## Archivo {i} ({kb} KB)\n\n### Léxico (mensajes con evento)\n\n{tabla_lexico(out)}\n\n"
                          f"### Resumen completo\n\n```text\n{resumen(out)}\n```\n")
        else:
            trozos.append(f"## Archivo {i} ({kb} KB)\n\nNo se analizó: {out['importacion']} — "
                          f"{', '.join(out['requisitos_pendientes'] or ['importación no aceptada'])}\n")
    md = [f"# Informe «{etiqueta}» — {meta['fecha']}", '',
          f"- Código: `{meta['commit']}` · léxico `{meta['huella_lexico']}` · configuración `{meta['huella_config']}`",
          f"- Archivos analizados: {len(outs)} de {len(files)} (índices como `$archivos[N]`)",
          '- Solo números: ningún nombre de archivo, de persona ni texto de mensajes. A = primer autor de cada archivo.', '',
          '## Tabla comparativa (% de A; B = resto)', '', '```text', tabla(filas), '```', '', *trozos]
    os.makedirs(sal, exist_ok=True)
    base = os.path.join(sal, f'informe_{etiqueta}_{sello}')
    with open(base + '.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    with open(base + '.json', 'w', encoding='utf-8') as f:
        json.dump({'meta': meta, 'archivos': outs}, f, ensure_ascii=False, default=str, sort_keys=True)
    print('\nInforme :', base + '.md')
    print('Foto    :', base + '.json  (para --comparar)')
    print(f"Código {meta['commit']} · léxico {meta['huella_lexico']} · config {meta['huella_config']}")


def _hojas(d, pre=''):
    """Hojas (número o texto) de un diccionario anidado: {ruta: valor}."""
    if isinstance(d, dict):
        r = {}
        for k, v in d.items():
            r.update(_hojas(v, f'{pre}.{k}' if pre else str(k)))
        return r
    if isinstance(d, (list, tuple)):
        r = {}
        for i, v in enumerate(d):
            r.update(_hojas(v, f'{pre}[{i}]'))
        return r
    return {pre: d}


def _delta(x, y):
    if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
        d = y - x
        return f' ({"+" if d > 0 else "−"}{abs(round(d, 4)):g})'
    return ''


def comparar(a):
    for p in a.comparar:
        if is_inside(os.path.realpath(p), os.path.realpath(ROOT)):
            sys.exit('Por privacidad no se leen informes dentro del repositorio.')
    antes, despues = (json.load(open(p, encoding='utf-8')) for p in (a.comparar[0], a.comparar[1]))
    L = [f"# Comparación: «{antes['meta']['etiqueta']}» ({antes['meta']['fecha']}) → «{despues['meta']['etiqueta']}» ({despues['meta']['fecha']})", '',
         f"- Antes:   código `{antes['meta']['commit']}` · léxico `{antes['meta']['huella_lexico']}` · config `{antes['meta']['huella_config']}`",
         f"- Después: código `{despues['meta']['commit']}` · léxico `{despues['meta']['huella_lexico']}` · config `{despues['meta']['huella_config']}`", '']
    comunes = sorted(set(antes['archivos']) & set(despues['archivos']), key=int)
    for idx in comunes:
        x, y = _hojas(antes['archivos'][idx]['out']), _hojas(despues['archivos'][idx]['out'])
        sec = {}
        for k in sorted(set(x) | set(y)):
            vx, vy = x.get(k, '(no existía)'), y.get(k, '(ya no existe)')
            if vx != vy:
                sec.setdefault(k.split('.')[0], []).append((k, vx, vy))
        total = sum(len(v) for v in sec.values())
        L += [f'## Archivo {idx}: {total} valores distintos', '']
        if not total:
            L += ['Sin cambios.', '']
            continue
        L += [md_tabla(['sección', 'valores que cambian'], [[s, len(v)] for s, v in sorted(sec.items())]), '']
        for s, v in sorted(sec.items()):
            L += [f'### {s} ({len(v)})', '', '```text']
            for k, vx, vy in v[:a.max]:
                L.append(f'{k[len(s) + 1:] or s}: {vx} → {vy}{_delta(vx, vy)}')
            if len(v) > a.max:
                L.append(f'… y {len(v) - a.max} más (usa --max)')
            L += ['```', '']
    solo = sorted((set(antes['archivos']) ^ set(despues['archivos'])), key=int)
    if solo:
        L += ['Archivos que solo están en uno de los dos informes: ' + ', '.join(solo), '']
    nombre = f"comparacion_{antes['meta']['etiqueta']}_vs_{despues['meta']['etiqueta']}.md"
    dest = os.path.join(os.path.dirname(os.path.realpath(a.comparar[1])), nombre)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print('\n'.join(L))
    print('Escrito:', dest)


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('carpeta', nargs='?')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--hint', action='append', default=[], metavar='N=dmy')
    ap.add_argument('--alias', action='append', default=[], type=int, metavar='N')
    ap.add_argument('--solo', help='índices a analizar, separados por coma (por defecto todos)')
    ap.add_argument('--etiqueta', help='nombre del informe, p. ej. inicio, fase5, final')
    ap.add_argument('--salida', help='carpeta de los informes (por defecto CARPETA\\informes)')
    ap.add_argument('--comparar', nargs=2, metavar=('ANTES.json', 'DESPUES.json'))
    ap.add_argument('--max', type=int, default=40, help='valores por sección en la comparación')
    a = ap.parse_args(argv)
    if a.comparar:
        return comparar(a)
    if not a.carpeta:
        sys.exit('Indica la CARPETA de exportaciones, o --comparar ANTES.json DESPUES.json.')
    generar(a)


if __name__ == '__main__':
    main()

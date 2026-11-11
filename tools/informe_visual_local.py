#!/usr/bin/env python3
r"""Informe VISUAL (una página HTML con scroll) a partir de la "foto" .json de `informe_local.py`.

    python tools/informe_visual_local.py CARPETA\informes\informe_fase5_2026-11-11_0046.json [--salida ARCHIVO.html]

(o directamente al generar:  python tools/informe_local.py CARPETA --confirmo-individual --etiqueta fase5 --html)

- Escribe un .html junto al .json (fuera del repo). Se abre con doble clic en el navegador.
- Estilos con Tailwind (CDN, `cdn.tailwindcss.com`): el navegador descarga la librería de estilos, pero NINGÚN dato
  sale de tu computadora. Sin internet la página se sigue leyendo, solo con estilos básicos. Las gráficas son SVG
  propios (sin librerías de gráficas).
- Contiene los NOMBRES de los participantes si el informe se generó con nombres (por defecto): archivo privado.
  Nunca contiene texto de mensajes. No se lee ni se escribe dentro del repositorio.
- Solo describe: no interpreta interés, cercanía ni reciprocidad."""
import argparse
import html
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from validar_exportacion_local import is_inside  # noqa: E402

TAILWIND = 'https://cdn.tailwindcss.com/3.4.17'
E = html.escape
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

CSS = r"""
:root{--a:#2563eb;--b:#ea580c;--bg:#f8fafc;--card:#ffffff;--ink:#0f172a;--mute:#64748b;--line:#e2e8f0;--ok:#15803d;--warn:#b45309}
@media (prefers-color-scheme: dark){:root{--a:#60a5fa;--b:#fb923c;--bg:#0b1120;--card:#111a2e;--ink:#e2e8f0;--mute:#94a3b8;--line:#243049;--ok:#4ade80;--warn:#fbbf24}}
html{scroll-behavior:smooth;scroll-padding-top:4.5rem}
body{background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:1.1rem 1.25rem}
.mute{color:var(--mute)} .ca{color:var(--a)} .cb{color:var(--b)} .ba{background:var(--a)} .bb{background:var(--b)}
.fa{fill:var(--a)} .fb{fill:var(--b)} .sa{stroke:var(--a)} .sb{stroke:var(--b)} .sx{stroke:var(--ink)} .sy{stroke:var(--mute);stroke-dasharray:6 4} .fx{fill:var(--ink)} .fy{fill:var(--mute)}
.axis{stroke:var(--line)} .tick{fill:var(--mute);font-size:10px}
.chip{display:inline-block;border-radius:999px;padding:.05rem .55rem;font-size:.72rem;border:1px solid var(--line);color:var(--mute);white-space:nowrap}
.chip.ok{color:var(--ok);border-color:var(--ok)} .chip.warn{color:var(--warn);border-color:var(--warn)}
.track{background:var(--line);border-radius:999px;overflow:hidden;display:flex;height:.6rem;position:relative}
table.t{width:100%;border-collapse:collapse;font-size:.85rem} table.t th{color:var(--mute);font-weight:500;text-align:left;padding:.35rem .5rem;border-bottom:1px solid var(--line)}
table.t td{padding:.4rem .5rem;border-bottom:1px solid var(--line);vertical-align:middle}
nav a{display:block;padding:.2rem .5rem;border-radius:8px;color:var(--mute);font-size:.85rem;text-decoration:none} nav a:hover{background:var(--line);color:var(--ink)}
h2{font-size:1.05rem;font-weight:650;margin:0 0 .6rem} h3{font-size:.9rem;font-weight:600;margin:1rem 0 .4rem}
details>summary{cursor:pointer;color:var(--mute);font-size:.85rem}

/* Respaldo mínimo con las mismas utilidades de Tailwind que usa la página: sin internet se ve igual; con Tailwind coinciden. */
*,*::before,*::after{box-sizing:border-box}
.flex{display:flex}.grid{display:grid}.hidden{display:none}.flex-wrap{flex-wrap:wrap}.items-center{align-items:center}.items-baseline{align-items:baseline}.justify-between{justify-content:space-between}
.grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.grid-cols-12{grid-template-columns:repeat(12,minmax(0,1fr))}.col-span-12{grid-column:span 12/span 12}
.gap-1\.5{gap:.375rem}.gap-2{gap:.5rem}.gap-3{gap:.75rem}.gap-x-3{column-gap:.75rem}.gap-x-6{column-gap:1.5rem}
.mx-auto{margin-left:auto;margin-right:auto}.max-w-7xl{max-width:80rem}.min-w-0{min-width:0}.w-full{width:100%}.w-12{width:3rem}
.px-4{padding-left:1rem;padding-right:1rem}.py-1{padding-top:.25rem;padding-bottom:.25rem}.py-1\.5{padding-top:.375rem;padding-bottom:.375rem}.py-2{padding-top:.5rem;padding-bottom:.5rem}.py-2\.5{padding-top:.625rem;padding-bottom:.625rem}.py-6{padding-top:1.5rem;padding-bottom:1.5rem}
.p-2{padding:.5rem}.p-3{padding:.75rem}.pb-10{padding-bottom:2.5rem}.pl-5{padding-left:1.25rem}
.mt-0\.5{margin-top:.125rem}.mt-1{margin-top:.25rem}.mt-2{margin-top:.5rem}.mt-3{margin-top:.75rem}.mb-1{margin-bottom:.25rem}.mb-1\.5{margin-bottom:.375rem}.mb-2{margin-bottom:.5rem}.mb-3{margin-bottom:.75rem}.mb-14{margin-bottom:3.5rem}
.space-y-0\.5>*+*{margin-top:.125rem}.space-y-1\.5>*+*{margin-top:.375rem}.space-y-5>*+*{margin-top:1.25rem}
.text-xs{font-size:.75rem;line-height:1rem}.text-sm{font-size:.875rem;line-height:1.25rem}.text-lg{font-size:1.125rem;line-height:1.75rem}.text-right{text-align:right}.font-medium{font-weight:500}.font-semibold{font-weight:600}
.rounded-lg{border-radius:.5rem}.rounded-xl{border-radius:.75rem}.list-disc{list-style:disc}.whitespace-nowrap{white-space:nowrap}.overflow-x-auto{overflow-x:auto}.overflow-y-auto{overflow-y:auto}
.sticky{position:sticky}.top-0{top:0}.top-16{top:4rem}.z-10{z-index:10}.max-h-\[calc\(100vh-5rem\)\]{max-height:calc(100vh - 5rem)}
@media (min-width:640px){.sm\:col-span-4{grid-column:span 4/span 4}.sm\:col-span-8{grid-column:span 8/span 8}}
@media (min-width:768px){.md\:grid-cols-2{grid-template-columns:repeat(2,minmax(0,1fr))}.md\:grid-cols-4{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media (min-width:1024px){.lg\:block{display:block}.lg\:grid{display:grid}.lg\:gap-8{gap:2rem}.lg\:grid-cols-\[13rem_1fr\]{grid-template-columns:13rem 1fr}}
@media (min-width:1280px){.xl\:grid-cols-3{grid-template-columns:repeat(3,minmax(0,1fr))}}
"""


# ---------------------------------------------------------------- utilidades
def pct(x, d=0):
    return '—' if x is None else f'{x * 100:.{d}f}%'


def num(x, d=1):
    if x is None:
        return '—'
    return f'{x:,.{d}f}'.rstrip('0').rstrip('.') if isinstance(x, float) else f'{x:,}'


def minutos(m):
    if m is None:
        return '—'
    if m < 90:
        return f'{m:g} min'
    if m < 60 * 36:
        return f'{m / 60:.1f} h'
    return f'{m / 1440:.1f} días'


def corto(nombre, n=26):
    return nombre if len(nombre) <= n else nombre[:n - 1] + '…'


def chip(texto, tipo=''):
    return f'<span class="chip {tipo}">{E(str(texto))}</span>'


def etiqueta_chip(e):
    if not e:
        return ''
    t = {'robusto': 'ok', 'robusto_ante_indicadores': 'ok', 'suficiente': 'ok', 'simetrica': 'ok',
         'sensible_a_granularidad': 'warn', 'sensible_a_indicadores': 'warn', 'insuficiente': 'warn',
         'sensible_a_umbrales': 'warn'}.get(e, '')
    return chip(str(e).replace('_', ' '), t)


def periodo_corto(p):
    if '-W' in p:
        return p.replace('-W', ' s')
    y, m = p.split('-')
    return f"{MESES[int(m) - 1]} {y[2:]}"


class Ctx:
    """Nombres a mostrar y títulos de una conversación."""
    def __init__(self, out):
        n = out.get('nombres') or {}
        self.n = {'A': n.get('A', 'A'), 'B': n.get('B', 'B')}

    def a(self):
        return E(corto(self.n['A']))

    def b(self):
        return E(corto(self.n['B']))

    def leyenda(self):
        return (f'<span class="ca">●</span> {self.a()} &nbsp; <span class="cb">●</span> {self.b()}')


# ---------------------------------------------------------------- piezas visuales
def split_bar(a, b=None, base=None, fa=None, fb=None, titulo=''):
    """Barra partida A | B (a + b = 100 %). `base` = proporción de referencia (marca)."""
    if b is None and a is not None:
        b = 1 - a
    if a is None:
        return '<div class="mute text-xs">—</div>'
    t = f' title="{E(titulo)}"' if titulo else ''
    marca = f'<div style="position:absolute;left:{base * 100:.1f}%;top:-2px;bottom:-2px;width:2px;background:var(--ink);opacity:.55" title="referencia: {pct(base)}"></div>' if base is not None else ''
    return (f'<div class="track"{t}><div class="ba" style="width:{a * 100:.2f}%"></div><div class="bb" style="width:{b * 100:.2f}%"></div>{marca}</div>'
            f'<div class="flex justify-between text-xs mt-0.5"><span class="ca">{fa if fa is not None else pct(a)}</span>'
            f'<span class="cb">{fb if fb is not None else pct(b)}</span></div>')


def fila_split(etiqueta, a, b=None, base=None, fa=None, fb=None, nota=''):
    return (f'<div class="grid grid-cols-12 gap-3 items-center py-1.5"><div class="col-span-12 sm:col-span-4 text-sm">{E(etiqueta)}'
            f'{f"<div class=mute style=font-size:.72rem>{E(nota)}</div>" if nota else ""}</div>'
            f'<div class="col-span-12 sm:col-span-8">{split_bar(a, b, base, fa, fb)}</div></div>')


def fila_par(etiqueta, a, b, fmt=pct):
    """Dos barras independientes (cada una en su escala 0..max)."""
    m = max([v for v in (a, b) if v is not None] + [1e-9])
    def barra(v, cl):
        w = 0 if v is None else v / m * 100
        return f'<div class="flex items-center gap-2"><div class="track" style="flex:1;height:.5rem"><div class="{cl}" style="width:{w:.1f}%"></div></div><span class="text-xs w-12 text-right">{fmt(v)}</span></div>'
    return (f'<div class="grid grid-cols-12 gap-3 items-center py-1"><div class="col-span-12 sm:col-span-4 text-sm">{E(etiqueta)}</div>'
            f'<div class="col-span-12 sm:col-span-8 space-y-0.5">{barra(a, "ba")}{barra(b, "bb")}</div></div>')


def _escala(vals, ymin=None, ymax=None):
    v = [x for x in vals if x is not None]
    lo = ymin if ymin is not None else (min(v) if v else 0)
    hi = ymax if ymax is not None else (max(v) if v else 1)
    if hi <= lo:
        hi = lo + 1
    return lo, hi


def ejes_x(periodos, x0, x1, y, w_step, cada=None):
    n = len(periodos)
    cada = cada or max(1, -(-n // 10))
    out = []
    for i, p in enumerate(periodos):
        if i % cada == 0:
            cx = x0 + (i + .5) * w_step
            out.append(f'<text class="tick" x="{cx:.1f}" y="{y}" text-anchor="middle">{E(periodo_corto(p))}</text>')
    return ''.join(out)


def barras_apiladas(periodos, a_vals, b_vals, marcas=None, w=760, h=210, fmt=num):
    """Barras apiladas A/B por periodo. marcas[i] in {None,'parcial','pausa'}."""
    if not periodos:
        return ''
    l, r, t, bt = 44, 8, 8, 24
    tot = [(x or 0) + (y or 0) for x, y in zip(a_vals, b_vals)]
    lo, hi = _escala(tot, 0)
    pw = (w - l - r) / len(periodos)
    bw = max(1.5, pw * .72)
    Y = lambda v: t + (h - t - bt) * (1 - (v - lo) / (hi - lo))   # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" class="w-full" role="img">']
    for g in range(5):
        v = lo + (hi - lo) * g / 4
        out.append(f'<line class="axis" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="tick" x="{l - 5}" y="{Y(v) + 3:.1f}" text-anchor="end">{fmt(v, 0) if v >= 10 else fmt(v)}</text>')
    for i, p in enumerate(periodos):
        x = l + i * pw + (pw - bw) / 2
        va, vb = a_vals[i] or 0, b_vals[i] or 0
        op = '.45' if marcas and marcas[i] == 'parcial' else '1'
        tip = f'{periodo_corto(p)}: A {num(va, 0)} · B {num(vb, 0)}' + (f' ({marcas[i]})' if marcas and marcas[i] else '')
        out.append(f'<g opacity="{op}"><title>{E(tip)}</title><rect class="fa" x="{x:.1f}" y="{Y(va):.1f}" width="{bw:.1f}" height="{max(0, Y(0) - Y(va)):.1f}"/>'
                   f'<rect class="fb" x="{x:.1f}" y="{Y(va + vb):.1f}" width="{bw:.1f}" height="{max(0, Y(va) - Y(va + vb)):.1f}"/></g>')
        if marcas and marcas[i] == 'pausa':
            out.append(f'<rect x="{l + i * pw:.1f}" y="{t}" width="{pw:.1f}" height="{h - t - bt}" fill="currentColor" opacity=".06"/>')
    out.append(ejes_x(periodos, l, w - r, h - 8, pw))
    out.append('</svg>')
    return ''.join(out)


def lineas(periodos, series, w=760, h=200, ymin=None, ymax=None, fmt=pct, ref=None, marcas=None, small=False):
    """series = [(nombre, clase 'a'|'b'|'x', valores con None)]; los None cortan la línea."""
    if not periodos:
        return ''
    l, r, t, bt = (30, 4, 4, 14) if small else (44, 10, 10, 24)
    allv = [v for _, _, vs in series for v in vs]
    lo, hi = _escala(allv, ymin, ymax)
    n = len(periodos)
    pw = (w - l - r) / max(1, n)
    X = lambda i: l + (i + .5) * pw          # noqa: E731
    Y = lambda v: t + (h - t - bt) * (1 - (v - lo) / (hi - lo))   # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" class="w-full" role="img">']
    for g in range(3 if small else 5):
        v = lo + (hi - lo) * g / (2 if small else 4)
        out.append(f'<line class="axis" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="tick" x="{l - 4}" y="{Y(v) + 3:.1f}" text-anchor="end">{fmt(v)}</text>')
    if ref is not None and lo < ref < hi:
        out.append(f'<line x1="{l}" x2="{w - r}" y1="{Y(ref):.1f}" y2="{Y(ref):.1f}" stroke="currentColor" stroke-dasharray="4 4" opacity=".35"/>')
    if marcas:
        for i, m in enumerate(marcas):
            if m == 'pausa':
                out.append(f'<rect x="{l + i * pw:.1f}" y="{t}" width="{pw:.1f}" height="{h - t - bt}" fill="currentColor" opacity=".06"/>')
    cl = {'a': 'sa', 'b': 'sb', 'x': 'sx', 'y': 'sy'}
    fl = {'a': 'fa', 'b': 'fb', 'x': 'fx', 'y': 'fy'}
    for nombre, c, vs in series:
        seg, ds = [], []
        for i, v in enumerate(vs):
            if v is None:
                if seg:
                    ds.append(seg)
                seg = []
            else:
                seg.append((X(i), Y(v)))
        if seg:
            ds.append(seg)
        for s in ds:
            if len(s) > 1:
                out.append(f'<polyline class="{cl[c]}" fill="none" stroke-width="2" stroke-linejoin="round" points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in s)}"/>')
        for i, v in enumerate(vs):
            if v is not None:
                out.append(f'<circle class="{fl[c]}" cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{1.8 if small else 2.6}"><title>{E(nombre)} · {E(periodo_corto(periodos[i]))}: {E(fmt(v))}</title></circle>')
    if not small:
        out.append(ejes_x(periodos, l, w - r, h - 8, pw))
    out.append('</svg>')
    return ''.join(out)


def horas_chart(por_hora_a, por_hora_b, w=760, h=170):
    """24 barras agrupadas: proporción de los mensajes de cada persona por hora del día."""
    tot_a, tot_b = sum(por_hora_a.values()) or 1, sum(por_hora_b.values()) or 1
    va = [por_hora_a.get(str(i), 0) / tot_a for i in range(24)]
    vb = [por_hora_b.get(str(i), 0) / tot_b for i in range(24)]
    l, r, t, bt = 36, 6, 6, 20
    hi = max(va + vb + [1e-9])
    pw = (w - l - r) / 24
    Y = lambda v: t + (h - t - bt) * (1 - v / hi)   # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" class="w-full" role="img">']
    for g in range(3):
        v = hi * g / 2
        out.append(f'<line class="axis" x1="{l}" x2="{w - r}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text class="tick" x="{l - 4}" y="{Y(v) + 3:.1f}" text-anchor="end">{pct(v)}</text>')
    for i in range(24):
        x = l + i * pw
        out.append(f'<rect class="fa" x="{x + pw * .08:.1f}" y="{Y(va[i]):.1f}" width="{pw * .4:.1f}" height="{max(0, Y(0) - Y(va[i])):.1f}"><title>{i:02d} h · A {pct(va[i], 1)}</title></rect>'
                   f'<rect class="fb" x="{x + pw * .5:.1f}" y="{Y(vb[i]):.1f}" width="{pw * .4:.1f}" height="{max(0, Y(0) - Y(vb[i])):.1f}"><title>{i:02d} h · B {pct(vb[i], 1)}</title></rect>')
        if i % 3 == 0:
            out.append(f'<text class="tick" x="{x + pw / 2:.1f}" y="{h - 6}" text-anchor="middle">{i:02d}</text>')
    out.append('</svg>')
    return ''.join(out)


def apilada_h(partes, color='--a'):
    """Barra 100 % de varias partes [(etiqueta, valor, opacidad)] en el color de la persona; la etiqueta va dentro si cabe."""
    tot = sum(v for _, v, _ in partes) or 1
    seg = ''
    for e, v, op in partes:
        if not v:
            continue
        txt = f'<span style="font-size:.62rem;color:#fff;white-space:nowrap;overflow:hidden">{E(e)}</span>' if v / tot >= .11 and op >= .4 else ''
        seg += (f'<div style="width:{v / tot * 100:.2f}%;background:var({color});opacity:{op};display:flex;align-items:center;justify-content:center" '
                f'title="{E(e)}: {pct(v / tot, 1)}">{txt}</div>')
    leg = ' '.join(f'<span class="text-xs mute">{E(e)} {pct(v / tot)}</span>' for e, v, _ in partes)
    return f'<div class="track" style="height:1.1rem">{seg}</div><div class="flex flex-wrap gap-x-3 mt-0.5">{leg}</div>'


def card(titulo, cuerpo, id_=None, extra=''):
    i = f' id="{id_}"' if id_ else ''
    return f'<section class="card"{i}><div class="flex items-baseline justify-between gap-3 flex-wrap"><h2>{E(titulo)}</h2>{extra}</div>{cuerpo}</section>'


# ---------------------------------------------------------------- secciones de un chat
def s_participacion(o, cx):
    p, ct = o['participacion'], o['contenido_turnos']
    pr, pe = p['proporciones'], ct['proporciones_entre_participantes']
    pp = p['por_participante']
    d = pp['A']['dias_con_mensajes'], pp['B']['dias_con_mensajes']
    f = [fila_split('Mensajes', pr['mensajes']['A'], pr['mensajes']['B'], fa=num(pp['A']['mensajes'], 0), fb=num(pp['B']['mensajes'], 0)),
         fila_split('Palabras', pr['palabras']['A'], pr['palabras']['B'], fa=num(pp['A']['palabras'], 0), fb=num(pp['B']['palabras'], 0)),
         fila_split('Turnos', pr['turnos']['A'], pr['turnos']['B'], nota='los turnos alternan: ~50/50 por definición'),
         fila_split('Turnos que no son mínimos', pe['turnos_no_minimos']['A'], pe['turnos_no_minimos']['B']),
         fila_split(f'Turnos desarrollados (≥ {ct["umbral_desarrollado_palabras"]} palabras)', pe['turnos_desarrollados']['A'], pe['turnos_desarrollados']['B'],
                    nota=f'dirección: {ct["direccion_desarrollados"].replace("_", " ")}'),
         fila_split('Días con mensajes', d[0] / (d[0] + d[1]) if sum(d) else None, fa=str(d[0]), fb=str(d[1]))]
    sens = ct.get('sensibilidad_desarrollados', {})
    ss = ' · '.join(f'umbral {k}: {pct(v["A"])} / {pct(v["B"])}' for k, v in sens.items())
    return card('Participación', f'<div class="text-xs mb-2">{cx.leyenda()} <span class="mute"> — cada barra reparte 100 % entre ambos</span></div>{"".join(f)}'
                f'<div class="mt-2 text-xs mute">Sensibilidad de «desarrollados» (A / B): {E(ss)}</div>'
                f'<div class="mt-1 text-xs mute">{E(p["nota"])}</div>', extra=etiqueta_chip(p.get('suficiencia_de_datos')))


def s_evolucion(o, cx):
    ev = o.get('evolucion')
    if not ev or not ev['periodos']:
        return ''
    ps = ev['periodos']
    keys = [r['periodo'] for r in ps]
    marcas = ['pausa' if r.get('pausa') else 'parcial' if r.get('parcial') else None for r in ps]
    a = [(r['mensajes'] * r['mensajes_A']) if r.get('mensajes_A') is not None else None for r in ps]
    b = [(r['mensajes'] - x) if x is not None else None for r, x in zip(ps, a)]
    g = 'mes' if ev['granularidad'] == 'month' else 'semana'
    sh = lineas(keys, [('Mensajes', 'x', [r.get('mensajes_A') for r in ps]), ('Palabras', 'y', [r.get('palabras_A') for r in ps])], ymin=0, ymax=1, ref=.5, marcas=marcas, w=420, h=200)
    ini = lineas(keys, [('Abre el día', 'x', [r.get('inicia_dia_A') for r in ps]), ('Cierra la sesión', 'y', [r.get('cierra_A') for r in ps])], ymin=0, ymax=1, ref=.5, marcas=marcas, w=420, h=200)
    lat = lineas(keys, [(cx.n['A'], 'a', [r.get('latencia_A') for r in ps]), (cx.n['B'], 'b', [r.get('latencia_B') for r in ps])], ymin=0, fmt=lambda v: minutos(round(v)), marcas=marcas)
    cs = [(k, v) for k, v in ev['cambios_sostenidos'].items() if v.get('detectado')]
    gl = ev.get('sensibilidad_granularidad', {}).get('etiquetas', {})
    chips = ''.join(f'<li class="mb-1">{E(k.replace("_", " "))}: {E(v["direccion"])} desde {E(v["desde"])} {etiqueta_chip(gl.get(k))}</li>' for k, v in cs)
    solo = ''.join(f'<li class="mb-1">{E(k.replace("_", " "))}: solo se detecta con la otra granularidad {etiqueta_chip(v)}</li>'
                   for k, v in gl.items() if not ev['cambios_sostenidos'][k].get('detectado'))
    pausas = ''.join(f'<li class="mb-1">Chat parado: {E(z["desde"])} → {E(z["hasta"])} ({z["periodos"]} periodos). No es un cambio.</li>' for z in ev.get('pausas', []))
    ninguno = '' if (chips or solo or pausas) else '<div class="text-sm mute">Ninguno detectado.</div>'
    cuerpo = (f'<div class="text-xs mb-1">{cx.leyenda()} <span class="mute">· periodos de un {g}; tenue = parcial, sombreado = pausa larga</span></div>'
              f'<h3>Mensajes por periodo</h3>{barras_apiladas(keys, a, b, marcas)}'
              f'<div class="grid md:grid-cols-2 gap-x-6"><div><h3>Parte que escribe {cx.a()}: <span class="mute" style="font-weight:400">línea continua = mensajes · discontinua = palabras</span></h3>{sh}</div>'
              f'<div><h3>Parte de {cx.a()}: <span class="mute" style="font-weight:400">continua = días que abre · discontinua = sesiones que cierra</span></h3>{ini}</div></div>'
              f'<h3>Mediana de espera dentro de la sesión</h3>{lat}'
              f'<h3>Cambios sostenidos</h3><ul class="text-sm">{chips or ""}{solo}{pausas}</ul>'
              f'{ninguno}'
              f'<div class="mt-2 text-xs mute">Línea punteada = 50 %. Un cambio solo cuenta si es sostenido; los que dependen de la granularidad no se reportan como patrón.</div>')
    return card('Evolución en el tiempo', cuerpo, extra='')


def s_respuesta(o, cx):
    la = o['latencias']
    k = '6' if '6' in la else sorted(la)[0]
    per = la[k]['por_participante_que_interviene']
    bins = [('mismo minuto', 'mismo_minuto', 1), ('≤ 1 min', 'hasta_1_min', .85), ('≤ 5 min', 'hasta_5_min', .7), ('≤ 15 min', 'hasta_15_min', .55), ('≤ 60 min', 'hasta_60_min', .4)]
    filas = []
    for X, c in (('A', 'ca'), ('B', 'cb')):
        d = per[X]['distribucion']
        partes = [(e, d.get(kk, 0) or 0, op) for e, kk, op in bins]
        resto = max(0, 1 - sum(v for _, v, _ in partes))
        partes.append(('> 60 min', resto, .2))
        filas.append(f'<div class="py-2"><div class="text-sm mb-1"><span class="{c}">●</span> {E(corto(cx.n[X]))} <span class="mute text-xs">· mediana {minutos(per[X]["mediana_dentro"])} · p90 {minutos(per[X]["p90_dentro"])} · n={per[X]["n"]} {etiqueta_chip(per[X].get("suficiencia_de_datos"))}</span></div>{apilada_h(partes, "--a" if X == "A" else "--b")}</div>')
    ent = ' · '.join(f'{E(corto(cx.n[X]))}: {minutos(per[X].get("mediana_entre_sin_pausas_largas"))} (n={per[X].get("n_entre_sin_pausas_largas", 0)})' for X in ('A', 'B'))
    pl = la[k]['pausas_largas']
    pausas = f' · pausas largas (> {pl["umbral_dias"]} días): {pl["n"]}' + (f', máx. {pl["maxima_dias"]} d' if pl.get('maxima_dias') else '') if pl['n'] else ''
    sens = la
    sens_txt = ' · '.join(f'hueco {h} h: ' + ' / '.join(minutos(sens[h]['por_participante_que_interviene'][X].get('mediana_entre_sin_pausas_largas') if 'mediana_entre_sin_pausas_largas' in sens[h]['por_participante_que_interviene'][X] else None) for X in ('A', 'B')) for h in sorted(sens, key=int))
    return card('Tiempo de respuesta', f'<div class="text-xs mb-1 mute">Qué tan rápido escribe cada persona tras el turno de la otra (hueco de sesión {k} h).</div>{"".join(filas)}'
                f'<div class="text-sm mt-1"><span class="mute">Al volver tras un hueco largo (entre sesiones):</span> {ent}{E(pausas)}</div>'
                f'<details class="mt-1"><summary>Sensibilidad al hueco de sesión</summary><div class="text-xs mute mt-1">{E(sens_txt)} (A / B, mediana al volver)</div></details>')


def s_habitos(o, cx):
    h = o['habitos']
    pp = h['por_participante']
    ch = horas_chart(pp['A']['por_hora'], pp['B']['por_hora'])
    fr = ''
    for X, c in (('A', 'ca'), ('B', 'cb')):
        pf = pp[X]['proporcion_por_franja']
        fr += f'<div class="py-1.5"><div class="text-sm mb-1"><span class="{c}">●</span> {E(corto(cx.n[X]))}</div>' + apilada_h([(k, pf.get(k, 0), op) for k, op in (('madrugada', .3), ('manana', .55), ('tarde', .8), ('noche', 1))], '--a' if X == 'A' else '--b') + '</div>'
    ini = fila_split('Abre el día (primer mensaje del día lógico)', pp['A']['proporcion_inicia_el_dia'], pp['B']['proporcion_inicia_el_dia'],
                     fa=f"{pp['A']['inicia_el_dia']} días", fb=f"{pp['B']['inicia_el_dia']} días")
    cie = fila_split('Cierra el día (último mensaje)', pp['A']['proporcion_cierra_el_dia'], pp['B']['proporcion_cierra_el_dia'],
                     fa=f"{pp['A']['cierra_el_dia']} días", fb=f"{pp['B']['cierra_el_dia']} días")
    med = ' · '.join(f"{E(corto(cx.n[X]))}: {_hhmm(pp[X]['hora_mediana_al_iniciar_el_dia'])}" for X in ('A', 'B'))
    dias = ['lun', 'mar', 'mie', 'jue', 'vie', 'sab', 'dom']
    semana = ''.join(fila_par(dd, pp['A']['proporcion_por_dia'].get(dd), pp['B']['proporcion_por_dia'].get(dd)) for dd in dias)
    cuerpo = (f'<div class="text-xs mb-1">{cx.leyenda()}</div><h3>Mensajes por hora del día (hora del teléfono que exportó)</h3>{ch}'
              f'<h3>Franja del día</h3>{fr}<h3>Quién abre y quién cierra el día</h3>{ini}{cie}'
              f'<div class="text-sm mt-1"><span class="mute">Hora mediana al abrir el día:</span> {med}</div>'
              f'<details class="mt-2"><summary>Mensajes por día de la semana</summary><div class="mt-1">{semana}</div></details>'
              f'<div class="mt-2 text-xs mute">{E(h["nota"])}</div>')
    return card('Hábitos horarios', cuerpo)


def _hhmm(x):
    return '—' if x is None else f'{int(x):02d}:{round((x % 1) * 60):02d}'


def s_estilo(o, cx):
    s = o['estilo']['por_participante']
    A, B = s['A'], s['B']
    filas = ''.join(fila_par(n, A.get(k), B.get(k)) for n, k in (('Mensajes con pregunta', 'proporcion_preguntas'), ('Con emoji', 'proporcion_con_emoji'),
                    ('Con risa escrita', 'proporcion_con_risa'), ('Con mayúsculas sostenidas', 'proporcion_mayusculas'),
                    ('Solo acuse, risa o emoji', 'proporcion_solo_minimo'), ('Multimedia (de sus mensajes)', 'proporcion_media'), ('Eliminados', 'proporcion_eliminados')))
    ext = fila_par('Palabras por mensaje (mediana)', A['palabras_mediana'], B['palabras_mediana'], fmt=lambda v: num(v)) + fila_par('Palabras por mensaje (p90)', A['palabras_p90'], B['palabras_p90'], fmt=lambda v: num(v))
    return card('Estilo de escritura', f'<div class="text-xs mb-1">{cx.leyenda()} <span class="mute">· en cada fila la barra más larga es la mayor de las dos; el valor exacto va a la derecha</span></div>{filas}{ext}'
                f'<div class="mt-2 text-xs mute">{E(o["estilo"]["nota"])}</div>')


def s_ritmo(o, cx):
    r = o['ritmo']
    se, co, fr = r['sesiones'], r['continuidad'], r['fragmentacion']
    cierra = fila_split('Quién deja el último turno de una sesión sin respuesta', se['proporcion_cierra']['A'], se['proporcion_cierra']['B'],
                        fa=f'{se["cierra"]["A"]} sesiones', fb=f'{se["cierra"]["B"]} sesiones')
    frag = fila_par('Turnos de un solo mensaje', fr['A']['proporcion_turnos_de_un_mensaje'], fr['B']['proporcion_turnos_de_un_mensaje']) + \
        fila_par('Mensajes por ráfaga (media)', fr['A']['mensajes_por_rafaga_media'], fr['B']['mensajes_por_rafaga_media'], fmt=lambda v: num(v, 2))
    kpi = lambda t, v: f'<div class="rounded-xl p-3" style="background:var(--bg);border:1px solid var(--line)"><div class="text-xs mute">{E(t)}</div><div class="text-lg font-semibold">{v}</div></div>'  # noqa: E731
    k = (kpi('Sesiones', f'{se["n"]} {etiqueta_chip(se.get("suficiencia_de_datos"))}') + kpi('Duración mediana', minutos(se['duracion_minutos_mediana']))
         + kpi('Mensajes por sesión', num(se['mensajes_por_sesion_mediana'], 0)) + kpi('Días activos', f'{pct(co["proporcion_dias_activos"])} <span class="text-xs mute">({co["dias_activos"]} de {co["dias_del_rango"]})</span>')
         + kpi('Racha más larga', f'{co["racha_mas_larga_dias"]} días') + kpi('Pausa más larga', f'{co["pausa_mas_larga_dias"]} días')
         + kpi('Días en que escribe solo', f'<span class="ca">{co["dias_solo_uno"]["A"]}</span> · <span class="cb">{co["dias_solo_uno"]["B"]}</span>'))
    return card('Ritmo de la conversación', f'<div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">{k}</div><div class="text-xs mb-1">{cx.leyenda()}</div>{cierra}<h3>Fragmentación</h3>{frag}'
                f'<div class="mt-2 text-xs mute">{E(r["nota"])}</div>')


def s_saludos(o, cx):
    sg = o.get('saludos', {}).get('por_clase')
    if not sg:
        return ''
    filas = ''
    for k, nombre in (('manana', 'Buenos días'), ('noche', 'Buenas noches')):
        v = sg[k]
        m = v['mensajes']
        if not (m['A'] or m['B']):
            continue
        tot = m['A'] + m['B']
        filas += fila_split(nombre, m['A'] / tot, m['B'] / tot, fa=f"{m['A']} msj · primero {v['dias_lo_dice_primero']['A']} d", fb=f"{m['B']} msj · primero {v['dias_lo_dice_primero']['B']} d",
                            nota=f"el otro corresponde: {E(corto(cx.n['A'], 10))} {pct(v['el_otro_corresponde']['A'])} · {E(corto(cx.n['B'], 10))} {pct(v['el_otro_corresponde']['B'])}")
    return card('Saludos y despedidas', filas + f'<div class="mt-2 text-xs mute">{E(o["saludos"]["nota"])}</div>') if filas else ''


ORDEN_LEX = ['afecto_explicito', 'apodo_carinoso', 'cumplido', 'apoyo', 'disculpa', 'gratitud', 'propuesta_de_verse', 'conflicto', 'risa_texto']


def s_lexico(o, cx):
    lx = o.get('lexico')
    if not lx:
        return ''
    base = lx['base']
    bt = (base['A']['mensajes_texto'], base['B']['mensajes_texto'])
    ref = bt[0] / sum(bt) if sum(bt) else None
    cats = lx['por_categoria']
    orden = [c for c in ORDEN_LEX if c in cats] + sorted(c for c in cats if c not in ORDEN_LEX and not c.startswith('emoji'))
    emo = sorted(c for c in cats if c.startswith('emoji'))

    def filas(lista):
        out = []
        for c in lista:
            d = cats[c]
            e, w = d['estricta'], d['amplia']
            ea, eb = e['A']['mensajes_con_evento'], e['B']['mensajes_con_evento']
            wa, wb = w['A']['mensajes_con_evento'], w['B']['mensajes_con_evento']
            tot = ea + eb
            barra = split_bar(ea / tot, eb / tot, base=ref, fa=str(ea), fb=str(eb)) if tot else '<span class="mute text-xs">sin eventos estrictos</span>'
            amp = f'{wa} / {wb}' if (wa, wb) != (ea, eb) else '='
            neg = d.get('negadas', {})
            aparte = ' · '.join(f"{k} {neg_a}/{neg_b}" for k, neg_a, neg_b in (('negadas', d['negadas']['A']['mensajes_con_evento'], d['negadas']['B']['mensajes_con_evento']),
                                                                                   ('preguntas', d['preguntas']['A']['mensajes_con_evento'], d['preguntas']['B']['mensajes_con_evento'])) if neg_a or neg_b)
            out.append(f'<tr><td class="whitespace-nowrap"><div class="text-sm">{E(c.replace("_", " "))}</div><div class="mute" style="font-size:.7rem">{E(d["clase_provisional"].replace("_", " "))}</div></td>'
                       f'<td style="min-width:11rem">{barra}</td><td class="text-xs whitespace-nowrap">{e["A"]["por_100_mensajes"]:g} / {e["B"]["por_100_mensajes"]:g}</td>'
                       f'<td class="text-xs whitespace-nowrap">{amp}</td><td>{etiqueta_chip(d["robustez_indicadores"])}</td>'
                       f'<td class="text-xs mute">{E(aparte)}</td></tr>')
        return ''.join(out)

    head = '<thead><tr><th>Categoría</th><th>Mensajes con evento (estricta)</th><th>Por 100 msj</th><th>Amplia</th><th>Robustez</th><th>Aparte</th></tr></thead>'
    t1 = f'<div class="overflow-x-auto"><table class="t">{head}<tbody>{filas(orden)}</tbody></table></div>'
    t2 = f'<details class="mt-3"><summary>Emojis por categoría ({len(emo)})</summary><div class="overflow-x-auto mt-1"><table class="t">{head}<tbody>{filas(emo)}</tbody></table></div></details>' if emo else ''
    exp = ''
    for c, ex in lx.get('mensajes_por_expresion', {}).items():
        if c.startswith('emoji'):
            continue
        top = list(ex.items())[:8]
        exp += f'<div class="mb-1.5"><span class="text-sm">{E(c.replace("_", " "))}</span> ' + ' '.join(f'<span class="chip">{E(x)} <b class="ca">{v["A"]}</b>/<b class="cb">{v["B"]}</b></span>' for x, v in top) + '</div>'
    exp = f'<details class="mt-3"><summary>Expresiones más frecuentes (mensajes A/B)</summary><div class="mt-2">{exp}</div></details>' if exp else ''
    dis = lx.get('descartes_por_regla')
    ds = f'<details class="mt-2"><summary>Coincidencias descartadas por excepción</summary><div class="text-xs mute mt-1">{E(", ".join(f"{k} {v}" for k, v in dis.items()))}</div></details>' if dis else ''
    bs = f'{cx.a()}: {num(bt[0], 0)} mensajes de texto · {cx.b()}: {num(bt[1], 0)}'
    return card('Léxico: conteo bruto de coincidencias',
                f'<div class="text-xs mb-2">{cx.leyenda()} <span class="mute">· la marca vertical es el % de mensajes de texto de {cx.a()} ({pct(ref)}): si las barras coinciden con la marca, el reparto del evento es el esperado por participación. Base: {bs}.</span></div>'
                f'{t1}{t2}{exp}{ds}<div class="mt-2 text-xs mute">Estricta = reglas no ambiguas, forma afirmativa; amplia = además las ambiguas. «Por 100 msj» = A / B. Un evento es un dato sobre el texto, no sobre la persona ni la relación. {E(lx.get("nota", ""))}</div>')


def s_lexico_serie(o, cx):
    ls = o.get('lexico_serie')
    if not ls or not ls['por_categoria']:
        return ''
    keys = ls['periodos']
    cards = ''
    orden = [c for c in ORDEN_LEX if c in ls['por_categoria']] + sorted(c for c in ls['por_categoria'] if c not in ORDEN_LEX and not c.startswith('emoji'))
    for c in orden:
        d = ls['por_categoria'][c]
        if d['periodos_validos'] < 3:
            continue
        rows = d['periodos']
        a = [r.get('estricta_por_100_A') if (r['estricta_A'] + r['estricta_B']) >= ls['min_eventos_periodo'] else None for r in rows]
        b = [r.get('estricta_por_100_B') if (r['estricta_A'] + r['estricta_B']) >= ls['min_eventos_periodo'] else None for r in rows]
        dom = d['dominante']
        domt = dom if dom in ('mixto', 'insuficiente', None) else cx.n[dom]
        sg = d['sensibilidad_granularidad']
        cards += (f'<div class="rounded-xl p-3" style="border:1px solid var(--line)"><div class="flex justify-between items-center gap-2 flex-wrap"><span class="text-sm font-medium">{E(c.replace("_", " "))}</span>'
                  f'{etiqueta_chip(sg["etiqueta"])}</div>'
                  f'{lineas(keys, [(cx.n["A"], "a", a), (cx.n["B"], "b", b)], ymin=0, fmt=lambda v: num(v), small=True, w=360, h=120)}'
                  f'<div class="text-xs mute">lidera: {E(corto(cx.n["A"], 14))} {d["lidera"]["A"]} · {E(corto(cx.n["B"], 14))} {d["lidera"]["B"]} de {d["periodos_validos"]} periodos → <b>{E(corto(domt, 20))}</b></div></div>')
    ocultas = [c for c in ls['por_categoria'] if ls['por_categoria'][c]['periodos_validos'] < 3 and not c.startswith('emoji')]
    if not cards:
        return card('Léxico por periodo', f'<div class="text-sm mute">Ninguna categoría tiene al menos 3 periodos con ≥ {ls["min_eventos_periodo"]} eventos.</div>')
    oc = f'<div class="mt-2 text-xs mute">Sin gráfica (menos de 3 periodos válidos): {E(", ".join(c.replace("_", " ") for c in ocultas))}.</div>' if ocultas else ''
    return card('Léxico por periodo', f'<div class="text-xs mb-2">{cx.leyenda()} <span class="mute">· mensajes con evento (estricta) por 100 mensajes de texto, por {"mes" if ls["granularidad"] == "month" else "semana"}; '
                f'se omiten los periodos con menos de {ls["min_eventos_periodo"]} eventos entre ambos.</span></div><div class="grid md:grid-cols-2 xl:grid-cols-3 gap-3">{cards}</div>{oc}'
                f'<div class="mt-2 text-xs mute">«Lidera» cuenta los periodos válidos en que alguien supera al otro por ≥ 25 %. Líder dominante: ≥ 75 % de los periodos válidos. Una etiqueta «sensible a granularidad» no se toma como patrón. {E(ls["nota"])}</div>')


def s_correspondencia(o, cx):
    c = o.get('correspondencia')
    if not c:
        return ''
    filas = ''
    for key, nombre, f in (('R1_extension', 'R1 · extensión: ¿una respuesta larga sigue a un mensaje largo?', 'rho'),
                           ('R2_preguntas', 'R2 · preguntas: ¿se responde con contenido tras una pregunta?', 'diferencia'),
                           ('R3_desarrollados', 'R3 · desarrollados: ¿se corresponde un turno desarrollado?', 'diferencia_no_minimo')):
        r = c[key]
        celdas = ''
        for d, quien in (('A_a_B', 'A'), ('B_a_A', 'B')):
            v = r[d]
            cl = 'ca' if quien == 'A' else 'cb'
            celdas += (f'<div class="rounded-lg p-2 text-sm" style="background:var(--bg);border:1px solid var(--line)"><span class="{cl}">●</span> {E(corto(cx.n["A" if d == "A_a_B" else "B"], 14))} → {E(corto(cx.n["B" if d == "A_a_B" else "A"], 14))}'
                       f'<div class="text-lg font-semibold">{num(v[f], 3)}</div><div class="text-xs mute">{E((v.get("nivel") or "-").replace("_", " "))} · n={v["n"]}</div></div>')
        filas += f'<div class="py-2"><div class="flex justify-between gap-2 flex-wrap items-center"><span class="text-sm">{E(nombre)}</span>{etiqueta_chip(r["etiqueta"])}</div><div class="grid grid-cols-2 gap-2 mt-1">{celdas}</div></div>'
    r4 = c['R4_iniciativa']
    rean = ''.join(fila_split(f'Reanuda la conversación (hueco {h} h)', v['A'] / (v['A'] + v['B']) if (v['A'] + v['B']) else None, fa=str(v['A']), fb=str(v['B'])) for h, v in r4['reanudaciones'].items())
    ini = fila_split('Abre el día', r4['inicia_dia']['A'] / (r4['inicia_dia']['A'] + r4['inicia_dia']['B']) if sum(r4['inicia_dia'].values()) else None, fa=str(r4['inicia_dia']['A']), fb=str(r4['inicia_dia']['B']))
    return card('Correspondencia formal', f'<div class="text-xs mb-1 mute">{c["pares_misma_sesion"]:,} pares de turnos en la misma sesión. «X → Y» = lo que Y da después de X (ρ de Spearman o diferencia de tasas).</div>{filas}'
                f'<h3>R4 · iniciativa {etiqueta_chip(r4["robustez_reanudaciones"])}</h3><div class="text-xs mb-1">{cx.leyenda()}</div>{ini}{rean}'
                f'<div class="mt-2 text-xs mute">{E(c["nota"])}</div>', extra='')


def seccion_chat(i, d):
    o = d['out']
    cx = Ctx(o)
    quien = f'{E(cx.n["A"])} <span class="mute">×</span> {E(cx.n["B"])}' if o.get('nombres') else 'A × B'
    if not o.get('analisis_habilitado'):
        return (f'<div id="c{i}" class="space-y-5"><div class="card"><h2>Chat {i}</h2><div class="text-sm">No se analizó: {E(str(o.get("importacion")))} — '
                f'{E(", ".join(o.get("requisitos_pendientes") or ["importación no aceptada"]))}</div></div></div>')
    pa = o['participantes']['por_participante']
    desde = min(v['primer_mensaje_fecha'] for v in pa.values())[:10]
    hasta = max(v['ultimo_mensaje_fecha'] for v in pa.values())[:10]
    tot = sum(v['mensajes'] for v in o['participacion']['por_participante'].values())
    head = (f'<div class="card"><div class="flex flex-wrap items-baseline justify-between gap-2"><h2 style="font-size:1.35rem">Chat {i}: {quien}</h2>'
            f'<div class="flex gap-1.5 flex-wrap">{chip(o["importacion"], "ok" if o["importacion"] == "accepted" else "warn")}{chip("calidad: " + o["estado_calidad"].replace("_", " "), "ok" if o["estado_calidad"].startswith("sin") else "warn")}</div></div>'
            f'<div class="text-sm mute mt-1">{E(desde)} → {E(hasta)} · {tot:,} mensajes · {d["kb"]} KB</div></div>')
    partes = [s_participacion(o, cx), s_evolucion(o, cx), s_respuesta(o, cx), s_habitos(o, cx), s_estilo(o, cx), s_ritmo(o, cx), s_saludos(o, cx),
              s_lexico(o, cx), s_lexico_serie(o, cx), s_correspondencia(o, cx)]
    ids = ['participacion', 'evolucion', 'respuesta', 'habitos', 'estilo', 'ritmo', 'saludos', 'lexico', 'lexico-serie', 'correspondencia']
    cuerpo = ''
    for pid, p in zip(ids, partes):
        if p:
            cuerpo += p.replace('<section class="card"', f'<section id="c{i}-{pid}" class="card"', 1)
    return f'<div id="c{i}" class="space-y-5 mb-14">{head}{cuerpo}</div>'


SECCIONES = [('participacion', 'Participación'), ('evolucion', 'Evolución'), ('respuesta', 'Tiempo de respuesta'), ('habitos', 'Hábitos horarios'), ('estilo', 'Estilo'),
             ('ritmo', 'Ritmo'), ('saludos', 'Saludos'), ('lexico', 'Léxico'), ('lexico-serie', 'Léxico por periodo'), ('correspondencia', 'Correspondencia')]


def resumen_general(archivos):
    filas = ''
    for i, d in archivos.items():
        o = d['out']
        if not o.get('analisis_habilitado'):
            filas += f'<tr><td>{i}</td><td colspan="6" class="mute">No analizado: {E(str(o.get("importacion")))}</td></tr>'
            continue
        cx = Ctx(o)
        pp = o['participacion']['por_participante']
        tot = sum(v['mensajes'] for v in pp.values())
        pr = o['participacion']['proporciones']['mensajes']['A']
        pa = o['participantes']['por_participante']
        desde, hasta = min(v['primer_mensaje_fecha'] for v in pa.values())[:7], max(v['ultimo_mensaje_fecha'] for v in pa.values())[:7]
        ra = o['ritmo']['continuidad']['proporcion_dias_activos']
        filas += (f'<tr><td><a href="#c{i}" class="font-medium">Chat {i}</a></td><td class="text-sm">{E(corto(cx.n["A"], 18))} <span class="mute">×</span> {E(corto(cx.n["B"], 18))}</td>'
                  f'<td class="text-xs whitespace-nowrap">{E(desde)} → {E(hasta)}</td><td class="text-right">{tot:,}</td><td style="min-width:9rem">{split_bar(pr, fa=pct(pr), fb=pct(1 - pr))}</td>'
                  f'<td class="text-right">{pct(ra)}</td><td>{etiqueta_chip(o["participacion"].get("suficiencia_de_datos"))}</td></tr>')
    return card('Resumen de los chats', f'<div class="overflow-x-auto"><table class="t"><thead><tr><th></th><th>Participantes</th><th>Periodo</th><th class="text-right">Mensajes</th><th>% de mensajes (primer nombre | segundo)</th><th class="text-right">Días activos</th><th>Datos</th></tr></thead><tbody>{filas}</tbody></table></div>'
                f'<div class="mt-2 text-xs mute">Primer nombre = quien aparece primero en el archivo exportado. No indica quién exportó ni quién inició la relación.</div>', id_='resumen')


def como_leer():
    return card('Cómo leer este informe', '''<ul class="text-sm space-y-1.5 list-disc pl-5">
<li><span class="ca">Azul</span> es la primera persona del chat y <span class="cb">naranja</span> la segunda (el orden es solo el de aparición en el archivo exportado).</li>
<li>Todo son <b>conteos y proporciones observables</b>. Nada de esto afirma interés, cercanía, afecto ni intención: son datos para revisar con tu propio criterio.</li>
<li><b>Estricta / amplia</b>: la estricta usa solo reglas no ambiguas; la amplia suma las ambiguas (p. ej. «perdón», «nos vemos mañana»). Si cambian mucho, la categoría es <i>sensible a indicadores</i>.</li>
<li><b>Robusto / sensible a granularidad</b>: se repite el cálculo por mes y por semana; si el resultado no coincide, no se toma como patrón.</li>
<li><b>Datos insuficientes</b>: con pocos eventos o periodos, la cifra se muestra pero no se interpreta.</li>
<li>Pasa el cursor sobre barras y puntos para ver el valor exacto.</li></ul>''', id_='leer')


def render(foto):
    meta = foto['meta']
    archivos = foto['archivos']
    ids = sorted(archivos, key=int)
    cuerpos = {i: seccion_chat(i, archivos[i]) for i in ids}
    cuerpo = ''.join(cuerpos.values())
    nav = ''.join(f'<a href="#c{i}">Chat {i}</a>' + ''.join(f'<a href="#c{i}-{k}" style="padding-left:1.4rem;font-size:.78rem">{E(t)}</a>'
                  for k, t in SECCIONES if f'id="c{i}-{k}"' in cuerpos[i]) for i in ids)
    titulo = f'Informe «{meta.get("etiqueta", "")}» · {meta.get("fecha", "")}'
    priv = any(archivos[i]['out'].get('nombres') for i in ids)
    aviso = ('<div class="card" style="border-color:var(--warn)"><span class="text-sm">Este informe contiene nombres de personas. Es un archivo privado: no lo subas ni lo compartas.</span></div>' if priv else '')
    return f'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(titulo)}</title><meta name="color-scheme" content="light dark">
<script src="{TAILWIND}"></script>
<style>{CSS}</style></head><body>
<header class="sticky top-0 z-10" style="background:var(--card);border-bottom:1px solid var(--line)"><div class="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-between gap-3 flex-wrap">
<div><b>{E(titulo)}</b></div><div class="text-xs mute">código {E(str(meta.get("commit", "")))} · léxico {E(str(meta.get("huella_lexico", "")))} · config {E(str(meta.get("huella_config", "")))}</div></div></header>
<div class="max-w-7xl mx-auto px-4 py-6 lg:grid lg:grid-cols-[13rem_1fr] lg:gap-8">
<aside class="hidden lg:block"><nav class="sticky top-16 max-h-[calc(100vh-5rem)] overflow-y-auto"><a href="#resumen">Resumen</a><a href="#leer">Cómo leer</a>{nav}</nav></aside>
<main class="space-y-5 min-w-0">{aviso}{resumen_general(archivos)}{como_leer()}{cuerpo}
<footer class="text-xs mute pb-10">Observaciones descriptivas: no interpretan interés, cercanía ni reciprocidad. Generado localmente; ningún dato sale de tu computadora.</footer></main></div></body></html>'''


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('informe_json')
    ap.add_argument('--salida', help='archivo .html de salida (por defecto junto al .json)')
    a = ap.parse_args(argv)
    src = os.path.realpath(a.informe_json)
    dest = os.path.realpath(a.salida or os.path.splitext(src)[0] + '.html')
    if is_inside(src, os.path.realpath(ROOT)) or is_inside(dest, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se lee ni se escribe dentro del repositorio.')
    with open(src, encoding='utf-8') as f:
        foto = json.load(f)
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(render(foto))
    print('Informe visual:', dest)


if __name__ == '__main__':
    main()

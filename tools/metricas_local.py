#!/usr/bin/env python3
"""Participación y latencias de UNA exportación propia, en local, imprimiendo solo números (sin contenido).

Uso:  python tools/metricas_local.py RUTA --confirmo-individual [--date-order-hint dmy|mdy]
                                     [--aceptar-alias-sospechosos | --unir C=B] [--aceptar-perdidas L1,L2]
                                     [--yo A|B] [--resumen]

--yo A|B   indica cuál etiqueta eres tú (ver `participantes`: línea del primer mensaje de cada uno). A es quien
           escribe PRIMERO en el archivo, no quien exporta.
--resumen  texto corto y legible (hueco de sesión de config) en lugar del JSON completo.

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

from metrics.correspondence import correspondence  # noqa: E402
from metrics.greetings import greetings  # noqa: E402
from metrics.habits import habits  # noqa: E402
from metrics.latency import latency_sensitivity  # noqa: E402
from metrics.lexical import lexical_counts  # noqa: E402
from metrics.participants import participant_guide, role_name  # noqa: E402
from metrics.participation import participation  # noqa: E402
from metrics.rhythm import rhythm  # noqa: E402
from metrics.style import style  # noqa: E402
from metrics.trends import trends  # noqa: E402
from metrics.turn_content import turn_content  # noqa: E402
from parsers import parse_file  # noqa: E402
from validar_exportacion_local import is_inside  # noqa: E402


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):          # Windows/cp1252 al redirigir: no fallar por ρ o →
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ruta')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--date-order-hint', choices=['dmy', 'mdy'])
    ap.add_argument('--aceptar-alias-sospechosos', action='store_true')
    ap.add_argument('--unir', action='append', default=[], metavar='C=B')
    ap.add_argument('--aceptar-perdidas', default='', metavar='L1,L2')
    ap.add_argument('--yo', choices=['A', 'B'])
    ap.add_argument('--lexico-local', metavar='RUTA', help='léxico local (por defecto lexicon_local.yaml junto a la exportación, si existe)')
    ap.add_argument('--resumen', action='store_true')
    ap.add_argument('--semanal', action='store_true', help='evolución por semana ISO en lugar de mes')
    a = ap.parse_args(argv)

    merge = dict(x.split('=', 1) for x in a.unir) if a.unir else None
    out = analizar(a.ruta, confirmo=a.confirmo_individual, date_order_hint=a.date_order_hint, merge=merge,
                   aceptar_alias=a.aceptar_alias_sospechosos,
                   perdidas=[int(x) for x in a.aceptar_perdidas.split(',')] if a.aceptar_perdidas else None, yo=a.yo,
                   granularity='week' if a.semanal else None, lexico_local=a.lexico_local)
    print(resumen(out) if a.resumen else json.dumps(out, ensure_ascii=False, indent=2))


def analizar(ruta, confirmo=False, date_order_hint=None, merge=None, aceptar_alias=False, perdidas=None, yo=None,
             granularity=None, lexico_local=None):
    """Todas las métricas de UNA exportación (solo números). Reutilizado por comparar_local."""
    real = os.path.realpath(ruta)
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    res = parse_file(real, date_order_hint=date_order_hint, merge_authors=merge, accept_suspected_aliases=aceptar_alias)
    if res.accepted and confirmo:
        res = res.confirm_individual()
    if res.accepted and perdidas:
        res = res.accept_losses(perdidas)
    out = {'importacion': res.report['decision_importacion'], 'estado_calidad': res.report['estado_calidad'],
           'analisis_habilitado': res.analysis_enabled, 'requisitos_pendientes': res.pending_requirements}
    if res.analysis_enabled:
        out['participantes'] = participant_guide(res.messages, yo=yo)
        out['participacion'] = participation(res.messages)
        out['contenido_turnos'] = turn_content(res.messages)
        out['latencias'] = latency_sensitivity(res.messages)
        out['habitos'] = habits(res.messages)
        out['estilo'] = style(res.messages)
        out['ritmo'] = rhythm(res.messages)
        out['saludos'] = greetings(res.messages)
        out['correspondencia'] = correspondence(res.messages)
        local = lexico_local or os.path.join(os.path.dirname(real), 'lexicon_local.yaml')
        out['lexico'] = lexical_counts(res.messages, local_path=local)
        out['evolucion'] = trends(res.messages, granularity=granularity)
    return out


def _fmt(x, pct=False):
    if x is None:
        return '—'
    return f'{x * 100:.0f}%' if pct else (f'{x:g}' if isinstance(x, (int, float)) else str(x))


def _hhmm(h):
    return '—' if h is None else f'{int(h):02d}:{round((h % 1) * 60):02d}'


def _abs(key, d):
    """Tasas absolutas de respuesta no mínima: una diferencia ~0 puede ser techo (siempre responde con contenido)."""
    if key == 'R2_preguntas':
        return f" {{con preg. {_fmt(d['con_pregunta'], True)} / sin {_fmt(d['sin_pregunta'], True)}}}"
    if key == 'R3_desarrollados':
        nm = lambda x: None if not x or x['minimo'] is None else 1 - x['minimo']   # noqa: E731
        return f" {{tras desarr. {_fmt(nm(d['tras_desarrollado']), True)} / tras breve {_fmt(nm(d['tras_breve']), True)}}}"
    return ''


def _evolucion(ev, lab):
    a, b = list(lab)
    p = ev['parametros']
    out = [f"== Evolución por {'mes' if ev['granularidad'] == 'month' else 'semana'} (% de {lab[a]}; — = menos de "
           f"{p['min_ev']} eventos) ==",
           f"  {'periodo':<9} {'msj':>6} {'msj A':>6} {'palab.A':>7} {'desar.A':>7} {'abre A':>6} {'cierra A':>8} {'media A':>7} {'media B':>7} {'días':>5} "
           f"{'lat A':>6} {'lat B':>6} {'≤5m A':>6} {'≤5m B':>6}"]
    for r in ev['periodos']:
        out.append(f"  {r['periodo']:<9} {r['mensajes']:>6} {_fmt(r['mensajes_A'], True):>6} {_fmt(r['palabras_A'], True):>7} "
                   f"{_fmt(r['desarrollados_A'], True):>7} {_fmt(r['inicia_dia_A'], True):>6} {_fmt(r['cierra_A'], True):>8} "
                   f"{_fmt(r['multimedia_A'], True):>7} {_fmt(r['multimedia_B'], True):>7} "
                   f"{_fmt(r['dias_activos'], True):>5} "
                   f"{_fmt(r['latencia_' + a]):>6} {_fmt(r['latencia_' + b]):>6} {_fmt(r['rapida_' + a], True):>6} {_fmt(r['rapida_' + b], True):>6}"
                   + ('  parcial' if r['parcial'] else '') + ('  pausa' if r['pausa'] else ''))
    gl = ev.get('sensibilidad_granularidad', {}).get('etiquetas', {})
    det = [f"{k} {v['direccion']} desde {v['desde']} (base {v['base']})" + (f" [{gl[k]}]" if gl.get(k) else '')
           for k, v in ev['cambios_sostenidos'].items() if v.get('detectado')]
    for k, lab_ in gl.items():          # detectado solo en la otra granularidad
        if not ev['cambios_sostenidos'][k].get('detectado'):
            det.append(f"{k}: solo en {ev['sensibilidad_granularidad']['otra_granularidad']} [{lab_}]")
    out.append(f"  cambios sostenidos ({p['n_seq']} periodos; proporciones ±{p['abs']}, latencias ±{p['ratio'] * 100:.0f}% y ≥{p['lat_min']} min): "
               + ('; '.join(det) if det else 'ninguno'))
    for z in ev.get('pausas', []):
        out.append(f"  pausa larga (chat parado, no es un cambio): {z['desde']} a {z['hasta']} ({z['periodos']} periodos)")
    out.append('  lat = mediana de minutos dentro de la sesión; ≤5m = % de respuestas en ≤5 min dentro de la sesión; '
               'días = días con mensajes / días del periodo; parcial = primer/último periodo incompleto; '
               'pausa = periodo sin mensajes dentro de una pausa larga; ni uno ni otro cuentan para cambios')
    return out


def resumen(out, gap=None):
    """Texto legible, solo números. Usa el hueco de config (o el central de la sensibilidad)."""
    lines = [f"Importación: {out['importacion']} | calidad: {out['estado_calidad']} | "
             f"análisis: {'sí' if out['analisis_habilitado'] else 'NO'}"]
    if not out['analisis_habilitado']:
        return '\n'.join(lines + ['Pendiente: ' + ', '.join(out['requisitos_pendientes'] or ['importación no aceptada'])])
    g = out['participantes']
    lab = {k: role_name(k, g) for k in g['por_participante']}
    lines += ['', '== Quién es quién ==', g['regla']]
    for k, v in g['por_participante'].items():
        lines.append(f"  {lab[k]}: primer mensaje línea {v['primer_mensaje_linea']} ({v['primer_mensaje_fecha']}), "
                     f"último línea {v['ultimo_mensaje_linea']}")
    if 'roles' not in g:
        lines.append('  (usa --yo A o --yo B para marcar cuál eres tú)')

    p = out['participacion']
    lines += ['', '== Participación ==']
    for k, v in p['por_participante'].items():
        pr = p['proporciones']
        lines.append(f"  {lab[k]}: {v['mensajes']} mensajes ({_fmt(pr['mensajes'][k], True)}), {v['turnos']} turnos "
                     f"({_fmt(pr['turnos'][k], True)}), {v['palabras']} palabras ({_fmt(pr['palabras'][k], True)}), "
                     f"{v['dias_con_mensajes']} días")

    tc = out['contenido_turnos']
    pe = tc['proporciones_entre_participantes']
    lines += ['', f"== Contenido de turnos (los turnos alternan: ~50/50 por definición; desarrollado >= "
                  f"{tc['umbral_desarrollado_palabras']} palabras sustantivas) =="]
    for k, v in tc['por_participante'].items():
        lines.append(f"  {lab[k]}: mínimos {_fmt(v['proporcion_minimo'], True)}, breves {_fmt(v['proporcion_breve'], True)}, "
                     f"desarrollados {_fmt(v['proporcion_desarrollado'], True)} de sus turnos | "
                     f"{_fmt(v['palabras_sustantivas_por_turno_mediana'])} palabras sustantivas/turno "
                     f"(p90 {_fmt(v['palabras_sustantivas_por_turno_p90'])}), {_fmt(v['mensajes_por_turno_mediana'])} mensajes/turno")
    lines.append('  reparto entre ambos: ' + '; '.join(
        f"{u.replace('_', ' ')} " + ' / '.join(f'{lab[k]} {_fmt(pe[u][k], True)}' for k in lab)
        for u in ('turnos', 'turnos_no_minimos', 'turnos_desarrollados', 'palabras_sustantivas')))
    lines.append('  desarrollados con umbral ' + '; '.join(
        f'{th}: ' + ' / '.join(f'{lab[k]} {_fmt(v[k], True)}' for k in lab)
        for th, v in tc['sensibilidad_desarrollados'].items()) + f" -> dirección {tc['direccion_desarrollados']}")

    lat = out['latencias']
    gaps = sorted(lat, key=float)
    key = str(gap) if gap is not None and str(gap) in lat else gaps[len(gaps) // 2]
    L = lat[key]
    lines += ['', f"== Latencia (hueco de sesión {L['hueco_horas']} h; minutos; resolución {L['resolucion']}) =="]
    for k, v in L['por_participante_que_interviene'].items():
        d = v['distribucion']
        lines.append(f"  {lab[k]} tarda: mediana {_fmt(v['mediana_general'])}, p75 {_fmt(v.get('p75_general'))}, "
                     f"p90 {_fmt(v.get('p90_general'))} | mismo minuto {_fmt(d.get('mismo_minuto'), True)}, "
                     f"<=5 min {_fmt(d.get('hasta_5_min'), True)}, <=60 min {_fmt(d.get('hasta_60_min'), True)} "
                     f"(n={v['n']}, {v['suficiencia_de_datos']})")
        ms, ns = v['mediana_entre_sin_pausas_largas'], v['n_entre_sin_pausas_largas']
        lines.append(f"      al volver tras > {L['hueco_horas']} h (sin pausas largas): mediana {_fmt(ms)} min "
                     f"(n={ns}, {'suficiente' if ns >= 20 else 'insuficiente'})")
    pl = L['pausas_largas']
    if pl['n']:
        lines.append(f"  pausas largas (> {pl['umbral_dias']} días, chat parado): {pl['n']}, máxima {pl['maxima_dias']} días; "
                     'retoma: ' + ', '.join(f'{lab[k]} {v}' for k, v in pl['por_participante_que_retoma'].items()))
    lines.append('  sensibilidad (mediana al volver, sin pausas largas, por hueco): ' + '; '.join(
        f"{h} h: " + ', '.join(f"{k} {_fmt(lat[h]['por_participante_que_interviene'][k]['mediana_entre_sin_pausas_largas'])}"
                               for k in lab) for h in gaps))

    lines += ['', ('== Hábitos (día lógico desde las {}:00; hora local del teléfono que exportó) ==').format(out['habitos']['inicio_del_dia_hora'])]
    for k, v in out['habitos']['por_participante'].items():
        fr = ', '.join(f'{n} {_fmt(x, True)}' for n, x in v['proporcion_por_franja'].items())
        lines.append(f"  {lab[k]}: inicia el día {_fmt(v['proporcion_inicia_el_dia'], True)}, lo cierra "
                     f"{_fmt(v['proporcion_cierra_el_dia'], True)}, hora mediana al iniciarlo "
                     f"{_hhmm(v['hora_mediana_al_iniciar_el_dia'])} | {fr}")

    lines += ['', '== Estilo (mensajes de texto) ==']
    for k, v in out['estilo']['por_participante'].items():
        lines.append(f"  {lab[k]}: {_fmt(v['palabras_mediana'])} palabras/mensaje (p90 {_fmt(v['palabras_p90'])}), "
                     f"preguntas {_fmt(v['proporcion_preguntas'], True)}, emoji {_fmt(v['proporcion_con_emoji'], True)}, "
                     f"risa {_fmt(v['proporcion_con_risa'], True)}, mayúsculas {_fmt(v['proporcion_mayusculas'], True)}, "
                     f"solo acuse/risa/emoji {_fmt(v['proporcion_solo_minimo'], True)}, multimedia {_fmt(v['proporcion_media'], True)}")
    rt = out['ritmo']
    se, co = rt['sesiones'], rt['continuidad']
    lines += ['', f"== Ritmo (hueco de sesión {rt['hueco_horas']} h) ==",
              f"  sesiones: {se['n']} ({se['suficiencia_de_datos']}); duración mediana {_fmt(se['duracion_minutos_mediana'])} min "
              f"(p90 {_fmt(se['duracion_minutos_p90'])}), {_fmt(se['turnos_por_sesion_mediana'])} turnos y "
              f"{_fmt(se['mensajes_por_sesion_mediana'])} mensajes por sesión",
              '  deja el último turno sin respuesta (cierra): ' + ' / '.join(
                  f"{lab[k]} {v} ({_fmt(se['proporcion_cierra'][k], True)})" for k, v in se['cierra'].items()),
              f"  días: {co['dias_activos']} de {co['dias_del_rango']} ({_fmt(co['proporcion_dias_activos'], True)}); racha más "
              f"larga {co['racha_mas_larga_dias']} días; racha al final {co['racha_al_final_dias']}; pausa más larga "
              f"{co['pausa_mas_larga_dias']} días",
              f"  días en que escribe solo uno: " + ' / '.join(f"{lab[k]} {v}" for k, v in co['dias_solo_uno'].items())
              + f" (ambos: {co['dias_ambos']})"]
    for k, v in rt['fragmentacion'].items():
        lines.append(f"  {lab[k]}: {_fmt(v['mensajes_por_turno_mediana'])} mensajes/turno (p90 {_fmt(v['mensajes_por_turno_p90'])}), "
                     f"turnos de un solo mensaje {_fmt(v['proporcion_turnos_de_un_mensaje'], True)}, "
                     f"{_fmt(v['mensajes_por_rafaga_media'])} mensajes/ráfaga")

    sg = out['saludos']['por_clase']
    lines += ['', '== Saludos y despedidas (línea base; no son indicadores de interés) ==']
    for k, name in (('manana', 'buenos días'), ('noche', 'buenas noches')):
        v = sg[k]
        lines.append(f"  {name}: mensajes " + ' / '.join(f"{lab[x]} {n}" for x, n in v['mensajes'].items())
                     + '; días en que lo dice primero ' + ' / '.join(f"{lab[x]} {n}" for x, n in v['dias_lo_dice_primero'].items())
                     + '; el otro corresponde ese día ' + ' / '.join(
                         f"a {lab[x]} {_fmt(n, True)}" for x, n in v['el_otro_corresponde'].items()))

    lx = out['lexico']
    lines += ['', f"== Léxico: conteo bruto de coincidencias ({lx['reglas']['n']} reglas, {lx['reglas']['n_locales']} locales; "
                  'estricta = reglas no ambiguas, forma afirmativa; amplia = + ambiguas) ==']
    for k, v in lx['base'].items():
        lines.append(f"  base {lab[k]}: {v['mensajes_texto']} mensajes de texto, {v['turnos']} turnos, {v['dias_activos']} días activos (día lógico)")
    for cat, d in lx['por_categoria'].items():
        lines.append(f"  {cat} [{d['clase_provisional']}] (robustez ante indicadores: {d['robustez_indicadores']}; "
                     f"más días con evento: estricta {d['mas_dias_con_evento']['estricta']}, amplia {d['mas_dias_con_evento']['amplia']})")
        for var in ('estricta', 'amplia'):
            lines.append(f'      {var}: ' + ' | '.join(
                f"{lab[k]} {b['mensajes_con_evento']} msj ({b['ocurrencias']} ocurr.), {b['turnos_con_evento']} turnos, "
                f"{b['dias_con_evento']} días, {_fmt(b['por_100_mensajes'])}/100 msj" for k, b in d[var].items()))
        aparte = [f"{var}: " + '/'.join(f"{lab[k]} {b['mensajes_con_evento']}" for k, b in d[var].items())
                  for var in ('negadas', 'preguntas') if any(b['mensajes_con_evento'] for b in d[var].values())]
        if aparte:
            lines.append('      aparte (no cuentan): ' + '; '.join(aparte))
    lines.append('  mensajes por regla (qué regla produce cada conteo): ' + '; '.join(
        f"{r} " + '/'.join(f'{lab[k]} {n}' for k, n in v.items()) for r, v in lx['mensajes_por_regla'].items()))
    lines.append('  expresiones más frecuentes por categoría (mensajes; las reglas locales aparecen como "(local)"):')
    for cat, ex in lx['mensajes_por_expresion'].items():
        lines.append(f'      {cat}: ' + '; '.join(f"{x} " + '/'.join(f'{lab[k]} {n}' for k, n in v.items())
                                                  for x, v in list(ex.items())[:int(os.environ.get('LEXICO_TOP', 10))]))
    if lx['descartes_por_regla']:
        lines.append('  coincidencias descartadas por excepción: ' + ', '.join(f'{r} {n}' for r, n in lx['descartes_por_regla'].items()))
    lines.append('  ' + lx['nota'])

    c = out['correspondencia']
    lines += ['', f"== Correspondencia formal (pares en la misma sesión, hueco {c['hueco_horas']} h: "
                  f"{c['pares_misma_sesion']}; X_a_Y = lo que Y da a X) =="]
    for key, name, f in (('R1_extension', 'R1 extensión (rho)', 'rho'), ('R2_preguntas', 'R2 preguntas (dif.)', 'diferencia'),
                         ('R3_desarrollados', 'R3 desarrollados (dif. no mín.)', 'diferencia_no_minimo')):
        r = c[key]
        dirs = [k for k in r if '_a_' in k]
        nst = {'R2_preguntas': ('n_con_pregunta', 'preguntas'), 'R3_desarrollados': ('n_tras_desarrollado', 'desarr.')}.get(key)
        lines.append(f"  {name}: " + '; '.join(
            f"{d} {_fmt(r[d][f])} [{r[d]['nivel'] or '-'}] (pares={r[d]['n']}"
            + (f", {nst[1]}={r[d][nst[0]]}" if nst else '') + ')' + _abs(key, r[d]) for d in dirs) + f" -> {r['etiqueta']}")
    r4 = c['R4_iniciativa']
    lines.append('  R4 iniciativa: reanudaciones ' + '; '.join(f"{g} h " + '/'.join(f'{k} {v}' for k, v in d.items())
                 for g, d in r4['reanudaciones'].items()) + f" ({r4['robustez_reanudaciones']}); inicia día "
                 + '/'.join(f'{k} {v}' for k, v in r4['inicia_dia'].items()))
    lines.append('  ' + c['nota'])
    lines += ['', *_evolucion(out['evolucion'], lab)]
    lines += ['', 'Observaciones descriptivas: no interpretan interés, cercanía ni reciprocidad.']
    return '\n'.join(lines)


if __name__ == '__main__':
    main()

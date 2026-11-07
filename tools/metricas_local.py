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
from metrics.habits import habits  # noqa: E402
from metrics.latency import latency_sensitivity  # noqa: E402
from metrics.participants import participant_guide, role_name  # noqa: E402
from metrics.participation import participation  # noqa: E402
from metrics.style import style  # noqa: E402
from metrics.turn_content import turn_content  # noqa: E402
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
    ap.add_argument('--yo', choices=['A', 'B'])
    ap.add_argument('--resumen', action='store_true')
    a = ap.parse_args(argv)

    merge = dict(x.split('=', 1) for x in a.unir) if a.unir else None
    out = analizar(a.ruta, confirmo=a.confirmo_individual, date_order_hint=a.date_order_hint, merge=merge,
                   aceptar_alias=a.aceptar_alias_sospechosos,
                   perdidas=[int(x) for x in a.aceptar_perdidas.split(',')] if a.aceptar_perdidas else None, yo=a.yo)
    print(resumen(out) if a.resumen else json.dumps(out, ensure_ascii=False, indent=2))


def analizar(ruta, confirmo=False, date_order_hint=None, merge=None, aceptar_alias=False, perdidas=None, yo=None):
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
        out['correspondencia'] = correspondence(res.messages)
    return out


def _fmt(x, pct=False):
    if x is None:
        return '—'
    return f'{x * 100:.0f}%' if pct else (f'{x:g}' if isinstance(x, (int, float)) else str(x))


def _hhmm(h):
    return '—' if h is None else f'{int(h):02d}:{round((h % 1) * 60):02d}'


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
    c = out['correspondencia']
    lines += ['', f"== Correspondencia formal (pares en la misma sesión, hueco {c['hueco_horas']} h: "
                  f"{c['pares_misma_sesion']}; X_a_Y = lo que Y da a X) =="]
    for key, name, f in (('R1_extension', 'R1 extensión (ρ)', 'rho'), ('R2_preguntas', 'R2 preguntas (dif.)', 'diferencia'),
                         ('R3_desarrollados', 'R3 desarrollados (dif. no mín.)', 'diferencia_no_minimo')):
        r = c[key]
        dirs = [k for k in r if '_a_' in k]
        lines.append(f"  {name}: " + '; '.join(f"{d} {_fmt(r[d][f])} (n={r[d]['n']})" for d in dirs) + f" -> {r['etiqueta']}")
    r4 = c['R4_iniciativa']
    lines.append('  R4 iniciativa: reanudaciones ' + '; '.join(f"{g} h " + '/'.join(f'{k} {v}' for k, v in d.items())
                 for g, d in r4['reanudaciones'].items()) + f" ({r4['robustez_reanudaciones']}); inicia día "
                 + '/'.join(f'{k} {v}' for k, v in r4['inicia_dia'].items()))
    lines.append('  ' + c['nota'])
    lines += ['', 'Observaciones descriptivas: no interpretan interés, cercanía ni reciprocidad.']
    return '\n'.join(lines)


if __name__ == '__main__':
    main()

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

from metrics.habits import habits  # noqa: E402
from metrics.latency import latency_sensitivity  # noqa: E402
from metrics.participants import participant_guide, role_name  # noqa: E402
from metrics.participation import participation  # noqa: E402
from metrics.style import style  # noqa: E402
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
        out['participacion'] = participation(res.messages)
        out['latencias'] = latency_sensitivity(res.messages)
        out['habitos'] = habits(res.messages)
        out['estilo'] = style(res.messages)
    print(resumen(out) if a.resumen else json.dumps(out, ensure_ascii=False, indent=2))


def _fmt(x, pct=False):
    if x is None:
        return '—'
    return f'{x * 100:.0f}%' if pct else (f'{x:g}' if isinstance(x, (int, float)) else str(x))


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
        lines.append(f"      al volver tras > {L['hueco_horas']} h: mediana {_fmt(v['mediana_entre'])} min "
                     f"(n={v['n_entre']}, {v['suficiencia_entre']})")
    lines.append('  sensibilidad (mediana entre sesiones por hueco): ' + '; '.join(
        f"{h} h: " + ', '.join(f"{k} {_fmt(lat[h]['por_participante_que_interviene'][k]['mediana_entre'])}"
                               for k in lab) for h in gaps))

    lines += ['', '== Hábitos (hora local del teléfono que exportó) ==']
    for k, v in out['habitos']['por_participante'].items():
        fr = ', '.join(f'{n} {_fmt(x, True)}' for n, x in v['proporcion_por_franja'].items())
        lines.append(f"  {lab[k]}: hora más frecuente {v['hora_mas_frecuente']} h | {fr}")

    lines += ['', '== Estilo (mensajes de texto) ==']
    for k, v in out['estilo']['por_participante'].items():
        lines.append(f"  {lab[k]}: {_fmt(v['palabras_mediana'])} palabras/mensaje (p90 {_fmt(v['palabras_p90'])}), "
                     f"preguntas {_fmt(v['proporcion_preguntas'], True)}, emoji {_fmt(v['proporcion_con_emoji'], True)}, "
                     f"mayúsculas {_fmt(v['proporcion_mayusculas'], True)}, multimedia {_fmt(v['proporcion_media'], True)}")
    lines += ['', 'Observaciones descriptivas: no interpretan interés, cercanía ni reciprocidad.']
    return '\n'.join(lines)


if __name__ == '__main__':
    main()

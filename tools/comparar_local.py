#!/usr/bin/env python3
r"""Compara TODAS las exportaciones de una carpeta en una sola tabla (solo números, sin nombres de archivo).

Uso:  python tools/comparar_local.py RUTA [RUTA ...] --confirmo-individual [--hint 4=dmy] [--alias 0]
      PowerShell (recomendado, mismos índices que $archivos[N]):
        py -3 tools\comparar_local.py $archivos.FullName --confirmo-individual --hint 4=dmy
      Con UNA carpeta se listan sus .txt (orden aproximado al de PowerShell; verifica con la columna KB).

Los archivos .txt se ordenan por nombre SIN distinguir mayúsculas y se identifican SOLO por índice (0, 1, …), igual que $archivos[N] en
PowerShell: el nombre del archivo suele traer el nombre de la persona y nunca se imprime.
--confirmo-individual  declaras que TODOS son chats individuales (si no, no se analiza ninguno)
--hint N=dmy|mdy       orden de fecha del archivo N (repetible)
--alias N              acepta los alias sospechosos que el parser reporte en el archivo N (repetible)
Columnas: proporción de A en cada unidad (B = 100% - A). "no mín." = turnos con contenido; "desarr." = turnos
desarrollados. Latencia: p90 en minutos de cada uno (6 h). Retoma: veces que vuelve tras > 6 h (A/B).
Correspondencia R1–R3: sim = simétrica; →A = A recibe más correspondencia formal de la que da; insuf.; sensible; base = ante el estímulo ambos responden igual, solo difiere su línea base.
·nivel (pres/baja/inv) por dirección A_a_B/B_a_A, o uno solo si coinciden; ver config reciprocity.min_level_*.
cierra A = sesiones cuyo último turno sin respuesta es de A; días act. = días con mensajes / días del rango;
racha = máximo de días seguidos con mensajes.
Descriptivo: no interpreta interés, cercanía ni reciprocidad."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from metricas_local import analizar  # noqa: E402

COLS = ['#', 'KB', 'estado', 'msj A', 'turnos A', 'no mín. A', 'desarr. A', 'desarr. A 10/15/25', 'palabras A', 'p90 lat A/B', 'retoma A/B',
        'inicia día A', 'cierra A', 'días act.', 'racha', 'pausas >30d', 'R1 ext.', 'R2 preg.', 'R3 desarr.']


def _pct(x):
    return '—' if x is None else f'{x * 100:.0f}%'


def _num(x):
    return '—' if x is None else f'{x:g}'


def fila(i, out, kb=''):
    if not out['analisis_habilitado']:
        return [str(i), kb, 'NO: ' + ','.join(out['requisitos_pendientes'] or [out['importacion']])] + [''] * (len(COLS) - 3)
    p, tc = out['participacion']['proporciones'], out['contenido_turnos']['proporciones_entre_participantes']
    lat = out['latencias'].get(6) or out['latencias'][sorted(out['latencias'])[len(out['latencias']) // 2]]
    lp, h = lat['por_participante_que_interviene'], out['habitos']['por_participante']
    return [str(i), kb, {'sin_observaciones_de_calidad': 'ok', 'con_observaciones': 'con obs.'}.get(out['estado_calidad'], out['estado_calidad']), _pct(p['mensajes']['A']), _pct(p['turnos']['A']),
            _pct(tc['turnos_no_minimos']['A']), _pct(tc['turnos_desarrollados']['A']),
            '/'.join(_pct(v['A']).rstrip('%') for v in out['contenido_turnos']['sensibilidad_desarrollados'].values()),
            _pct(tc['palabras_sustantivas']['A']),
            f"{_num(lp['A']['p90_general'])}/{_num(lp['B']['p90_general'])}",
            f"{lp['A']['n_entre']}/{lp['B']['n_entre']}", _pct(h['A']['proporcion_inicia_el_dia']),
            _pct(out['ritmo']['sesiones']['proporcion_cierra']['A']),
            _pct(out['ritmo']['continuidad']['proporcion_dias_activos']), str(out['ritmo']['continuidad']['racha_mas_larga_dias']),
            str(lat['pausas_largas']['n'])] + [_corr(out['correspondencia'][k])
                                               for k in ('R1_extension', 'R2_preguntas', 'R3_desarrollados')]


def _corr(r):
    """Etiqueta + nivel cuando ambas direcciones lo comparten (p. ej. sim·baja); si difieren, A/B."""
    lab = _short(r['etiqueta'])
    lv = [r[k].get('nivel') for k in r if '_a_' in k]
    if r['etiqueta'] == 'insuficiente' or None in lv:
        return lab
    abbr = {'presente': 'pres', 'baja_o_nula': 'baja', 'inversa': 'inv'}
    return f"{lab}·{abbr[lv[0]]}" if lv[0] == lv[1] else f"{lab}·{abbr[lv[0]]}/{abbr[lv[1]]}"


def _short(label):
    return {'simetrica': 'sim', 'asimetrica_hacia_A': '→A', 'asimetrica_hacia_B': '→B', 'insuficiente': 'insuf.',
            'sensible_a_umbrales': 'sensible', 'diferencia_de_linea_base': 'base'}.get(label, label)


def tabla(rows):
    w = [max(len(r[c]) for r in [COLS] + rows) for c in range(len(COLS))]
    fmt = lambda r: '  '.join(x.ljust(w[c]) for c, x in enumerate(r))   # noqa: E731
    return '\n'.join([fmt(COLS), '  '.join('-' * x for x in w)] + [fmt(r) for r in rows])


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):          # Windows/cp1252 al redirigir: no fallar por ρ o →
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('rutas', nargs='+')
    ap.add_argument('--confirmo-individual', action='store_true')
    ap.add_argument('--hint', action='append', default=[], metavar='N=dmy')
    ap.add_argument('--alias', action='append', default=[], type=int, metavar='N')
    a = ap.parse_args(argv)
    hints = {int(k): v for k, v in (x.split('=', 1) for x in a.hint)}
    # Orden SIN distinguir mayúsculas (como Sort-Object de PowerShell). Puede diferir en casos raros de acentos o
    # símbolos: por eso se imprime el tamaño en KB, para cruzar cada fila con $archivos[N].Length sin ver nombres.
    if len(a.rutas) == 1 and os.path.isdir(a.rutas[0]):
        d = a.rutas[0]
        files = [os.path.join(d, f) for f in sorted((f for f in os.listdir(d) if f.lower().endswith('.txt')),
                                                    key=lambda f: (f.casefold(), f))]
    else:
        files = list(a.rutas)              # orden EXACTO en que llegan (p. ej. $archivos.FullName)
    if not files:
        sys.exit('No hay archivos .txt en esa carpeta.')
    rows = [fila(i, analizar(f, confirmo=a.confirmo_individual, date_order_hint=hints.get(i),
                             aceptar_alias=i in a.alias), str(round(os.path.getsize(f) / 1024)))
            for i, f in enumerate(files)]
    print(tabla(rows))
    print('\nA = primer autor de cada archivo. Columnas en % de A (B = resto). Solo descriptivo.')


if __name__ == '__main__':
    main()

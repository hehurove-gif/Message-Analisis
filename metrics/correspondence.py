"""Correspondencia formal (Fase 3, v0.1; definiciones §6). En config: `reciprocity` (nombre interno).

Se reporta como "correspondencia" y no como "reciprocidad": mide solo la FORMA de los mensajes (extensión,
presencia de preguntas, turnos mínimos), no su contenido. No mide interés, afecto, seguimiento de temas ni apoyo.

Unidad: PAR DE TURNOS = turno de X (estímulo) seguido del siguiente turno de Y (respuesta) en la MISMA sesión
(latencia <= hueco). Los pares entre sesiones y los fuera de orden se excluyen. Dirección "A_a_B" = estímulo de A,
respuesta de B: describe cuánto corresponde B a A (lo que A RECIBE).
  R1 extensión     Spearman entre palabras sustantivas del estímulo y de la respuesta + mediana de la respuesta
                   según la clase del estímulo (mínimo / breve / desarrollado).
  R2 preguntas     proporción de respuestas no mínimas tras un turno con pregunta, menos la misma proporción tras
                   turnos sin pregunta (línea base de quien responde). No verifica que se CONTESTE la pregunta.
  R3 desarrollados distribución de la respuesta tras un turno desarrollado vs tras uno breve (línea base);
                   diferencia en proporción no mínima. Se recalcula con los umbrales 10/15/25.
  R4 iniciativa    reanudaciones de sesión (2/6/12 h) e inicio del día lógico: reparto y margen, sin pares.
Etiqueta R1–R3: simetrica | asimetrica_hacia_A | asimetrica_hacia_B ("hacia A" = A recibe más correspondencia de
la que da) | insuficiente | sensible_a_umbrales (la dirección cambia con el hueco o el umbral: no es patrón).
Sin índice compuesto: las dimensiones pueden contradecirse y se leen por separado."""
import statistics
from collections import Counter

import yaml

from metrics.habits import habits
from metrics.style import is_question
from metrics.text_units import DEFAULT_ACKS
from metrics.turn_content import classify_turn
from segmentation.sessions import sensitivity as session_sensitivity
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns

NOTE = 'correspondencia formal observable (forma de los mensajes); no mide interés, afecto ni contenido'
DEFAULTS = {'min_pairs': 30, 'min_stimuli': 10, 'max_symmetric_diff': 0.10, 'max_symmetric_diff_rho': 0.15}


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    rc, tc, seg = raw.get('reciprocity', {}), raw.get('turn_content', {}), raw.get('segmentation', {})
    return {**DEFAULTS, **{k: rc[k] for k in DEFAULTS if k in rc}, 'defined': rc.get('defined', False),
            'acks': tc.get('acknowledgements', DEFAULT_ACKS), 'dev': tc.get('developed_min_words', 15),
            'dev_sens': tc.get('sensitivity_developed_min_words', [10, 15, 25]),
            'gap': seg.get('session_gap_hours', 6), 'gaps': seg.get('sensitivity_session_gap_hours', [2, 6, 12])}


def _ranks(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1                # rango promedio en empates
        i = j + 1
    return r


def spearman(x, y):
    """ρ de Spearman con rangos promedio; None con < 3 pares o sin variación."""
    if len(x) < 3:
        return None
    rx, ry = _ranks(x), _ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx, sy = sum((a - mx) ** 2 for a in rx) ** .5, sum((b - my) ** 2 for b in ry) ** .5
    return round(sxy / (sx * sy), 3) if sx and sy else None


def turn_pairs(messages, session_gap_hours, acks=DEFAULT_ACKS):
    """Pares (estímulo, respuesta) dentro de la misma sesión. Cada lado: participante, palabras, pregunta, mínimo."""
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    pos = {m.seq: i for i, m in enumerate(people)}
    info = []
    for t in build_turns(people, session_gap_hours=session_gap_hours):
        msgs = people[pos[t.seq_primero]:pos[t.seq_ultimo] + 1]
        c, w = classify_turn(msgs, acks, developed_min=10 ** 9)   # solo 'minimo' vs con contenido
        info.append({'p': t.participante, 's': t.sesion, 'w': w, 'min': c == 'minimo', 'ini': t.primer_ts,
                     'fin': t.ultimo_ts, 'q': any(is_question(m.texto) for m in msgs if m.tipo == 'texto')})
    return [(a, b) for a, b in zip(info, info[1:])
            if a['s'] == b['s'] and a['p'] != b['p'] and b['ini'] >= a['fin']]


def _cls(t, dev):
    return 'minimo' if t['min'] else ('desarrollado' if t['w'] >= dev else 'breve')


def _nomin(rs):
    return round(sum(not r['min'] for r in rs) / len(rs), 3) if rs else None


def _label(vals, enough, thr):
    """vals/ns por dirección {'A_a_B': x, 'B_a_A': y}."""
    if not enough or any(v is None for v in vals.values()):
        return 'insuficiente'
    d = vals['A_a_B'] - vals['B_a_A']
    return 'simetrica' if abs(d) < thr else ('asimetrica_hacia_A' if d > 0 else 'asimetrica_hacia_B')


def _dirs(pairs, names):
    a, b = names
    return {f'{a}_a_{b}': [p for p in pairs if p[0]['p'] == a], f'{b}_a_{a}': [p for p in pairs if p[0]['p'] == b]}


def _r1(pairs, names, c):
    out = {}
    for k, ps in _dirs(pairs, names).items():
        med = lambda cl: (lambda xs: statistics.median(xs) if xs else None)(   # noqa: E731
            [r['w'] for s, r in ps if _cls(s, c['dev']) == cl])
        out[k] = {'rho': spearman([s['w'] for s, _ in ps], [r['w'] for _, r in ps]), 'n': len(ps),
                  **{f'mediana_tras_{cl}': med(cl) for cl in ('minimo', 'breve', 'desarrollado')}}
    enough = all(v['n'] >= c['min_pairs'] for v in out.values())
    out['etiqueta'] = _label({k: out[k]['rho'] for k in _dirs(pairs, names)}, enough, c['max_symmetric_diff_rho'])
    return out


def _r2(pairs, names, c):
    out = {}
    for k, ps in _dirs(pairs, names).items():
        con, sin = [r for s, r in ps if s['q']], [r for s, r in ps if not s['q']]
        pc, ps_ = _nomin(con), _nomin(sin)
        out[k] = {'con_pregunta': pc, 'sin_pregunta': ps_, 'n_con_pregunta': len(con), 'n_sin_pregunta': len(sin),
                  'diferencia': round(pc - ps_, 3) if pc is not None and ps_ is not None else None, 'n': len(ps)}
    enough = all(v['n'] >= c['min_pairs'] and min(v['n_con_pregunta'], v['n_sin_pregunta']) >= c['min_stimuli']
                 for v in out.values())
    out['etiqueta'] = _label({k: out[k]['diferencia'] for k in _dirs(pairs, names)}, enough, c['max_symmetric_diff'])
    return out


def _r3(pairs, names, c, dev):
    out = {}
    for k, ps in _dirs(pairs, names).items():
        grp = {g: [r for s, r in ps if _cls(s, dev) == g] for g in ('desarrollado', 'breve')}
        dist = {g: {cl: (round(Counter(_cls(r, dev) for r in rs)[cl] / len(rs), 3) if rs else None)
                    for cl in ('minimo', 'breve', 'desarrollado')} for g, rs in grp.items()}
        nd, nb = _nomin(grp['desarrollado']), _nomin(grp['breve'])
        out[k] = {'tras_desarrollado': dist['desarrollado'], 'tras_breve': dist['breve'],
                  'n_tras_desarrollado': len(grp['desarrollado']), 'n_tras_breve': len(grp['breve']),
                  'diferencia_no_minimo': round(nd - nb, 3) if nd is not None and nb is not None else None,
                  'n': len(ps)}
    enough = all(v['n'] >= c['min_pairs'] and min(v['n_tras_desarrollado'], v['n_tras_breve']) >= c['min_stimuli']
                 for v in out.values())
    out['etiqueta'] = _label({k: out[k]['diferencia_no_minimo'] for k in _dirs(pairs, names)}, enough,
                             c['max_symmetric_diff'])
    return out


def _combine(central, labels):
    """Etiqueta final: la central, salvo que la dirección cambie entre huecos/umbrales."""
    dirs = {x for x in labels if x.startswith('asimetrica')}
    return 'sensible_a_umbrales' if central != 'insuficiente' and len(dirs) > 1 else central


def _r4(messages, names, c):
    ss = session_sensitivity(messages, gaps=c['gaps'])
    h = habits(messages)['por_participante']
    ini = {n: h[n]['inicia_el_dia'] for n in names}
    tot = sum(ini.values())
    return {'reanudaciones': {g: v['reanudaciones'] for g, v in ss['por_hueco'].items()},
            'margen_reanudaciones': {g: v['margen_reanudaciones'] for g, v in ss['por_hueco'].items()},
            'robustez_reanudaciones': ss['robustez']['reanudaciones'],
            'inicia_dia': ini, 'margen_inicia_dia': round(abs(ini[names[0]] - ini[names[1]]) / tot, 3) if tot else 0.0}


def correspondence(messages, cfg_path=None):
    c = _cfg(cfg_path)
    names = sorted({m.participante for m in messages if m.tipo in PERSON_TYPES})
    if len(names) != 2:
        raise ValueError('la correspondencia espera exactamente 2 participantes')
    by_gap = {g: turn_pairs(messages, g, c['acks']) for g in c['gaps']}
    central_gap = c['gap'] if c['gap'] in by_gap else c['gaps'][len(c['gaps']) // 2]
    pairs = by_gap.get(central_gap) or turn_pairs(messages, central_gap, c['acks'])

    r1, r2, r3 = _r1(pairs, names, c), _r2(pairs, names, c), _r3(pairs, names, c, c['dev'])
    s1 = {g: _r1(p, names, c)['etiqueta'] for g, p in by_gap.items()}
    s2 = {g: _r2(p, names, c)['etiqueta'] for g, p in by_gap.items()}
    s3 = {f'{g}h_{th}': _r3(p, names, c, th)['etiqueta'] for g, p in by_gap.items() for th in c['dev_sens']}
    for r, s in ((r1, s1), (r2, s2), (r3, s3)):
        r['etiqueta_central'] = r['etiqueta']
        r['sensibilidad'] = s
        r['etiqueta'] = _combine(r['etiqueta'], list(s.values()))
    return {'hueco_horas': central_gap, 'umbral_desarrollado_palabras': c['dev'], 'pares_misma_sesion': len(pairs),
            'umbrales': {k: c[k] for k in DEFAULTS},
            'R1_extension': r1, 'R2_preguntas': r2, 'R3_desarrollados': r3, 'R4_iniciativa': _r4(messages, names, c),
            'nota': NOTE}

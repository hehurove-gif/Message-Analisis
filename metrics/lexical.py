"""Conteo bruto de eventos léxicos por persona (Fase 5.1). Solo números; ningún texto sale de aquí.

Por categoría y variante (estricta | amplia) y por participante: mensajes con evento, ocurrencias, turnos con
evento, días con evento (día lógico) y sus denominadores (mensajes de texto, turnos, días activos). Las tasas son
derivadas de esos conteos. Negadas y preguntas se cuentan aparte. No hay índices compuestos ni interpretación."""
import bisect
from collections import Counter
from datetime import datetime, timedelta

import yaml

from nlp.lexicon import events_for_message, load_lexicon
from metrics.trends import _all_periods, _cfg as _tcfg, period_key
from segmentation.turns import DEFAULT_CONFIG_PATH, build_turns


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return raw.get('habits', {}).get('day_start_hour', 5), raw.get('romantic_interest', {}).get('min_events_for_pattern', 3)


def _pct(a, b):
    return round(100 * a / b, 2) if b else None


def lexical_counts(messages, lexicon=None, local_path=None, cfg_path=None):
    lex = lexicon or load_lexicon(local_path=local_path, cfg_path=cfg_path)
    day_start, min_events = _cfg(cfg_path)
    names = sorted({m.participante for m in messages if m.participante})
    people = [m for m in messages if m.participante and m.timestamp_local]
    turns = build_turns(messages)
    starts = [t.seq_primero for t in turns]

    def turn_of(seq):
        return bisect.bisect_right(starts, seq) - 1

    day = lambda m: (datetime.fromisoformat(m.timestamp_local) - timedelta(hours=day_start)).date()
    base = {n: {'mensajes_texto': sum(m.tipo == 'texto' for m in people if m.participante == n),
                'turnos': sum(t.participante == n for t in turns),
                'dias_activos': len({day(m) for m in people if m.participante == n})} for n in names}

    descartes, cats = Counter(), {}
    por_expr = {}                     # categoría -> expresión -> {persona: mensajes} (afirmativas, amplia)
    por_regla = {}                    # id de regla -> {persona: mensajes con evento afirmativo (variante amplia)}
    acc = {}      # (cat, variante, persona) -> dict de conjuntos/contadores
    for m in people:
        if m.tipo != 'texto':
            continue
        evs, desc = events_for_message(m, lex)
        descartes.update(desc)
        for e in evs:
            variants = []
            if e.forma == 'afirmativa':
                variants = ['amplia'] + ([] if e.ambiguo else ['estricta'])
            else:
                variants = [e.forma + 's']
            for v in variants:
                a = acc.setdefault((e.categoria, v, e.participante),
                                   {'mensajes': 0, 'ocurrencias': 0, 'turnos': set(), 'dias': set()})
                a['mensajes'] += 1
                a['ocurrencias'] += e.n_coincidencias
                a['turnos'].add(turn_of(e.seq))
                a['dias'].add(day(m))
            cats.setdefault(e.categoria, e.clase_provisional)
            if e.forma == 'afirmativa':
                for x, _ in e.expresiones:
                    por_expr.setdefault(e.categoria, {}).setdefault(x, Counter())[e.participante] += 1
                for rid in e.reglas:
                    d = por_regla.setdefault(rid, Counter())
                    d[e.participante] += 1

    def block(cat, v, n):
        a = acc.get((cat, v, n), {'mensajes': 0, 'ocurrencias': 0, 'turnos': set(), 'dias': set()})
        b = base[n]
        d = {'mensajes_con_evento': a['mensajes'], 'ocurrencias': a['ocurrencias'],
             'turnos_con_evento': len(a['turnos']), 'dias_con_evento': len(a['dias'])}
        if v in ('estricta', 'amplia'):
            d.update({'por_100_mensajes': _pct(a['mensajes'], b['mensajes_texto']),
                      'por_100_turnos': _pct(len(a['turnos']), b['turnos']),
                      'pct_dias_activos_con_evento': _pct(len(a['dias']), b['dias_activos'])})
        return d

    def direction(cat, v):
        da = {n: block(cat, v, n)['dias_con_evento'] for n in names}
        tot = sum(da.values())
        if tot < min_events:
            return 'insuficiente'
        if len(names) < 2 or da[names[0]] == da[names[1]]:
            return 'igual'
        return max(da, key=da.get)

    out = {}
    for cat in sorted(cats):
        dirs = {v: direction(cat, v) for v in ('estricta', 'amplia')}
        out[cat] = {'clase_provisional': cats[cat],
                    **{v: {n: block(cat, v, n) for n in names} for v in ('estricta', 'amplia', 'negadas', 'preguntas')},
                    'mas_dias_con_evento': dirs,
                    'robustez_indicadores': ('insuficiente' if 'insuficiente' in dirs.values() else
                                             'robusto_ante_indicadores' if dirs['estricta'] == dirs['amplia'] else
                                             'sensible_a_indicadores')}
    return {'base': base, 'por_categoria': out, 'descartes_por_regla': dict(sorted(descartes.items())),
            'mensajes_por_expresion': {c: {x: {n: v.get(n, 0) for n in names} for x, v in sorted(d.items(), key=lambda kv: -sum(kv[1].values()))}
                                       for c, d in sorted(por_expr.items())},
            'mensajes_por_regla': {r: {n: c.get(n, 0) for n in names} for r, c in sorted(por_regla.items())},
            'reglas': {'n': len(lex.rules), 'n_locales': lex.n_local},
            'nota': 'conteo bruto de coincidencias léxicas; un evento es un dato sobre el texto, no sobre la persona ni la relación'}


def lexical_series(messages, lexicon=None, local_path=None, cfg_path=None, granularity=None, compare_granularity=True):
    """Serie del conteo bruto por periodo (Fase 5.3), mes o semana ISO, por categoría y persona.

    Por periodo: mensajes con evento (estricta y amplia) y mensajes de texto (denominador). La "dirección" de un
    periodo (quién tiene más mensajes con evento por cada 100 mensajes de texto, variante estricta) solo se da si el
    periodo tiene al menos `min_events_per_period_for_trend` eventos y la diferencia es ≥ 25 %; si no, es None o 'igual'. El resumen cuenta en cuántos
    periodos válidos lidera cada persona y se repite con la otra granularidad: `robusto` si coincide el líder
    dominante, `sensible_a_granularidad` si no. Sin interpretación: es el mismo conteo bruto, solo repartido en el tiempo."""
    lex = lexicon or load_lexicon(local_path=local_path, cfg_path=cfg_path)
    tc = _tcfg(cfg_path)
    gran = granularity or tc['gran']
    day_start, min_ev = tc['day_start'], tc['min_ev']
    names = sorted({m.participante for m in messages if m.participante})
    people = [m for m in messages if m.participante and m.timestamp_local]
    day = lambda m: (datetime.fromisoformat(m.timestamp_local) - timedelta(hours=day_start)).date()   # noqa: E731
    if not people:
        return {'granularidad': gran, 'periodos': [], 'por_categoria': {}}
    evs_by = []                                   # (periodo_mes, periodo_semana, persona, [(cat, ambiguo)])
    for m in people:
        if m.tipo != 'texto':
            evs_by.append((day(m), m.participante, None))
            continue
        evs, _ = events_for_message(m, lex)
        evs_by.append((day(m), m.participante, {(e.categoria, e.ambiguo) for e in evs if e.forma == 'afirmativa'}))

    def build(g):
        keys = _all_periods(evs_by[0][0], max(d for d, _, _ in evs_by), g)
        base = {k: Counter() for k in keys}
        cnt = {}                                  # (cat, variante) -> periodo -> Counter(persona)
        for d, who, cats_ in evs_by:
            k = period_key(d, g)
            if cats_ is None:
                continue
            base[k][who] += 1
            for cat in {c for c, _ in cats_}:
                cnt.setdefault((cat, 'amplia'), {}).setdefault(k, Counter())[who] += 1
            for cat in {c for c, amb in cats_ if not amb}:
                cnt.setdefault((cat, 'estricta'), {}).setdefault(k, Counter())[who] += 1
        res = {}
        for cat in sorted({c for c, _ in cnt}):
            rows, lead = [], Counter()
            for k in keys:
                e = cnt.get((cat, 'estricta'), {}).get(k, Counter())
                w = cnt.get((cat, 'amplia'), {}).get(k, Counter())
                r = {'periodo': k}
                for n in names:
                    r['estricta_' + n], r['amplia_' + n], r['texto_' + n] = e.get(n, 0), w.get(n, 0), base[k].get(n, 0)
                    r['estricta_por_100_' + n] = _pct(e.get(n, 0), base[k].get(n, 0))
                tot = sum(e.values())
                direc = None
                if tot >= min_ev and len(names) == 2:
                    ra, rb = (r['estricta_por_100_' + n] or 0 for n in names)
                    direc = 'igual' if max(ra, rb) < 1.25 * min(ra, rb) or ra == rb else (names[0] if ra > rb else names[1])   # margen: ≥ 25 % de diferencia
                r['direccion'] = direc
                if direc and direc != 'igual':
                    lead[direc] += 1
                rows.append(r)
            valid = sum(1 for r in rows if r['direccion'])
            dom = None
            if valid >= 3 and lead:
                top, nt = lead.most_common(1)[0]
                dom = top if nt / valid >= 0.75 else 'mixto'
            elif valid < 3:
                dom = 'insuficiente'
            res[cat] = {'periodos': rows, 'periodos_validos': valid, 'lidera': {n: lead.get(n, 0) for n in names},
                        'dominante': dom}
        return keys, res

    keys, res = build(gran)
    out = {'granularidad': gran, 'min_eventos_periodo': min_ev, 'periodos': keys, 'por_categoria': res}
    if compare_granularity:
        other = 'week' if gran == 'month' else 'month'
        _, alt = build(other)
        for cat, d in res.items():
            a, b = d['dominante'], alt.get(cat, {}).get('dominante')
            d['sensibilidad_granularidad'] = {'otra': other, 'dominante_otra': b,
                                              'etiqueta': 'robusto' if a == b else 'sensible_a_granularidad'}
    out['nota'] = 'conteo bruto repartido por periodo; no interpreta interés, cercanía ni reciprocidad'
    return out

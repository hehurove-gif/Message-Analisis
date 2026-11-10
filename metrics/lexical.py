"""Conteo bruto de eventos léxicos por persona (Fase 5.1). Solo números; ningún texto sale de aquí.

Por categoría y variante (estricta | amplia) y por participante: mensajes con evento, ocurrencias, turnos con
evento, días con evento (día lógico) y sus denominadores (mensajes de texto, turnos, días activos). Las tasas son
derivadas de esos conteos. Negadas y preguntas se cuentan aparte. No hay índices compuestos ni interpretación."""
import bisect
from collections import Counter
from datetime import datetime, timedelta

import yaml

from nlp.lexicon import events_for_message, load_lexicon
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
            'reglas': {'n': len(lex.rules), 'n_locales': lex.n_local},
            'nota': 'conteo bruto de coincidencias léxicas; un evento es un dato sobre el texto, no sobre la persona ni la relación'}

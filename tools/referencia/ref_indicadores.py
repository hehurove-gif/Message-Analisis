"""Cálculo de referencia INDEPENDIENTE (no es el código del sistema) de:
palabras, días activos, candidatos por semana, rejilla de robustez de la
recurrencia, latencia según el tipo de turno y conteo de categorías de respuesta.

Uso: python3 -I tools/referencia/ref_indicadores.py CHAT.txt ETIQUETAS.csv
"""
import csv, os, sys, statistics as st
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ref_latency as R

WEEK = lambda d: d.isocalendar()[:2]          # (año ISO, semana ISO), lunes a domingo
MONTH = lambda d: (d.year, d.month)


def load_labels(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            r['ts'] = datetime.strptime(r['fecha_hora'], '%Y-%m-%d %H:%M')
            rows.append(r)
    return rows


def words_and_days(msgs):
    words, nmsg, days = Counter(), Counter(), defaultdict(set)
    for m in msgs:
        days[m['who']].add(m['ts'].date()); days['_todos'].add(m['ts'].date())
        if m['txt'].strip() == '<Multimedia omitido>':
            continue
        words[m['who']] += len(m['txt'].split()); nmsg[m['who']] += 1
    span = (msgs[-1]['ts'].date() - msgs[0]['ts'].date()).days + 1
    return words, nmsg, days, span


def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    return 0 if s == 0 else sum((2 * (i + 1) - n - 1) * x for i, x in enumerate(xs)) / (n * s)


def grid(events, period):
    """events: lista de fechas de eventos candidatos de una persona."""
    periods = {period(d) for d in events}
    ok = 0; total = 0
    for me in (2, 3, 4, 5):
        for mp in (1, 2, 3):
            total += 1
            ok += (len(events) >= me and len(periods) >= mp)
    return len(events), len(periods), ok, total


def main(chat, labels):
    msgs = R.load(chat); L = load_labels(labels)
    who = sorted({m['who'] for m in msgs})
    print('MENSAJES', Counter(m['who'] for m in msgs), 'total', len(msgs))
    w, nm, days, span = words_and_days(msgs)
    print('PALABRAS (mensajes de texto, separadas por espacios):', dict(w), ' mensajes de texto:', dict(nm))
    tot = sum(w.values())
    print('  % palabras:', {k: round(100 * v / tot, 1) for k, v in w.items()},
          ' Gini de palabras:', round(gini(list(w.values())), 3))
    print('DÍAS: con mensajes', len(days['_todos']), 'de', span, ' por persona', {k: len(v) for k, v in days.items() if k != '_todos'})
    print('  mensajes por día activo:', round(len(msgs) / len(days['_todos']), 2))

    cand = [r for r in L if r['cuenta_como_candidato'] == 'si']
    print('\nCANDIDATOS (cuenta_como_candidato=si):', Counter(r['autor'] for r in cand))
    for a in who:
        ev = [r['ts'].date() for r in cand if r['autor'] == a and r['categoria_candidata'] != 'declaracion_explicita']
        if not ev: continue
        wk = Counter(WEEK(d) for d in ev)
        print(f'  {a}: por semana ISO', {f'{y}-S{s}': c for (y, s), c in sorted(wk.items())})
        n, p, ok, t = grid(ev, WEEK)
        print(f'    eventos={n} semanas={p}: cumple {ok} de {t} combinaciones (min_eventos 2-5 x min_periodos 1-3, semanal)')
        n, p, ok, t = grid(ev, MONTH)
        print(f'    mensual: meses={p}: cumple {ok} de {t} combinaciones')

    if 'categoria_respuesta' in (L[0] if L else {}):
        print('\nCATEGORÍAS DE RESPUESTA (candidatos antes de la declaración):')
        pre = [r for r in cand if r['categoria_candidata'] != 'declaracion_explicita']
        print(' ', dict(Counter(r['categoria_respuesta'] for r in pre)))
        print('  secundarias:', dict(Counter(r['categoria_secundaria'] for r in pre if r['categoria_secundaria'])))
        # latencia del interlocutor según el tipo de turno del candidato
        ind_msgs = {(r['ts'], r['autor']) for r in pre}
        decl = {(r['ts'], r['autor']) for r in cand if r['categoria_candidata'] == 'declaracion_explicita'}
        autor = pre[0]['autor']
        for gap in (2, 6, 12):
            turns = R.build(msgs, gap); Ls = R.latencies(msgs, turns, gap)
            cat = {'candidatos': [], 'declaracion': [], 'resto': []}; sin_prev = 0
            for t, state, lat, who2, within in Ls:
                if t['who'] != autor: continue
                keys = {(msgs[i]['ts'], msgs[i]['who']) for i in t['idx']}
                k = 'candidatos' if keys & ind_msgs else ('declaracion' if keys & decl else 'resto')
                if state == 'con_intervencion': cat[k].append((lat, within))
                elif k == 'candidatos': sin_prev += 1
            print(f'  -- hueco {gap} h (quien interviene tras turnos de {autor}); candidatos sin intervención previa: {sin_prev}')
            for k, v in cat.items():
                a = [x for x, _ in v]; wn = [x for x, y in v if y]; bt = [x for x, y in v if not y]
                print(f'     {k:12} n={len(a):2} general={R.fmt(R.med(a))} dentro={R.fmt(R.med(wn))}(n={len(wn)}) entre={R.fmt(R.med(bt))}(n={len(bt)})')
            if gap == 6:
                print('     latencias candidatos:', sorted(round(x) for x, _ in cat['candidatos']))
                print('     latencias resto     :', sorted(round(x) for x, _ in cat['resto']))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])

"""Saludos y despedidas convencionales (Fase 3, provisional): quién da los buenos días / las buenas noches.

Un mensaje `texto` cuenta como saludo de mañana o despedida de noche si contiene una de las frases de
`greetings` en config como palabra(s) completa(s) (comparación en minúsculas, sin acentos y con límites de palabra). Son LÍNEA BASE de comunicación (config
`romantic_interest.greeting_alone_is_candidate: false`): rituales, no indicadores de interés.
Por participante: mensajes con saludo/despedida, días en que lo dice primero y proporción de esos días en que
el otro corresponde con la misma clase de frase en el mismo día lógico. Solo números."""
import re
import unicodedata
from datetime import datetime, timedelta

import yaml

from segmentation.turns import DEFAULT_CONFIG_PATH

DEFAULT = {'manana': ['buenos dias', 'buen dia', 'good morning'],
           'noche': ['buenas noches', 'good night', 'que descanses', 'descansa']}


def _norm(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t.lower()) if unicodedata.category(c) != 'Mn')


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    g = raw.get('greetings', {})
    return ({k: [_norm(x) for x in g.get(k, v)] for k, v in DEFAULT.items()},
            raw.get('habits', {}).get('day_start_hour', 5))


def kind_of(text, phrases):
    t = _norm(text)
    # límites de palabra: "descansa" no debe coincidir con "descansar" ni "buen dia" con "buen diario"
    return [k for k, ps in phrases.items() if any(re.search(r'(?<!\w)' + re.escape(p) + r'(?!\w)', t) for p in ps)]


def greetings(messages, cfg_path=None):
    phrases, day_start = _cfg(cfg_path)
    msgs = [m for m in messages if m.tipo == 'texto' and m.timestamp_local]
    names = sorted({m.participante for m in messages if m.participante})
    per_day = {}                                     # (día, clase) -> [participantes en orden]
    count = {n: {k: 0 for k in phrases} for n in names}
    for m in msgs:
        for k in kind_of(m.texto, phrases):
            count[m.participante][k] += 1
            d = (datetime.fromisoformat(m.timestamp_local) - timedelta(hours=day_start)).date()
            per_day.setdefault((d, k), []).append(m.participante)
    out = {}
    for k in phrases:
        firsts = {n: [w for (d, kk), w in per_day.items() if kk == k and w[0] == n] for n in names}
        out[k] = {'mensajes': {n: count[n][k] for n in names},
                  'dias_lo_dice_primero': {n: len(firsts[n]) for n in names},
                  'proporcion_dias_A': (round(len(firsts[names[0]]) / sum(len(v) for v in firsts.values()), 3)
                                        if any(firsts.values()) else None),
                  'el_otro_corresponde': {n: (round(sum(len(set(w)) == 2 for w in firsts[n]) / len(firsts[n]), 3)
                                              if firsts[n] else None) for n in names}}
    return {'por_clase': out, 'nota': 'rituales de línea base (buenos días / buenas noches); no son indicadores de interés'}

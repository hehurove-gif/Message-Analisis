"""Contenido de los turnos (Fase 3, provisional): no todos los turnos pesan igual.

POR QUÉ: los turnos se ALTERNAN por definición (A, B, A, B…), así que su número queda casi 50/50 siempre; contar
turnos no distingue un "ok" de una respuesta elaborada. Aquí cada turno se clasifica por su contenido:
  minimo        sin palabras sustantivas (solo acuses tipo ok/va/sí, risas, emojis, multimedia o eliminados)
                y sin pregunta
  breve         con contenido, pero menos de `turn_content.developed_min_words` palabras sustantivas
  desarrollado  >= `developed_min_words` palabras sustantivas en el turno (sumando sus mensajes)
Palabras sustantivas: ver metrics/text_units.py. Umbrales EXPERIMENTALES en config; no miden calidad ni interés,
solo extensión del contenido. Se reporta por participante: conteos, proporciones dentro de sus turnos y
proporción de cada participante entre los turnos no mínimos (eso sí puede alejarse del 50/50)."""
import statistics
from collections import Counter

import yaml

from metrics.latency import percentile
from metrics.style import is_question
from metrics.text_units import DEFAULT_ACKS, substantive_words
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES, build_turns

CLASSES = ('minimo', 'breve', 'desarrollado')


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    tc = raw.get('turn_content', {})
    return (tc.get('acknowledgements', DEFAULT_ACKS), tc.get('developed_min_words', 15),
            raw.get('data_sufficiency', {}).get('min_turns_for_response_time', 20))


def classify_turn(msgs, acks=DEFAULT_ACKS, developed_min=15):
    texts = [m.texto for m in msgs if m.tipo == 'texto']
    words = sum(len(substantive_words(t, acks)) for t in texts)
    if words == 0 and not any(is_question(t) for t in texts):
        return 'minimo', 0
    return ('desarrollado' if words >= developed_min else 'breve'), words


def turn_content(messages, session_gap_hours=None, cfg_path=None):
    acks, dev_min, min_turns = _cfg(cfg_path)
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    by_seq = {m.seq: i for i, m in enumerate(people)}
    turns = build_turns(people, session_gap_hours=session_gap_hours)
    names = sorted({t.participante for t in turns})
    cls, words, nmsg = {n: Counter() for n in names}, {n: [] for n in names}, {n: [] for n in names}
    for t in turns:
        msgs = people[by_seq[t.seq_primero]:by_seq[t.seq_ultimo] + 1]
        c, w = classify_turn(msgs, acks, dev_min)
        cls[t.participante][c] += 1
        words[t.participante].append(w)
        nmsg[t.participante].append(t.n_mensajes)

    def share(key_fn):
        tot = {n: key_fn(n) for n in names}
        s = sum(tot.values())
        return {n: (round(v / s, 4) if s else None) for n, v in tot.items()}

    por = {}
    for n in names:
        tot = sum(cls[n].values())
        por[n] = {'turnos': tot, **{f'turnos_{c}': cls[n][c] for c in CLASSES},
                  **{f'proporcion_{c}': (round(cls[n][c] / tot, 3) if tot else None) for c in CLASSES},
                  'palabras_sustantivas_por_turno_mediana': statistics.median(words[n]) if words[n] else None,
                  'palabras_sustantivas_por_turno_p90': percentile(words[n], 90),
                  'mensajes_por_turno_mediana': statistics.median(nmsg[n]) if nmsg[n] else None,
                  'suficiencia_de_datos': 'suficiente' if tot >= min_turns else 'insuficiente'}
    return {'umbral_desarrollado_palabras': dev_min, 'por_participante': por,
            'proporciones_entre_participantes': {
                'turnos': share(lambda n: sum(cls[n].values())),
                'turnos_no_minimos': share(lambda n: cls[n]['breve'] + cls[n]['desarrollado']),
                'turnos_desarrollados': share(lambda n: cls[n]['desarrollado']),
                'palabras_sustantivas': share(lambda n: sum(words[n]))},
            'nota': 'clasificación por extensión del contenido; no mide calidad, interés ni reciprocidad'}

"""Estilo de escritura (Fase 3, provisional): CÓMO escribe cada participante, con su propia línea base.

Sobre mensajes `texto` de cada participante:
  palabras / caracteres   mediana y p90 (palabras = fragmentos separados por espacios, como en participación)
  preguntas               definiciones §4: contiene "?" / "¿" o empieza con palabra interrogativa (lista en
                          config `style.interrogatives`). Aproximación; se revisará con muestras manuales.
  con_emoji               al menos un carácter en rangos de emoji Unicode (aproximación, sin librería externa)
  mayusculas              >= `style.min_letters_uppercase` letras y todas en mayúscula, SIN contar las risas
                          ("JAJAJA" no es un mensaje en mayúsculas)
  con_risa                al menos un token de risa (jaja, jeje, haha, jsjs, xd; ver metrics/text_units.py)
  solo_minimo             sin palabras sustantivas (solo ok/va/sí, risas o emojis)
Multimedia: además de la proporción, `multimedia_por_tipo` (sticker, imagen…) cuando el marcador lo distingue;
en Android en español suele ser genérico ("<Multimedia omitido>") y no separa stickers.
Sobre todos sus mensajes de persona: proporción de `media` y `deleted`.
Regla general (§9.3): estos son hábitos individuales; usar pocos emojis o mensajes cortos no es "frialdad"."""
import statistics
from collections import Counter

import yaml

from metrics.latency import percentile
from metrics.text_units import EMOJI, has_laugh, strip_laughs, substantive_words
from segmentation.turns import DEFAULT_CONFIG_PATH, PERSON_TYPES

DEFAULT_INTERROGATIVES = ['qué', 'cómo', 'cuándo', 'dónde', 'adónde', 'por qué', 'cuál', 'cuáles', 'quién',
                          'quiénes', 'cuánto', 'cuánta', 'cuántos', 'cuántas', 'what', 'how', 'when', 'where',
                          'why', 'who', 'which']


def _cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    st = raw.get('style', {})
    return (st.get('interrogatives', DEFAULT_INTERROGATIVES), st.get('min_letters_uppercase', 4),
            raw.get('data_sufficiency', {}).get('min_messages_for_any_metric', 30))


def is_question(text, interrogatives=DEFAULT_INTERROGATIVES):
    t = text.strip().lower()
    if '?' in t or '¿' in t:
        return True
    return any(t == w or t.startswith(w + ' ') for w in interrogatives)


def is_uppercase(text, min_letters=4):
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= min_letters and all(c.isupper() for c in letters)


def _share(n, total):
    return round(n / total, 3) if total else None


def style(messages, cfg_path=None):
    inter, min_up, min_msgs = _cfg(cfg_path)
    people = [m for m in messages if m.tipo in PERSON_TYPES]
    names = sorted({m.participante for m in people})
    por = {}
    for n in names:
        mine = [m for m in people if m.participante == n]
        texts = [m.texto for m in mine if m.tipo == 'texto']
        words = [len(t.split()) for t in texts]
        chars = [len(t) for t in texts]
        por[n] = {
            'n_texto': len(texts),
            'palabras_mediana': statistics.median(words) if words else None,
            'palabras_p90': percentile(words, 90),
            'caracteres_mediana': statistics.median(chars) if chars else None,
            'proporcion_preguntas': _share(sum(is_question(t, inter) for t in texts), len(texts)),
            'proporcion_con_emoji': _share(sum(bool(EMOJI.search(t)) for t in texts), len(texts)),
            'proporcion_mayusculas': _share(sum(is_uppercase(strip_laughs(t), min_up) for t in texts), len(texts)),
            'proporcion_con_risa': _share(sum(has_laugh(t) for t in texts), len(texts)),
            'proporcion_solo_minimo': _share(sum(not substantive_words(t) for t in texts), len(texts)),
            'proporcion_media': _share(sum(m.tipo == 'media' for m in mine), len(mine)),
            'multimedia_por_tipo': dict(Counter(m.media_kind or 'sin_tipo' for m in mine if m.tipo == 'media')),
            'proporcion_eliminados': _share(sum(m.tipo == 'deleted' for m in mine), len(mine)),
            'suficiencia_de_datos': 'suficiente' if len(texts) >= min_msgs else 'insuficiente'}
    return {'por_participante': por,
            'nota': 'hábitos individuales y aproximados; no son señales de interés, frialdad ni cercanía'}

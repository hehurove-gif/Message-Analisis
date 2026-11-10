"""Normalización de texto SOLO para comparar (Fase 5). El texto original nunca se altera ni se guarda."""
import re
import unicodedata

_VOWEL_RUN = re.compile(r'([aeiou])\1+')
_CONS_RUN = re.compile(r'([^\W\d_aeiou])\1{2,}')


def normalize(text):
    """minúsculas, sin acentos (ni selectores de variación de emoji), espacios colapsados y letras alargadas
    reducidas: vocal repetida (2 o más) -> una; consonante repetida 3 o más -> una (conserva 'll', 'rr', 'cc').
    Se aplica por igual al texto y a los patrones, así que 'te quieroooo' y 'te amoo' coinciden con sus reglas."""
    t = ''.join(c for c in unicodedata.normalize('NFD', text.lower()) if unicodedata.category(c) != 'Mn')
    t = _VOWEL_RUN.sub(r'\1', t)
    t = _CONS_RUN.sub(r'\1', t)
    return re.sub(r'[ \t]+', ' ', t).strip()

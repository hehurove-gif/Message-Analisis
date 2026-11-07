"""Unidades léxicas compartidas por estilo y contenido de turnos (aproximaciones, sin librerías externas).

RISA: token (sin puntuación) como jaja, JAJAJA, jeje, jiji, haha, jsjs, xd. EMOJI: rangos Unicode de emoji.
PALABRAS SUSTANTIVAS: tokens del texto que no son risa, ni emoji/símbolo, ni acuse breve (lista en config
`turn_content.acknowledgements`: ok, va, sí, ya…). Un mensaje sin palabras sustantivas es "mínimo"."""
import re

EMOJI = re.compile('[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF\U00002B50\U00002764\U0000FE0F\U0000200D]')
LAUGH = re.compile(r'^(?:(?:[jh][aeiou]){2,}[jh]?|(?:js){2,}j?|(?:a?j){2,}a?|x+d+|ja+|je+|jsj+|lol|lmao)$', re.I)
PUNCT = re.compile(r'^[\W_]+|[\W_]+$')

DEFAULT_ACKS = ['ok', 'oki', 'okey', 'okay', 'okk', 'va', 'vale', 'sale', 'sí', 'si', 'no', 'ya', 'aja', 'ajá',
                'claro', 'bueno', 'bien', 'ah', 'oh', 'eh', 'mmm', 'mm', 'k', 'sip', 'nop', 'simon', 'simón',
                'neta', 'jsjs', 'xd', 'okis', 'yes', 'yep', 'nope', 'cool', 'gracias', 'grax', 'perfecto', 'listo']


def tokens(text):
    out = []
    for raw in text.split():
        t = PUNCT.sub('', raw)
        if t:
            out.append(t)
    return out


def is_laugh_token(tok):
    return bool(LAUGH.match(tok))


def has_laugh(text):
    return any(is_laugh_token(t) for t in tokens(text))


def substantive_words(text, acks=DEFAULT_ACKS):
    ack = {str(a).lower() for a in acks if isinstance(a, str)}
    return [t for t in tokens(text)
            if not is_laugh_token(t) and t.lower() not in ack and not EMOJI.fullmatch(t) and any(c.isalnum() for c in t)
            and not EMOJI.sub('', t) == '']


def strip_laughs(text):
    return ' '.join(t for t in text.split() if not is_laugh_token(PUNCT.sub('', t) or '_'))

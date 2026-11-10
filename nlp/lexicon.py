"""Motor léxico basado en reglas (Fase 5.1). Detecta coincidencias de palabra(s) completa(s) y emojis, marca
negación y pregunta, aplica excepciones y entrega EVENTOS CON EVIDENCIA (línea, regla, forma); el texto del
mensaje no forma parte del evento. Nada se escribe a disco ni se imprime desde aquí."""
import os
import re
from collections import Counter
from dataclasses import dataclass

import yaml

from nlp.text import EMOJI_RE, normalize
from segmentation.turns import DEFAULT_CONFIG_PATH

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEXICON_PATH = os.path.join(ROOT, 'lexicon', 'es_mx.yaml')
LOCAL_LEXICON_NAME = 'lexicon_local.yaml'
CATEGORIAS = ('afecto_explicito', 'apodo_carinoso', 'cumplido', 'propuesta_de_verse', 'apoyo', 'conflicto',
              'disculpa', 'gratitud', 'risa_texto', 'emoji_afectivo', 'emoji_risa', 'emoji_tristeza',
              'emoji_enojo', 'emoji_posible_ironia', 'emoji_base', 'emoji_otro')
FORMAS = ('afirmativa', 'negada', 'pregunta')
DEFAULT_CFG = {'negators': ['no', 'nunca', 'jamas', 'ni', 'tampoco', 'nadie'], 'negation_window_tokens': 3}
_PUNCT = ',.!?¡¿;:\n'
_NO_VOCATIVO_SIGUE = {'propio', 'propia', 'por', 'de', 'del', 'a'}
_SIGUE_VOCATIVO = {'como', 'que', 'te', 'ya', 'estas', 'donde', 'cuando', 'me', 'tu', 'quieres', 'vienes', 'puedes', 'hola',
                   'buenos', 'buenas', 'gracias', 'si', 'no', 'oye', 'mira', 'dime', 'vamos', 'extrano', 'quiero', 'amo'}


@dataclass(frozen=True)
class Rule:
    id: str
    categoria: str
    subetiqueta: str | None
    patrones: tuple               # regex compiladas (palabra completa) sobre texto normalizado
    emojis: tuple                 # subcadenas normalizadas
    ambiguo: bool
    clase_provisional: str
    no_seguido_de: str | None     # 'infinitivo'
    salvo_si_sigue: frozenset
    vocativo: bool
    regex: tuple                  # regex compiladas (palabra completa) para patrones con variantes
    pregunta_cuenta: bool         # la forma interrogativa cuenta como afirmativa (p. ej. invitaciones)
    no_si_sigue_pregunta: bool    # descarta si después viene una pregunta ("disculpa, ¿a qué hora…?")
    excepto_si_sigue: tuple       # frases que, si siguen a la coincidencia, la descartan ("gracias a dios")
    origen: str                   # 'generico' | 'local'


@dataclass(frozen=True)
class Event:
    seq: int
    linea: int
    timestamp: str
    participante: str
    categoria: str
    subetiquetas: tuple
    reglas: tuple
    forma: str                    # afirmativa | negada | pregunta
    ambiguo: bool                 # verdadero si TODAS las coincidencias del evento vienen de reglas ambiguas
    expresiones: tuple            # ((expresión, n), …) coincidentes; '(local)' en reglas locales
    n_coincidencias: int
    clase_provisional: str


@dataclass(frozen=True)
class Lexicon:
    rules: tuple
    negators: frozenset
    negation_window: int
    n_local: int = 0
    emoji_cubiertos: frozenset = frozenset()   # caracteres que alguna regla de emoji cubre


def _compile(pat):
    words = normalize(pat).split(' ')
    return re.compile(r'(?<!\w)' + r'\s+'.join(re.escape(w) for w in words) + r'(?!\w)')


def _rule_from(d, origen):
    for k in ('id', 'categoria'):
        if not d.get(k):
            raise ValueError(f'regla sin {k}')
    if d['categoria'] not in CATEGORIAS:
        raise ValueError(f"categoría desconocida: {d['categoria']}")
    if not d.get('patrones') and not d.get('emojis') and not d.get('regex'):
        raise ValueError(f"regla {d['id']} sin patrones ni emojis")
    return Rule(id=d['id'], categoria=d['categoria'], subetiqueta=d.get('subetiqueta'),
                patrones=tuple(_compile(p) for p in d.get('patrones', [])),
                emojis=tuple(normalize(e) for e in d.get('emojis', [])),
                ambiguo=bool(d.get('ambiguo', False)),
                clase_provisional=d.get('clase_provisional', 'pendiente_fase_6'),
                no_seguido_de=d.get('no_seguido_de'),
                salvo_si_sigue=frozenset(normalize(x) for x in d.get('salvo_si_sigue', [])),
                vocativo=bool(d.get('vocativo', False)),
                regex=tuple(re.compile(r'(?<!\w)(?:' + x.replace(' ', r'\s+') + r')(?!\w)') for x in d.get('regex', [])),
                pregunta_cuenta=bool(d.get('pregunta_cuenta', False)),
                no_si_sigue_pregunta=bool(d.get('no_si_sigue_pregunta', False)),
                excepto_si_sigue=tuple(normalize(x) for x in d.get('excepto_si_sigue', [])), origen=origen)


def _local_rules(path):
    """Archivo local: `reglas:` (mismo esquema) o atajos `apodos:` / `afecto:` (listas de frases)."""
    with open(path, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    rules = [_rule_from({**r, 'id': r.get('id') or f'local.regla{i}.v1'}, 'local')
             for i, r in enumerate(raw.get('reglas') or [], 1)]
    if raw.get('apodos'):
        rules.append(_rule_from({'id': 'local.apodos.v1', 'categoria': 'apodo_carinoso', 'patrones': raw['apodos'],
                                 'vocativo': True}, 'local'))
    if raw.get('afecto'):
        rules.append(_rule_from({'id': 'local.afecto.v1', 'categoria': 'afecto_explicito', 'patrones': raw['afecto']},
                                'local'))
    return rules


def load_lexicon(path=None, local_path=None, cfg_path=None):
    with open(cfg_path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        cfg = {**DEFAULT_CFG, **((yaml.safe_load(f) or {}).get('lexicon') or {})}
    with open(path or DEFAULT_LEXICON_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    rules = [_rule_from(r, 'generico') for r in raw.get('reglas', [])]
    local = _local_rules(local_path) if local_path and os.path.isfile(local_path) else []
    ids = [r.id for r in rules + local]
    if len(ids) != len(set(ids)):
        raise ValueError('ids de regla repetidos')
    # reglas no ambiguas primero: si dos reglas de una categoría coinciden en el mismo lugar, gana la estricta
    return Lexicon(rules=tuple(sorted(rules + local, key=lambda r: r.ambiguo)), negators=frozenset(normalize(x) for x in cfg['negators']),
                   negation_window=cfg['negation_window_tokens'], n_local=len(local),
                   emoji_cubiertos=frozenset(c for r in rules + local for e in r.emojis for c in e))


# Todo emoji que ninguna regla cubre se cuenta como `emoji_otro` (así la suma de las categorías de emoji cubre TODOS).
OTRO_RULE = Rule(id='emoji.otro.v1', categoria='emoji_otro', subetiqueta=None, patrones=(), emojis=(), ambiguo=False,
                 clase_provisional='pendiente_fase_6', no_seguido_de=None, salvo_si_sigue=frozenset(), vocativo=False,
                 regex=(), pregunta_cuenta=False, no_si_sigue_pregunta=False, excepto_si_sigue=(), origen='generico')


def _is_infinitive(tok):
    return len(tok) >= 3 and tok.endswith(('ar', 'er', 'ir'))


def _context(t, start, end, lex):
    """(forma, tokens_siguientes) de una coincidencia sobre el texto normalizado `t`."""
    sent_start = max(t.rfind(c, 0, start) for c in '.!?\n') + 1
    before = re.findall(r'\w+', t[sent_start:start])[-lex.negation_window:]
    m = re.search(r'[.!?\n]', t[end:])
    # '¿' después de la coincidencia = la coincidencia queda FUERA de la pregunta ("tigre, ¿vienes?")
    ends_q = bool(m and m.group() == '?') and '¿' not in t[end:end + m.start()]
    opened_q = '¿' in t[sent_start:start]
    forma = 'negada' if any(w in lex.negators for w in before) else ('pregunta' if ends_q or opened_q else 'afirmativa')
    q_after = bool(m and m.group() == '?') and '¿' in t[end:end + m.start()]
    return forma, re.findall(r'\w+', t[end:end + 60]), q_after


def _vocative(t, start, end):
    prev = t[:start].rstrip()
    nxt = t[end:].lstrip()
    pb = prev == '' or prev[-1] in _PUNCT
    nb = nxt == '' or nxt[0] in _PUNCT
    nxt_tok = (re.findall(r'\w+', nxt[:30]) or [''])[0]
    # vocativo: cierra la cláusula ("gracias, tigre"), o abre una y sigue un pronombre/verbo típico ("amor, ¿vienes?")
    return (nb or (pb and nxt_tok in _SIGUE_VOCATIVO)) and nxt_tok not in _NO_VOCATIVO_SIGUE


def detect(text, lex):
    """Coincidencias de UN mensaje. Devuelve (hits, descartes): hits = [(regla, forma, n)], descartes = Counter(id)."""
    hits, desc, _ = detect_full(text, lex)
    return hits, desc


def _expr(r, s):
    """Expresión que se reporta: la coincidencia (vocabulario de la regla) o, en reglas locales, solo '(local)'."""
    return '(local)' if r.origen == 'local' else s[:40]


def detect_full(text, lex):
    """Como `detect`, y además la lista de expresiones coincidentes [(regla, forma, expresión, n)]."""
    t = normalize(text)
    hits, desc, exprs = [], Counter(), []
    spans = {}                                   # categoría -> tramos ya usados (aceptados o descartados)
    for r in lex.rules:
        n_by_form = Counter()
        for rx in r.patrones + r.regex:
            for m in rx.finditer(t):
                used = spans.setdefault(r.categoria, [])
                if any(m.start() < b and a < m.end() for a, b in used):
                    continue                     # ya cubierto por otra regla de la misma categoría
                used.append((m.start(), m.end()))
                forma, sig, q_after = _context(t, m.start(), m.end(), lex)
                rest = t[m.end():].lstrip(' ,')
                if (r.no_seguido_de == 'infinitivo' and sig and _is_infinitive(sig[0]) and sig[0] not in r.salvo_si_sigue) \
                        or (r.vocativo and not _vocative(t, m.start(), m.end())) \
                        or (r.no_si_sigue_pregunta and q_after) \
                        or any(rest.startswith(x) for x in r.excepto_si_sigue):
                    desc[r.id] += 1
                    continue
                if forma == 'pregunta' and r.pregunta_cuenta:
                    forma = 'afirmativa'
                n_by_form[forma] += 1
                exprs.append((r, forma, _expr(r, m.group()), 1))
        for e in r.emojis:
            c = t.count(e)
            if c:
                n_by_form['afirmativa'] += c
                exprs.append((r, 'afirmativa', _expr(r, e), c))
        hits += [(r, f, n) for f, n in n_by_form.items()]
    otros = [c for c in EMOJI_RE.findall(t) if c not in lex.emoji_cubiertos]
    if otros:
        hits.append((OTRO_RULE, 'afirmativa', len(otros)))
        exprs += [(OTRO_RULE, 'afirmativa', c, k) for c, k in Counter(otros).items()]
    return hits, desc, exprs


def events_for_message(msg, lex):
    """Eventos del mensaje: UNO por (categoría, forma). Devuelve (eventos, descartes)."""
    hits, desc, exprs = detect_full(msg.texto, lex)
    groups = {}
    for r, f, n in hits:
        groups.setdefault((r.categoria, f), []).append((r, n))
    evs = []
    for (cat, f), lst in sorted(groups.items()):
        evs.append(Event(seq=msg.seq, linea=msg.linea_inicial, timestamp=msg.timestamp_local,
                         participante=msg.participante, categoria=cat,
                         subetiquetas=tuple(sorted({r.subetiqueta for r, _ in lst if r.subetiqueta})),
                         reglas=tuple(sorted({r.id for r, _ in lst})), forma=f,
                         ambiguo=all(r.ambiguo for r, _ in lst),
                         expresiones=tuple(sorted(Counter({x: sum(n for rr, ff, xx, n in exprs if rr.categoria == cat and ff == f and xx == x)
                                                           for x in {xx for rr, ff, xx, _ in exprs if rr.categoria == cat and ff == f}}).items())),
                         n_coincidencias=sum(n for _, n in lst),
                         clase_provisional=lst[0][0].clase_provisional))
    return evs, desc

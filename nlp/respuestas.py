"""Marcadores léxicos de la RESPUESTA a un indicador (Fase 6, paso 5). Solo vocabulario: dice qué marcadores aparecen en un
texto; la clasificación (estímulo, precedencia, familias) vive en metrics/romantic_response.py. El texto no sale de aquí."""
import os
import re

import yaml

from nlp.text import normalize

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, 'lexicon', 'respuestas_es_mx.yaml')
_START = r'(?:^|[.!?;,¡¿]\s*)'


def _rx(pat, inicio):
    toks = normalize(pat).strip(' ,!').split(' ')
    words = r'\s+'.join(re.escape(w) for w in toks)
    if inicio and len(toks) == 1:      # una sola palabra al inicio de cláusula debe CERRAR la cláusula ("sí, vamos", no "si quieres")
        return re.compile(_START + words + r'(?=\s*(?:[.,!?;]|$))')
    return re.compile((_START if inicio else r'(?<!\w)') + words + r'(?!\w)')


def load_markers(path=None):
    """{'grupos': {nombre: (regex, …, excepciones)}, 'limites': {'explicito'|'suave': [(alcance, regex)]}, 'alias': {...}}"""
    with open(path or DEFAULT_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    grupos = {}
    for name, g in (raw.get('grupos') or {}).items():
        grupos[name] = (tuple(_rx(p, bool(g.get('inicio'))) for p in g['patrones']),
                        tuple(normalize(x) for x in g.get('excepto_si_sigue', [])))
    limites = {k: [(b['alcance'], tuple(_rx(p, False) for p in b['patrones'])) for b in v]
               for k, v in (raw.get('limites') or {}).items()}
    return {'grupos': grupos, 'limites': limites, 'alcances': tuple(raw.get('alcances') or ()),
            'alias': dict(raw.get('alias_de_alcance') or {})}


def canon_alcance(valor, markers):
    """Nombre canónico de un alcance (convierte el vocabulario de etiquetas anteriores)."""
    return markers['alias'].get(valor, valor)


def markers_in(text, markers):
    """Marcadores presentes en un texto: {'grupos': {nombre, …}, 'limite_explicito': {alcance, …}, 'limite_suave': {alcance, …}}."""
    t = normalize(text or '')
    found = set()
    for name, (rxs, excep) in markers['grupos'].items():
        for rx in rxs:
            m = next((m for m in rx.finditer(t) if not any(t[m.end():].lstrip(' ,').startswith(x) for x in excep)), None)
            if m:
                found.add(name)
                break
    out = {'grupos': found}
    for tipo in ('explicito', 'suave'):
        out['limite_' + tipo] = {alc for alc, rxs in markers['limites'].get(tipo, []) if any(rx.search(t) for rx in rxs)}
    return out

"""Clasificación del cuerpo de un encabezado: aviso del sistema o mensaje de persona, y tipo final."""
from . import patterns


def split_author(body):
    """('Autor', 'texto') separando por el primer ': ', o None si no hay autor (aviso estilo Android)."""
    i = body.find(': ')
    return (body[:i], body[i + 2:]) if i > 0 else None


def classify_body(body):
    """Dict con 'es_sistema' y, según el caso:
    - sistema: 'texto' (sin el nombre antepuesto), 'clase' ('grupo'|'conocido'|'sin_catalogar'), 'codigo_grupo'.
    - persona: 'autor' y 'texto'.
    El catálogo se aplica ANTES de separar `Autor: texto`, para que un aviso con ": " (E04) no cree un autor fantasma."""
    notice = patterns.classify_notice(body)
    if notice:
        clase, codigo = notice
        return {'es_sistema': True, 'texto': body, 'clase': clase, 'codigo_grupo': codigo}
    sp = split_author(body)
    if sp is None:
        return {'es_sistema': True, 'texto': body, 'clase': 'sin_catalogar', 'codigo_grupo': None}
    autor, texto = sp
    if patterns.is_known_notice_text(texto):       # aviso conocido mostrado con un nombre antepuesto (B01)
        return {'es_sistema': True, 'texto': texto, 'clase': 'conocido', 'codigo_grupo': None}
    return {'es_sistema': False, 'autor': autor, 'texto': texto}


def person_type(texto):
    """('media', kind) | ('deleted', None) | ('texto', None): el marcador debe ser el cuerpo COMPLETO."""
    kind = patterns.media_kind(texto)
    if kind is not None:
        return 'media', kind
    if patterns.is_deleted(texto):
        return 'deleted', None
    return 'texto', None

"""Catálogo de formatos de encabezado y su reconocimiento.

Cada formato es una fila de la tabla FORMATS (editable sin tocar el resto del parser). Todos los
formatos son SIMULADOS o documentados por terceros: ninguno está observado en una exportación real
(ver docs/formatos_exportacion_whatsapp.md). Este módulo solo reconoce la FORMA del encabezado y valida
sus valores; no interpreta el orden de la fecha (eso es timestamps.py).

Los grupos con nombre de cada patrón: d1, d2 (los dos primeros números de la fecha, sin asumir cuál es
el día), y (año), H, M, S (opcional), ap (a. m./p. m./AM/PM, opcional), ts (el timestamp completo, tal
cual) y body (todo lo que sigue al encabezado).
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class FormatSpec:
    id: str
    platform: str
    pattern: re.Pattern
    twelve_hour: bool
    precision: str           # 'minuto' | 'segundo'


def _f(id_, platform, regex, twelve, precision):
    return FormatSpec(id_, platform, re.compile('^' + regex + '$'), twelve, precision)


_AND = r'(?P<ts>{ts}) - (?P<body>.*)'        # Android: "<ts> - <cuerpo>"
_IOS = r'\[(?P<ts>{ts})\] (?P<body>.*)'      # iOS: "[<ts>] <cuerpo>"
_DMY4C = r'(?P<d1>\d{1,2})/(?P<d2>\d{1,2})/(?P<y>\d{4}), '
_DMY2C = r'(?P<d1>\d{1,2})/(?P<d2>\d{1,2})/(?P<y>\d{2}), '

FORMATS = [
    _f('android_24h_coma', 'android', _AND.format(ts=_DMY4C + r'(?P<H>\d{1,2}):(?P<M>\d{2})'), False, 'minuto'),
    _f('android_24h_sin_coma', 'android', _AND.format(ts=r'(?P<d1>\d{1,2})/(?P<d2>\d{1,2})/(?P<y>\d{4}|\d{2}) (?P<H>\d{1,2}):(?P<M>\d{2})'), False, 'minuto'),
    _f('android_12h_es_nnbsp', 'android', _AND.format(ts=_DMY4C + r'(?P<H>\d{1,2}):(?P<M>\d{2}) (?P<ap>[ap]\. m\.)'), True, 'minuto'),
    _f('android_12h_compacto', 'android', _AND.format(ts=_DMY4C + r'(?P<H>\d{1,2}):(?P<M>\d{2}) (?P<ap>[ap]\.m\.)'), True, 'minuto'),
    _f('android_12h_en_mdy', 'android', _AND.format(ts=_DMY2C + r'(?P<H>\d{1,2}):(?P<M>\d{2}) (?P<ap>[AP]M)'), True, 'minuto'),
    _f('android_24h_puntos_segundos', 'android', _AND.format(ts=r'(?P<d1>\d{1,2})\.(?P<d2>\d{1,2})\.(?P<y>\d{4}), (?P<H>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2})'), False, 'segundo'),
    _f('android_24h_guiones', 'android', _AND.format(ts=r'(?P<d1>\d{1,2})-(?P<d2>\d{1,2})-(?P<y>\d{4}) (?P<H>\d{1,2}):(?P<M>\d{2})'), False, 'minuto'),
    _f('ios_24h_corchetes', 'ios', _IOS.format(ts=_DMY4C + r'(?P<H>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2})'), False, 'segundo'),
    _f('ios_12h_es_corchetes', 'ios', _IOS.format(ts=_DMY2C + r'(?P<H>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2}) (?P<ap>[ap]\. m\.)'), True, 'segundo'),
    _f('ios_12h_en_mdy_corchetes', 'ios', _IOS.format(ts=_DMY2C + r'(?P<H>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2}) (?P<ap>[AP]M)'), True, 'segundo'),
    _f('ios_24h_puntos_corchetes', 'ios', _IOS.format(ts=r'(?P<d1>\d{1,2})\.(?P<d2>\d{1,2})\.(?P<y>\d{2}), (?P<H>\d{1,2}):(?P<M>\d{2}):(?P<S>\d{2})'), False, 'segundo'),
]
BY_ID = {f.id: f for f in FORMATS}


@dataclass(frozen=True)
class Header:
    spec: FormatSpec
    ts_original: str         # tal cual está en el archivo (conserva U+202F, etc.)
    d1: int
    d2: int
    year: int
    hour: int                # ya en 24 h
    minute: int
    second: int
    time_ok: bool            # hora/minuto/segundo reales
    body: str                # texto tras el encabezado, original (sin normalizar)


def _time_ok(spec, h, m, s):
    hour_ok = (1 <= h <= 12) if spec.twelve_hour else (0 <= h <= 23)
    return hour_ok and 0 <= m <= 59 and 0 <= s <= 59


def _to_24h(h, ap):
    if ap is None:
        return h
    pm = ap[0].lower() == 'p'
    return (h % 12) + (12 if pm else 0)


def split_leading(line, cfg):
    """Quita los caracteres ignorables al inicio (solo para reconocer) y devuelve (núcleo, núcleo_normalizado).
    U+202F (y los caracteres 'space_like') se tratan como espacio ordinario en la copia normalizada; la
    sustitución es 1 a 1, así que los índices valen también para el texto original."""
    i = 0
    while i < len(line) and line[i] in cfg.ignored_leading_chars:
        i += 1
    core = line[i:]
    norm = core
    for ch in cfg.space_like_chars:
        norm = norm.replace(ch, ' ')
    return core, norm


def match_shape(spec, core, norm, cfg):
    """Header si la línea tiene la FORMA del formato (aunque sus valores sean imposibles), si no None."""
    m = spec.pattern.match(norm)
    if not m:
        return None
    g = m.groupdict()
    year = int(g['y']) + (cfg.two_digit_year_century if len(g['y']) == 2 else 0)
    h, mi, s = int(g['H']), int(g['M']), int(g['S'] or 0) if g.get('S') else 0
    ok = _time_ok(spec, h, mi, s)
    return Header(spec, core[m.start('ts'):m.end('ts')], int(g['d1']), int(g['d2']), year,
                  _to_24h(h, g.get('ap')) if ok else h, mi, s, ok, core[m.start('body'):])

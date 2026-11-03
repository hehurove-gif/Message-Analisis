"""Reconocimiento de líneas y disposición de cada una (contrato v0.2, sección 3).

Dos pasadas: (1) clasificar cada línea sin depender de las demás y elegir el formato del archivo;
(2) tras resolver el orden de la fecha, asignar la disposición definitiva y agrupar en mensajes.
Ninguna línea queda sin disposición ni se anexa por suposición."""
import re
from dataclasses import dataclass

from . import formats, timestamps

# Aspecto de timestamp: fecha n/n/n, n.n.n o n-n-n al inicio (tras un '[' opcional) y una hora h:m cerca.
_LIKE_DATE = re.compile(r'^\[?\d{1,2}([/.-])\d{1,2}\1\d{2,4}')
_LIKE_TIME = re.compile(r'\d{1,2}:\d{1,2}')

ENC, CONT, BLANK, UNP = 'encabezado', 'continuacion', 'en_blanco', 'no_procesada'


@dataclass
class RawLine:
    n: int                       # número de línea (1 = primera)
    text: str
    kind: str                    # blank | header | invalid | mismatch | like | text
    header: object = None        # formats.Header si kind in (header, invalid)


@dataclass
class Draft:
    """Mensaje en construcción: todavía sin tipo ni participante."""
    header: object
    first_line: int
    body_first: str
    cont: list                   # (n, texto) de continuaciones y blancos intermedios, en orden
    last_line: int


def looks_like_timestamp(norm, window):
    probe = norm
    return bool(_LIKE_DATE.match(probe) and _LIKE_TIME.search(probe[:window]))


def classify_lines(text_lines, cfg, spec=None):
    """Primera pasada. Con `spec=None` se clasifica contra todo el catálogo (para elegir el formato)."""
    out = []
    for n, raw in enumerate(text_lines, 1):
        if raw.strip() == '':
            out.append(RawLine(n, raw, 'blank'))
            continue
        core, norm = formats.split_leading(raw, cfg)
        hit = None
        for s in ([spec] if spec else formats.FORMATS):
            h = formats.match_shape(s, core, norm, cfg)
            if h:
                hit = h
                break
        if hit and timestamps.header_valid(hit):
            out.append(RawLine(n, raw, 'header', hit))
        elif hit:
            out.append(RawLine(n, raw, 'invalid', hit))
        elif spec and any((h2 := formats.match_shape(s, core, norm, cfg)) and timestamps.header_valid(h2)
                          for s in formats.FORMATS if s is not spec):
            out.append(RawLine(n, raw, 'mismatch'))
        elif looks_like_timestamp(norm, cfg.timestamp_like_window_chars):
            out.append(RawLine(n, raw, 'like'))
        else:
            out.append(RawLine(n, raw, 'text'))
    return out


def choose_format(first_pass):
    """(spec_id | None, motivo). Gana el formato con más encabezados válidos, estrictamente mayor al resto."""
    counts = {}
    for rl in first_pass:
        if rl.kind == 'header':
            counts[rl.header.spec.id] = counts.get(rl.header.spec.id, 0) + 1
    if not counts:
        return None, 'FORMAT_NOT_RECOGNIZED'
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return None, 'FORMAT_AMBIGUOUS'
    return ranked[0][0], None


def assemble(second_pass, order):
    """Segunda pasada: disposiciones y borradores de mensaje. `order` ya está resuelto (o es None si ambiguo).

    Devuelve (disposiciones {n: disposición}, no_procesadas [{linea, motivo}], borradores)."""
    disp, unproc, drafts = {}, [], []
    cur = None                # borrador abierto
    pending_blank = []        # líneas en blanco desde el último contenido del mensaje abierto
    seen_header = False

    def unprocessed(n, motivo):
        nonlocal cur, pending_blank
        disp[n] = UNP
        unproc.append({'linea': n, 'motivo': motivo})
        cur, pending_blank = None, []

    for rl in second_pass:
        n = rl.n
        if rl.kind == 'blank':
            disp[n] = BLANK
            if cur is not None:
                pending_blank.append((n, rl.text))
            continue
        if rl.kind == 'header' and order is not None and not timestamps.date_valid_in(rl.header, order):
            unprocessed(n, 'TIMESTAMP_INVALID')
            continue
        if rl.kind == 'header':
            seen_header = True
            cur = Draft(rl.header, n, rl.header.body, [], n)
            drafts.append(cur)
            pending_blank = []
            disp[n] = ENC
        elif rl.kind == 'invalid':
            unprocessed(n, 'TIMESTAMP_INVALID')
        elif rl.kind == 'mismatch':
            unprocessed(n, 'FORMAT_MISMATCH')
        elif rl.kind == 'like':
            unprocessed(n, 'TIMESTAMP_LIKE_UNRECOGNIZED')
        elif cur is None:
            unprocessed(n, 'ORPHAN_AFTER_UNPROCESSED' if seen_header else 'ORPHAN_BEFORE_FIRST_MESSAGE')
        else:
            cur.cont.extend(pending_blank)
            pending_blank = []
            cur.cont.append((n, rl.text))
            cur.last_line = n
            disp[n] = CONT
    return disp, unproc, drafts


def draft_text(d):
    """Texto original: primera línea + continuaciones y blancos intermedios unidos con '\\n'."""
    return '\n'.join([d.body_first] + [t for _, t in d.cont])

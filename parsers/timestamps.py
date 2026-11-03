"""Normalización de timestamps: orden de la fecha y construcción del datetime LOCAL.

No se asume zona horaria ni se convierte nada: el resultado es la hora local que escribe el archivo
(datetime ingenuo). Sin evidencia ni pista, el orden día/mes NO se elige (no hay valor por defecto).
"""
from datetime import datetime

DMY, MDY = 'dmy', 'mdy'


def _valid_date(y, month, day):
    try:
        datetime(y, month, day)
        return True
    except ValueError:
        return False


def date_valid_in(h, order):
    return _valid_date(h.year, h.d2, h.d1) if order == DMY else _valid_date(h.year, h.d1, h.d2)


def date_valid_any_order(h):
    return date_valid_in(h, DMY) or date_valid_in(h, MDY)


def header_valid(h):
    """Valores reales de hora y de fecha (en al menos un orden): lo exigible antes de conocer el orden."""
    return h.time_ok and date_valid_any_order(h)


def resolve_date_order(headers, hint=None):
    """(orden_fecha, orden o None, pista_usada) según la evidencia de los encabezados válidos.

    Un primer número > 12 solo puede ser un día (evidencia de DMY); un segundo número > 12, también
    (evidencia de MDY). Evidencias en ambos sentidos: contradictorio. Ninguna: ambiguo, y solo una pista
    explícita lo resuelve; sin pista, se bloquea."""
    dmy = any(h.d1 > 12 for h in headers)
    mdy = any(h.d2 > 12 for h in headers)
    if dmy and mdy:
        return 'contradictorio', None, False
    if dmy:
        return 'dmy_resuelto_por_dato', DMY, False
    if mdy:
        return 'mdy_resuelto_por_dato', MDY, False
    if hint in (DMY, MDY):
        return f'{hint}_por_indicacion', hint, True
    return 'ambiguo', None, False


def to_local_iso(h, order):
    """ISO 8601 sin zona (p. ej. 2026-10-14T09:12:00) o None si el orden no está resuelto."""
    if order is None:
        return None
    day, month = (h.d1, h.d2) if order == DMY else (h.d2, h.d1)
    return datetime(h.year, month, day, h.hour, h.minute, h.second).isoformat()

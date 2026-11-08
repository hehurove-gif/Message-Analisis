"""Generador determinista de chats sintéticos largos (solo para pruebas de evolución, Fase 4).

`balanceado`: ambos participantes con el mismo comportamiento durante todo el periodo (con ruido aleatorio fijado
por semilla). `enfriamiento`: igual los primeros `cool_from_month` meses; después baja la frecuencia de contacto,
B deja de abrir el día y B tarda mucho más en responder. Contenido ficticio sin datos reales."""
import random
from datetime import datetime, timedelta

from parsers import parse_text

WORDS = 'hoy salimos tarde pasa mañana vamos comer clase tarea casa trabajo película semana viernes plan'.split()


def _sentence(rng, n):
    return ' '.join(rng.choice(WORDS) for _ in range(n))


def build_text(seed=1, months=10, cool_from_month=None, p_contact=0.85, start=datetime(2025, 1, 1)):
    rng = random.Random(seed)
    lines, day = [], start
    end = start + timedelta(days=30 * months)
    while day < end:
        cooled = cool_from_month is not None and (day - start).days >= 30 * cool_from_month
        p = 0.3 if cooled else p_contact
        if rng.random() < p:
            opener = ('A' if rng.random() < 0.5 else 'B') if not cooled else ('A' if rng.random() < 0.9 else 'B')
            other = 'B' if opener == 'A' else 'A'
            t = day.replace(hour=rng.randint(9, 21), minute=rng.randint(0, 59))
            for _ in range(rng.randint(2, 4)):
                for who in (opener, other):
                    slow = cooled and who == 'B'
                    t += timedelta(minutes=rng.randint(40, 120) if slow else rng.randint(1, 3))
                    n = rng.randint(1, 3) if slow else rng.randint(3, 9)
                    lines.append((t, who, _sentence(rng, n)))
        day += timedelta(days=1)
    lines.sort(key=lambda x: x[0])
    text = '\n'.join(f"{t.day:02d}/{t.month:02d}/{t.year}, {t.strftime('%H:%M')} - {'Ana' if w == 'A' else 'Beto'}: {s}"
                     for t, w, s in lines) + '\n'
    return text


def build_chat(*args, **kwargs):
    return parse_text(build_text(*args, **kwargs), date_order_hint='dmy').messages

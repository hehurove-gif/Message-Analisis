"""Matemática de la validación por muestra (Fase 5.4): tamaño de muestra por porcentaje, reparto proporcional entre
estratos e intervalo de Wilson. Sin lectura de archivos ni de texto."""
import math
import random

import yaml

from segmentation.turns import DEFAULT_CONFIG_PATH

DEFAULTS = {'n0': 96, 'min_events': 10, 'recall_max_messages': 300, 'accept_point': 0.80, 'accept_lower': 0.70,
            'drop_point': 0.60, 'min_reviewed_rule': 10}


def load_cfg(path=None):
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    return {**DEFAULTS, **((raw.get('lexicon') or {}).get('validation') or {})}


def sample_size(N, n0=96):
    """Muestra para estimar una proporción (±10 % al 95 %) en una población finita de N eventos: n = N·n0/(n0+N−1).
    N=10 → 10, 30 → 24, 100 → 50, 500 → 81, 2000 → 92 (redondeo hacia arriba). Nunca más que N; con N<=1, N."""
    if N <= 1:
        return N
    return min(N, math.ceil(N * n0 / (n0 + N - 1)))


def wilson(k, n, z=1.96):
    """Intervalo de Wilson para k aciertos de n; (None, None) si n == 0."""
    if n == 0:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def allocate(strata, n_total):
    """Reparto proporcional de `n_total` entre estratos {clave: tamaño}, mínimo 1 por estrato y máximo su tamaño.
    Determinista (desempates por clave)."""
    total = sum(strata.values())
    n_total = min(max(n_total, len(strata)), total)
    alloc = {k: min(v, max(1, int(n_total * v / total))) for k, v in strata.items()}
    keys = sorted(strata)
    while sum(alloc.values()) > n_total:                      # recortar donde más sobra respecto a lo proporcional
        k = max((k for k in keys if alloc[k] > 1), key=lambda k: alloc[k] - n_total * strata[k] / total, default=None)
        if k is None:
            break
        alloc[k] -= 1
    while sum(alloc.values()) < n_total:                      # completar donde más falta
        cand = [k for k in keys if alloc[k] < strata[k]]
        if not cand:
            break
        k = max(cand, key=lambda k: n_total * strata[k] / total - alloc[k])
        alloc[k] += 1
    return alloc


def draw(items, k, seed, key):
    """k elementos al azar (reproducible) de `items`, devueltos en su orden original."""
    idx = sorted(random.Random(f'{seed}:{key}').sample(range(len(items)), k))
    return [items[i] for i in idx]


def systematic(items, k, seed):
    """k elementos repartidos a lo largo de la lista (paso fijo con arranque aleatorio)."""
    if k >= len(items):
        return list(items)
    step = len(items) / k
    off = random.Random(f'{seed}:rec').random() * step
    return [items[min(len(items) - 1, int(off + i * step))] for i in range(k)]


def label_category(reviewed, correct, cfg):
    if reviewed < cfg['min_events'] or reviewed == 0:
        return 'no_validada'
    p = correct / reviewed
    lo, _ = wilson(correct, reviewed)
    return 'valida' if (p >= cfg['accept_point'] or lo >= cfg['accept_lower']) else 'baja_precision'

"""Lectura de los parámetros de `parsing` en config.yaml (PyYAML es la única dependencia)."""
import os
from dataclasses import dataclass

import yaml

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.yaml')


@dataclass(frozen=True)
class ParsingConfig:
    date_order_hint: str | None = None          # None | "dmy" | "mdy". Sin valor por defecto.
    two_digit_year_century: int = 2000
    timestamp_like_window_chars: int = 40
    ignored_leading_chars: tuple = ('‎', '‏', '﻿')
    space_like_chars: tuple = (' ',)
    allow_network: bool = False                 # privacy.allow_network (ver parsers/privacy.py)

    def with_hint(self, hint):
        """Copia con otra pista de orden de fecha (la pista se pasa por llamada, no se asume)."""
        return ParsingConfig(**{**self.__dict__, 'date_order_hint': hint})


def load_config(path=None) -> ParsingConfig:
    with open(path or DEFAULT_CONFIG_PATH, encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}
    p, priv = raw.get('parsing', {}), raw.get('privacy', {})
    cfg = ParsingConfig(
        date_order_hint=p.get('date_order_hint'),
        two_digit_year_century=int(p.get('two_digit_year_century', 2000)),
        timestamp_like_window_chars=int(p.get('timestamp_like_window_chars', 40)),
        ignored_leading_chars=tuple(p.get('ignored_leading_chars', ('‎', '‏', '﻿'))),
        space_like_chars=tuple(p.get('space_like_chars', (' ',))),
        allow_network=bool(priv.get('allow_network', False)),
    )
    if cfg.date_order_hint not in (None, 'dmy', 'mdy'):
        raise ValueError('parsing.date_order_hint debe ser null, "dmy" o "mdy"')
    return cfg

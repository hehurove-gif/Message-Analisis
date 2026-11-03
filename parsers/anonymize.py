"""Anonimización de participantes: A, B, C… por orden de primera aparición.

La correspondencia nombre → etiqueta vive SOLO en memoria, en un atributo privado; no se serializa, no se
imprime (repr oculto) y no entra a ningún reporte."""


class Anonymizer:
    def __init__(self):
        self._map = {}

    def label(self, name):
        if name not in self._map:
            self._map[name] = chr(65 + len(self._map))
        return self._map[name]

    def __len__(self):
        return len(self._map)

    def mapping(self):
        """Copia de la correspondencia; solo para la persona que consume el resultado en memoria."""
        return dict(self._map)

    def __repr__(self):
        return f'Anonymizer({len(self._map)} participantes)'

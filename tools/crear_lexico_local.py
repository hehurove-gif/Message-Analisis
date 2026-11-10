"""Crea la plantilla vacía del léxico LOCAL (apodos y frases propias de un chat) junto a tus exportaciones.

    python tools/crear_lexico_local.py [CARPETA]      (por defecto: ..\\exportaciones_reales, al lado del repo)

El archivo `lexicon_local.yaml` se usa automáticamente en `metricas_local` si está en la misma carpeta que la
exportación. Nunca se versiona ni se imprime su contenido. No sobrescribe un archivo existente y se niega a
escribir dentro del repositorio."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from validar_exportacion_local import is_inside  # noqa: E402

PLANTILLA = """# Léxico LOCAL: privado, nunca se sube a git. Un patrón = palabra(s) completa(s), sin acentos da igual.
# Atajos:
apodos: []        # apelativos dirigidos al otro, p. ej. ["nombre-cariñoso"]; solo cuentan como vocativo (con puntuación o al inicio/fin)
afecto: []        # frases propias de afecto explícito
# Reglas completas (opcional), mismo esquema que lexicon/es_mx.yaml:
reglas: []
"""


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    carpeta = os.path.realpath(argv[0] if argv else os.path.join(os.path.dirname(ROOT), 'exportaciones_reales'))
    if is_inside(carpeta, os.path.realpath(ROOT)):
        sys.exit('Por privacidad el léxico local no se crea dentro del repositorio.')
    os.makedirs(carpeta, exist_ok=True)
    dest = os.path.join(carpeta, 'lexicon_local.yaml')
    if os.path.exists(dest):
        sys.exit('Ya existe lexicon_local.yaml en esa carpeta; no se sobrescribe.')
    with open(dest, 'w', encoding='utf-8') as f:
        f.write(PLANTILLA)
    print('Creado:', dest)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Diagnóstico LOCAL de por qué se detectan más (o menos) autores de los esperados, sin mostrar contenido.

Uso:  python tools/diagnostico_autores_local.py RUTA_AL_TXT

Solo LEE el archivo (que debe estar fuera del repositorio). Por cada autor detectado imprime su etiqueta
(orden de aparición), mensajes por tipo, primera y última línea donde aparece y la FORMA enmascarada de su
nombre (dígitos → 9, letras → a). Con ella se distingue, sin ver nombres, un contacto renombrado, un número
de teléfono o un aviso mal clasificado. Agrupa también por forma los avisos sin catalogar.
No imprime nombres ni texto de mensajes.
"""
import json
import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import classify, lines, load_config  # noqa: E402
from parsers import timestamps  # noqa: E402
from parsers.formats import BY_ID  # noqa: E402
from validar_exportacion_local import is_inside, mask  # noqa: E402


def diagnose(text):
    """Dict con autores y avisos sin catalogar, sin nombres ni contenido. `text` ya decodificado."""
    cfg = load_config()
    text = text.lstrip('﻿')
    tl = text.replace('\r\n', '\n').split('\n')
    if tl and tl[-1] == '':
        tl.pop()
    first = lines.classify_lines(tl, cfg)
    spec_id, err = lines.choose_format(first)
    if err:
        return {'error': err}
    second = lines.classify_lines(tl, cfg, BY_ID[spec_id])
    heads = [rl.header for rl in second if rl.kind == 'header']
    _, order, _ = timestamps.resolve_date_order(heads, cfg.date_order_hint)
    _, _, drafts = lines.assemble(second, order)
    authors, notices = {}, Counter()
    for d in drafts:
        info = classify.classify_body(d.body_first)
        if info['es_sistema']:
            if info['clase'] == 'sin_catalogar':
                notices[mask(d.body_first, 40)] += 1
            continue
        a = authors.setdefault(info['autor'], {'tipos': Counter(), 'primera': d.first_line, 'ultima': d.first_line})
        texto = '\n'.join([info['texto']] + [t for _, t in d.cont])
        a['tipos'][classify.person_type(texto)[0]] += 1
        a['ultima'] = d.first_line
    out = []
    for i, (name, a) in enumerate(authors.items()):
        digits = sum(c.isdigit() for c in name)
        out.append({'etiqueta': chr(65 + i), 'mensajes': sum(a['tipos'].values()), 'por_tipo': dict(a['tipos']),
                    'primera_linea': a['primera'], 'ultima_linea': a['ultima'],
                    'forma_nombre': mask(name, 40), 'longitud_nombre': len(name),
                    'parece_telefono': digits >= 7 and digits >= len(name) // 2})
    return {'formato': spec_id, 'autores': out,
            'avisos_sin_catalogar_por_forma': [{'forma': k, 'cantidad': v} for k, v in notices.most_common(15)]}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit(__doc__)
    real = os.path.realpath(argv[0])
    if is_inside(real, os.path.realpath(ROOT)):
        sys.exit('Por privacidad no se leen archivos dentro del repositorio. Guarda la exportación fuera de él.')
    with open(real, 'rb') as f:
        try:
            text = f.read().decode('utf-8')
        except UnicodeDecodeError:
            sys.exit('ENCODING_ERROR')
    print(json.dumps(diagnose(text), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

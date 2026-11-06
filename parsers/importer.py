"""Orquestador: bytes/archivo/texto → ImportResult. Cada paso vive en su propio módulo.

Todo ocurre en memoria. El único acceso a disco es LEER el archivo indicado (`parse_file`); no se escribe
nada. No hay red (privacy.enforce lo exige)."""
from . import classify, groups, lines, privacy, report, timestamps
from .anonymize import Anonymizer
from .config import ParsingConfig, load_config
from .results import ImportResult, Message

PERSON_TYPES = ('texto', 'media', 'deleted')


def normalize_for_analysis(text):
    """Representación derivada (contrato 4): U+202F → espacio; se eliminan U+200E, U+200F y U+FEFF.
    No sustituye a `texto`."""
    return text.replace(' ', ' ').translate({0x200E: None, 0x200F: None, 0xFEFF: None})


def _empty_result(warning, *, decoded=None, n_lines=None, disp=None):
    rep = report.build_report(
        formato=None, n_participants=0, conv_state=groups.NOT_EVALUATED, decision='rejected',
        order_state=None, n_lines=n_lines, disp=disp, unprocessed=[], messages=[], group_evidence=[],
        n_uncatalogued=0, date_range=None, n_equal_ts=0, n_out_of_order=0,
        special_chars=report.count_special_chars(decoded) if decoded else {}, warnings=[warning])
    return ImportResult(_report=rep, messages=None)


def parse_bytes(data, cfg=None, date_order_hint=None, merge_authors=None):
    cfg = cfg or load_config()
    privacy.enforce(cfg)
    if date_order_hint is not None:
        cfg = cfg.with_hint(date_order_hint)
    try:
        text = data.decode('utf-8')
    except UnicodeDecodeError:
        # Sin `from e` ni el mensaje original: la excepción incluye bytes del archivo.
        return _empty_result('ENCODING_ERROR')
    return parse_text(text, cfg, merge_authors=merge_authors)


def parse_file(path, cfg=None, date_order_hint=None, merge_authors=None):
    with open(path, 'rb') as f:        # solo lectura
        return parse_bytes(f.read(), cfg, date_order_hint, merge_authors)


def parse_text(text, cfg=None, date_order_hint=None, merge_authors=None):
    cfg = cfg or load_config()
    privacy.enforce(cfg)
    if date_order_hint is not None:
        cfg = cfg.with_hint(date_order_hint)
    special = report.count_special_chars(text)
    if text.startswith('﻿'):                 # BOM de codificación del ARCHIVO, no contenido
        text = text[1:]
    text_lines = text.replace('\r\n', '\n').split('\n')
    if text_lines and text_lines[-1] == '':       # salto de línea final: no es una línea más
        text_lines.pop()
    n_lines = len(text_lines)
    if text.strip() == '':
        return _empty_result('EMPTY_FILE', decoded=text, n_lines=n_lines,
                             disp={n: lines.BLANK for n in range(1, n_lines + 1)})

    first = lines.classify_lines(text_lines, cfg)
    spec_id, fmt_error = lines.choose_format(first)
    if fmt_error:
        return _reject_format(text_lines, fmt_error, special)

    from .formats import BY_ID
    spec = BY_ID[spec_id]
    second = lines.classify_lines(text_lines, cfg, spec)
    headers = [rl.header for rl in second if rl.kind == 'header']
    order_state, order, hint_used = timestamps.resolve_date_order(headers, cfg.date_order_hint)
    disp, unproc, drafts = lines.assemble(second, order)

    anon = Anonymizer()
    raw_msgs, authors, evidence, n_uncat = [], [], [], 0
    for d in drafts:
        info = classify.classify_body(d.body_first)
        if info['es_sistema']:
            texto = lines.draft_text(d) if info['texto'] == d.body_first else \
                '\n'.join([info['texto']] + [t for _, t in d.cont])
            if info['clase'] == 'grupo':
                evidence.append({'linea': d.first_line, 'codigo': info['codigo_grupo']})
            elif info['clase'] == 'sin_catalogar':
                n_uncat += 1
            raw_msgs.append((d, 'system', None, None, texto))
        else:
            first_text = info['texto']
            texto = '\n'.join([first_text] + [t for _, t in d.cont])
            tipo, kind = classify.person_type(texto)
            authors.append(info['autor'])
            raw_msgs.append((d, tipo, info['autor'], kind, texto))

    distinct = list(dict.fromkeys(authors))       # orden de primera aparición
    for name in distinct:                          # solo memoria; las etiquetas siguen ese orden
        anon.label(name)
    label = anon.mapping()
    suspects = alias_suspects(distinct, label, raw_msgs)
    final_of, merged = apply_merges(label, merge_authors, raw_msgs)   # decisión EXPLÍCITA del usuario
    label = {name: final_of[lab] for name, lab in label.items()}
    n_authors = len(set(label.values()))
    conv_state, warnings = groups.conversation_state(n_authors, evidence)
    if suspects:
        warnings.append('AUTHOR_ALIAS_SUSPECTED')
    if merged:
        warnings.append('AUTHORS_MERGED_BY_USER')
    if unproc:
        warnings.append('UNPROCESSED_LINES')
    if n_uncat:
        warnings.append('SYSTEM_LINES_UNCLASSIFIED')

    if order_state == 'contradictorio':
        warnings.append('DATE_ORDER_CONTRADICTORY')
    elif order_state == 'ambiguo':
        warnings.append('DATE_ORDER_AMBIGUOUS')

    messages = []
    for seq, (d, tipo, autor, kind, texto) in enumerate(raw_msgs, 1):
        h = d.header
        messages.append(Message(
            seq=seq, linea_inicial=d.first_line, linea_final=d.last_line, tipo=tipo,
            participante=label.get(autor) if autor is not None else None,
            timestamp_original=h.ts_original, timestamp_local=timestamps.to_local_iso(h, order),
            precision=h.spec.precision, texto=texto, texto_normalizado=normalize_for_analysis(texto),
            media_kind=kind))

    person = [m for m in messages if m.tipo in PERSON_TYPES]
    n_equal = sum(1 for a, b in zip(person, person[1:]) if a.timestamp_original == b.timestamp_original
                  or (a.timestamp_local and a.timestamp_local == b.timestamp_local))
    n_out = sum(1 for a, b in zip(person, person[1:])
                if a.timestamp_local and b.timestamp_local and b.timestamp_local < a.timestamp_local)
    if n_out:
        warnings.append('TIMESTAMPS_OUT_OF_ORDER')
    stamps = [m.timestamp_local for m in person if m.timestamp_local]
    date_range = {'primero': min(stamps), 'ultimo': max(stamps)} if stamps else None   # ISO: orden léxico = cronológico

    if order_state == 'contradictorio' or conv_state.startswith('rejected'):
        decision = 'rejected'
    elif order_state == 'ambiguo':
        decision = 'blocked_pending_confirmation'
    else:
        decision = 'accepted'
    if order_state == 'contradictorio':
        conv_state = groups.NOT_EVALUATED

    rep = report.build_report(
        formato=spec_id, n_participants=n_authors, conv_state=conv_state, decision=decision,
        order_state=order_state, n_lines=n_lines, disp=disp, unprocessed=unproc, messages=messages,
        group_evidence=evidence, n_uncatalogued=n_uncat, date_range=date_range, n_equal_ts=n_equal,
        n_out_of_order=n_out, special_chars=special, warnings=warnings,
        extra={'autores_alias_sospechosos': suspects, 'autores_unidos': merged})
    return ImportResult(_report=rep, messages=tuple(messages) if decision == 'accepted' else None,
                        _anonymization=label)


def alias_suspects(distinct, label, raw_msgs):
    """Autores cuyo nombre es `<prefijo> - <nombre de otro autor>`: posible alias o encabezado con prefijo
    extra. Solo se REPORTA (por etiqueta, con las líneas donde aparece); nunca se une automáticamente."""
    out = []
    for x in distinct:
        for y in distinct:
            if x != y and x.endswith(' - ' + y) and len(x) > len(y) + 3:
                lines_ = [d.first_line for d, _t, a, _k, _x in raw_msgs if a == x]
                out.append({'etiqueta': label[x], 'posible_de': label[y], 'mensajes': len(lines_),
                            'lineas': lines_[:20]})
                break
    return out


def apply_merges(label, merge_authors, raw_msgs):
    """(etiqueta→etiqueta final, lista de uniones aplicadas). `merge_authors` = {'C': 'B'}: etiquetas del
    reporte de una importación previa. Se valida y se registra; sin él, cada etiqueta es su propia final."""
    labels = set(label.values())
    final = {lab: lab for lab in labels}
    merged = []
    for src, dst in (merge_authors or {}).items():
        if src not in labels or dst not in labels or src == dst or dst in (merge_authors or {}):
            raise ValueError('unión de autores inválida: usa etiquetas existentes, distintas y sin encadenar')
        final[src] = dst
        names = [n for n, lab in label.items() if lab == src]
        lines_ = [d.first_line for d, _t, a, _k, _x in raw_msgs if a in names]
        merged.append({'de': src, 'a': dst, 'mensajes': len(lines_), 'lineas': lines_[:20]})
    return final, merged


def _reject_format(text_lines, motivo, special):
    disp, unproc = {}, []
    for n, raw in enumerate(text_lines, 1):
        if raw.strip() == '':
            disp[n] = lines.BLANK
        else:
            disp[n] = lines.UNP
            unproc.append({'linea': n, 'motivo': motivo})
    rep = report.build_report(
        formato=None, n_participants=0, conv_state=groups.NOT_EVALUATED, decision='rejected',
        order_state=None, n_lines=len(text_lines), disp=disp, unprocessed=unproc, messages=[],
        group_evidence=[], n_uncatalogued=0, date_range=None, n_equal_ts=0, n_out_of_order=0,
        special_chars=special, warnings=[motivo])
    return ImportResult(_report=rep, messages=None)

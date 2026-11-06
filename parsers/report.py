"""Reporte de calidad de importación (contrato v0.2, sección 9).

Solo números, códigos y números de línea: nunca nombres ni texto de mensajes."""
from collections import Counter

SPECIAL_CHARS = {'U+200E': '‎', 'U+200F': '‏', 'U+202F': ' ', 'U+FEFF': '﻿'}

REJECTING = {'EMPTY_FILE', 'ENCODING_ERROR', 'FORMAT_NOT_RECOGNIZED', 'FORMAT_AMBIGUOUS',
             'DATE_ORDER_CONTRADICTORY'}


def count_special_chars(text):
    counts = {name: text.count(ch) for name, ch in SPECIAL_CHARS.items()}
    return {k: v for k, v in counts.items() if v}


def disposition_counts(disp):
    c = Counter(disp.values())
    return {k: c.get(k, 0) for k in ('encabezado', 'continuacion', 'en_blanco', 'no_procesada')}


def type_counts(messages):
    c = Counter(m.tipo for m in messages)
    return {k: c.get(k, 0) for k in ('texto', 'media', 'system', 'deleted')}


def quality_state(decision, n_unprocessed):
    if decision == 'rejected':
        return 'rechazado'
    if decision == 'blocked_pending_confirmation':
        return 'bloqueado'
    return 'pendiente_revision_calidad' if n_unprocessed else 'sin_observaciones_de_calidad'


def requirements(decision, n_unprocessed):
    """Lo que falta para habilitar el análisis. El parser nunca lo habilita por sí mismo."""
    if decision == 'rejected':
        return []
    if decision == 'blocked_pending_confirmation':
        return ['INDICAR_ORDEN_FECHA']
    req = ['CONFIRMAR_TIPO_CONVERSACION']
    if n_unprocessed:
        req.append('REVISAR_LINEAS_NO_PROCESADAS')
    return req


def build_report(*, formato, n_participants, conv_state, decision, order_state, n_lines, disp, unprocessed,
                 messages, group_evidence, n_uncatalogued, date_range, n_equal_ts, n_out_of_order,
                 special_chars, warnings, extra=None):
    n_unp = len(unprocessed)
    rep = {
        'formato_esperado': formato,
        'decision_importacion': decision,
        'estado_tipo_conversacion': conv_state,
        'orden_fecha': order_state,
        'participantes_detectados': n_participants,
        'lineas_totales': n_lines,
        'lineas_por_disposicion': None if disp is None else disposition_counts(disp),
        'mensajes_por_tipo': type_counts(messages),
        'lineas_no_procesadas': list(unprocessed),
        'evidencias_grupo': list(group_evidence),
        'avisos_sistema_sin_catalogar': n_uncatalogued,
        'rango_fechas': date_range,
        'timestamps_consecutivos_iguales': n_equal_ts,
        'timestamps_fuera_de_orden': n_out_of_order,
        'caracteres_especiales_en_archivo': special_chars,
        'advertencias': sorted(set(warnings)),
        'procesamiento_completo': decision == 'accepted' and n_unp == 0,
        'estado_calidad': quality_state(decision, n_unp),
        'analisis_habilitado': False,
        'requisitos_analisis': requirements(decision, n_unp),
    }
    rep.update(extra or {})
    return rep

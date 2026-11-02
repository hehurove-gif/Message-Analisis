"""Generador de fixtures SINTÉTICOS de exportaciones de WhatsApp (NO es el parser).

Por qué existe: los caracteres invisibles (U+200E, U+200F, U+202F, BOM) no se ven en un
editor; aquí se escriben con escapes explícitos. Cada fixture se declara como una lista
de líneas con su INTENCIÓN (encabezado de mensaje, aviso del sistema, continuación,
línea en blanco, línea no procesable). Los resultados esperados (.esperado.json) se
derivan de esa declaración, no de interpretar el texto generado: son lo que el parser
DEBERÍA producir según docs/contrato_parser.md.

Todos los formatos son SIMULADOS. Ver docs/formatos_exportacion_whatsapp.md para el
respaldo (o la falta de él) de cada uno. Nombres, fechas y contenidos son ficticios.

Uso (desde la raíz del repositorio):
    python3 -I tools/fixtures/generar_fixtures_whatsapp.py
"""
import json, os
from collections import Counter
from datetime import datetime as D

LRM, RLM, NNBSP, BOM = '‎', '‏', ' ', '﻿'
INVISIBLES = {'U+200E': LRM, 'U+200F': RLM, 'U+202F': NNBSP, 'U+FEFF': BOM}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'tests', 'fixtures', 'whatsapp')


# ---------------------------------------------------------------- formatos simulados
def h12(d): return (d.hour % 12) or 12


FORMATOS = {
    # id: (ts_original(d), prefijo(ts), precisión, orden_fecha_declarado, 24h/12h)
    'android_24h_coma': (lambda d: f"{d:%d/%m/%Y}, {d:%H:%M}", lambda t: t + ' - ', 'minuto'),
    'android_24h_sin_coma': (lambda d: f"{d:%d/%m/%y} {d:%H:%M}", lambda t: t + ' - ', 'minuto'),
    'android_12h_es_nnbsp': (lambda d: f"{d:%d/%m/%Y}, {h12(d)}:{d:%M}{NNBSP}{'a. m.' if d.hour < 12 else 'p. m.'}", lambda t: t + ' - ', 'minuto'),
    'android_12h_compacto': (lambda d: f"{d:%d/%m/%Y}, {h12(d)}:{d:%M} {'a.m.' if d.hour < 12 else 'p.m.'}", lambda t: t + ' - ', 'minuto'),
    'android_12h_en_mdy': (lambda d: f"{d.month}/{d.day}/{d:%y}, {h12(d)}:{d:%M} {'AM' if d.hour < 12 else 'PM'}", lambda t: t + ' - ', 'minuto'),
    'android_24h_puntos_segundos': (lambda d: f"{d:%d.%m.%Y}, {d:%H:%M:%S}", lambda t: t + ' - ', 'segundo'),
    'android_24h_guiones': (lambda d: f"{d:%d-%m-%Y} {d:%H:%M}", lambda t: t + ' - ', 'minuto'),
    'ios_24h_corchetes': (lambda d: f"{d:%d/%m/%Y}, {d:%H:%M:%S}", lambda t: '[' + t + '] ', 'segundo'),
    'ios_12h_es_corchetes': (lambda d: f"{d:%d/%m/%y}, {h12(d)}:{d:%M}:{d:%S} {'a. m.' if d.hour < 12 else 'p. m.'}", lambda t: '[' + t + '] ', 'segundo'),
    'ios_12h_en_mdy_corchetes': (lambda d: f"{d.month}/{d.day}/{d:%y}, {h12(d)}:{d:%M}:{d:%S}{NNBSP}{'AM' if d.hour < 12 else 'PM'}", lambda t: '[' + t + '] ', 'segundo'),
    'ios_24h_puntos_corchetes': (lambda d: f"{d:%d.%m.%y}, {d:%H:%M:%S}", lambda t: '[' + t + '] ', 'segundo'),
}


# ---------------------------------------------------------------- DSL de líneas
def m(d, autor, texto, tipo='texto', **kw):      # mensaje atribuido a una persona
    return dict(k='m', d=d, autor=autor, texto=texto, tipo=tipo, **kw)
def s(d, texto, **kw):                           # aviso del sistema SIN autor (estilo Android)
    return dict(k='s', d=d, texto=texto, **kw)
def sa(d, autor, texto, **kw):                   # aviso del sistema que el archivo muestra con nombre (estilo iOS, a verificar)
    return dict(k='sa', d=d, autor=autor, texto=texto, **kw)
def c(texto): return dict(k='c', texto=texto)    # continuación de la línea anterior
def b(): return dict(k='b')                      # línea en blanco
def u(raw, motivo): return dict(k='u', raw=raw, motivo=motivo)   # no procesable: se declara, no se anexa


def construir(nombre, fmt, items, bom=False, crlf=False, orden_fecha='dmy_resuelto_por_dato',
              decision='accepted', tipo_conv='pending_confirmation', advertencias=(), notas='',
              limitacion=None, base='simulado', formato_id=None):
    ts_f, pre_f, prec = FORMATOS[fmt] if fmt else (None, None, None)
    lineas, msgs, cur = [], [], None
    disp = Counter(); ev_grupo = []; no_proc = []
    def cerrar():
        nonlocal cur
        if cur is None: return
        cuerpo = list(cur['cuerpo'])
        while cuerpo and cuerpo[-1][1] == '': cuerpo.pop()
        cur['linea_final'] = cuerpo[-1][0] if cuerpo else cur['linea_inicial']
        cur['texto'] = '\n'.join(t for _, t in cuerpo) if cuerpo else ''
        cur.pop('cuerpo'); msgs.append(cur); cur = None
    for it in items:
        n = len(lineas) + 1
        k = it['k']
        if k in ('m', 's', 'sa'):
            cerrar()
            ts = ts_f(it['d']); pre = pre_f(ts)
            lead = it.get('lead', '')
            cuerpo0 = (it['autor'] + ': ' if k in ('m', 'sa') else '') + it['texto']
            lineas.append(lead + pre + cuerpo0)
            disp['encabezado'] += 1
            cur = dict(linea_inicial=n, tipo=('system' if k in ('s', 'sa') else it['tipo']),
                       autor_archivo=it.get('autor'), timestamp_original=ts, d=it['d'],
                       cuerpo=[(n, it['texto'])], media_kind=it.get('media_kind'))
            if it.get('grupo'): ev_grupo.append(dict(linea=n, codigo=it['grupo']))
            if it.get('conocido_no_grupo'): cur['sistema_clase'] = 'conocido_no_grupo'
            elif k in ('s', 'sa'): cur['sistema_clase'] = 'grupo' if it.get('grupo') else 'sin_catalogar'
        elif k == 'c':
            assert cur is not None, f'{nombre}: continuación sin mensaje abierto (línea {n})'
            lineas.append(it['texto']); disp['continuacion'] += 1; cur['cuerpo'].append((n, it['texto']))
        elif k == 'b':
            lineas.append(''); disp['en_blanco'] += 1
            if cur is not None: cur['cuerpo'].append((n, ''))
        elif k == 'u':
            cerrar()
            lineas.append(it['raw']); disp['no_procesada'] += 1
            no_proc.append(dict(linea=n, motivo=it['motivo']))
    cerrar()
    assert sum(disp.values()) == len(lineas), nombre
    personas = [x for x in msgs if x['tipo'] != 'system']
    autores = []
    for x in personas:
        if x['autor_archivo'] not in autores: autores.append(x['autor_archivo'])
    mapa = {a: chr(65 + i) for i, a in enumerate(autores)}
    ambiguo = orden_fecha in ('ambiguo', 'contradictorio')
    por_tipo = Counter(x['tipo'] for x in msgs)
    desc = sum(1 for p, q in zip(personas, personas[1:]) if q['d'] < p['d'])
    mismos = sum(1 for p, q in zip(personas, personas[1:]) if q['d'] == p['d'])
    texto_archivo = '\n'.join(lineas) + '\n' if lineas else ''
    if bom: texto_archivo = BOM + texto_archivo
    chars = {cod: texto_archivo.count(ch) for cod, ch in INVISIBLES.items() if texto_archivo.count(ch)}
    sist_sin_cat = sum(1 for x in msgs if x['tipo'] == 'system' and x.get('sistema_clase') == 'sin_catalogar')
    adv = list(advertencias)
    if no_proc and 'UNPROCESSED_LINES' not in adv: adv.append('UNPROCESSED_LINES')
    emitir = decision == 'accepted'
    def norm(t):
        for ch in (LRM, RLM, BOM): t = t.replace(ch, '')
        return t.replace(NNBSP, ' ')
    exp = dict(
        fixture=nombre, origen=base, formato_esperado=formato_id or fmt,
        decision_importacion=decision, estado_tipo_conversacion=tipo_conv, orden_fecha=orden_fecha,
        participantes_detectados=len(autores), mapa_anonimizacion_esperado=mapa,
        lineas_totales=len(lineas), lineas_por_disposicion={k_: disp.get(k_, 0) for k_ in ('encabezado', 'continuacion', 'en_blanco', 'no_procesada')},
        mensajes_por_tipo={t: por_tipo.get(t, 0) for t in ('texto', 'media', 'system', 'deleted')},
        lineas_no_procesadas=no_proc, evidencias_grupo=ev_grupo,
        avisos_sistema_sin_catalogar=sist_sin_cat,
        rango_fechas=(None if (not personas or ambiguo) else dict(primero=min(x['d'] for x in personas).isoformat(), ultimo=max(x['d'] for x in personas).isoformat())),
        timestamps_consecutivos_iguales=mismos, timestamps_fuera_de_orden=desc,
        caracteres_normalizados=chars, advertencias=sorted(adv), notas=notas,
    )
    if limitacion: exp['limitacion_conocida'] = limitacion
    if emitir:
        exp['mensajes_esperados'] = [dict(
            seq=i + 1, linea_inicial=x['linea_inicial'], linea_final=x['linea_final'], tipo=x['tipo'],
            participante=(mapa[x['autor_archivo']] if x['tipo'] != 'system' else None),
            timestamp_original=x['timestamp_original'], timestamp_local=x['d'].isoformat(),
            precision=prec, texto=norm(x['texto']),
            **({'media_kind': x['media_kind']} if x.get('media_kind') else {}))
            for i, x in enumerate(msgs)]
    else:
        exp['mensajes_esperados'] = None
    os.makedirs(OUT, exist_ok=True)
    contenido = texto_archivo.replace('\n', '\r\n') if crlf else texto_archivo
    with open(os.path.join(OUT, nombre + '.txt'), 'w', encoding='utf-8', newline='') as f:
        f.write(contenido)
    with open(os.path.join(OUT, nombre + '.esperado.json'), 'w', encoding='utf-8') as f:
        json.dump(exp, f, ensure_ascii=False, indent=2); f.write('\n')
    return exp


def crudo(nombre, contenido, **exp):
    """Archivos que no siguen ningún formato (o vacíos): se escriben tal cual."""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, nombre + '.txt'), 'w', encoding='utf-8', newline='') as f: f.write(contenido)
    lines = contenido.split('\n')
    if lines and lines[-1] == '': lines.pop()
    exp = dict(fixture=nombre, origen='simulado', lineas_totales=len(lines), **exp)
    with open(os.path.join(OUT, nombre + '.esperado.json'), 'w', encoding='utf-8') as f:
        json.dump(exp, f, ensure_ascii=False, indent=2); f.write('\n')


AM, JL, CR = 'Ana María', 'José Luis', 'Carlos Ruiz'
EMMA, LIAM = 'Emma Clark', 'Liam Brooks'
CIFR_ES = 'Los mensajes y las llamadas están cifrados de extremo a extremo. Nadie fuera de este chat, ni siquiera WhatsApp, puede leerlos ni escucharlos. Toca para obtener más información.'
CIFR_EN = 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them. Learn more.'
def t(dia, h, mi, s_=0, mes=10, anio=2026): return D(anio, mes, dia, h, mi, s_)

if __name__ == '__main__':
    # ---------- A. Formatos ----------
    construir('A01_android24_coma_es', 'android_24h_coma', [
        s(t(14, 9, 12), CIFR_ES, conocido_no_grupo=True),
        m(t(14, 9, 12), AM, 'Buenos días 😊'),
        m(t(14, 9, 14), JL, 'Hola, ¿qué tal? ¿Todo bien en casa?'),
        m(t(14, 9, 15), AM, 'Me dijo: "no hay problema, ya lo vi"'),
        m(t(14, 9, 16), JL, 'Te mando la lista:'), c('- pan'), c('- leche'), c('- café ☕'),
        m(t(14, 9, 20), AM, '<Multimedia omitido>', 'media', media_kind='desconocido'),
        m(t(14, 9, 21), JL, 'Se eliminó este mensaje', 'deleted'),
        m(t(14, 23, 59), JL, 'Buenas noches'),
        m(t(15, 0, 1), AM, '¡Buenas noches! 🙂❤️'),
    ], notas='Formato base con coma. Cubre texto, multilínea, media, eliminado, aviso de cifrado, cambio de día y emojis.')
    construir('A02_android24_sin_coma_anio2', 'android_24h_sin_coma', [
        m(t(14, 9, 5), AM, '¿Mañana a las 10:30 en la biblioteca?'),
        m(t(14, 9, 7), JL, 'Sí, llevo el café ☕ y la laptop 👩‍💻'),
        m(t(14, 9, 8), JL, 'Ñoño, ¡no olvides la tarea!'),
        m(t(14, 9, 9), AM, 'Jaja, ok. Gracias, José 🙏'),
    ], notas='Sin coma tras la fecha y año de 2 dígitos. Es la variante que usan los chats de data/synthetic. Incluye secuencia con ZWJ (👩‍💻).',
        formato_id='android_24h_sin_coma')
    construir('A03_android12_es_nnbsp', 'android_12h_es_nnbsp', [
        s(t(14, 9, 5), CIFR_ES, conocido_no_grupo=True),
        m(t(14, 9, 5), AM, 'Buen día'),
        m(t(14, 12, 0), JL, 'Ya es mediodía'),
        m(t(14, 12, 30), AM, 'Voy a comer'),
        m(t(14, 23, 59), JL, 'Última del día'),
        m(t(15, 0, 0), AM, 'Medianoche exacta'),
        m(t(15, 0, 1), JL, 'Ya es otro día'),
    ], notas='12 h con "a. m."/"p. m." y U+202F antes del indicador. 12:00 p. m. = 12:00; 12:00 a. m. = 00:00 del día siguiente.')
    construir('A04_android12_compacto', 'android_12h_compacto', [
        m(t(14, 9, 5), AM, 'Hola'),
        m(t(14, 12, 0), JL, 'Mediodía'),
        m(t(14, 23, 59), AM, 'Casi medianoche'),
        m(t(15, 0, 0), JL, 'Medianoche'),
    ], notas='Indicadores "a.m."/"p.m." sin espacios internos y con espacio normal antes del indicador.')
    construir('A05_android12_en_mdy', 'android_12h_en_mdy', [
        s(t(14, 9, 5), CIFR_EN, conocido_no_grupo=True),
        m(t(14, 9, 5), EMMA, 'Good morning!'),
        m(t(14, 9, 6), LIAM, 'Morning. Did you see this?'),
        m(t(14, 9, 7), EMMA, '<Media omitted>', 'media', media_kind='desconocido'),
        m(t(14, 9, 8), LIAM, 'You deleted this message', 'deleted'),
        m(t(14, 21, 30), EMMA, 'This message was deleted', 'deleted'),
        m(t(15, 8, 0), LIAM, 'See you at 8:00 PM'),
    ], orden_fecha='mdy_resuelto_por_dato',
        notas='Mes/día/año con AM/PM. El día 14 en segunda posición fija el orden como mes/día. Mensajes eliminados y multimedia en inglés.')
    construir('A06_android24_puntos_segundos', 'android_24h_puntos_segundos', [
        m(t(14, 9, 12, 5), AM, 'Con segundos'),
        m(t(14, 9, 12, 40), JL, 'Respuesta'),
        m(t(14, 9, 13, 1), AM, 'Otra'),
    ], notas='Separador de fecha ".", con segundos (precisión de segundo) y coma tras la fecha.')
    construir('A07_android24_guiones', 'android_24h_guiones', [
        m(t(14, 9, 12), AM, 'Fecha con guiones'),
        m(t(14, 9, 13), JL, 'Respuesta'),
        m(t(14, 9, 14), AM, 'Otra'),
    ], notas='Separador de fecha "-" sin coma. Variante SIN respaldo en las fuentes consultadas; se mantiene para probar tolerancia de separadores.')
    construir('A08_android24_adjuntos_es', 'android_24h_coma', [
        m(t(14, 9, 12), AM, 'IMG-20261014-WA0001.jpg (archivo adjunto)', 'media', media_kind='imagen'),
        m(t(14, 9, 13), JL, '<Multimedia omitido>', 'media', media_kind='desconocido'),
        m(t(14, 9, 14), AM, 'Mira esa foto'),
    ], notas='Exportación con adjuntos: el TXT solo enseña el nombre del archivo; el parser no lee los adjuntos (fuera de alcance del MVP).',
        formato_id='android_24h_coma')
    construir('B01_ios24_corchetes', 'ios_24h_corchetes', [
        sa(t(14, 9, 12, 0), JL, CIFR_ES, lead=LRM, conocido_no_grupo=True),
        m(t(14, 9, 12, 5), AM, 'Hola 😊'),
        m(t(14, 9, 13, 20), JL, LRM + 'imagen omitida', 'media', lead=LRM, media_kind='imagen'),
        m(t(14, 9, 14, 2), AM, LRM + 'sticker omitido', 'media', lead=LRM, media_kind='sticker'),
        m(t(14, 9, 15, 11), JL, LRM + 'audio omitido', 'media', lead=LRM, media_kind='audio'),
        m(t(14, 9, 16, 0), AM, LRM + 'documento omitido', 'media', lead=LRM, media_kind='documento'),
        m(t(14, 9, 17, 30), JL, LRM + 'Se eliminó este mensaje.', 'deleted'),
        m(t(14, 9, 18, 45), AM, 'Primera línea'), c('Segunda línea: con dos puntos'),
    ], notas='iOS con corchetes y 24 h. El aviso de cifrado aparece con nombre de persona (hipótesis a verificar con una exportación real): debe tratarse como system, sin autor. Las líneas con LRM al inicio deben reconocerse.')
    construir('B02_ios12_es_corchetes', 'ios_12h_es_corchetes', [
        m(t(14, 9, 12, 5), AM, 'Buen día'),
        m(t(14, 12, 0, 1), JL, 'Mediodía'),
        m(t(14, 23, 59, 59), AM, 'Antes de medianoche'),
        m(t(15, 0, 0, 0), JL, 'Medianoche'),
    ], notas='iOS 12 h con año de 2 dígitos, segundos y "a. m."/"p. m." con espacio normal.')
    construir('B03_ios12_en_mdy_corchetes', 'ios_12h_en_mdy_corchetes', [
        m(t(14, 9, 12, 5), EMMA, 'Morning'),
        m(t(14, 12, 0, 1), LIAM, 'Noon'),
        m(t(14, 23, 59, 59), EMMA, 'Late'),
        m(t(15, 0, 0, 0), LIAM, 'Midnight'),
    ], orden_fecha='mdy_resuelto_por_dato',
        notas='Mes/día/año con AM/PM y U+202F antes del indicador, entre corchetes (la familia que documenta chatpack, con U+202F simulado).')
    construir('B04_ios24_puntos_corchetes', 'ios_24h_puntos_corchetes', [
        m(t(14, 9, 12, 5), AM, 'Fecha con puntos'),
        m(t(14, 9, 13, 5), JL, 'Respuesta'),
        m(t(14, 9, 14, 5), AM, 'Otra'),
    ], notas='Formato europeo con puntos y corchetes (documentado por chatpack como "EU").')
    # ---------- B. Fechas ----------
    construir('C01_fecha_ambigua', 'android_24h_coma', [
        m(t(3, 9, 12), AM, 'Todos los días son menores de 13'),
        m(t(4, 9, 14), JL, 'Respuesta'),
        m(t(5, 9, 15), AM, 'Otra'),
    ], orden_fecha='ambiguo', decision='blocked_pending_confirmation',
        advertencias=['DATE_ORDER_AMBIGUOUS'],
        notas='03/10, 04/10 y 05/10 son válidos como día/mes y como mes/día. Sin evidencia ni indicación del usuario, el parser no elige: no emite timestamps normalizados.')
    construir('C02_fecha_orden_contradictorio', 'android_24h_coma', [
        m(t(14, 9, 12), AM, 'Día primero'),
        m(t(14, 9, 13), JL, 'Respuesta'),
    ], orden_fecha='contradictorio', decision='rejected', tipo_conv='not_evaluated', advertencias=['DATE_ORDER_CONTRADICTORY'],
        notas='Se sustituye abajo una línea por "10/14/2026" (mes primero) para que el mismo archivo contenga evidencia de ambos órdenes.')
    # C02 requiere una línea con mes primero: se reescribe a mano
    p = os.path.join(OUT, 'C02_fecha_orden_contradictorio.txt')
    txt = open(p, encoding='utf-8').read().replace('14/10/2026, 09:13', '10/14/2026, 09:13')
    open(p, 'w', encoding='utf-8', newline='').write(txt)
    construir('C03_cambio_de_dia_mes_anio', 'android_24h_coma', [
        m(t(14, 23, 58), AM, 'Fin del día'),
        m(t(15, 0, 0), JL, 'Nuevo día'),
        m(t(31, 23, 59), AM, 'Fin de mes'),
        m(t(1, 0, 1, mes=11), JL, 'Nuevo mes'),
        m(t(31, 23, 59, mes=12), AM, 'Fin de año'),
        m(t(1, 0, 0, mes=1, anio=2027), JL, 'Feliz año'),
    ], notas='Cambios de día, de mes y de año.')
    # ---------- C. Casos especiales ----------
    construir('D01_invisibles_bom', 'android_24h_coma', [
        s(t(14, 9, 12), LRM + CIFR_ES, conocido_no_grupo=True, lead=LRM),
        m(t(14, 9, 12), AM, 'Texto con marca LRM ' + LRM + 'en medio'),
        m(t(14, 9, 13), JL, 'Nos vemos a las 5' + NNBSP + 'p. m.'),
        m(t(14, 9, 14), AM, RLM + 'مرحبا' + RLM + ' (árabe con RLM)'),
        m(t(14, 9, 15), JL, 'Línea final'),
    ], bom=True, notas='BOM al inicio del archivo (línea 1), U+200E al inicio de línea y dentro del texto, U+200F, y U+202F dentro del texto. El BOM no debe impedir reconocer la primera línea.')
    construir('D02_timestamps_iguales', 'android_24h_coma', [
        m(t(14, 10, 0), AM, 'Uno'), m(t(14, 10, 0), JL, 'Dos'), m(t(14, 10, 0), AM, 'Tres'),
        m(t(14, 10, 1), JL, 'Cuatro'), m(t(14, 10, 1), JL, 'Cinco'),
    ], notas='Con precisión de minuto es normal que varios mensajes compartan timestamp. Se conserva el orden del archivo (seq); no se reordena.')
    construir('D03_ios_mismo_segundo', 'ios_24h_corchetes', [
        m(t(14, 9, 12, 5), AM, 'A'), m(t(14, 9, 12, 5), AM, 'B'), m(t(14, 9, 12, 5), JL, 'C'),
        m(t(14, 9, 12, 6), JL, 'D'),
    ], notas='Mensajes en el mismo segundo, incluso de autores distintos.')
    construir('D04_fuera_de_orden', 'android_24h_coma', [
        m(t(14, 9, 10), AM, 'Primero'), m(t(14, 9, 20), JL, 'Segundo'),
        m(t(14, 9, 15), AM, 'Retrocede 5 minutos'), m(t(14, 9, 30), JL, 'Sigue'),
        m(t(13, 9, 40), AM, 'Retrocede un día'),
    ], advertencias=['TIMESTAMPS_OUT_OF_ORDER'],
        notas='Dos retrocesos entre mensajes consecutivos. El parser no reordena ni corrige: reporta.')
    construir('D05_sistema_1a1', 'android_24h_coma', [
        s(t(14, 9, 0), CIFR_ES, conocido_no_grupo=True),
        s(t(14, 9, 1), 'Los mensajes temporales están activados. Los mensajes nuevos desaparecerán de este chat después de 24 horas.', conocido_no_grupo=True),
        s(t(14, 9, 2), 'Ana María cambió su número de teléfono. Toca para chatear con el número nuevo.', conocido_no_grupo=True),
        m(t(14, 9, 3), AM, 'Hola, soy yo con número nuevo'),
        m(t(14, 9, 4), JL, 'Anotado'),
    ], notas='Avisos del sistema propios de chats individuales: no son evidencia de grupo. Dos autores y ninguna evidencia: tipo pendiente de confirmación.')
    construir('D06_contenido_especial', 'android_24h_coma', [
        m(t(14, 9, 0), AM, 'Hora: 10:30, lugar: aula 5'),
        m(t(14, 9, 1), JL, 'https://ejemplo.mx/a?x=1:2&y="3"'),
        m(t(14, 9, 2), AM, '“comillas curvas” \'simples\' "dobles"'),
        m(t(14, 9, 3), JL, 'Te mandé <Multimedia omitido> por error'),
        m(t(14, 9, 4), AM, '😂😂😂'),
        m(t(14, 9, 5), JL, 'Primer párrafo'), b(), c('Segundo párrafo tras línea en blanco'),
        m(t(14, 9, 6), AM, 'Recuerden:'), c('14/10/2026 fue el cumpleaños de mamá'),
        m(t(14, 9, 7), JL, '.'),
        m(t(14, 9, 8), AM, 'Con\ttabulador'),
    ], notas='Un mensaje cuyo cuerpo contiene "<Multimedia omitido>" pero no es solo eso es texto. Una continuación que empieza con una fecha SIN hora no parece encabezado y se anexa. La línea en blanco entre párrafos se conserva en el texto.')
    construir('D07_lineas_desconocidas', 'android_24h_coma', [
        u('Exportado el 14 de octubre desde WhatsApp', 'ORPHAN_BEFORE_FIRST_MESSAGE'),
        m(t(14, 9, 10), AM, 'Hola'),
        m(t(14, 9, 11), JL, 'Qué tal'),
        u('14-10-2026 09:12 > Ana María: separadores desconocidos', 'TIMESTAMP_LIKE_UNRECOGNIZED'),
        u('esta línea sigue a una no procesada y no debe unirse al mensaje anterior', 'ORPHAN_AFTER_UNPROCESSED'),
        m(t(14, 9, 13), AM, 'Mensaje normal'),
        u('31/02/2026, 10:00 - Ana María: fecha imposible', 'TIMESTAMP_INVALID'),
        u('14/10/2026, 25:61 - José Luis: hora imposible', 'TIMESTAMP_INVALID'),
        u('14/10/2026, 09:3 - Ana María: minutos malformados', 'TIMESTAMP_LIKE_UNRECOGNIZED'),
        u('[14/10/2026, 09:14:00] José Luis: encabezado iOS en archivo Android', 'FORMAT_MISMATCH'),
        m(t(14, 9, 15), JL, 'Primer renglón'), c('Segundo renglón legítimo'),
        u('14/10/2026 a las 10:30 se movió la cita', 'TIMESTAMP_LIKE_UNRECOGNIZED'),
        u('renglón posterior sin timestamp', 'ORPHAN_AFTER_UNPROCESSED'),
        m(t(14, 9, 16), AM, 'Último mensaje válido'),
    ], notas='Ninguna de las 9 líneas no procesadas se anexa a un mensaje. "14/10/2026 a las 10:30 ..." podría ser una continuación legítima, pero tiene aspecto de timestamp (fecha + hora al inicio): se reporta, no se adivina.')
    construir('D08_crlf_lineas_en_blanco', 'android_24h_coma', [
        b(),
        m(t(14, 9, 0), AM, 'Archivo con saltos CRLF'),
        m(t(14, 9, 1), JL, 'Con párrafos'), c('uno'), b(), c('dos'), b(), b(),
        m(t(14, 9, 2), AM, 'Penúltimo'),
        m(t(14, 9, 3), JL, 'Último'), b(), b(),
    ], crlf=True, notas='Saltos de línea \\r\\n. Una línea en blanco inicial, blancos dentro de un mensaje (se conservan) y blancos al final de un mensaje o del archivo (se cuentan como en blanco y no pasan al texto).')
    construir('D09_encabezado_citado', 'android_24h_coma', [
        m(t(14, 9, 0), AM, 'Te copio lo que dijo:'),
        m(t(14, 10, 5), JL, 'mañana sí voy'),
        m(t(14, 9, 6), JL, 'Gracias'),
    ], limitacion='En el archivo la línea 2 es una cita pegada dentro del mensaje de Ana María, pero tiene un encabezado válido: el TXT no permite distinguirla de un mensaje real. El parser la procesa como mensaje nuevo de José Luis. Estos esperados reflejan lo que el parser puede determinar, no la realidad.',
        advertencias=['TIMESTAMPS_OUT_OF_ORDER'], notas='Limitación inherente al TXT.')
    # ---------- D. Conversaciones grupales ----------
    construir('E01_tres_autores', 'android_24h_coma', [
        m(t(14, 9, 0), AM, 'Hola a todos'), m(t(14, 9, 1), JL, 'Hola'), m(t(14, 9, 2), CR, 'Buenas'),
        m(t(14, 9, 3), AM, 'Empecemos'),
    ], decision='rejected', tipo_conv='rejected_more_than_two_participants', advertencias=['PARTICIPANTS_GT_2'],
        notas='Más de dos autores: se rechaza. Los conteos se reportan igualmente; no se entrega ningún mensaje.')
    construir('E02_dos_autores_eventos_grupo', 'android_24h_coma', [
        s(t(14, 8, 0), 'Ana María creó el grupo "Equipo de estadística"', grupo='GROUP_CREATED'),
        s(t(14, 8, 1), 'Ana María añadió a José Luis', grupo='MEMBER_ADDED'),
        s(t(14, 8, 2), 'Ana María añadió a Carlos Ruiz', grupo='MEMBER_ADDED'),
        m(t(14, 9, 0), AM, 'Bienvenidos'),
        m(t(14, 9, 1), JL, 'Gracias'),
        s(t(14, 9, 30), 'Ana María cambió el asunto de "Equipo de estadística" a "Equipo 2"', grupo='SUBJECT_CHANGED'),
        s(t(14, 10, 0), 'Carlos Ruiz salió', grupo='MEMBER_LEFT'),
    ], decision='rejected', tipo_conv='rejected_possible_group', advertencias=['GROUP_EVIDENCE'],
        notas='Solo hablan dos personas, pero hay creación del grupo, altas, cambio de asunto y una salida: posible grupal, se rechaza.')
    construir('E03_grupo_idioma_no_catalogado', 'android_24h_coma', [
        s(t(14, 8, 0), 'Ana María hat die Gruppe „Statistik" erstellt'),
        s(t(14, 8, 1), 'Ana María hat Carlos Ruiz hinzugefügt'),
        m(t(14, 9, 0), AM, 'Hallo'),
        m(t(14, 9, 1), JL, 'Hi'),
    ], advertencias=['SYSTEM_LINES_UNCLASSIFIED'],
        notas='LIMITACIÓN: es un grupo, pero los avisos están en un idioma que el catálogo no cubre. Los avisos se reconocen como system por su forma (sin "autor:"), no se reconocen como evidencia de grupo y el resultado es "pendiente de confirmación" (falso negativo posible). La advertencia indica que hay avisos sin catalogar.')
    construir('E04_sistema_con_dos_puntos', 'android_24h_coma', [
        s(t(14, 8, 0), 'Ana María cambió el asunto a "Equipo: planes"', grupo='SUBJECT_CHANGED'),
        m(t(14, 9, 0), AM, 'Hola'),
        m(t(14, 9, 1), JL, 'Hola'),
    ], decision='rejected', tipo_conv='rejected_possible_group', advertencias=['GROUP_EVIDENCE'],
        notas='El aviso contiene ": " y no debe leerse como un autor llamado "Ana María cambió el asunto a \\"Equipo". Se identifica por catálogo antes de separar autor y texto. Sin el catálogo, el autor fantasma haría 3 participantes (rechazo conservador).')
    construir('E05_un_solo_autor', 'android_24h_coma', [
        s(t(14, 9, 0), CIFR_ES, conocido_no_grupo=True),
        m(t(14, 9, 1), AM, 'Notas para mí'), m(t(14, 9, 2), AM, 'Comprar pan'),
    ], decision='rejected', tipo_conv='rejected_fewer_than_two_participants', advertencias=['PARTICIPANTS_LT_2'],
        notas='Un solo autor (por ejemplo, un chat contigo mismo o una exportación incompleta): no hay conversación entre dos personas.')
    # ---------- E. Archivos sin formato ----------
    crudo('F01_formato_no_reconocido', 'fecha;autor;texto\n2026-10-14;Ana;hola\n2026-10-14;Luis;qué tal\n',
          decision_importacion='rejected', formato_esperado=None, advertencias=['FORMAT_NOT_RECOGNIZED'],
          lineas_por_disposicion=dict(encabezado=0, continuacion=0, en_blanco=0, no_procesada=3),
          lineas_no_procesadas=[dict(linea=i, motivo='FORMAT_NOT_RECOGNIZED') for i in (1, 2, 3)],
          mensajes_esperados=None, notas='Un CSV: ninguna línea coincide con un formato. Ninguna línea desaparece: las 3 se reportan.')
    crudo('F02_archivo_vacio', '', decision_importacion='rejected', formato_esperado=None,
          advertencias=['EMPTY_FILE'], lineas_por_disposicion=dict(encabezado=0, continuacion=0, en_blanco=0, no_procesada=0),
          lineas_no_procesadas=[], mensajes_esperados=None, notas='Archivo de 0 bytes.')
    print('fixtures generados en', os.path.normpath(OUT))

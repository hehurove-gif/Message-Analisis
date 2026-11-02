# Matriz de cobertura de fixtures de WhatsApp

Todos los fixtures son **simulados** (datos ficticios; formatos con el respaldo indicado en `docs/formatos_exportacion_whatsapp.md`). Cada `X.txt` tiene su `X.esperado.json`: lo que el parser debería producir según `docs/contrato_parser.md`. Se generan con `tools/fixtures/generar_fixtures_whatsapp.py` (que **no** es el parser). Los esperados salen de la intención declarada en el generador; las formas de los encabezados y los conteos de líneas e invisibles se comprobaron contra los archivos con un script de forma independiente.

## 1. Fixture → caso que comprueba

| Fixture | Formato | Caso que comprueba | Decisión esperada |
| --- | --- | --- | --- |
| A01_android24_coma_es | `android_24h_coma` | Base: texto, multilínea (3 continuaciones), dos puntos y comillas, emoji, multimedia, eliminado, aviso de cifrado, cambio de día | accepted · pending_confirmation |
| A02_android24_sin_coma_anio2 | `android_24h_sin_coma` | Sin coma, año de 2 dígitos, emojis con ZWJ, `ñ` y acentos, una hora dentro del texto | accepted |
| A03_android12_es_nnbsp | `android_12h_es_nnbsp` | `a. m.`/`p. m.` con U+202F; 12:00 p. m. = 12:00 y 12:00 a. m. = 00:00; cambio de día | accepted |
| A04_android12_compacto | `android_12h_compacto` | Indicadores `a.m.`/`p.m.` sin espacios internos | accepted |
| A05_android12_en_mdy | `android_12h_en_mdy` | Mes/día/año con AM/PM, resuelto por el día 14; cifrado, multimedia y eliminados en inglés | accepted · `mdy_resuelto_por_dato` |
| A06_android24_puntos_segundos | `android_24h_puntos_segundos` | Fecha con puntos y segundos; precisión de segundo | accepted |
| A07_android24_guiones | `android_24h_guiones` | Fecha con guiones (formato sin respaldo) | accepted |
| A08_android24_adjuntos_es | `android_24h_coma` | `IMG-… (archivo adjunto)` como media de tipo imagen; media genérica | accepted |
| B01_ios24_corchetes | `ios_24h_corchetes` | iOS: corchetes, LRM al inicio de línea, aviso de sistema con nombre antepuesto (no se atribuye), `imagen/sticker/audio/documento omitido`, eliminado, multilínea | accepted |
| B02_ios12_es_corchetes | `ios_12h_es_corchetes` | iOS 12 h, año de 2 dígitos, medianoche y mediodía | accepted |
| B03_ios12_en_mdy_corchetes | `ios_12h_en_mdy_corchetes` | iOS mes/día/año con AM/PM y U+202F | accepted · `mdy_resuelto_por_dato` |
| B04_ios24_puntos_corchetes | `ios_24h_puntos_corchetes` | iOS fecha con puntos | accepted |
| C01_fecha_ambigua | `android_24h_coma` | Todos los números de fecha ≤ 12: orden sin resolver | blocked_pending_confirmation |
| C02_fecha_orden_contradictorio | `android_24h_coma` | Una línea solo válida como día/mes y otra solo como mes/día | rejected |
| C03_cambio_de_dia_mes_anio | `android_24h_coma` | Cambio de día, de mes y de año | accepted |
| D01_invisibles_bom | `android_24h_coma` | BOM en la línea 1, U+200E (inicio y medio), U+200F, U+202F dentro del texto, árabe | accepted |
| D02_timestamps_iguales | `android_24h_coma` | Varios mensajes con el mismo minuto, de autores distintos | accepted · 3 pares iguales consecutivos |
| D03_ios_mismo_segundo | `ios_24h_corchetes` | Mensajes en el mismo segundo | accepted |
| D04_fuera_de_orden | `android_24h_coma` | Dos retrocesos de timestamp; no se reordena | accepted · `TIMESTAMPS_OUT_OF_ORDER` |
| D05_sistema_1a1 | `android_24h_coma` | Avisos propios de chat individual (cifrado, mensajes temporales, cambio de número): no son evidencia de grupo | accepted · pending_confirmation |
| D06_contenido_especial | `android_24h_coma` | Dos puntos, URL, comillas, marcador de media dentro de un texto (es `texto`), solo emojis, párrafo con línea en blanco, continuación que empieza con fecha sin hora, `.` y tabulador | accepted |
| D07_lineas_desconocidas | `android_24h_coma` | 9 líneas no procesadas con motivo: previa al primer mensaje, separadores desconocidos, huérfanas, fecha y hora imposibles, minutos malformados, encabezado iOS, texto con aspecto de timestamp. Ninguna se anexa | accepted · `UNPROCESSED_LINES` |
| D08_crlf_lineas_en_blanco | `android_24h_coma` | `\r\n`, línea en blanco inicial, blancos dentro y al final de mensajes y del archivo | accepted |
| D09_encabezado_citado | `android_24h_coma` | **Limitación**: cita pegada con encabezado válido se procesa como mensaje | accepted · `TIMESTAMPS_OUT_OF_ORDER` |
| E01_tres_autores | `android_24h_coma` | Más de dos autores | rejected |
| E02_dos_autores_eventos_grupo | `android_24h_coma` | Dos autores y avisos de grupo: creación, altas, cambio de asunto, salida | rejected_possible_group |
| E03_grupo_idioma_no_catalogado | `android_24h_coma` | **Limitación**: grupo con avisos en alemán → no se detecta evidencia | accepted · pending_confirmation · `SYSTEM_LINES_UNCLASSIFIED` |
| E04_sistema_con_dos_puntos | `android_24h_coma` | Aviso con ": " no genera un autor fantasma | rejected_possible_group |
| E05_un_solo_autor | `android_24h_coma` | Un solo autor | rejected |
| F01_formato_no_reconocido | ninguno | CSV: ninguna línea coincide; las 3 se reportan | rejected |
| F02_archivo_vacio | ninguno | 0 bytes | rejected |

**Fixtures de referencia anteriores** (`data/synthetic/`, formato `android_24h_sin_coma` con año de 4 dígitos, también simulados): `00_escenarios_validacion` (21 líneas; **fechas con orden ambiguo**), `01_amistad_equilibrada` (75 encabezados, 2 continuaciones, 1 multimedia, 1 aviso de cifrado) y `02_interes_romantico_unilateral` (73 encabezados). Aún no tienen `.esperado.json` de parser.

## 2. Caso solicitado → fixtures

| Caso pedido | Fixtures |
| --- | --- |
| Android 24 h | A01, A02, A06, A07, A08, C01-C03, D01-D09, E01-E05, `data/synthetic` |
| Android 12 h, `a. m.`/`p. m.` y variantes | A03 (`a. m.` con U+202F), A04 (`a.m.`), A05 (`AM`/`PM`) |
| iOS con corchetes | B01-B04, D03 |
| Variaciones de fecha, segundos, separadores y región | Año de 2 dígitos: A02, B02-B04 · Segundos: A06, B01-B04, D03 · Separadores `.` y `-`: A06, A07, B04 · Mes/día: A05, B03 · Orden ambiguo o contradictorio: C01, C02 |
| Texto normal | A01 y casi todos |
| Varias líneas | A01, B01, D06, D08 |
| Emojis y Unicode | A01, A02 (ZWJ), D01 (árabe), D06 |
| Invisibles U+200E, U+200F, U+202F, BOM | D01 (los cuatro), B01 (U+200E), A03 y B03 (U+202F en el encabezado) |
| Nombres con espacios y acentos | Todos (Ana María, José Luis, Emma Clark, Carlos Ruiz) |
| Mismo timestamp | D02 (minuto), D03 (segundo) |
| Cambio de día | A01, A03, B02, B03, C03 |
| Avisos del sistema | A01, D05, E02, E03, E04, B01 |
| Aviso de cifrado | A01, A05, B01, D01, D05 |
| Multimedia omitida | A01, A05, A08, B01, D06 (caso negativo: dentro de un texto) |
| Mensajes eliminados | A01, A05, B01 |
| Dos puntos, comillas y saltos de línea | A01, D06, B01, E04 |
| Líneas desconocidas o timestamps malformados | D07, F01 |
| Línea con aspecto de timestamp que no se anexa | D07 (líneas 4, 9 y 13) |
| Más de dos participantes | E01 |
| Dos participantes con evidencia de grupo | E02, E04 |
| Dos participantes sin evidencia (pendiente) | A01, D05, E03 (con la limitación) |
| Archivo sin formato o vacío | F01, F02 |

## 3. Limitaciones documentadas con fixture

| Fixture | Limitación |
| --- | --- |
| D09 | Una cita pegada con encabezado válido no se distingue de un mensaje real |
| E03 | Un grupo con avisos en un idioma no catalogado queda "pendiente de confirmación" (falso negativo posible) |
| D07 (línea 13) | Un texto legítimo con fecha y hora al inicio se reporta como no procesado |
| C01 | Con todas las fechas ambiguas no se puede resolver el orden sin ayuda del usuario |

Un grupo sin avisos en el rango exportado, o donde solo escriben dos personas, es **idéntico** a un chat individual en el TXT; no existe un fixture que lo distinga porque no hay forma de distinguirlo (A01 y D05 lo representan).

## 4. Qué no cubre

Marcadores de multimedia o avisos de otros idiomas; exportaciones reales (ninguna examinada); reacciones, ediciones, respuestas citadas y reenviados; mezcla de formatos en proporciones similares (`FORMAT_AMBIGUOUS`); errores de codificación (`ENCODING_ERROR`); archivos grandes o de rendimiento.

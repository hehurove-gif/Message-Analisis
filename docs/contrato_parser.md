# Contrato del parser de exportaciones de WhatsApp

Versión 0.2 · 2026-11-03 · Fase 1.2. Dice qué entra, qué debe salir, qué se rechaza y qué se reporta. Lo implementa `parsers/` y lo ejercitan `tests/fixtures/whatsapp/` (cada `.esperado.json` es lo que el parser debe producir) y los formatos descritos en `formatos_exportacion_whatsapp.md`. Los nombres de campo son los de los `.esperado.json`.

Los cambios respecto a la v0.1 y las decisiones que los motivaron están en la sección 12 (historial). Las definiciones operativas v0.6 adoptan los tipos de mensaje de este contrato.

## 1. Entrada

- **Archivo:** ruta a un TXT exportado, leído como UTF-8 estricto. Puede empezar con BOM (U+FEFF) y usar `\n` o `\r\n`. Un error de decodificación rechaza el archivo (`ENCODING_ERROR`, fixture F04); no se prueba otra codificación.
- **Parámetros opcionales:** `date_order_hint` (`dmy` o `mdy`), que solo se usa si el archivo no permite resolver el orden de la fecha (sección 6); **no hay valor por defecto**. Nada más: no hay nombres de participantes, zona horaria ni idioma como entrada.
- El nombre del archivo **no se usa** para nada.

## 2. Principio rector

**Ninguna línea desaparece sin explicación.** Cada línea física del archivo recibe exactamente una disposición:

| Disposición | Qué es |
| --- | --- |
| `encabezado` | Inicia un mensaje (de persona o del sistema) |
| `continuacion` | Texto que continúa el mensaje abierto |
| `en_blanco` | Solo espacios o vacía |
| `no_procesada` | Línea que el parser no pudo clasificar; se reporta con número de línea y motivo y **no se anexa a ningún mensaje** |

Invariantes verificables:

1. `lineas_totales = encabezado + continuacion + en_blanco + no_procesada`.
2. `encabezado = texto + media + system + deleted` (cada encabezado produce un mensaje).
3. `len(lineas_no_procesadas) = no_procesada`, con motivo para cada una.
4. Si la importación se acepta, hay un objeto de mensaje por encabezado, con `seq` consecutivo desde 1 y rangos de líneas ascendentes que no se solapan.
5. Ningún mensaje `system` tiene participante.

## 3. Reconocimiento de líneas

Se aplica en este orden a cada línea (con `\r\n` ya normalizado y sin BOM inicial):

1. **En blanco** (solo espacios): `en_blanco`.
2. **Encabezado.** Tras ignorar al inicio de la línea U+200E, U+200F y U+FEFF (solo para este reconocimiento; la línea original no se altera) y tratar U+202F como un espacio ordinario (solo dentro del reconocimiento del timestamp), la línea empieza con el encabezado de uno de los formatos del catálogo con **valores válidos** (fecha real, hora real). Mientras el orden de la fecha no está resuelto, una fecha es válida si lo es en al menos uno de los dos órdenes; ya resuelto, una línea que no es válida en el orden elegido es `TIMESTAMP_INVALID`.
   - **Formato del archivo:** el formato con más líneas de encabezado (mínimo 1) que supere estrictamente a los demás. Sin ninguno: `FORMAT_NOT_RECOGNIZED`; con empate: `FORMAT_AMBIGUOUS` (fixture F03). En ambos casos se rechaza y las líneas no en blanco se reportan como no procesadas, con ese mismo motivo.
   - Un encabezado válido de **otro** formato conocido: no procesada, `FORMAT_MISMATCH`.
   - Encabezado con la forma del formato del archivo pero valores imposibles (`31/02/2026`, `25:61`): no procesada, `TIMESTAMP_INVALID`.
3. **Aspecto de timestamp.** Si no es un encabezado pero, tras quitar un `[` inicial, empieza con una fecha (`n/n/n`, `n.n.n` o `n-n-n`) y en los primeros 40 caracteres hay una hora (`h:m` con 1 o 2 dígitos), es **no procesada** con `TIMESTAMP_LIKE_UNRECOGNIZED`. No se anexa al mensaje anterior. *(La heurística de 40 caracteres es experimental.)*
4. **Continuación.** Cualquier otra línea no vacía se anexa al mensaje **abierto**. Un mensaje queda abierto desde su encabezado hasta que aparece una línea no procesada o un nuevo encabezado; las líneas en blanco no lo cierran.
5. **Huérfanas.** Si no hay mensaje abierto: `ORPHAN_BEFORE_FIRST_MESSAGE` (aún no hubo ningún encabezado) u `ORPHAN_AFTER_UNPROCESSED` (hay una línea no procesada desde el último encabezado). Nunca se anexan.

Motivos posibles de una línea no procesada: `TIMESTAMP_LIKE_UNRECOGNIZED`, `TIMESTAMP_INVALID`, `FORMAT_MISMATCH`, `ORPHAN_BEFORE_FIRST_MESSAGE`, `ORPHAN_AFTER_UNPROCESSED`, `FORMAT_NOT_RECOGNIZED`, `FORMAT_AMBIGUOUS`.

**Regla firme.** Una línea con aspecto de timestamp que no cumple un formato reconocido **nunca se anexa** automáticamente a un mensaje: queda registrada con su número de línea y su motivo. Las líneas no procesadas **no se interpretan**: no se sabe si son texto perdido de un mensaje, ruido del exportador o un formato aún no catalogado, y esa investigación (qué significan de verdad) precede a cualquier umbral (sección 8).

**Costo aceptado.** Un texto legítimo que parezca un encabezado en forma, pero con valores inválidos o con fecha y hora al inicio, se reporta como no procesado y se pierde del texto del mensaje (D07, línea 13). Se prefiere un aviso visible a una unión silenciosa. A la inversa, una cita pegada con un encabezado **válido** se tratará como mensaje (D09): el TXT no permite distinguirla.

## 4. Mensaje

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `seq` | entero | Orden del encabezado en el archivo, desde 1. Es el identificador y el orden de origen. **No se reordena nunca**, aunque los timestamps retrocedan |
| `linea_inicial`, `linea_final` | enteros | Primera y última línea del mensaje en el archivo (1 = primera línea). `linea_final` es la última línea no en blanco del mensaje |
| `tipo` | `texto` \| `media` \| `system` \| `deleted` | Ver abajo |
| `participante` | `A` \| `B` \| nulo | Nulo si y solo si `tipo = system` |
| `timestamp_original` | cadena | Fecha y hora tal como están en el archivo, sin corchetes ni el ` - ` final, **conservando todos los caracteres y espacios originales** (p. ej. U+202F). Solo el reconocimiento los trata como espacio ordinario |
| `timestamp_local` | ISO 8601 sin zona (`2026-10-14T09:12:00`) \| nulo | Hora local de la exportación; nulo solo si el orden de fecha no se resolvió |
| `precision` | `minuto` \| `segundo` | Sin segundos en el archivo, los segundos se fijan en `00` y la precisión es `minuto`. No se inventan |
| `texto` | cadena | **Contenido original** del mensaje: no se elimina ni se sustituye ningún carácter (sección 4, "Contenido y normalización") |
| `texto_normalizado` | cadena | Representación **derivada**, separada, para análisis (sección 4). Nunca sustituye a `texto` |
| `media_kind` | opcional | `imagen`, `sticker`, `audio`, `video`, `documento` o `desconocido`; solo en `media` |

**Tipos.**

- `texto`: mensaje de persona con contenido escrito.
- `media`: el cuerpo es, completo, un marcador de multimedia omitida o de archivo adjunto. Si un marcador aparece dentro de un texto más largo, es `texto` (D06).
- `deleted`: el cuerpo es, completo, un marcador de mensaje eliminado. No se conoce su contenido ni quién lo eliminó.
- `system`: aviso sin autor (cifrado, cambios de grupo, mensajes temporales, cambio de número…). **Nunca se atribuye a un participante**, aunque el archivo le anteponga un nombre (B01). Se reconoce por catálogo antes de separar `Autor: texto`, o por no tener `Autor:` (Android).

Los marcadores y los catálogos de avisos son **simulados** (ver el catálogo de formatos).

**Contenido y normalización.**

- Primera línea = lo que sigue a `Autor: `; las continuaciones se unen con `\n`; las líneas en blanco intermedias se conservan; las líneas en blanco al final del mensaje no entran en el texto (siguen contándose como `en_blanco`).
- **`texto` conserva el contenido original.** No se elimina ni se sustituye ningún carácter dentro del mensaje: ni U+200E ni U+200F (marcas de dirección que pueden ser significativas en idiomas de derecha a izquierda), ni U+202F, ni emojis. Tampoco se aplica NFC ni se recortan espacios o tabuladores. El BOM (U+FEFF) al inicio del **archivo** es una marca de codificación, no contenido de ningún mensaje, y se descarta al decodificar; un U+FEFF dentro de un mensaje se conserva.
- Lo que se **ignora** (no es contenido): U+200E/U+200F/U+FEFF **antes del encabezado** de una línea, y el BOM inicial. Lo que se **trata como espacio ordinario**: U+202F, y solo para reconocer el timestamp. Son dos operaciones distintas y ninguna toca `texto`.
- **`texto_normalizado`** (campo derivado, para análisis léxico): `texto` con U+202F → espacio ordinario y U+200E, U+200F y U+FEFF eliminados. Sin NFC. Si un análisis de idiomas de derecha a izquierda exigiera conservar las marcas, bastará con usar `texto`; esta decisión se revisará con exportaciones reales.
- El reporte cuenta cuántas veces aparece cada uno de esos caracteres en todo el archivo (`caracteres_especiales_en_archivo`): es un conteo informativo, no una lista de lo eliminado.

## 5. Participantes y anonimización

- Participantes = autores distintos de los mensajes `texto`, `media` y `deleted`. Los de `system` no cuentan.
- Se etiquetan `A`, `B`, `C`… por **orden de primera aparición** en el archivo. Con más de dos autores el chat se rechaza y no se entrega ningún mensaje; el mapa (solo memoria) conserva las etiquetas (E01).
- La correspondencia nombre-etiqueta vive **solo en memoria**, no se escribe a disco, no aparece en el reporte ni en los registros. (El `.esperado.json` de los fixtures la incluye únicamente porque los nombres son ficticios.)
- El anonimizado cubre a los participantes. El contenido de `texto` puede nombrar a personas; eso lo procesa solo la memoria local y **no entra a ningún reporte**. Qué hacer con los nombres dentro del texto en la interfaz queda para una fase posterior.

## 6. Fechas

1. Cada encabezado se lee según el formato del archivo; hora de 12 h convertida a 24 h (`12:xx a. m.` = `00:xx`, `12:xx p. m.` = `12:xx`).
2. Año de 2 dígitos → 2000 a 2099.
3. **Orden de fecha** (todos los formatos del catálogo escriben la fecha con dos números ≤ 31 y el año al final):

| Evidencia en el archivo | `orden_fecha` | Efecto |
| --- | --- | --- |
| Algún primer número > 12, ninguno el segundo | `dmy_resuelto_por_dato` | Normal |
| Algún segundo número > 12, ninguno el primero | `mdy_resuelto_por_dato` | Normal |
| Ambos casos | `contradictorio` | **Rechazado** (`DATE_ORDER_CONTRADICTORY`) |
| Ninguno > 12 | `ambiguo` | **Bloqueado**: sin timestamps normalizados hasta que se dé `date_order_hint` (`DATE_ORDER_AMBIGUOUS`). Con la pista se procesa y el orden queda como `dmy_por_indicacion` o `mdy_por_indicacion` |

4. No se convierte zona horaria ni se asume una. No se reordena nada por timestamp.
5. **Timestamps consecutivos iguales:** número de pares de mensajes de persona adyacentes con el mismo timestamp. Es **informativo**: con precisión de minuto es normal. Se conserva el orden del archivo.
6. **Fuera de orden:** número de mensajes de persona cuyo timestamp es **anterior** al del mensaje de persona anterior. Advertencia `TIMESTAMPS_OUT_OF_ORDER`; el parser no corrige.
7. **Rango de fechas:** **mínimo y máximo** timestamp de los mensajes de persona (los avisos del sistema no cuentan; no es el primero y el último del archivo); nulo si el orden de fecha no se resolvió.

## 7. Tipo de conversación

Se evalúa con los autores y los avisos del sistema; **el parser no declara nunca que la conversación es individual**.

| Condición | `estado_tipo_conversacion` | Decisión |
| --- | --- | --- |
| Más de 2 autores | `rejected_more_than_two_participants` | `rejected` |
| Menos de 2 autores | `rejected_fewer_than_two_participants` | `rejected` |
| 2 autores y ≥1 aviso del sistema de grupo | `rejected_possible_group` | `rejected` |
| 2 autores sin evidencias de grupo | `pending_confirmation` | `accepted`; requiere confirmación del usuario antes de analizar |
| No evaluado (rechazo previo por formato o fecha) | `not_evaluated` | `rejected` |

Se reporta cada evidencia de grupo con su número de línea y su código (`GROUP_CREATED`, `MEMBER_ADDED`, `MEMBER_LEFT`, `MEMBER_JOINED_LINK`, `SUBJECT_CHANGED`, `ICON_CHANGED`, `DESCRIPTION_CHANGED`). Los avisos que no coinciden con ningún patrón conocido (de grupo o de chat individual) se cuentan en `avisos_sistema_sin_catalogar` y producen `SYSTEM_LINES_UNCLASSIFIED`: **la evidencia de grupo no puede descartarse**. Lo que el TXT no permite saber está en la sección 6 del catálogo de formatos.

Cuando el orden de fecha es ambiguo se calcula igualmente el tipo de conversación; ante un rechazo y un bloqueo simultáneos, gana el rechazo.

## 8. Decisión de importación

Precedencia: `rejected` > `blocked_pending_confirmation` > `accepted`.

| Decisión | Cuándo | Qué entrega |
| --- | --- | --- |
| `rejected` | Vacío, codificación inválida, formato no reconocido o ambiguo, orden de fecha contradictorio, tipo de conversación rechazado | Solo el reporte (con los conteos). **Ningún mensaje** |
| `blocked_pending_confirmation` | Orden de fecha ambiguo sin pista | Solo el reporte |
| `accepted` | Ninguna de las anteriores | Mensajes y reporte, con las advertencias que correspondan |

### Aceptación de la importación y disponibilidad del análisis

Son dos cosas distintas.

- **Importación** (`decision_importacion`): ¿se pudieron leer mensajes? Los mensajes reconocidos se entregan aunque haya líneas no procesadas.
- **Análisis** (`analisis_habilitado`): **siempre `false` al salir del parser.** Lo habilita una decisión posterior y explícita, y solo cuando `requisitos_analisis` está resuelto:

| Requisito | Cuándo aparece | Cómo se resuelve |
| --- | --- | --- |
| `CONFIRMAR_TIPO_CONVERSACION` | Toda importación aceptada (el TXT no prueba que sea 1-1) | El usuario confirma que es una conversación individual |
| `REVISAR_LINEAS_NO_PROCESADAS` | Hay al menos una línea no procesada | Se corrige/re-exporta el archivo hasta que no queden, **o** el usuario acepta expresamente la pérdida de esas líneas concretas (`aceptar_perdidas`, con la lista de números de línea; no una aceptación global ni un porcentaje) |
| `INDICAR_ORDEN_FECHA` | Importación bloqueada por orden de fecha ambiguo | Se vuelve a importar con `date_order_hint` |

Con líneas no procesadas el archivo queda **`pendiente_revision_calidad`**, `procesamiento_completo = false`, y no puede presentarse como una conversación completamente procesada. El parser **no fija ningún porcentaje tolerable** de líneas no procesadas: su significado (texto perdido, ruido del exportador, formato no catalogado) debe investigarse con exportaciones reales antes de proponer un umbral (sección 13).

## 9. Reporte de calidad de importación

Un reporte por archivo, siempre, aunque se rechace. Contiene solo números, códigos y números de línea: **ni nombres ni texto de mensajes**.

| Campo | Contenido |
| --- | --- |
| `formato` (`formato_esperado`) | Id del catálogo o nulo |
| `participantes_detectados` | Entero |
| `estado_tipo_conversacion` | Sección 7 |
| `decision_importacion` | Sección 8 |
| `orden_fecha` | Sección 6 |
| `lineas_totales`, `lineas_por_disposicion` | Sección 2 |
| `mensajes_por_tipo` | `texto`, `media` (multimedia omitida), `system`, `deleted`. Mensajes procesados de persona = `texto + media + deleted` |
| `lineas_no_procesadas` | Lista de `{linea, motivo}` |
| `evidencias_grupo` | Lista de `{linea, codigo}` |
| `avisos_sistema_sin_catalogar` | Entero |
| `rango_fechas` | `{primero, ultimo}` o nulo |
| `timestamps_consecutivos_iguales`, `timestamps_fuera_de_orden` | Enteros (sección 6) |
| `caracteres_especiales_en_archivo` | Conteo por punto de código (U+200E, U+200F, U+202F, U+FEFF). Informativo: no implica que se haya eliminado nada |
| `procesamiento_completo` | `true` solo si la importación se aceptó y **no** hay líneas no procesadas |
| `estado_calidad` | `rechazado`, `bloqueado`, `pendiente_revision_calidad`, `con_observaciones` (aceptada y sin líneas perdidas, pero con `SYSTEM_LINES_UNCLASSIFIED`, `TIMESTAMPS_OUT_OF_ORDER`, `AUTHORS_MERGED_BY_USER` o `AUTHOR_ALIAS_SUSPECTED`) o `sin_observaciones_de_calidad` (sección 8) |
| `lineas_fuera_de_orden` | Líneas iniciales de los mensajes de persona cuyo timestamp es anterior al del mensaje de persona anterior |
| `autores_alias_sospechosos`, `autores_unidos` | Por etiqueta y líneas, sin nombres. La unión solo ocurre por decisión explícita (`merge_authors` / `--unir` / `--aceptar-alias-sospechosos`) |
| `analisis_habilitado` | Siempre `false` al terminar el parser (sección 8) |
| `requisitos_analisis` | Lista de lo que falta para habilitarlo (sección 8) |
| `advertencias` | Códigos ordenados |

**Códigos de advertencia y error.**

| Código | Tipo | Efecto |
| --- | --- | --- |
| `EMPTY_FILE` | Error | Rechazo |
| `ENCODING_ERROR` (F04) | Error | Rechazo |
| `FORMAT_NOT_RECOGNIZED` (F01), `FORMAT_AMBIGUOUS` (F03) | Error | Rechazo |
| `DATE_ORDER_CONTRADICTORY` | Error | Rechazo |
| `DATE_ORDER_AMBIGUOUS` | Bloqueo | Pide `date_order_hint` |
| `PARTICIPANTS_GT_2`, `PARTICIPANTS_LT_2`, `GROUP_EVIDENCE` | Error | Rechazo por tipo de conversación |
| `UNPROCESSED_LINES` | Advertencia | Importación aceptada, **pendiente de revisión de calidad**; el análisis no se habilita (sección 8) |
| `TIMESTAMPS_OUT_OF_ORDER` | Advertencia | Aceptada; no se reordena |
| `SYSTEM_LINES_UNCLASSIFIED` | Advertencia | Aceptada; el tipo queda pendiente de confirmación |

## 10. Privacidad

- `persist_raw_chat: false`: el parser no escribe el chat, ni sus líneas, ni sus mensajes a disco; el procesamiento posterior recibe objetos en memoria. Los reportes no incluyen texto.
- `allow_network: false`: ninguna llamada de red ni servicio externo.
- `anonymize_participants: true`: etiquetas A y B; el mapa nombre-etiqueta solo en memoria (sección 5).
- Los fixtures contienen únicamente datos ficticios.

## 11. Parámetros

En `config.yaml`, sección `parsing`: `date_order_hint` (nulo por defecto), `two_digit_year_century` (2000), `timestamp_like_window_chars` (40), `ignored_leading_chars` (se ignoran antes del encabezado) y `space_like_chars` (se tratan como espacio ordinario en el timestamp). Los formatos, marcadores y avisos están en `parsers/` como tablas simuladas editables. No hay umbral de líneas no procesadas.

## 12. Historial y decisiones

**v0.2 (2026-11-03).** Resuelve las incompatibilidades y preguntas de la v0.1:

| # | Tema | Decisión |
| --- | --- | --- |
| 1 | Nombres de tipo | Valores canónicos: `texto`, `media`, `system`, `deleted`. Las definiciones operativas v0.6 sustituyen `sistema`/`eliminado`; no coexisten dos enumeraciones |
| 2 | Orden de fecha ambiguo | Se mantiene el bloqueo; **no hay DMY ni MDY por defecto** |
| 3 | `00_escenarios_validacion.txt` | Se ejecuta con `date_order_hint=dmy`, sin cambiar sus fechas. C01 sigue bloqueado y C02 sigue rechazado |
| 4 | Caracteres Unicode | Se separan los que se ignoran, los que se tratan como espacio y el contenido. U+202F → espacio ordinario solo para reconocer el timestamp; U+200E/U+200F **no se eliminan** del contenido; `texto` es original y `texto_normalizado` un campo aparte; `timestamp_original` conserva todo |
| 5 | Líneas con aspecto de timestamp | Nunca se anexan; se registran con línea y motivo |
| 6 | Importación vs análisis | Mensajes reconocidos se importan; con líneas no procesadas el archivo queda pendiente de revisión de calidad y el análisis no se habilita hasta resolver o aceptar expresamente cada pérdida |
| 7 | Umbral de líneas no procesadas | No se fija un porcentaje sin investigar su significado |
| 8 | `ref_latency.py` | Corregido: detecta continuaciones, reporta timestamps inválidos o con aspecto de timestamp, rechaza lo que no clasifica y nunca descarta contenido. Resultados de los tres chats sin cambios. No es el parser |
| 9 | Config | `parsing` separa caracteres ignorados y espacios, y ya no dice que los patrones se prueben con exportaciones reales |

Cambios de campo: `caracteres_normalizados` → `caracteres_especiales_en_archivo`; nuevos `texto_normalizado`, `procesamiento_completo`, `estado_calidad`, `analisis_habilitado`, `requisitos_analisis`; nuevo motivo `FORMAT_AMBIGUOUS`; nuevos fixtures F03 y F04.

**Ajustes al implementar el parser (Fase 1.2).** (a) `android_24h_sin_coma` acepta año de 2 o de 4 dígitos: los chats sintéticos de la Fase 0 usan 4 y el catálogo solo cubría 2 (formato simulado). (b) La heurística de "aspecto de timestamp" acepta minutos de 1 dígito (`09:3`), como exige D07. (c) `E01`: se etiqueta a todos los autores aunque el chat se rechace. (d) `rango_fechas` usa mínimo y máximo (D04, D09). (e) Un archivo con solo espacios en blanco es `EMPTY_FILE` y sus líneas cuentan como `en_blanco`. Los 33 fixtures y los tres chats de la Fase 0 pasan sin cambiar su contenido.

**Ajustes tras la primera exportación real (Fase 1.3).** (a) Nuevo `estado_calidad` = `con_observaciones`; (b) nuevo campo `lineas_fuera_de_orden`; (c) un autor con forma `<prefijo> - <otro autor>` se reporta (`AUTHOR_ALIAS_SUSPECTED`) y solo se une por decisión explícita del usuario (`AUTHORS_MERGED_BY_USER`); el tipo de conversación sigue pendiente de confirmación. Caso aún abierto: ver `limitaciones_y_formatos_pendientes.md`.

**Hallazgo al corregir `ref_latency.py`.** El lector anterior descartaba en silencio el aviso de cifrado (primera línea) de los chats 01 y 02: no afectaba a ningún resultado (un aviso del sistema no es un mensaje de persona), pero era exactamente el tipo de pérdida silenciosa que este contrato prohíbe. Ahora se reconoce y se cuenta aparte.

**v0.1 (2026-11-02).** Especificación inicial (Fase 1, paso 1).

## 13. Preguntas abiertas

1. ¿Qué significan realmente las líneas no procesadas en exportaciones reales, y es posible distinguir texto perdido de ruido? Hasta entonces no hay umbral.
2. ¿Cómo se resuelve un contacto renombrado que produce 3 autores?
3. ¿Aplicar NFC al texto normalizado? ¿Debe `texto_normalizado` conservar las marcas U+200E/U+200F en idiomas de derecha a izquierda?
4. ¿Deben reportarse en un nivel aparte los timestamps iguales a precisión de minuto (muy comunes) y a precisión de segundo (raros)?
5. ¿Qué formato de aceptación de pérdidas (`aceptar_perdidas`) necesita la interfaz futura?

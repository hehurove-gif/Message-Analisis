# Contrato del parser de exportaciones de WhatsApp

Versión 0.1 · 2026-11-02 · Fase 1, paso 1. **Especificación, no implementación.** Dice qué entra, qué debe salir, qué se rechaza y qué se reporta. Los casos están ejercitados por `tests/fixtures/whatsapp/` (cada `.esperado.json` es lo que el parser debería producir) y los formatos, descritos en `formatos_exportacion_whatsapp.md`. Los nombres de campo son los de los `.esperado.json`.

Este contrato no modifica las definiciones v0.5. Donde choca con ellas, está en la sección 12.

## 1. Entrada

- **Archivo:** ruta a un TXT exportado, leído como UTF-8 estricto. Puede empezar con BOM (U+FEFF) y usar `\n` o `\r\n`. Un error de decodificación rechaza el archivo (`ENCODING_ERROR`, sin fixture todavía).
- **Parámetros opcionales:** `date_order_hint` (`dmy` o `mdy`), que solo se usa si el archivo no permite resolver el orden de la fecha (sección 6). Nada más: no hay nombres de participantes, zona horaria ni idioma como entrada.
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
2. **Encabezado.** Tras quitar al inicio U+200E, U+200F y U+FEFF (solo para este reconocimiento), la línea empieza con el encabezado de uno de los formatos del catálogo con **valores válidos** (fecha real, hora real). Mientras el orden de la fecha no está resuelto, una fecha es válida si lo es en al menos uno de los dos órdenes; ya resuelto, una línea que no es válida en el orden elegido es `TIMESTAMP_INVALID`.
   - **Formato del archivo:** el formato con más líneas de encabezado (mínimo 1) que supere estrictamente a los demás. Sin ninguno: `FORMAT_NOT_RECOGNIZED`; con empate: `FORMAT_AMBIGUOUS` (sin fixture todavía). En ambos casos se rechaza y las líneas no en blanco se reportan como no procesadas.
   - Un encabezado válido de **otro** formato conocido: no procesada, `FORMAT_MISMATCH`.
   - Encabezado con la forma del formato del archivo pero valores imposibles (`31/02/2026`, `25:61`): no procesada, `TIMESTAMP_INVALID`.
3. **Aspecto de timestamp.** Si no es un encabezado pero, tras quitar un `[` inicial, empieza con una fecha (`n/n/n`, `n.n.n` o `n-n-n`) y en los primeros 40 caracteres hay una hora (`h:m` con 1 o 2 dígitos), es **no procesada** con `TIMESTAMP_LIKE_UNRECOGNIZED`. No se anexa al mensaje anterior. *(La heurística de 40 caracteres es experimental.)*
4. **Continuación.** Cualquier otra línea no vacía se anexa al mensaje **abierto**. Un mensaje queda abierto desde su encabezado hasta que aparece una línea no procesada o un nuevo encabezado; las líneas en blanco no lo cierran.
5. **Huérfanas.** Si no hay mensaje abierto: `ORPHAN_BEFORE_FIRST_MESSAGE` (aún no hubo ningún encabezado) u `ORPHAN_AFTER_UNPROCESSED` (hay una línea no procesada desde el último encabezado). Nunca se anexan.

Motivos posibles de una línea no procesada: `TIMESTAMP_LIKE_UNRECOGNIZED`, `TIMESTAMP_INVALID`, `FORMAT_MISMATCH`, `ORPHAN_BEFORE_FIRST_MESSAGE`, `ORPHAN_AFTER_UNPROCESSED`, `FORMAT_NOT_RECOGNIZED`.

**Costo aceptado.** Un texto legítimo que parezca un encabezado en forma, pero con valores inválidos o con fecha y hora al inicio, se reporta como no procesado y se pierde del texto del mensaje (D07, línea 13). Se prefiere un aviso visible a una unión silenciosa. A la inversa, una cita pegada con un encabezado **válido** se tratará como mensaje (D09): el TXT no permite distinguirla.

## 4. Mensaje

| Campo | Tipo | Descripción |
| --- | --- | --- |
| `seq` | entero | Orden del encabezado en el archivo, desde 1. Es el identificador y el orden de origen. **No se reordena nunca**, aunque los timestamps retrocedan |
| `linea_inicial`, `linea_final` | enteros | Primera y última línea del mensaje en el archivo (1 = primera línea). `linea_final` es la última línea no en blanco del mensaje |
| `tipo` | `texto` \| `media` \| `system` \| `deleted` | Ver abajo |
| `participante` | `A` \| `B` \| nulo | Nulo si y solo si `tipo = system` |
| `timestamp_original` | cadena | Fecha y hora tal como están en el archivo, sin corchetes ni el ` - ` final, conservando espacios especiales (p. ej. U+202F) |
| `timestamp_local` | ISO 8601 sin zona (`2026-10-14T09:12:00`) \| nulo | Hora local de la exportación; nulo solo si el orden de fecha no se resolvió |
| `precision` | `minuto` \| `segundo` | Sin segundos en el archivo, los segundos se fijan en `00` y la precisión es `minuto`. No se inventan |
| `texto` | cadena | Ver normalización |
| `media_kind` | opcional | `imagen`, `sticker`, `audio`, `video`, `documento` o `desconocido`; solo en `media` |

**Tipos.**

- `texto`: mensaje de persona con contenido escrito.
- `media`: el cuerpo es, completo, un marcador de multimedia omitida o de archivo adjunto. Si un marcador aparece dentro de un texto más largo, es `texto` (D06).
- `deleted`: el cuerpo es, completo, un marcador de mensaje eliminado. No se conoce su contenido ni quién lo eliminó.
- `system`: aviso sin autor (cifrado, cambios de grupo, mensajes temporales, cambio de número…). **Nunca se atribuye a un participante**, aunque el archivo le anteponga un nombre (B01). Se reconoce por catálogo antes de separar `Autor: texto`, o por no tener `Autor:` (Android).

Los marcadores y los catálogos de avisos son **simulados** (ver el catálogo de formatos).

**Normalización de `texto`.**

- Primera línea = lo que sigue a `Autor: `; las continuaciones se unen con `\n`; las líneas en blanco intermedias se conservan; las líneas en blanco al final del mensaje no entran en el texto (siguen contándose como `en_blanco`).
- Se **eliminan** U+200E, U+200F y U+FEFF; U+202F se **sustituye por un espacio**. No se hace normalización Unicode (NFC), no se recortan espacios internos ni tabuladores.
- El reporte cuenta cuántas veces apareció cada uno de esos caracteres en todo el archivo (`caracteres_normalizados`).

## 5. Participantes y anonimización

- Participantes = autores distintos de los mensajes `texto`, `media` y `deleted`. Los de `system` no cuentan.
- Se etiquetan `A`, `B` por **orden de primera aparición** en el archivo. Con más de dos autores no se etiqueta (se rechaza).
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
7. **Rango de fechas:** primer y último timestamp de los mensajes de persona (los avisos del sistema no cuentan); nulo si el orden de fecha no se resolvió.

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

Una importación aceptada **no** implica calidad suficiente: hay advertencias (sección 9) y la decisión sobre un umbral de líneas no procesadas está pendiente (sección 13).

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
| `caracteres_normalizados` | Conteo por punto de código (U+200E, U+200F, U+202F, U+FEFF) |
| `advertencias` | Códigos ordenados |

**Códigos de advertencia y error.**

| Código | Tipo | Efecto |
| --- | --- | --- |
| `EMPTY_FILE` | Error | Rechazo |
| `ENCODING_ERROR` (sin fixture) | Error | Rechazo |
| `FORMAT_NOT_RECOGNIZED`, `FORMAT_AMBIGUOUS` (sin fixture) | Error | Rechazo |
| `DATE_ORDER_CONTRADICTORY` | Error | Rechazo |
| `DATE_ORDER_AMBIGUOUS` | Bloqueo | Pide `date_order_hint` |
| `PARTICIPANTS_GT_2`, `PARTICIPANTS_LT_2`, `GROUP_EVIDENCE` | Error | Rechazo por tipo de conversación |
| `UNPROCESSED_LINES` | Advertencia | Aceptada; revisar `lineas_no_procesadas` |
| `TIMESTAMPS_OUT_OF_ORDER` | Advertencia | Aceptada; no se reordena |
| `SYSTEM_LINES_UNCLASSIFIED` | Advertencia | Aceptada; el tipo queda pendiente de confirmación |

## 10. Privacidad

- `persist_raw_chat: false`: el parser no escribe el chat, ni sus líneas, ni sus mensajes a disco; el procesamiento posterior recibe objetos en memoria. Los reportes no incluyen texto.
- `allow_network: false`: ninguna llamada de red ni servicio externo.
- `anonymize_participants: true`: etiquetas A y B; el mapa nombre-etiqueta solo en memoria (sección 5).
- Los fixtures contienen únicamente datos ficticios.

## 11. Parámetros previstos

Se añadirán a `config.yaml` al implementar el parser (no se han añadido): `parsing.date_order_hint` (nulo), `parsing.two_digit_year_century` (2000), `parsing.timestamp_like_window_chars` (40), los catálogos de marcadores y de avisos (hoy simulados) y el umbral de calidad por líneas no procesadas (pendiente).

## 12. Incompatibilidades detectadas

No se modificó nada de lo siguiente; se reporta para decidir:

1. **Nombres de tipo.** Las definiciones v0.5 (sección 1) llaman a los tipos `texto`, `media`, `sistema` y `eliminado`; este contrato usa `texto`, `media`, `system` y `deleted`, como se pidió. Hay que elegir qué nombre prevalece (y actualizar las definiciones en una versión posterior si cambian).
2. **Caracteres invisibles.** `config.yaml` lista U+202F en `parsing.invisible_chars` como carácter a eliminar. El contrato lo **sustituye por un espacio** en el texto (no es invisible: es un espacio estrecho) y lo conserva en `timestamp_original`. La lista de la configuración debería separarse en "se eliminan" y "se sustituyen por espacio".
3. **`00_escenarios_validacion.txt` tiene orden de fecha ambiguo.** Sus fechas van del 02/11 al 06/11/2026: ambos números son siempre ≤ 12 (`02/11` podría ser el 11 de febrero). Con este contrato la importación quedaría **bloqueada** sin `date_order_hint=dmy`. Los chats 01 y 02 sí se resuelven (tienen días 26 y 30 en la primera posición). Sus resultados esperados no se tocaron.
4. **`tools/referencia/ref_latency.py`.** Su lector adjunta al mensaje anterior toda línea que no empiece con una fecha y descarta en silencio las que empiezan con fecha y no encajan: no cumple la regla de la sección 3. Solo se usa con los tres chats de la Fase 0, y se comprobó que en ellos no hay ninguna línea de ese tipo (las únicas no-encabezado son las 2 continuaciones del chat 01), así que sus resultados no cambian.
5. **Comentario de la configuración.** `parsing` dice que los patrones "se prueban con exportaciones reales"; hoy no hay ninguna, solo fixtures simulados.

## 13. Preguntas abiertas

1. ¿Prevalecen `system`/`deleted` o `sistema`/`eliminado`?
2. Con orden de fecha ambiguo, ¿bloquear siempre (como aquí) o aceptar un valor por defecto de la configuración (por ejemplo `dmy`) y reportarlo? Se prefiere bloquear para no elegir por el usuario.
3. ¿Qué hacer con `00_escenarios_validacion`: pasar `date_order_hint` en sus pruebas o cambiar sus fechas?
4. ¿A partir de qué fracción de líneas no procesadas se considera el archivo de calidad insuficiente?
5. ¿Cómo se resuelve un contacto renombrado que produce 3 autores?
6. ¿Aplicar NFC al texto o conservarlo tal cual? ¿Es aceptable eliminar U+200F del texto en idiomas de derecha a izquierda?
7. ¿Deben reportarse en un nivel aparte los timestamps iguales a precisión de minuto (muy comunes) y a precisión de segundo (raros)?

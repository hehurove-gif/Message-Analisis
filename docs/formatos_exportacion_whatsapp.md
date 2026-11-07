# Formatos de exportación de WhatsApp

Versión 0.3 · 2026-11-07 · Fase 1.3 (dos formatos ya **observados** en exportaciones reales; el resto sigue simulado o documentado por terceros). Este documento dice qué sabemos, qué suponemos y qué no se puede saber de un TXT exportado. El contrato de lo que el parser debe producir está en `contrato_parser.md`; los fixtures, en `tests/fixtures/whatsapp/`.

## 1. Niveles de evidencia

Cada afirmación sobre un formato lleva uno de estos niveles. Solo `android_12h_es_nnbsp` y `android_12h_en_mdy` están en el nivel "observado" (sección 9.1).

| Nivel | Significa | Estado actual |
| --- | --- | --- |
| **Oficial** | Lo publica WhatsApp | Solo que la exportación es un archivo de texto, con o sin multimedia, y que no se puede reimportar. WhatsApp **no publica el formato de las líneas**. |
| **Documentado por terceros** | Lo describen la documentación o el código de proyectos abiertos que leen estas exportaciones | Cuatro familias de encabezado (sección 3). No las he verificado con exportaciones reales. |
| **Observado** | Visto en una exportación real examinada en este proyecto | `android_12h_es_nnbsp` (4 exportaciones) y `android_12h_en_mdy` (1). Examinadas en local por el usuario; solo se compartieron conteos y códigos. |
| **Simulado** | Escrito por mí para probar el parser, por extrapolación de lo documentado o sin respaldo | Todos los fixtures. Los datos son ficticios. |

Consecuencia: los fixtures prueban que el parser **hace lo que el contrato dice** con variaciones plausibles; **no demuestran** que cubra lo que WhatsApp produce hoy en cualquier teléfono, versión o idioma. Un formato pasa de simulado a observado solo cuando alguien lo compara con una exportación real (sección 9).

## 2. Fuentes consultadas (2026-11-02)

- [WhatsApp, "How to export your chat history"](https://whatsapp.com/faq/en/android/23756533): confirma que es un archivo de texto, que se elige "Sin multimedia" o "Incluir multimedia" y que no se puede reimportar. No dice nada del formato de líneas, de las marcas de tiempo ni de las variantes regionales.
- [chatpack (código del parser, docs.rs)](https://docs.rs/crate/chatpack/latest/source/src/parsers/whatsapp.rs): documenta cuatro formatos regionales (tabla de la sección 3) y detecta el formato en las primeras 20 líneas. Dato útil como **advertencia**: añade las líneas que no encajan al mensaje anterior y descarta en silencio las líneas previas al primer mensaje, que es justo lo que el contrato prohíbe. No muestra el manejo de caracteres invisibles. La fuente tampoco revela los patrones de avisos del sistema; solo los ejemplos de sus pruebas.
- [whatstk, "Export a WhatsApp chat"](https://whatstk.readthedocs.io/en/v0.3.0/source/getting_started/export_chat.html): en Android solo interesa el TXT; en iOS la exportación es un ZIP. Muestra versiones probadas (Android 9, iOS 12). No describe cabeceras ni variantes regionales.

Las demás fuentes que aparecieron en la búsqueda no se leyeron.

## 3. Catálogo de formatos

Patrón = forma del encabezado de un mensaje; después del encabezado va `Autor: texto` (mensaje de persona) o solo el texto (aviso del sistema en Android). Todos los fixtures son **simulados**; la columna "Respaldo" dice en qué se apoyan.

| Id | Plataforma | Encabezado (ejemplo) | Respaldo | Fixtures |
| --- | --- | --- | --- | --- |
| `android_24h_coma` | Android | `14/10/2026, 09:12 - ` | Documentado por terceros (chatpack, "EU2": `15/01/2024, 10:30 - `) | A01, A08, C01-C03, D01-D09, E01-E05 |
| `android_24h_sin_coma` | Android | `14/10/26 09:12 - ` (o `14/10/2026 09:12 - `) | **Sin respaldo** en las fuentes consultadas. Es el formato de los chats de `data/synthetic/` (con año de 4 dígitos), escrito por mí; A02 usa año de 2 dígitos | A02, `data/synthetic/00-02` |
| `android_12h_es_nnbsp` | Android | `14/10/2026, 9:12 a. m. - ` (U+202F antes de `a. m.`) | **Observado** en 4 exportaciones reales (Android, español; 2026-11). La fecha de 2 o 4 dígitos de año no se registró | A03 |
| `android_12h_compacto` | Android | `14/10/2026, 9:12 a.m. - ` | **Sin respaldo.** Extrapolación | A04 |
| `android_12h_en_mdy` | Android | `10/14/26, 9:12 AM - ` | **Observado** en 1 exportación real (Android; la primera exportación de un chat cuya re-exportación salió en `es_nnbsp`; causa no confirmada) | A05 |
| `android_24h_puntos_segundos` | Android | `14.10.2026, 09:12:05 - ` | Parcial: chatpack documenta `15.01.2024, 10:30 - ` (sin segundos); los segundos son extrapolación | A06 |
| `android_24h_guiones` | Android | `14-10-2026 09:12 - ` | **Sin respaldo** | A07 |
| `ios_24h_corchetes` | iOS | `[14/10/2026, 09:12:05] ` | Extrapolación de la familia con corchetes documentada por chatpack | B01, D03 |
| `ios_12h_es_corchetes` | iOS | `[14/10/26, 9:12:05 a. m.] ` | **Sin respaldo.** Extrapolación | B02 |
| `ios_12h_en_mdy_corchetes` | iOS | `[10/14/26, 9:12:05 AM] ` | Documentado por terceros (chatpack, "US": `[1/15/24, 10:30:45 AM] `); el U+202F antes de AM/PM es simulado | B03 |
| `ios_24h_puntos_corchetes` | iOS | `[14.10.26, 09:12:05] ` | Documentado por terceros (chatpack, "EU": `[15.01.24, 10:30:45] `) | B04 |

Los encabezados de ejemplo muestran el orden día/mes (o mes/día donde se indica); eso **no es un dato del formato**, sino una propiedad del idioma y la región del teléfono (sección 5).

### Elementos que se repiten en los fixtures (todos simulados)

| Elemento | Variantes simuladas |
| --- | --- |
| Aviso de cifrado | Español: "Los mensajes y las llamadas están cifrados de extremo a extremo…" · Inglés: "Messages and calls are end-to-end encrypted…" |
| Multimedia omitida (Android) | `<Multimedia omitido>`, `<Media omitted>`, `IMG-20261014-WA0001.jpg (archivo adjunto)` |
| Multimedia omitida (iOS) | `imagen omitida`, `sticker omitido`, `audio omitido`, `documento omitido` (con U+200E al inicio) |
| Mensaje eliminado | `Se eliminó este mensaje`, `Eliminaste este mensaje`, `You deleted this message`, `This message was deleted` |
| Avisos de chat individual | Mensajes temporales activados; cambio de número de teléfono |
| Avisos de grupo | Creación del grupo, altas y salidas, cambio de asunto (también un ejemplo en alemán, que el catálogo no cubre) |
| Invisibles | BOM al inicio del archivo; U+200E al inicio de línea y dentro del texto; U+200F; U+202F antes de `a. m.`/`AM` y dentro de un texto |

## 4. Rasgos de estructura que los fixtures dan por supuestos

1. Cada mensaje empieza con un **encabezado** (fecha y hora) y su texto puede continuar en las líneas siguientes, que **no** llevan encabezado.
2. En Android el aviso del sistema no lleva `Autor:`. En iOS puede aparecer con un nombre antepuesto (**hipótesis sin verificar**: se simula en B01 para probar que el parser no atribuya al nombre un aviso reconocido como sistema).
3. Una exportación usa un único formato de encabezado.
4. La codificación es UTF-8 y puede empezar con BOM. Los saltos de línea pueden ser `\n` o `\r\n`.

Si una exportación real contradice cualquiera de estos supuestos, se corrige el catálogo y los fixtures antes de tocar el parser.

## 5. Fechas, horas y regiones

- **Orden de la fecha.** `03/10/2026` puede ser 3 de octubre o 10 de marzo. El TXT **no declara** el orden. Reglas del contrato: si algún encabezado tiene un valor mayor que 12 en la primera posición, el orden es día/mes; si lo tiene en la segunda, mes/día; si hay ambos, el archivo es contradictorio y se rechaza; si ninguno lo tiene (todas las fechas con valores de 1 a 12), el orden **queda sin resolver** y la importación se bloquea hasta que el usuario lo indique. Fixtures C01 y C02.
  Se puede estudiar más adelante deducir el orden por la monotonía de las fechas (si solo un orden produce una secuencia cronológica), pero es evidencia débil y no se usa en esta versión.
- **12 horas.** `12:00 a. m.` es 00:00; `12:00 p. m.` es 12:00. Los indicadores pueden ser `a. m.`, `a.m.`, `AM`, con espacio normal, sin espacio o con U+202F. Fixtures A03, A04, A05, B02, B03.
- **Año de 2 dígitos.** `26` se interpreta como 2026 (siglo fijo: 2000 a 2099). Es una convención del proyecto, no un dato del formato.
- **Segundos.** Algunos formatos los traen y otros no; el timestamp normalizado declara su precisión (`minuto` o `segundo`). Sin segundos, **no se inventa**: se reporta precisión de minuto.
- **Zona horaria.** El TXT no incluye zona ni desfase. Los timestamps se conservan como hora local naive, tal como aparecen; no se convierten ni se asume zona. Un cambio de huso del teléfono o de horario de verano **no es detectable** (puede verse como retroceso, ver D04).

## 6. Conversaciones individuales y grupales

El proyecto solo analiza conversaciones entre dos personas. **Encontrar dos nombres no demuestra que el chat sea individual.**

### Qué puede y qué no puede determinar el TXT

| Se puede determinar | No se puede determinar |
| --- | --- |
| Cuántos autores distintos escriben mensajes en el archivo | Cuántas personas hay realmente en el chat (miembros que nunca escribieron no aparecen) |
| Si hay avisos del sistema propios de un grupo (creación, altas, salidas, cambio de asunto, de ícono o descripción) | Que no es un grupo, solo porque no hay esos avisos: un grupo exportado sin esos eventos, o con ellos fuera del rango exportado, es idéntico a un chat individual |
| Si un aviso menciona a una persona que no es uno de los autores | Si un nombre cambió (un contacto guardado con otro nombre, o con su número en lugar del nombre) y por eso parecen dos autores |
| Si el chat tiene exactamente un autor | Quién es el dueño del teléfono que exportó |
| | El nombre o el tipo del chat: en las exportaciones el nombre del chat suele estar en el nombre del archivo, que **no se usa** |

### Tres resultados, no dos

| Situación | Estado de tipo de conversación | Decisión de importación |
| --- | --- | --- |
| Más de dos autores | `rejected_more_than_two_participants` | Rechazada |
| Menos de dos autores | `rejected_fewer_than_two_participants` | Rechazada |
| Dos autores y al menos un aviso del sistema propio de grupo | `rejected_possible_group` | Rechazada |
| Dos autores sin evidencia de grupo | `pending_confirmation` | Aceptada; **requiere confirmación del usuario** antes del análisis |

El parser **nunca** emite "individual confirmado". Ese estado solo puede fijarlo el usuario, fuera del parser. "Pendiente de confirmación" significa que no se encontró evidencia de grupo en lo que hay, no que se haya descartado.

### Evidencias de grupo (catálogo dependiente del idioma)

Códigos: `GROUP_CREATED`, `MEMBER_ADDED`, `MEMBER_LEFT`, `MEMBER_JOINED_LINK`, `SUBJECT_CHANGED`, `ICON_CHANGED`, `DESCRIPTION_CHANGED`. El catálogo inicial cubre español e inglés y es **simulado**. Un aviso del sistema que no coincide con ningún patrón conocido se cuenta como "aviso sin catalogar" y genera la advertencia `SYSTEM_LINES_UNCLASSIFIED`: indica que la evidencia de grupo **no puede descartarse**. Fixtures E01-E05 y D05.

Avisos de chat individual que no cuentan como evidencia de grupo (también simulados): cifrado, mensajes temporales, cambio de número de teléfono.

### Riesgos conocidos

- **Falso negativo** (un grupo se acepta como pendiente): grupo con avisos en un idioma no catalogado (E03), grupo sin avisos en el rango exportado, grupo donde solo escriben dos personas.
- **Falso positivo** (un chat individual se rechaza): un contacto que cambia de nombre durante el periodo da 3 autores. El contrato no permite saltarse el rechazo; si ocurre, es una pregunta abierta (sección 10).
- **Aviso con dos puntos** (E04): un aviso como `Ana María cambió el asunto a "Equipo: planes"` se parte en "autor" y texto. Para no crear un autor fantasma, el parser reconoce los avisos por catálogo antes de separar autor y texto. Un aviso con dos puntos en un idioma no catalogado sí produciría un autor fantasma (el resultado conservador es rechazar por más de dos autores).

## 7. Limitaciones que el TXT no permite resolver

1. **Cita pegada con forma de encabezado** (D09): un mensaje que contiene, en una línea propia, algo con la forma de un encabezado válido es indistinguible de un mensaje real. El parser lo procesará como mensaje nuevo.
2. **Línea continuación con aspecto de timestamp** (D07, línea 13): `14/10/2026 a las 10:30 se movió la cita` puede ser texto legítimo. Se trata como "con aspecto de timestamp", se reporta y **no se anexa**; se acepta esa pérdida de precisión a cambio de no anexar nada por suposición.
3. **Orden de la fecha** cuando todas las fechas son ambiguas (C01).
4. **Zona horaria** y horario de verano.
5. **Miembros silenciosos de un grupo** y **cambios de nombre** (sección 6).
6. **Tipo real de una multimedia** cuando el marcador es genérico (`<Multimedia omitido>`): el subtipo es `desconocido`. Los stickers solo se distinguen donde el marcador lo dice (iOS simulado: `sticker omitido`).
7. **Reacciones, ediciones, respuestas citadas y mensajes reenviados**: en lo que revisé no hay constancia de que el TXT los marque; no se asume ninguna representación.
8. **Autoría de un mensaje eliminado**: el marcador no dice quién lo borró ni su contenido.
9. **Completitud de la exportación**: no se sabe si WhatsApp recortó el historial exportado (posible límite de mensajes, **no verificado** en las fuentes consultadas) ni si faltan líneas.
10. **Identidad del dueño del teléfono** y del propio nombre mostrado (`Tú`, un número, un nombre).

## 8. Archivos del repositorio relacionados

- `tests/fixtures/whatsapp/*.txt` y `*.esperado.json`: 33 fixtures simulados y lo que el parser debería producir con cada uno.
- `tests/fixtures/whatsapp/MATRIZ_COBERTURA.md`: relación fixture-caso.
- `tools/fixtures/generar_fixtures_whatsapp.py`: generador (escapes explícitos de caracteres invisibles) **que no es el parser**.
- `data/synthetic/00-02`: chats de comportamiento de la Fase 0; sirven también como fixtures de referencia del formato `android_24h_sin_coma`.

## 9. Cómo pasar un formato de "simulado" a "observado"

Si tienes una exportación real, no hace falta compartir conversaciones. Basta con tres o cuatro encabezados con nombres y texto reemplazados (p. ej. `14/10/2026, 09:12 - Persona1: texto`), más: sistema operativo y versión de WhatsApp, idioma y región del teléfono, y cómo se ven un aviso del sistema, una multimedia omitida y un mensaje eliminado. Con eso se actualiza el catálogo, se ajustan los fixtures y se corrige la columna "Respaldo".

### 9.1 Observaciones con exportaciones reales (2026-11-07)

| Formato | Exportaciones | Notas |
| --- | --- | --- |
| `android_12h_es_nnbsp` | 4 | Espacio estrecho U+202F antes de `a. m.`/`p. m.` |
| `android_12h_en_mdy` | 1 | Primera exportación de un chat; su re-exportación posterior salió en `es_nnbsp` |

Sin confirmar: región del teléfono, versión de WhatsApp y por qué la misma persona obtuvo dos formatos distintos. Pendientes en esas exportaciones: avisos del sistema sin catalogar y timestamps fuera de orden; se ubican sin ver contenido con `tools/revisar_avisos_y_orden_local.py`. Un formato observado en un solo teléfono no autoriza a llamar al parser "compatible con WhatsApp".

## 10. Preguntas abiertas

- ¿Debe existir una forma de que el usuario resuelva un rechazo por 3 autores cuando son dos personas con un contacto renombrado? Hoy no.
- ¿Debe el parser intentar resolver el orden de fecha por monotonía antes de bloquear? Hoy no.
- ¿Qué fracción de líneas no procesadas hace que un archivo se considere de calidad insuficiente? El contrato solo reporta; no hay umbral.

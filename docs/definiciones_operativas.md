# Definiciones operativas

Versión 0.6 · 2026-11-03 · Los tipos de mensaje se alinean con el contrato del parser v0.2 (única enumeración vigente). El resto de definiciones es el de la v0.5 aprobada para iniciar la Fase 1. El registro de cambios está al final.

Fijan qué significa cada término en el código y en los reportes. Los valores numéricos viven en `config.yaml`. Todo valor marcado como *provisional* o *experimental* es un criterio operativo configurable, no una afirmación sobre la realidad. El sistema analiza **lo que las personas comunican y cómo responden**; no pretende conocer directamente sus sentimientos.

## 1. Unidades de análisis

**Mensaje.** Entrada individual de la exportación, con timestamp y autor. Siempre se conservan los mensajes originales y sus timestamps. Tipos (valores canónicos, los mismos que `docs/contrato_parser.md`): `texto`, `media` (multimedia omitida o adjunta), `system` (aviso sin autor) y `deleted` (mensaje eliminado). Solo `texto` entra en las métricas lingüísticas; `media` y `deleted` cuentan como actividad sin contenido analizable; `system` no pertenece a ninguna persona y no cuenta como mensaje de ninguna. El contenido de un mensaje es el **original** (`texto`); cualquier representación normalizada para análisis es un campo derivado aparte (`texto_normalizado`) y no lo sustituye.

**Ráfaga.** Mensajes consecutivos del mismo participante cuyo intervalo es **menor o igual** a `segmentation.burst_max_gap_seconds` (valor inicial **experimental** de 300 s). Sirve para estudiar hábitos de escritura y fragmentación.

**Turno conversacional.** Mensajes consecutivos del mismo participante hasta que interviene el otro, dentro de una misma sesión. El turno **no** depende del intervalo de la ráfaga: un turno puede contener varias ráfagas.

> Ejemplo. A las 10:00, A envía 3 mensajes. A las 10:08, A envía 2 más. A las 10:15, B responde.
> Resultado: un turno de A (con dos ráfagas, de 3 y 2 mensajes) y luego un turno de B.

**Sesión.** Conjunto de turnos separados entre sí por un intervalo **menor o igual** a `segmentation.session_gap_hours` (valor **provisional** de 6 h; se prueba con 2, 6 y 12 h). La sesión se corta solo cuando el silencio **supera** el umbral. Es un criterio operativo y **no se asume que represente una separación real entre conversaciones**.

**Registro por turno.** De cada turno se conserva, sin interpretarlo: primer y último timestamp, **tiempo transcurrido**, número de mensajes, número de ráfagas, **intervalos de silencio** entre mensajes consecutivos y **tiempo dentro de ráfagas** (suma de los intervalos que no superan el de la ráfaga). El tiempo transcurrido **no equivale a actividad efectiva**: un turno de 10:00 a 15:00 no significa cinco horas de conversación, ni es por sí solo indicador de interés o participación.

## 2. Eventos de sesión

Se registran por separado y sin atribuir intención:

**Reanudación.** Primer turno de una sesión (quién retoma la comunicación tras un periodo de inactividad). No se interpreta que quien reanuda tenga más interés.

**Último mensaje de la sesión.** Autor del último turno de una sesión. No se interpreta que esa persona terminó voluntariamente la conversación.

Ambos son **observaciones**. Un mismo turno puede ser a la vez una reanudación y la siguiente intervención del interlocutor (A escribe a las 23:30, B contesta a las 08:00: reanudación **y** latencia de 8 h 30 min).

## 3. Latencia hasta la siguiente intervención del interlocutor

**Intervención siguiente.** Para un turno de X, el mensaje inmediatamente posterior del chat, si es del otro participante Y. No hay límite máximo de tiempo ni dependencia de la sesión.

**Latencia.** Tiempo entre el **último** mensaje del turno de X y esa intervención de Y. Se asigna a quien interviene.

> A escribe a las 10:00, 10:00 y 10:01; B interviene a las 10:03: latencia de B **2 min**.
> A escribe a las 23:30; B interviene a las 08:00 del día siguiente: latencia de B **510 min**, entre sesiones.

**Estados de un turno** (mutuamente excluyentes):

1. **Con intervención.** El siguiente mensaje es del otro participante. Tiene latencia.
2. **Sin intervención previa a su nuevo turno.** El siguiente mensaje es del **mismo autor**, ya en otra sesión: la persona vuelve a escribir tras un periodo de inactividad sin que el otro haya intervenido. Es un estado **independiente** de "sin respuesta observada" y:
    - **no tiene latencia** y **no entra en las medianas**;
    - **no demuestra indiferencia ni rechazo** del otro participante;
    - **su clasificación puede cambiar con el hueco de sesión**: un turno puede ser "con intervención" con 12 h y "sin intervención previa" con 2 h (ver `00_escenarios_validacion`: 5, 2 y 2 turnos en ese estado con 2, 6 y 12 h). Se reporta con cada hueco.
3. **Sin respuesta observada.** No hay ningún mensaje posterior (solo ocurre en el último turno del chat). Es un límite de los datos y **no** evidencia de indiferencia ni de rechazo.

**Métricas obligatorias**, por participante que interviene: mediana **general**, mediana **dentro de la misma sesión** (latencia ≤ hueco), mediana **entre sesiones** (latencia > hueco), **proporción** de intervenciones dentro y fuera de sesión y número de turnos en cada estado. La mediana general no depende del hueco; las demás sí, y se reportan con 2, 6 y 12 h.

**Siguiente intervención no equivale a respuesta semántica.** Que B sea el siguiente en escribir no demuestra que conteste el mensaje de A. La **relación semántica** de una intervención con el mensaje anterior puede ser `directa`, `parcial`, `no_relacionada` o `no_determinada` (valor por defecto hasta la Fase 6; las etiquetas manuales de los chats sintéticos sirven de referencia).

**Pregunta.** Mensaje de texto con `?` o que empieza con palabra interrogativa. Aproximación: se revisará con muestras manuales.

## 4. Eventos léxicos, clases de evento e indicadores candidatos

**Evento léxico.** Coincidencia entre un mensaje y una regla de diccionario. Guarda mensaje, fecha, categoría y regla. Es un dato sobre el texto, no sobre la persona. **Unidad de conteo: un evento por mensaje**, aunque tenga varias coincidencias.

**Clases de evento** (cada evento etiquetado tiene una):

| Clase | Qué es | Conteo principal |
| --- | --- | --- |
| `linea_base` | Saludo convencional ("buenos días", "buenas noches") o emoji no afectivo por sí solo (😊, ☀️). Forma la línea base de esa persona. | No |
| `calidez_no_especifica` | Expresión amable que excede la convención pero no apunta a una persona ni a un vínculo en concreto (p. ej. "que tengas un día increíble"). Se conserva como **evidencia contextual**, porque puede indicar un cambio en la comunicación de esa persona. | **No**; sí en la sensibilidad S1 |
| `indicador_candidato` | Cumplidos personales o físicos, propuestas de verse a solas, apodos cariñosos, saludos con elemento afectivo (apodo, ❤️), interés en la vida íntima del otro. | Sí |
| `declaracion_explicita` | Manifestación directa de interés. Se reporta como cita y se analiza aparte de la recurrencia. | No (separada) |
| `no_candidato` | Cualquier otro evento (elogio de una habilidad, sarcasmo, queja en broma). | No |

Un deseo amable no contribuye igual que una invitación explícita a verse a solas: por eso no se cuentan en la misma clase. **No hay suma ponderada ni índice romántico.**

**Un candidato no equivale a interés romántico.** Un cumplido puede ser amistoso, romántico, sarcástico, cortés o parte de la manera habitual de hablar de alguien. Para considerarse algo más que ruido se exige: (1) **recurrencia** (`min_events_for_pattern` eventos en `min_distinct_periods` periodos distintos); (2) **línea base individual**; (3) **contexto**; (4) **respuesta de la otra persona** (sección 5). Los umbrales de recurrencia son **valores experimentales**: tres eventos en dos semanas no son una validación científica de interés romántico; solo deciden si el sistema reporta una recurrencia **descriptiva**, necesaria pero no suficiente.

**Dos dimensiones separadas** de los candidatos:

- **Frecuencia:** número de eventos candidatos por persona y periodo (se mide y se compara).
- **Especificidad provisional:** anotación cualitativa (`baja`, `media`, `alta`) de qué tan específicamente romántico es el evento frente a una expresión afectuosa general. **No es una puntuación científica, no pondera la frecuencia y no altera ninguna métrica**. Se reporta aparte (distribución de valores) y solo puede usarse en una sensibilidad si se justifica explícitamente.

Marca `ambiguo`: un candidato cuya inclusión es discutible (p. ej. un ❤️ en un saludo, un elogio genérico) se marca para la sensibilidad S2, sin quitarlo del conteo principal.

## 5. Respuesta a un indicador

Para cada candidato se registran, por separado: (a) la **siguiente intervención y su latencia** (sección 3); (b) su **relación semántica**; (c) la **categoría de respuesta**, que describe lo comunicado y no sentimientos. Hay una categoría principal y, como máximo, una secundaria.

| Categoría | Qué significa |
| --- | --- |
| `respuesta_directa` | Contesta el contenido de la pregunta o petición, sin carga afectiva ni invitación. Ej.: "no, ahorita estoy enfocada en la escuela". |
| `reconocimiento_sin_correspondencia_afectiva` | Agradece, acusa recibo o devuelve cortesía sin devolver afecto equivalente. |
| `correspondencia_afectiva` | Devuelve afecto equivalente de forma explícita (apodos, cumplidos, emojis o expresiones propias). No se infiere de la cordialidad. |
| `reciprocidad_amistosa_ambigua` | Devuelve confianza o cordialidad que cabe en una amistad y en otros vínculos. |
| `invitacion_aceptada` | Acepta la invitación. |
| `invitacion_declinada` | Rechaza **esa** invitación concreta, con o sin motivo. No demuestra por sí sola ausencia de interés romántico ni se extiende a otras invitaciones. |
| `invitacion_pospuesta_o_no_comprometida` | Ni acepta ni rechaza: aplaza o condiciona ("veamos cómo nos va", "no sé"). No es una negativa definitiva. |
| `cambio_de_tema` | Reconoce o pasa por alto el mensaje y reorienta hacia otro asunto. Suele ser etiqueta secundaria. |
| `respuesta_no_relacionada` | La siguiente intervención no hace referencia al mensaje. |
| `limite_interpersonal_suave` / `limite_interpersonal_explicito` | Pide que cese una conducta o delimita la relación. Se registra con su **alcance** (apodos, trato, relación romántica, contacto) y **no se extiende automáticamente** a otros aspectos. |
| `sin_respuesta_semantica_observable` | No hay intervención evaluable (sin respuesta observada o sin intervención previa a un nuevo turno). |

**Reglas.** Una respuesta ambigua no se clasifica como rechazo: si el texto no establece una negativa, se usa `invitacion_pospuesta_o_no_comprometida` o `reciprocidad_amistosa_ambigua`. Ni la demora ni la ausencia de respuesta se interpretan como indiferencia. Una respuesta corta o lenta puede ser el estilo normal de esa persona, por lo que se compara con su línea base de longitud y latencia y con el **tipo de mensaje** al que responde.

**Límite de la interpretación.** Con base en las respuestas, el sistema puede decir que **no hay correspondencia romántica explícita en la conversación analizada**; **no puede determinar** que la otra persona carezca de interés romántico. Cuando alguien lo expresa, sí puede reportarse como observación (con cita) que dijo, por ejemplo, que ve a la otra persona como un amigo.

## 6. Balance de participación y reciprocidad

Son conceptos distintos:

- **Balance de participación:** distribución de turnos, mensajes y palabras entre los participantes (palabras = fragmentos separados por espacios en mensajes de texto). Cada unidad se reporta **por separado**, con su distribución. **No se reduce todavía a una etiqueta única** como "participación equilibrada", y no existe un indicador compuesto de equilibrio hasta investigar cómo construirlo. Solo se puede describir, de forma neutra, que las distribuciones están relativamente cercanas o alejadas **en cada unidad medida**. La distribución de turnos depende del hueco de sesión; la de mensajes y palabras no.
- **Reciprocidad:** concepto amplio (respuestas, seguimiento de temas, preguntas, iniciativas y apoyo). **No se mide completo**; seguimiento de temas y apoyo requieren análisis semántico (Fase 6). Que ambos tengan el mismo número de turnos no demuestra una relación recíproca.
- **Correspondencia formal (v0.1, `metrics/correspondence.py`):** la parte medible de la reciprocidad. En los reportes se llama **correspondencia**, no reciprocidad, porque solo mide la **forma** de los mensajes. Unidad: **par de turnos** (turno de X seguido del siguiente turno de Y) **dentro de la misma sesión** y sin fuera de orden. Dirección `A_a_B` = estímulo de A, respuesta de B (lo que A recibe). Cuatro dimensiones separadas, **sin índice compuesto**:
  - **R1 Extensión:** ρ de Spearman entre palabras sustantivas del estímulo y de la respuesta; mediana de la respuesta tras turnos mínimos, breves y desarrollados.
  - **R2 Preguntas:** proporción de respuestas no mínimas tras un turno con pregunta menos la misma proporción tras turnos sin pregunta (línea base de quien responde, §9.3). No verifica que la pregunta se conteste.
  - **R3 Turnos desarrollados:** distribución mínimo/breve/desarrollado de la respuesta tras un turno desarrollado vs tras uno breve; se etiqueta con la diferencia en proporción no mínima. Sensibilidad con umbrales 10/15/25.
  - **R4 Iniciativa:** reanudaciones de sesión (2/6/12 h, con la robustez existente) e inicio del día lógico; reparto, no pares.
  - **Etiquetas R1–R3:** `simetrica` (diferencia entre direcciones < 0.10; ρ: < 0.15), `asimetrica_hacia_A`/`_B` ("hacia A" = A recibe más correspondencia de la que da), `diferencia_de_linea_base` (R2/R3: la diferencia es asimétrica pero las tasas absolutas ante el estímulo difieren menos de 0.10; lo distinto es lo habitual de quien responde, p. ej. efecto techo), `insuficiente` (< 30 pares por dirección o < 10 estímulos por grupo), `sensible_a_umbrales` (la dirección cambia con el hueco 2/6/12 h o el umbral 10/15/25; no se reporta como patrón). Umbrales experimentales en `config.yaml → reciprocity`.
  - **No es** interés, afecto, cercanía ni calidad de la relación; un chat exportado es una muestra parcial.

## 7. Frecuencia de comunicación y cercanía (reserva para la clasificación de vínculos)

Al clasificar relaciones se separan:

- **Frecuencia de comunicación:** medición observable (días con mensajes sobre días del periodo, mensajes por día activo, mensajes por semana).
- **Cercanía interpersonal:** interpretación compleja, siempre **hipótesis**. Hablar a diario no implica una relación cercana, y una relación cercana no requiere hablar a diario; ninguna se infiere de la otra.

## 8. Evaluación de la evidencia

Cada hallazgo del reporte lleva **tres ejes independientes**:

**Estado epistémico**

- **Observación:** dato directo, calculable y reproducible, sin interpretación.
- **Patrón:** comportamiento que cumple la recurrencia y no cambia en la parte de la rejilla que le corresponde. Es descriptivo: dice *qué se repite*, no *por qué*.
- **Hipótesis:** interpretación sobre intención, sentimiento o naturaleza del vínculo. Siempre con su evidencia y explicaciones alternativas.

**Suficiencia de datos:** `suficiente`, `insuficiente` o `no_evaluada`, según los mínimos de `data_sufficiency`.

**Robustez, por familia de parámetros.** Las pruebas de sensibilidad se separan según la métrica y **no se cruzan entre familias**; cada hallazgo declara qué familias le afectan y cuáles se probaron:

| Familia | Parámetros que recorre | Afecta a |
| --- | --- | --- |
| **Recurrencia** | mínimo de eventos (2 a 5) × mínimo de periodos (1 a 3) × granularidad (semana, mes) | Si un comportamiento se reporta como recurrente |
| **Segmentación** | hueco de sesión (2, 6, 12 h) y separación de ráfagas (120, 300, 600 s) | Turnos, sesiones, reanudaciones, estados de turno, latencia dentro y entre sesiones, ráfagas |
| **Indicadores** | variantes de inclusión: P (principal), S1 (P + calidez no específica), S2 (P sin candidatos ambiguos) | Conteos de candidatos y cualquier comparación que dependa de ellos |

Resultado por familia: `robusto ante <familia>` (mantiene dirección y categoría en **toda la parte evaluable** de esa familia), `robusto en dirección, magnitud sensible`, `sensible a <familia>` o `no probada`. Reglas:

- **"Robusto" nunca se usa solo.** Siempre va con la familia y con lo que se probó (p. ej. "robusto ante recurrencia: 12 de 12 combinaciones semanales; 4 mensuales no evaluables").
- Una configuración que la ventana de datos no permite probar (la granularidad tiene menos periodos que el mínimo exigido) se marca **no evaluable**. No se cuenta como cumplida ni como incumplida y no equivale a una validación satisfactoria.
- Un hallazgo `sensible` no puede presentarse como patrón.
- **La robustez ante parámetros no equivale a validez científica**: indica que un resultado no depende de un parámetro, no que mida lo que se pretende medir.

No hay niveles de confianza ni probabilidades. Las etiquetas son heurísticas experimentales; no están calibradas estadísticamente. Reglas generales: una observación no sube a patrón sin recurrencia y sin robustez; un patrón nunca sube a hecho sobre intenciones; **no concluyente** es un resultado legítimo.

## 9. Reglas generales

1. Las conclusiones no se apoyan en eventos aislados.
2. Nunca se afirma un sentimiento o intención ("A está enamorado"); se reportan indicadores y respuestas observables.
3. Los hábitos individuales cuentan: quien responde tarde o casi no usa emojis no debe leerse como "frío".
4. Las reglas no se validan solo con ejemplos sencillos: los casos ambiguos y los falsos positivos conocidos forman parte de las pruebas.
5. Los chats sintéticos prueban definiciones y cálculos. **No demuestran** que el sistema identifique correctamente relaciones reales.
6. **Reproducibilidad:** cada cálculo de referencia imprime los parámetros que usa (bloque `PARAMETROS`) y cada tabla de resultados esperados indica el hueco de sesión, la variante de indicadores y la granularidad empleados.
7. Límites de alcance: las reacciones normalmente no aparecen en la exportación de WhatsApp y los stickers solo figuran como multimedia omitida.
8. Todo el procesamiento es local y los participantes se muestran como A y B.

## 10. Aspectos abiertos (no determinables todavía)

- Cómo construir un indicador compuesto de balance de participación, si procede.
- Qué características distinguen una expresión afectuosa general de una señal específicamente romántica, y qué tan fiable puede ser esa distinción (de eso depende cualquier uso de la especificidad).
- Dónde está el límite entre `calidez_no_especifica` e `indicador_candidato`; por ejemplo, el elogio genérico ("eres la mejor") de un agradecimiento.
- Reciprocidad semántica (seguimiento de temas, apoyo, respuesta efectiva a preguntas); calibración de los umbrales de correspondencia.
- Cómo estimar automáticamente la relación semántica de una intervención.
- Calibración de los umbrales experimentales con datos reales.

## Registro de cambios

**v0.12 (2026-11-08).** Evolución (`metrics/trends.py`), a partir de las primeras corridas con chats reales: (1) **pausa**: periodo sin mensajes dentro de un hueco > `latency.long_pause_days` (30) entre dos días con mensajes; se reporta en `pausas` y no entra en la detección (que el chat se detenga no es un cambio sostenido de frecuencia); (2) serie `rapida_X` = proporción de latencias de X dentro de la sesión ≤ `temporal.quick_response_minutes` (5), porque la mediana de latencia vale 0 casi siempre con resolución de minuto; (3) **sensibilidad a la granularidad**: cada cambio se repite con la otra granularidad (mes ↔ semana ISO): `robusto` si ambas lo detectan en la misma dirección, `sensible_a_granularidad` si solo una o difieren (no se reporta como patrón). `segmentar_local` añade `pares_de_turnos_fuera_de_orden` (retroceso entre turnos de distinto autor). Sin cambios en umbrales existentes.

**v0.13 (2026-11-09).** Fase 5.1, capa léxica de CONTEO BRUTO (`nlp/`, `metrics/lexical.py`, `lexicon/es_mx.yaml`, config `lexicon:`; ver `propuesta_fase5_lexico.md` v0.2): (1) evento = UN por (categoría, forma) y mensaje, con `n_coincidencias` (ocurrencias); (2) coincidencia por palabra(s) completa(s) sobre texto normalizado (sin acentos, letras alargadas reducidas); (3) forma `negada` (negador en las 3 palabras previas de la misma oración) o `pregunta` (aparte, no cuentan); (4) excepciones (`te quiero` + infinitivo, apodos solo como vocativo) no son eventos y se cuentan por regla en `descartes`; (5) por persona: mensajes con evento, ocurrencias, turnos con evento, días con evento (día lógico) junto a sus denominadores; variantes estricta (no ambiguas, afirmativa) y amplia (+ambiguas) y `robustez_indicadores`; (6) el léxico local (`lexicon_local.yaml`) vive junto a las exportaciones y nunca se imprime. Ninguna clase contextual se asigna (`pendiente_fase_6`). Sin cambios en umbrales existentes.

**v0.14 (2026-11-09).** Fase 5.2: categorías restantes en `lexicon/es_mx.yaml` (`apodo_carinoso`, `cumplido`, `propuesta_de_verse`, `apoyo`, `conflicto`, `disculpa`, `gratitud`, `risa_texto`). Motor: (1) reglas con `regex`, `pregunta_cuenta` (la invitación interrogativa cuenta como afirmativa; la negada no), `no_si_sigue_pregunta` ("disculpa, ¿a qué hora…?" se descarta), `excepto_si_sigue` ("gracias a dios"); (2) vocativo = cierra la cláusula, o la abre con pronombre/verbo típico; (3) si dos reglas de una categoría coinciden en el mismo tramo gana la no ambigua y no hay doble conteo; (4) ambiguas (solo en variante amplia): apodos generales ("amor", "linda"), "lo siento", "perdón"/"disculpa" sueltos, "ánimo", "abrazo", insultos coloquiales. Marcadores de "a solas" (`tu_y_yo`, `solos`) NO se implementan: dato abierto. `gratitud`, `risa_texto`, `emoji_risa`, `emoji_base` son `linea_base`; el resto `pendiente_fase_6`. Sin cambios en umbrales.

**v0.15 (2026-11-09).** Fase 5, primer ajuste con datos reales (solo recuentos; sin contenido): (1) nueva categoría `emoji_otro`: todo emoji que ninguna regla específica cubre se cuenta ahí, de modo que las categorías de emoji cubren TODOS los emojis (base de conteo bruto completa); los modificadores de tono de piel y los signos de género no cuentan como emojis por sí solos; (2) 😔 pasa a ambigua (uso como "ni modo"; en un chat real un solo emoji repetido dominaba `emoji_tristeza`); 🫶 → `emoji_afectivo`, 🤨 → `emoji_posible_ironia` (ambigua); (3) `mensajes_por_regla` en la salida para saber qué regla produce cada conteo; (4) `tools/emojis_frecuentes_local.py`. Sin cambios en umbrales.

**v0.16 (2026-11-09).** Fase 5: `mensajes_por_expresion` (por categoría, las expresiones coincidentes y cuántos mensajes de cada persona las contienen; vocabulario de la regla, nunca texto libre; las reglas locales aparecen como "(local)"). Sirve para saber qué expresión concreta domina un conteo antes de decidir si una regla es ambigua. `metricas_local` muestra las 10 más frecuentes por categoría (variable de entorno `LEXICO_TOP`). Sin cambios en umbrales.

**v0.17 (2026-11-09).** Fase 5, segundo ajuste con la tabla de expresiones de un chat real (solo recuentos): (1) "suerte"/"mucha suerte" salen de `apoyo` (buen deseo, dominaba el 70 % de la variante amplia); (2) los adjetivos (bonito/a, lindo/a, hermoso/a, guapo/a, precioso/a) dejan de ser apodos sueltos y solo cuentan con "mi" ("mi bonita"); (3) "quedamos en" y "quedamos para" salen de `propuesta_de_verse` ("quedamos en que…" es un acuerdo). Quedan para la validación manual (5.4): `disculpa` explícita ("perdóname" dominante en un participante), `insulto` no coloquial ("estúpido", "idiota" pueden ser autodirigidos), "ánimo" (también "sin ánimo"). Sin cambios en umbrales.

**v0.18 (2026-11-10).** Fase 5.4, validación manual por muestra (`tools/revisar_eventos_local.py`, `metrics/validation.py`, config `lexicon.validation`): (1) muestra por categoría n = ⌈N·96/(96+N−1)⌉ (margen ±10 % al 95 %, población finita; N<10 eventos → se revisan todos y la categoría queda `no_validada`), repartida proporcionalmente entre reglas y participantes con mínimo 1 por estrato; (2) solo eventos afirmativos de categorías de texto (los emojis no se revisan: la coincidencia es exacta); (3) veredicto del revisor c/i/a; precisión = correctos/revisados (ambiguos no cuentan como correctos) con intervalo de Wilson al 95 %; etiquetas `valida` (punto ≥ 0,80 o límite inferior ≥ 0,70), `baja_precision`, `no_validada` (< 10 revisados); regla con ≥ 10 revisados y precisión < 0,60 → `REVISAR/ELIMINAR`; (4) recuperación: muestra sistemática de hasta 300 mensajes sin evento, tasa de expresiones no detectadas con Wilson; (5) la hoja de revisión no contiene texto salvo `--con-texto`; vive fuera del repo y no se sobrescribe. Valores experimentales.

**v0.19 (2026-11-10).** Fase 5, primera revisión manual de una muestra real (190 eventos + 100 mensajes sin evento; veredictos de una primera lectura, pendientes de confirmar por el usuario). Hallazgos y cambios de léxico (reglas): (1) `apodo_carinoso`: precisión ≈ 6 % (sustantivos: "de mi vida", "el cariño", "al cielo"); el vocativo exige ahora que la expresión abra la cláusula y la cierre (o la siga un pronombre/verbo típico), o que la cierre tras un saludo/interjección; (2) `conflicto.insulto*`: ≈ 0 % (insultos a terceros o a uno mismo, no conflicto entre ambos); solo cuentan insultos DIRIGIDOS al otro ("eres un idiota", "qué idiota eres"); (3) `apoyo`: "ánimo" pasa a regla estricta (≈ 90 % de aciertos), "tranquilo/a" solo como vocativo y ambigua, "abrazo" suelto sale; (4) `propuesta_de_verse`: "nos vemos mañana/el/en la…" y "te veo a las…" (despedidas) pasan a la regla ambigua; "salimos a las" sale; (5) `disculpa`: "me equivoqué" pasa a ambigua (≈ 95 % de aciertos en el resto). Recuperación: 1 de 100 mensajes sin evento tenía una expresión no detectada. Estas cifras no se reportan como resultados: son de un chat privado. Sin cambios en umbrales.

**v0.11 (2026-11-08).** Saludos y despedidas: la coincidencia pasa de subcadena a palabra(s) completa(s) ("descansa" ya no coincide con "descansar" ni "buen dia" con "buen diario"). Cierre de Fases 3 y 4 con chats sintéticos largos (`docs/reporte_pruebas_fase_3_4.md`); no cambia ningún umbral ni definición de métricas.

**v0.10 (2026-11-07).** Saludos y despedidas (`metrics/greetings.py`, config `greetings`): mensajes con "buenos días"/"buenas noches" (y variantes), días en que cada uno lo dice primero y si el otro corresponde ese día lógico; línea base, no indicador de interés. Evolución: % de multimedia de cada uno por periodo.

**v0.9 (2026-11-07).** Ritmo (`metrics/rhythm.py`): duración, turnos y mensajes por sesión; quién deja el último turno sin respuesta antes del corte ("cierra", sin la última sesión del chat; no implica intención); días activos, racha más larga y pausa más larga en días lógicos; mensajes por turno y por ráfaga por participante.

**v0.8 (2026-11-07).** Evolución temporal (Fase 4, `metrics/trends.py`): por mes (semana ISO opcional) se reportan % de mensajes, palabras sustantivas, turnos desarrollados e inicio del día de A, días activos (§7) y latencia mediana dentro de la sesión de cada uno. Cambio sostenido = mediana móvil (4 periodos) alejada de la base de los 4 primeros más de 0.15 absoluto (proporciones) o 50% relativo (latencias) durante 3 periodos seguidos. Periodos con < 5 mensajes quedan sin dato.

**v0.7 (2026-11-07).** Correspondencia formal v0.1 (§6): R1–R4 por dirección, pares solo dentro de la misma sesión, sin índice compuesto, umbrales experimentales (30 pares, 10 estímulos, 0.10 / ρ 0.15). Se reporta como "correspondencia", no "reciprocidad".

**v0.6 (2026-11-03).** Solo la enumeración de tipos de mensaje: `sistema` → `system` y `eliminado` → `deleted`, para no mantener dos enumeraciones incompatibles con el contrato v0.2; se aclara que el contenido es el original y que la normalización es un campo derivado. No cambia ninguna otra definición, parámetro ni resultado esperado de los tres chats.

**v0.5 (2026-11-02)**

- Nueva clase `calidez_no_especifica`: evidencia contextual excluida del conteo principal y presente en la sensibilidad S1. Se separan las clases de evento y se añade la marca `ambiguo`.
- Frecuencia y especificidad provisional quedan como dimensiones separadas; sin suma ponderada ni índice romántico; `peso_esperado` pasa a `especificidad_provisional`.
- El balance de participación se reporta por unidad, sin etiqueta compuesta.
- La robustez se evalúa por familia (recurrencia, segmentación, indicadores); "robusto" no se usa solo; las configuraciones que no se pueden probar son "no evaluables"; la robustez no equivale a validez científica.
- Los scripts de referencia dejan de fijar un número de versión y siempre imprimen sus parámetros. Se añade la sección de aspectos abiertos.

**v0.4 (2026-11-01).** Estado "sin intervención previa" independiente; línea base de saludos; 12 categorías de respuesta con alcance de los límites; balance separado de reciprocidad; frecuencia separada de cercanía; estado epistémico, suficiencia y robustez en lugar de niveles de confianza.

**v0.3 (2026-10-31).** Latencia hasta la siguiente intervención del interlocutor sin ventana; medianas general, dentro y entre sesiones; registro por turno; respuesta semántica separada de la siguiente intervención.

**v0.2 (2026-10-30).** Ráfaga y turno separados; reanudación y último mensaje como eventos independientes; estados epistémicos; un indicador no equivale a interés romántico.

**v0.20 (2026-11-11).** Fase 5, segunda revisión manual (semilla 2, muestra nueva con las reglas ya corregidas; veredictos de una primera lectura, pendientes de confirmar por el usuario; cifras de un chat privado, no se reportan como resultados). Efecto de los ajustes de v0.19: `apodo_carinoso` sin falsos positivos en la muestra; `conflicto` sin insultos; `apoyo.consuelo` ≈ alta precisión. Cambio: `conflicto.reclamo` se divide en regla estricta ("me molesta que", "estoy harto/a", "me decepcionas", "nunca me escuchas…") y `conflicto.reclamo_ambigua` ("siempre dices/haces", "ya basta", "no es justo"; solo en variante amplia), porque eran descripciones o bromas. Conocido y sin cambio: `verse.ambigua` (despedidas) tiene baja precisión por diseño y solo cuenta en la amplia; "ya no estás sola" coincide con "no estás sola" (falso positivo aislado). Sin cambios en umbrales.

**v0.21 (2026-11-11).** Fase 5.3: serie del léxico por periodo (`metrics/lexical.py::lexical_series`, mes por defecto, semana ISO con `--semanal`). Por categoría, persona y periodo: mensajes con evento (estricta y amplia), mensajes de texto y tasa por 100 mensajes. La "dirección" de un periodo (quién tiene más por 100 mensajes, variante estricta) solo se asigna con ≥ 5 eventos en el periodo (`min_events_per_period_for_trend`) y una diferencia ≥ 25 %; si no, `igual` o sin dirección. Resumen: periodos válidos, cuántos lidera cada persona y líder dominante (≥ 75 % de los periodos válidos; si no, `mixto`; con < 3 válidos, `insuficiente`), repetido con la otra granularidad (`robusto` / `sensible_a_granularidad`, que no se reporta como patrón). Es el mismo conteo bruto repartido en el tiempo: sin interpretación. Informes locales: por defecto usan los nombres de cada chat en lugar de A/B (`nombres_local.json` junto a los chats, editable para nombres cortos; `--anonimo` conserva A/B). Con nombres el informe es un archivo privado local (no se sube al repo); el análisis interno y las fotos para comparar siguen con A/B y la comparación ignora los nombres.

**v0.22 (2026-11-11).** Informe visual (`tools/informe_visual_local.py`, o `informe_local.py --html`): una página HTML con scroll a partir de la "foto" .json del informe. Tailwind por CDN para los estilos (con respaldo local de las mismas utilidades) y gráficas SVG propias; ningún dato sale del equipo. Secciones por chat: participación, evolución por periodo, tiempo de respuesta, hábitos horarios, estilo, ritmo, saludos, léxico (conteo bruto con marca de referencia = reparto esperado por participación), léxico por periodo, correspondencia formal. Sin índices compuestos ni interpretación: solo las mismas métricas ya definidas, con sus etiquetas de suficiencia y robustez. Nunca incluye texto de mensajes; incluye nombres solo si el informe se generó con nombres (v0.21). No se lee ni se escribe dentro del repo.


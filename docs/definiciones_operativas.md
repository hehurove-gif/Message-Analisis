# Definiciones operativas

Versión 0.4 · 2026-11-01 · **Pendiente de aprobación definitiva** (criterio de salida de la Fase 0). El registro de cambios está al final.

Fijan qué significa cada término en el código y en los reportes. Los valores numéricos viven en `config.yaml`. Todo valor marcado como *provisional* o *experimental* es un criterio operativo configurable, no una afirmación sobre la realidad. El sistema analiza **lo que las personas comunican y cómo responden**; no pretende conocer directamente sus sentimientos.

## 1. Unidades de análisis

**Mensaje.** Entrada individual de la exportación, con timestamp y autor. Siempre se conservan los mensajes originales y sus timestamps. Tipos: `texto`, `media` (multimedia omitida, stickers, ubicación), `sistema` y `eliminado`. Solo `texto` entra en las métricas lingüísticas; `media` y `eliminado` cuentan como actividad sin contenido analizable; `sistema` no pertenece a ninguna persona.

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

## 4. Eventos léxicos, línea base e indicadores candidatos

**Evento léxico.** Coincidencia entre un mensaje y una regla de diccionario. Guarda mensaje, fecha, categoría y regla. Es un dato sobre el texto, no sobre la persona. **Unidad de conteo: un evento por mensaje**, aunque tenga varias coincidencias.

**Línea base de comunicación.** Los saludos convencionales ("buenos días", "buenas noches") y los emojis no afectivos por sí solos (😊, ☀️) **no son candidatos**: forman la línea base de esa persona. Un saludo cuenta únicamente si añade un elemento afectivo (apodo cariñoso, emoji afectivo como ❤️, un deseo que excede la convención). Esos casos son *límite* y se marcan como tales con peso bajo.

**Indicador candidato de posible interés romántico.** Evento léxico de una categoría candidata: cumplidos personales o físicos, propuestas de verse a solas, apodos cariñosos, saludos con elemento afectivo, interés en la vida íntima del otro, emojis afectivos. **Un candidato no equivale a interés romántico.** Un cumplido puede ser amistoso, romántico, sarcástico, cortés o parte de la manera habitual de hablar de alguien. Para considerarse algo más que ruido se exige:

1. **Recurrencia:** al menos `min_events_for_pattern` eventos en `min_distinct_periods` periodos (semanas ISO) distintos.
2. **Línea base individual:** compararlo con el estilo habitual de esa persona en este chat.
3. **Contexto:** a quién, sobre qué y en qué tono.
4. **Respuesta de la otra persona** (sección 5).

Los umbrales de recurrencia son **valores experimentales**. Tres eventos en dos semanas no constituyen una validación científica de interés romántico: solo deciden si el sistema reporta una recurrencia **descriptiva**, y esa recurrencia es **necesaria pero no suficiente**. No deben convertir en señal romántica una expresión ligeramente afectuosa. Un resultado que solo se sostiene en el borde de los umbrales es **sensible a umbrales** (sección 8).

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

- **Balance de participación:** distribución de turnos, mensajes y palabras entre los participantes (palabras = fragmentos separados por espacios en mensajes de texto). Es una **observación**.
- **Reciprocidad:** correspondencia en la interacción, incluidos respuestas, seguimiento de temas, preguntas, iniciativas y apoyo. **Todavía no tiene definición operativa ni métricas propias**; hasta entonces ningún reporte la afirma como patrón. Que ambos tengan el mismo número de turnos no demuestra por sí mismo una relación recíproca.

## 7. Frecuencia de comunicación y cercanía (reserva para la clasificación de vínculos)

Al clasificar relaciones se separan:

- **Frecuencia de comunicación:** medición observable (días con mensajes sobre días del periodo, mensajes por día activo, mensajes por semana).
- **Cercanía interpersonal:** interpretación compleja, siempre **hipótesis**. Hablar a diario no implica una relación cercana, y una relación cercana no requiere hablar a diario; ninguna se infiere de la otra.

## 8. Evaluación de la evidencia

Cada hallazgo del reporte lleva **tres etiquetas independientes**:

**Estado epistémico**

- **Observación:** dato directo, calculable y reproducible, sin interpretación. Ej.: "A envió 52.7 % de los mensajes".
- **Patrón:** comportamiento que cumple la recurrencia (mínimo de eventos en varios periodos) y es **robusto** ante los umbrales. Es descriptivo: dice *qué se repite*, no *por qué*.
- **Hipótesis:** interpretación sobre intención, sentimiento o naturaleza del vínculo. Siempre con su evidencia y explicaciones alternativas.

**Suficiencia de datos:** `suficiente`, `insuficiente` o `no_evaluada`, según los mínimos de `data_sufficiency`. Responde si hay información para estudiar la dimensión.

**Robustez:** responde si el hallazgo se mantiene al cambiar parámetros. Se evalúa con la rejilla de `robustness` (hueco de sesión 2, 6 y 12 h; mínimo de eventos de 2 a 5; mínimo de periodos de 1 a 3; semana o mes):

- `robusto`: mantiene dirección y categoría en toda la rejilla.
- `robusto_en_direccion_magnitud_sensible`: la dirección se mantiene pero la magnitud cambia mucho.
- `sensible_a_umbrales`: el resultado cambia en parte de la rejilla; **no puede presentarse como patrón**.
- `no_evaluada`.

**No hay niveles de confianza ni probabilidades.** Las etiquetas son heurísticas experimentales; no están calibradas estadísticamente y no deben leerse como probabilidades. Reglas:

- Una observación no sube a patrón sin recurrencia y robustez.
- Un patrón nunca sube a hecho sobre intenciones; el máximo es hipótesis.
- **No concluyente** es un resultado legítimo.

## 9. Reglas generales

1. Las conclusiones no se apoyan en eventos aislados.
2. Nunca se afirma un sentimiento o intención ("A está enamorado"); se reportan indicadores y respuestas observables.
3. Los hábitos individuales cuentan: quien responde tarde o casi no usa emojis no debe leerse como "frío".
4. Las reglas no se validan solo con ejemplos sencillos: los casos ambiguos y los falsos positivos conocidos forman parte de las pruebas.
5. Los chats sintéticos prueban definiciones y cálculos. **No demuestran** que el sistema identifique correctamente relaciones reales.
6. Límites de alcance: las reacciones normalmente no aparecen en la exportación de WhatsApp y los stickers solo figuran como multimedia omitida.
7. Todo el procesamiento es local y los participantes se muestran como A y B.

## Registro de cambios

**v0.4 (2026-11-01)**

- "Sin intervención previa a su nuevo turno" queda como estado independiente, con sus propiedades explícitas, incluida su dependencia del hueco de sesión.
- Línea base de comunicación: saludos convencionales y 😊/☀️ por sí solos no son candidatos. El evento es un mensaje. Los umbrales de recurrencia son experimentales.
- Categorías de respuesta refinadas (12; antes "desviada" mezclaba comportamientos distintos); los límites llevan alcance; una respuesta ambigua no se clasifica como rechazo.
- Límite de la interpretación: sin correspondencia romántica explícita no equivale a ausencia de interés.
- Balance de participación y reciprocidad se separan; la reciprocidad queda sin definición operativa.
- Frecuencia y cercanía se separan para la clasificación de vínculos.
- Se sustituye el nivel de confianza (baja, media, alta) por tres ejes: estado epistémico, suficiencia de datos y robustez, sin probabilidades.

**v0.3 (2026-10-31).** Latencia hasta la siguiente intervención del interlocutor sin ventana; medianas general, dentro y entre sesiones; registro por turno; respuesta semántica separada de la siguiente intervención.

**v0.2 (2026-10-30).** Ráfaga y turno separados; reanudación y último mensaje como eventos independientes; estados epistémicos; un indicador no equivale a interés romántico.

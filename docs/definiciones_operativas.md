# Definiciones operativas

Versión 0.3 · 2026-10-31 · **Pendiente de aprobación definitiva** (criterio de salida de la Fase 0). Aprobados conceptualmente: turno, ráfaga, sesión, reanudación y estados epistémicos (v0.2).

Fijan qué significa cada término en el código y en los reportes. Los valores numéricos viven en `config.yaml`. Todo valor marcado como *provisional* o *experimental* es un criterio operativo, no una afirmación sobre la realidad.

## 1. Unidades de análisis

**Mensaje.** Entrada individual de la exportación, con timestamp y autor. Siempre se conservan los mensajes originales y sus timestamps. Tipos: `texto`, `media` (multimedia omitida, stickers, ubicación), `sistema` y `eliminado`. Solo `texto` entra en las métricas lingüísticas; `media` y `eliminado` cuentan como actividad sin contenido analizable; `sistema` no pertenece a ninguna persona.

**Ráfaga.** Mensajes consecutivos del mismo participante cuyo intervalo es **menor o igual** a `segmentation.burst_max_gap_seconds` (valor inicial **experimental** de 300 s). Sirve para estudiar hábitos de escritura y fragmentación.

**Turno conversacional.** Mensajes consecutivos del mismo participante hasta que interviene el otro, dentro de una misma sesión. El turno **no** depende del intervalo de la ráfaga: un turno puede contener varias ráfagas.

> Ejemplo. A las 10:00, A envía 3 mensajes. A las 10:08, A envía 2 más. A las 10:15, B responde.
> Resultado: un turno de A (con dos ráfagas, de 3 y 2 mensajes) y luego un turno de B.

Los turnos son la unidad para participación, iniciativa y reciprocidad; así la fragmentación no distorsiona esas métricas. Las ráfagas conservan la información sobre hábitos de escritura.

**Sesión.** Conjunto de turnos separados entre sí por un intervalo **menor o igual** a `segmentation.session_gap_hours` (valor **provisional** de 6 h; se prueba con 2, 6 y 12 h). La sesión se corta solo cuando el silencio **supera** el umbral. Es un criterio operativo para segmentar periodos de interacción y **no se asume que represente una separación real entre conversaciones**.

**Registro por turno.** De cada turno se conserva, sin interpretarlo:

- primer y último timestamp;
- **tiempo transcurrido** (último menos primero);
- número de mensajes y número de ráfagas;
- **intervalos de silencio** entre mensajes consecutivos del turno;
- **tiempo dentro de ráfagas** (suma de los intervalos que no superan el de la ráfaga).

El tiempo transcurrido **no equivale a actividad efectiva**: un turno de 10:00 a 15:00 no significa que la persona estuviera cinco horas conversando. Estos datos sirven para estudiar fragmentación y hábitos de escritura, y **no** son por sí solos indicadores de interés o participación.

## 2. Eventos de sesión

Se registran por separado y sin atribuir intención:

**Reanudación.** Primer turno de una sesión (quién retoma la comunicación después de un periodo de inactividad). No se interpreta que quien reanuda tenga más interés: puede deberse a horarios, a quien tiene algo que contar, a convenciones entre ambos o a que el otro estaba ocupado.

**Último mensaje de la sesión.** Autor del último turno de una sesión. No se interpreta que esa persona terminó voluntariamente la conversación: la sesión se cierra por el criterio de segmentación, no por decisión de nadie.

Ambos se reportan como **observación**. Cualquier lectura sobre interés o intención requiere recurrencia y línea base individual y es, como mucho, **hipótesis**.

Un mismo turno puede ser a la vez una **reanudación** y la siguiente intervención del interlocutor: si A escribe a las 23:30 y B contesta a las 08:00, ese turno de B es una reanudación de sesión **y** cuenta como intervención con latencia de 8 h 30 min. Ninguna de las dos descripciones excluye a la otra.

## 3. Latencia hasta la siguiente intervención del interlocutor

**Intervención siguiente.** Para un turno de X, el mensaje inmediatamente posterior en el chat, si es del otro participante Y. No hay límite máximo de tiempo ni dependencia de la sesión.

**Latencia.** Tiempo entre el **último** mensaje del turno de X y esa intervención de Y.

> Ejemplo. A escribe a las 10:00, 10:00 y 10:01; B interviene a las 10:03. Latencia de B: **2 minutos**.
> Ejemplo. A escribe a las 23:30; B interviene a las 08:00 del día siguiente. Latencia de B: **8 h 30 min (510 min)**, entre sesiones.

La latencia se asigna a quien interviene (la latencia "de B" es el tiempo que B tarda en intervenir tras un turno de A).

**Estados de un turno** (cada turno tiene exactamente uno):

1. **Con intervención:** el siguiente mensaje es del otro participante. Tiene latencia.
2. **Sin intervención previa a su nuevo turno:** el siguiente mensaje es del mismo autor, tras un cambio de sesión (el otro participante aún no intervino). No tiene latencia y no entra en las medianas. Se registra como observación; no implica rechazo ni indiferencia del otro.
3. **Sin respuesta observada:** no hay ningún mensaje posterior (ocurre solo en el último turno del chat). Es un límite de los datos disponibles y **no** evidencia de indiferencia ni de rechazo.

**Métricas obligatorias**, por participante que interviene:

- mediana **general** de latencia;
- mediana **dentro de la misma sesión** (latencia ≤ hueco de sesión);
- mediana **entre sesiones** (latencia > hueco de sesión);
- **proporción** de intervenciones dentro y fuera de sesión, y número de turnos en cada estado.

La mediana general **no depende del hueco de sesión**; las otras dos y la proporción sí, por lo que se reportan para 2, 6 y 12 h. La segmentación en sesiones no debe hacer perder los tiempos reales de interacción.

**Siguiente intervención no equivale a respuesta semántica.** Que B sea el siguiente en escribir no demuestra que conteste el mensaje de A. La **respuesta semántica** es si esa intervención trata del contenido del mensaje anterior (`directa`, `parcial`, `no_relacionada` o `no_determinada`). Su evaluación automática queda para la Fase 6; mientras tanto el valor por defecto es `no_determinada`, y las etiquetas manuales de los chats sintéticos sirven de referencia.

**Pregunta.** Mensaje de texto con `?` o que empieza con palabra interrogativa. Aproximación: se revisará con muestras manuales.

## 4. Eventos léxicos e indicadores

**Evento léxico.** Coincidencia entre un mensaje y una regla de diccionario (afecto, apoyo, conflicto, reparación, cumplido, plan, etc.). Guarda mensaje, fecha, categoría y la regla que lo disparó, para poder auditarlo. Es un dato sobre el texto, no sobre la persona.

**Indicador de posible interés romántico.** Evento léxico de una categoría candidata (cumplidos personales o físicos, propuestas de verse a solas, apodos cariñosos, saludos de buenos días y buenas noches, interés en la vida íntima del otro, emojis afectivos).

**Un indicador no equivale a interés romántico.** Un cumplido puede ser amistoso, romántico, sarcástico, cortés o parte de la manera habitual de hablar de alguien. Para que un conjunto de indicadores se considere algo más que ruido, el sistema exige:

1. **Recurrencia:** al menos `min_events_for_pattern` eventos en `min_distinct_periods` periodos distintos.
2. **Línea base individual:** compararlo con el estilo habitual de esa persona en este chat (quien llama "cariño" a todo, o usa corazones en cualquier tema, no aporta señal diferencial).
3. **Contexto:** a quién, sobre qué y en qué tono; un cumplido en un tema laboral no es igual que uno en un tema personal.
4. **Respuesta de la otra persona** (ver sección 5).

La recurrencia es **necesaria pero no suficiente**. Si falta alguno de estos elementos, el resultado es **no concluyente**, que es un resultado válido y esperado.

## 5. Respuesta a un indicador

Para cada indicador se registran **dos cosas distintas**:

- **La siguiente intervención** del otro participante y su latencia (sección 3), sin ventana máxima.
- **La naturaleza de esa intervención**, solo si es semánticamente relacionada:
    - *correspondida:* afecto equivalente.
    - *reconocida sin correspondencia:* agradecimiento o respuesta neutral.
    - *reciprocidad ambigua:* devuelve confianza o cordialidad que cabe en una amistad.
    - *desviada:* cambia de tema, declina con excusa o responde con evasivas.
    - *límite suave* o *límite explícito:* pide que cese o declara una frontera.
    - *sin respuesta semántica observada:* hay una siguiente intervención, pero no trata del indicador; o no hay ninguna.

Ni la demora ni la ausencia de respuesta se interpretan como indiferencia o rechazo por sí solas. Una respuesta corta o lenta puede ser el estilo normal de esa persona, por lo que siempre se compara con su línea base de longitud y de latencia, y con el **tipo de mensaje** al que responde (las tareas suelen contestarse más rápido que los saludos).

## 6. Estados epistémicos

Cada hallazgo del reporte lleva exactamente una de estas etiquetas, con criterios verificables:

**Observación.** Dato directo, calculable y reproducible a partir de los mensajes, sin interpretación. Ejemplo: "A envió 62 % de los turnos". Solo depende de la calidad del parseo.

**Patrón.** Comportamiento que cumple los criterios de recurrencia (mínimo de eventos, en varios periodos) y se mantiene bajo el análisis de sensibilidad de los umbrales. Sigue siendo descriptivo: dice *qué se repite*, no *por qué*. Ejemplo: "B interviene con mediana de 40 min en 8 de 9 semanas".

**Hipótesis.** Interpretación sobre intención, sentimiento o naturaleza del vínculo. Puede ser razonable, pero los datos del chat no permiten confirmarla. Siempre se presenta con su evidencia, con explicaciones alternativas y con nivel de confianza. Ejemplo: "los indicadores de A podrían sugerir interés romántico; también son compatibles con un estilo afectuoso general".

Reglas:

- Una observación no puede subir a patrón sin cumplir recurrencia y robustez.
- Un patrón nunca sube a hecho sobre intenciones; el máximo es hipótesis.
- Si el resultado cambia al variar los umbrales de forma importante, se marca como **frágil** y no se presenta como patrón.
- **No concluyente** es un estado legítimo cuando no hay datos suficientes.

El nivel de **confianza** (baja, media, alta) depende de la cantidad de datos, la consistencia y la robustez ante los umbrales.

## 7. Reglas generales

1. Las conclusiones no se apoyan en eventos aislados.
2. Nunca se afirma un sentimiento o intención ("A está enamorado"); se reportan indicadores y respuestas observables.
3. Los hábitos individuales cuentan: quien responde siempre tarde o casi no usa emojis no debe leerse como "frío".
4. Las reglas no se validan solo con ejemplos sencillos: los casos ambiguos y los falsos positivos conocidos deben formar parte de las pruebas.
5. Los chats sintéticos prueban que las definiciones y los cálculos se comportan como se espera. **No demuestran** que el sistema identifique correctamente relaciones reales.
6. Límites de alcance: las reacciones normalmente no aparecen en la exportación de WhatsApp y los stickers solo figuran como multimedia omitida.
7. Todo el procesamiento es local y los participantes se muestran como A y B.

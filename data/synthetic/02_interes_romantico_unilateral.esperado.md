# Chat sintético 02: interés romántico unilateral

Archivos: `02_interes_romantico_unilateral.txt` (formato Android, 24 h) y `02_interes_romantico_unilateral.etiquetas.csv` (13 eventos con su clasificación esperada). Participantes ficticios: Diego y Sofía, compañeros de clase en un proyecto de estadística.

**Para qué sirve.** Probar que definiciones y cálculos se comportan como esperamos, incluido el caso de que una persona exprese indicadores recurrentes y la otra no los corresponda. No demuestra que el sistema identifique relaciones reales: el guion lo escribí yo y sus señales son más nítidas que las de un chat real.

**Cómo se verificaron los números.** Con scripts de referencia independientes del código del proyecto, aplicando `definiciones_operativas.md` v0.3. Las etiquetas de indicadores y de respuesta semántica son **juicio mío sobre texto inventado** y quedan sujetas a tu revisión.

## Comportamientos representados

- **Semanas 1 y 2 (7 a 20 de septiembre):** interacción académica, sin indicadores. Diego ya saluda ("buenos días", "buenas noches") sin afecto marcado.
- **Semanas 3 a 5 (21 de septiembre a 11 de octubre):** Diego introduce indicadores de forma recurrente y variada: saludos afectuosos, emojis ❤️, un cumplido físico, una pregunta sobre su vida íntima, apodos ("princesa", "linda") y tres propuestas de verse a solas.
- **Sofía** interviene con cortesía ("jaja gracias"), declina las propuestas a solas con excusas y vuelve a temas académicos. Es cálida y cooperativa en lo demás: comparte por iniciativa propia que le dieron una beca (06/10).
- **Semana 6:** Sofía pide que no le digan "linda" (08/10). Diego se declara (13/10) y Sofía responde con un límite explícito.
- **Semana 7:** Diego deja de usar indicadores y retoman una relación de equipo.

## Parser (Fase 1, referencia)

| Concepto | Esperado |
| --- | --- |
| Mensajes de las personas | 72 (Diego 36, Sofía 36) |
| Mensajes de sistema | 1 (cifrado) |
| Multimedia omitida | 2 (`<Multimedia omitido>`: Sofía 07/09 16:12, Diego 14/09 20:19) |
| Rango | 07/09/2026 16:10 a 23/10/2026 13:10 |
| Emojis afectivos de Diego | 3 (❤️ el 23/09, 02/10 y 07/10), además de ☀️ y 😊 que no son afectivos por sí solos |

## Segmentación: sensibilidad al hueco de sesión

| Hueco | Sesiones | Turnos (Diego / Sofía) | Reanudaciones (Diego / Sofía) | Último mensaje (Diego / Sofía) |
| --- | --- | --- | --- | --- |
| 2 h | 31 | 33 / 30 | 18 / 13 | 16 / 15 |
| **6 h (inicial)** | **28** | **33 / 30** | **18 / 10** | **13 / 15** |
| 12 h | 23 | 33 / 30 | 17 / 6 | 9 / 14 |

Con 6 h: 63 turnos y 63 ráfagas (300 s). Los 9 turnos con más de un mensaje duran 2 minutos o menos y tienen una sola ráfaga: **este chat no ejercita la distinción turno/ráfaga ni el silencio dentro de un turno**. Esos casos los cubren el chat 01 y `00_escenarios_validacion`.

**Reanudaciones.** Diego reanuda 58 % (2 h), 64 % (6 h) y 74 % (12 h) de las sesiones. La dirección es estable, pero la magnitud depende del hueco. Esperado: observación y patrón *descriptivo*, **sin** lectura sobre interés. Parte de esa cifra procede de saludos matutinos o nocturnos de Diego que Sofía contesta horas después.

**Último mensaje.** Con 2 h y 6 h casi no hay diferencia; con 12 h Sofía cierra más (14 contra 9). Observación sin patrón (cambia con el umbral).

## Latencia hasta la siguiente intervención del interlocutor

Medianas en minutos. "Diego" es la latencia con que Diego interviene tras un turno de Sofía, y viceversa. Sin ventana máxima.

| Hueco | Quien interviene | n | General | Dentro de sesión (n) | Entre sesiones (n) | Proporción dentro |
| --- | --- | --- | --- | --- | --- | --- |
| 2 h | Diego | 28 | 80 | 2 (15) | 2120 (13) | 53.6 % |
| 2 h | Sofía | 28 | 83.5 | 20 (17) | 675 (11) | 60.7 % |
| **6 h** | **Diego** | **28** | **80** | **2 (15)** | **2120 (13)** | **53.6 %** |
| **6 h** | **Sofía** | **28** | **83.5** | **34.5 (20)** | **724.5 (8)** | **71.4 %** |
| **6 h** | **Agregado** | **56** | **83.5** | **10 (35)** | **1654 (21)** | **62.5 %** |
| 12 h | Diego | 28 | 80 | 2.5 (16) | 2125 (12) | 57.1 % |
| 12 h | Sofía | 28 | 83.5 | 42.5 (24) | 1681.5 (4) | 85.7 % |

**Estados de los turnos** (iguales con 2, 6 y 12 h): 56 con intervención, 6 **sin intervención previa a su nuevo turno** (Sofía 09/09 18:05 y 19/10 18:04; Diego 10/09 19:42, 18/09 10:16, 22/09 16:00 y 02/10 21:00) y 1 **sin respuesta observada** (Diego, 23/10 13:10, último mensaje).

**Lectura esperada.** Las medianas generales son casi iguales (80 y 83.5 min). La diferencia está en la forma: Diego interviene muy rápido cuando lo hace dentro de la sesión (2 min), pero en 46 % de los casos lo hace después de un cambio de sesión (mediana 35 h); Sofía tarda más dentro de la sesión (34.5 min) y retrasa menos entre sesiones (12 h). Es una **observación**; con estos datos no se interpreta como diferencia de interés.

### Latencia de Sofía según el turno de Diego (6 h)

| Turno de Diego | n | General | Dentro de sesión (n) | Entre sesiones (n) |
| --- | --- | --- | --- | --- |
| 12 con indicadores candidatos | 11 (1 sin intervención previa) | **199** | 79 (7) | 647.5 (4) |
| Declaración del 13/10 | 1 | 88 | 88 (1) | sin casos |
| Resto de turnos | 16 | **15.5** | 7.5 (12) | 1681.5 (4) |

La mediana general (199 contra 15.5) no depende del hueco. **Hay un factor de confusión visible:** las latencias entre sesiones tras turnos sin indicadores (1681.5 min) son aún mayores que tras los indicadores (647.5 min), porque los fines de semana y las pausas retrasan cualquier mensaje. La lectura "Sofía tarda más con los indicadores" solo se sostiene dentro de la sesión y es **hipótesis de confianza baja**, compatible con que los saludos se contestan más tarde que las tareas.

## Indicadores: lo que el sistema debe detectar

12 candidatos antes de la declaración más 1 declaración explícita (ver el CSV).

| Semana | Eventos esperados |
| --- | --- |
| 1 (7/9) | 0 |
| 2 (14/9) | 0: saludos neutros y un elogio a su manera de explicar, que no es indicador romántico |
| 3 (21/9) | 4 |
| 4 (28/9) | 5 |
| 5 (5/10) | 3 |
| 6 (12/10) | 1 (declaración explícita) |
| 7 (19/10) | 0 |

**Naturaleza de la respuesta a los 12 candidatos:** 4 reconocidas con neutralidad, 1 amistosa ambigua, 4 desviadas, 1 sin respuesta semántica (la siguiente intervención no trata del indicador), 1 límite suave y 1 sin intervención previa a un nuevo turno de Diego. **Ninguna correspondida de forma romántica.** La declaración recibe un límite explícito.

## Resultados esperados del sistema

**Análisis completo (7/9 a 23/10).**

| Hallazgo | Etiqueta esperada |
| --- | --- |
| Diego envía 12 indicadores candidatos en 3 semanas seguidas y de varios tipos; ninguno antes del 21/09 | Patrón; **cambio respecto a su propia línea base** (no es su estilo habitual) |
| Sofía reconoce con neutralidad, desvía las propuestas a solas y no corresponde de forma romántica | Patrón, confianza media |
| Diego declara explícitamente su interés el 13/10 y Sofía pone un límite explícito | Observación (cita textual); el sistema reporta lo dicho, no un sentimiento |
| Tras el 13/10 los indicadores de Diego bajan a 0 | Observación temporal; no atribuir causa (se puede señalar la coincidencia con el límite) |
| Latencias generales casi iguales (80 y 83.5 min) | Observación; no concluyente como diferencia |
| Sofía tarda más dentro de la sesión tras los turnos con indicadores | Observación; la interpretación es hipótesis de confianza baja |
| Posible interés romántico de Diego no correspondido por Sofía | Hipótesis con alternativas (estilo afectuoso nuevo, buscar confianza), confianza media-alta por la declaración explícita |
| Contexto escolar, cercanía frecuente, amistad con posible interés romántico unilateral | Hipótesis, con las dimensiones por separado |

**Prueba de truncamiento: solo hasta el 11/10, antes de la declaración.** Esperado: el mismo patrón de indicadores y de respuestas, pero la conclusión sobre no correspondencia sale con **confianza media**, no alta, y se formula como hipótesis. Comprueba que el sistema no necesita la declaración explícita para detectar la asimetría ni exagera su certeza sin ella.

## Casos ambiguos (el sistema no debe forzar conclusiones)

1. **"Yo también te tengo confianza" (29/09).** Sofía reconoce y devuelve confianza de amistad. Esperado: *reciprocidad ambigua*. **No** "correspondida".
2. **Mensajes nocturnos contestados al día siguiente** (23/09 con 620 min, 30/09 20:46 con 744 min y 07/10 con 675 min). Esperado: se cuentan como siguiente intervención con su latencia, **entre sesiones**, y su naturaleza se clasifica por separado (reconocida, desviada, límite suave). No se descartan por exceder una ventana ni se leen como indiferencia.
3. **Siguiente intervención que no es respuesta semántica** (05/10). A "buenos días princesa" (08:00) la siguiente intervención de Sofía es a las 14:30 (390 min) y trata del correo del profe. Esperado: latencia registrada, intervención `no_relacionada`, naturaleza *sin respuesta semántica observada*. Además, el 28/09 Diego escribe a las 08:00 y 08:01 y Sofía contesta "ojalá!" a las 11:20: responde al mensaje del sueño del proyecto, no al saludo (`parcial`).
4. **Turno de Diego sin intervención previa** (02/10 21:00, "buenas noches ❤️"). Diego vuelve a escribir el 05/10 a las 08:00 antes de que Sofía intervenga. Esperado: estado *sin intervención previa a su nuevo turno*, sin latencia y sin lectura de rechazo; la primera intervención de Sofía (05/10 14:30) se asigna al turno del 05/10.
5. **Sofía tarda más con indicadores que con tareas** (199 contra 15.5 min). Esperado: observación sobre el tipo de mensaje. La interpretación ("prioriza lo académico") es hipótesis de confianza baja; no es "frialdad", y los turnos sin indicadores también tienen latencias entre sesiones largas.
6. **"¿Buenas noches? jaja ya es otro día" (18/09).** Corrección en broma. No es conflicto ni indicador.
7. **Cumplido de habilidad (15/09, "qué bien te explicas").** No es indicador romántico: es elogio de una habilidad dentro de una tarea. Sofía responde "para eso es el equipo".
8. **Calidez de Sofía en lo no romántico.** Comparte por iniciativa la noticia de la beca. Esperado: no resumir a Sofía como fría, evasiva o desinteresada en general.
9. **Saludos neutros de Diego en la semana 2** ("buenos días!", "buenas noches" sin emoji). No cuentan como indicadores; son su línea base antes del cambio.
10. **Primera propuesta a solas (22/09) aislada.** Sola no establece patrón. Tras las tres propuestas y varias semanas sí.

## Lo que el sistema NO debe producir

- "Diego está enamorado de Sofía" o "Sofía lo rechazó por X motivo".
- "Sofía lo ignora" para los mensajes contestados horas después, ni para el turno del 02/10 ni para el último turno del chat.
- "Sofía es fría" por sus latencias a los indicadores.
- Un patrón de indicadores en las semanas 1 y 2.
- Alta confianza en la prueba de truncamiento.
- Contar la intervención del 05/10 14:30 como respuesta a "princesa".

## Decisiones incorporadas (de tu revisión del 31/10)

1. La ventana de respuesta de 120 min desaparece: la latencia se mide hasta la siguiente intervención del interlocutor, sin límite máximo.
2. Se reportan siempre la mediana general, la mediana dentro de sesión, la mediana entre sesiones y la proporción de cada tipo.
3. Cada turno registra su primer y último timestamp, el tiempo transcurrido, mensajes, ráfagas, silencios y tiempo dentro de ráfagas.
4. La siguiente intervención y la respuesta semántica son conceptos distintos. En este chat la semántica solo está etiquetada a mano en el CSV.

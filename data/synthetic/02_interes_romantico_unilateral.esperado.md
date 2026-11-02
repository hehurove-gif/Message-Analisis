# Chat sintético 02: interés romántico unilateral

Archivos: `02_interes_romantico_unilateral.txt` (formato Android, 24 h) y `02_interes_romantico_unilateral.etiquetas.csv` (17 filas: 10 candidatos del conteo principal, 1 declaración explícita, 1 expresión de calidez no específica y 5 eventos que **no** entran en el conteo principal). Participantes ficticios: Diego y Sofía, compañeros de clase en un proyecto de estadística.

**Para qué sirve.** Probar que definiciones y cálculos se comportan como esperamos, incluido el caso de que una persona exprese indicadores recurrentes y la otra no los corresponda de forma explícita. No demuestra que el sistema identifique relaciones reales: el guion lo escribí yo y sus señales son más nítidas que las de un chat real.

**Cómo se verificaron los números.** Con `tools/referencia/ref_latency.py` y `tools/referencia/ref_indicadores.py`, independientes del código del proyecto, aplicando `docs/definiciones_operativas.md` v0.5. Cada script imprime un bloque `PARAMETROS`; las cifras de este documento corresponden a esos parámetros (hueco de sesión 6 h salvo que se indique, ráfaga 300 s, periodo = semana ISO, variante P salvo que se indique):

```bash
python3 -I tools/referencia/ref_latency.py data/synthetic/02_interes_romantico_unilateral.txt detalle
python3 -I tools/referencia/ref_indicadores.py data/synthetic/02_interes_romantico_unilateral.txt data/synthetic/02_interes_romantico_unilateral.etiquetas.csv
```

Las etiquetas del CSV (clase de evento, relación semántica, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**: los scripts las cuentan, no las comprueban.

## Comportamientos representados

- **Semanas 1 y 2 (7 a 20 de septiembre):** interacción académica. Diego saluda de forma convencional ("buenos días!", "buenas noches"): es su línea base.
- **21/09:** "Buenos días, que tengas un día increíble ☀️". Se registra como `calidez_no_especifica`: expresión amable que excede la convención pero no apunta a una persona ni a un vínculo. Es evidencia contextual (puede indicar un cambio en la comunicación de Diego), **excluida del conteo principal** e incluida en la sensibilidad S1.
- **Semanas 3 a 5 (22 de septiembre a 11 de octubre):** Diego introduce 10 candidatos de varios tipos: saludos con elemento afectivo (❤️), un cumplido físico, una pregunta sobre su vida íntima, apodos ("princesa", "linda") y tres propuestas de verse a solas.
- **Sofía** acusa recibo con cortesía, responde directamente a lo que se le pregunta y, ante las tres propuestas, **declina una, pospone una y no se compromete en otra**. Es cálida y cooperativa en lo demás: comparte por iniciativa propia que le dieron una beca (06/10).
- **Semana 6:** Sofía pide que no le digan "linda" (08/10). Diego se declara (13/10) y Sofía responde con un límite explícito.
- **Semana 7:** Diego deja de usar candidatos y retoman la colaboración.

## Parser (Fase 1, referencia)

| Concepto | Esperado |
| --- | --- |
| Mensajes de las personas | 72 (Diego 36, Sofía 36) |
| Mensajes de sistema | 1 (cifrado) |
| Multimedia omitida | 2 (`<Multimedia omitido>`: Sofía 07/09 16:12, Diego 14/09 20:19) |
| Rango | 07/09/2026 16:10 a 23/10/2026 13:10 |
| Emojis afectivos de Diego | 3 (❤️ el 23/09, 02/10 y 07/10); ☀️ y 😊 no son afectivos por sí solos |

## Participación y frecuencia (observaciones, cada unidad por separado)

| Unidad | Diego | Sofía |
| --- | --- | --- |
| Mensajes | 36 (50.0 %) | 36 (50.0 %) |
| Turnos (2, 6 y 12 h) | 33 (52.4 %) | 30 (47.6 %) |
| Palabras (mensajes de texto) | 204 (51.6 %) | 191 (48.4 %) |
| Días con mensajes | 25 | 22 |

No se reduce a una etiqueta única de equilibrio ni a un índice compuesto. Puede decirse, de forma neutra, que la distribución está relativamente cercana en las unidades medidas. Juntos hay mensajes en 26 de los 47 días del periodo (2.77 mensajes por día activo). **La reciprocidad no se evalúa**: todavía no tiene definición operativa.

## Segmentación: sensibilidad al hueco de sesión

| Hueco | Sesiones | Turnos (Diego / Sofía) | Reanudaciones (Diego / Sofía) | Último mensaje (Diego / Sofía) |
| --- | --- | --- | --- | --- |
| 2 h | 31 | 33 / 30 | 18 / 13 | 16 / 15 |
| **6 h (inicial)** | **28** | **33 / 30** | **18 / 10** | **13 / 15** |
| 12 h | 23 | 33 / 30 | 17 / 6 | 9 / 14 |

Con 6 h: 63 turnos. **Separación de ráfagas (120, 300 y 600 s):** 63 ráfagas con los tres umbrales y ningún turno con más de una ráfaga; los 9 turnos con más de un mensaje duran 2 minutos o menos. Este chat **no ejercita** ni el silencio dentro de un turno ni la rejilla de ráfagas: el resultado "no cambia" no valida nada sobre esa familia; lo cubren el chat 01 y `00_escenarios_validacion`.

**Reanudaciones.** Diego reanuda 58 % (2 h), 64 % (6 h) y 74 % (12 h) de las sesiones: dirección estable, magnitud sensible. **Último mensaje:** con 2 h y 6 h casi no hay diferencia; con 12 h Sofía cierra más (14 contra 9).

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

**Estados de los turnos** (los mismos con 2, 6 y 12 h): 56 con intervención, 6 **sin intervención previa a su nuevo turno** (Sofía 09/09 18:05 y 19/10 18:04; Diego 10/09 19:42, 18/09 10:16, 22/09 16:00 y 02/10 21:00) y 1 **sin respuesta observada** (Diego, 23/10 13:10, último mensaje). Su clasificación no cambia en esta rejilla, pero podría cambiar con otro hueco.

**Lectura.** Las medianas generales son casi iguales (80 y 83.5 min). La diferencia está en la forma: Diego interviene muy rápido dentro de la sesión (2 min), pero 46 % de sus intervenciones ocurren tras un cambio de sesión (mediana de 35 h); Sofía tarda más dentro de la sesión (34.5 min) y retrasa menos entre sesiones (12 h). Es una observación y no se interpreta como diferencia de interés.

### Latencia de Sofía según el turno de Diego

Se calcula para cada variante de indicadores (P, S1, S2) de forma separada, con hueco de 6 h; P se repite con 2 y 12 h (familia de segmentación). Las dos familias **no se cruzan**.

| Variante / hueco | Turnos de Diego con candidato: n | General | Dentro (n) | Entre (n) | Resto de turnos: n | General | Dentro (n) | Entre (n) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P, 2 h | 9 | 165 | 42.5 (4) | 620 (5) | 18 | 27.5 | 7.5 (12) | 1186.5 (6) |
| **P, 6 h** | **9** | **165** | **45 (5)** | **647.5 (4)** | **18** | **27.5** | **10.5 (14)** | **1681.5 (4)** |
| P, 12 h | 9 | 165 | 122 (8) | 744 (1) | 18 | 27.5 | 11 (15) | 1695 (3) |
| S1, 6 h | 10 | 222.5 | 62 (6) | 647.5 (4) | 17 | 20 | 10 (13) | 1681.5 (4) |
| S2, 6 h | 8 | 122 | 45 (5) | 675 (3) | 19 | 35 | 10.5 (14) | 1668 (5) |

En P, 1 de los 10 turnos candidatos (02/10) no tiene intervención previa y queda fuera de las medianas; en S2 ese turno ya no es candidato. La declaración del 13/10 se analiza aparte (n=1: 88 min, dentro de sesión).

**Lectura.** Con las tres variantes la mediana general es mayor para los turnos con candidatos (165, 222.5 y 122 contra 27.5, 20 y 35) y **dentro de sesión** la dirección se mantiene con los tres huecos (42.5, 45 y 122 contra 7.5, 10.5 y 11); **entre sesiones** la dirección se invierte (620 a 744 contra 1186 a 1695), porque los fines de semana y las pausas retrasan cualquier mensaje. Además, todos los subgrupos tienen n < 20 (mínimo configurado). Resultado: **datos insuficientes y sensible a la descomposición dentro/entre sesiones; no se presenta como patrón**.

## Candidatos: lo que el sistema debe detectar

Principal (P, clase `indicador_candidato`): **10 candidatos**, más 1 declaración explícita (aparte) y 1 expresión de calidez no específica (21/09; fuera del conteo principal). Los saludos convencionales, la expresión del 21/09 y el elogio de habilidad no cuentan.

| Semana ISO (inicio) | P (principal) | S1 (P + calidez) | S2 (P sin ambiguos) |
| --- | --- | --- | --- |
| S37 y S38 (7/9, 14/9) | 0 | 0 | 0 |
| S39 (21/9) | 3 (22/09, 23/09, 24/09) | 4 (añade el 21/09) | 2 (sin el 23/09, ambiguo) |
| S40 (28/9) | 4 (29/09, 30/09 20:00, 30/09 20:46, 02/10); el "buenos días 😊" del 28/09 es línea base | 4 | 3 (sin el 02/10, ambiguo) |
| S41 (5/10) | 3 (05/10, 06/10, 07/10) | 3 | 3 |
| S42 (12/10) | 0 candidatos; declaración el 13/10 (aparte); "buenos días Sofi" del 12/10 es línea base | 0 | 0 |
| S43 (19/10) | 0 | 0 | 0 |
| **Total** | **10 (3 / 4 / 3)** | **11 (4 / 4 / 3)** | **8 (2 / 3 / 3)** |

Coincide con `ref_indicadores.py` (P: S39=3, S40=4, S41=3; S1: 4/4/3; S2: 2/3/3).

**Especificidad provisional** (anotación cualitativa, se cuenta aparte; no pondera ni forma índice): P → media 8, baja 2; S1 → media 8, baja 3; S2 → media 8. La frecuencia y la especificidad son dimensiones distintas y no se combinan.

**Categoría de respuesta a los 10 candidatos de P** (CSV):

| Categoría principal | n | Casos |
| --- | --- | --- |
| `reconocimiento_sin_correspondencia_afectiva` | 2 | 23/09, 24/09 |
| `invitacion_pospuesta_o_no_comprometida` | 2 | 22/09, 30/09 20:46 |
| `respuesta_directa` | 1 | 30/09 20:00 |
| `reciprocidad_amistosa_ambigua` | 1 | 29/09 |
| `invitacion_declinada` | 1 | 06/10 |
| `respuesta_no_relacionada` | 1 | 05/10 |
| `limite_interpersonal_suave` (alcance: apodos y forma de tratamiento) | 1 | 07/10, respondido el 08/10 |
| `sin_respuesta_semantica_observable` | 1 | 02/10 (sin intervención previa a su nuevo turno) |

Secundarias: `cambio_de_tema` en 2 casos (22/09 y 24/09) y `reconocimiento_sin_correspondencia_afectiva` en 1 (06/10). **Cero** `correspondencia_afectiva` y cero `invitacion_aceptada`. La expresión del 21/09 recibe `reconocimiento_sin_correspondencia_afectiva` (Sofía responde "igualmente" a las 12:30, 280 min después, dentro de sesión). La declaración del 13/10 recibe `limite_interpersonal_explicito` (alcance: relación romántica; no extiende el límite a la colaboración en el equipo).

## Sensibilidad por familia

Cada familia se prueba por separado. **La robustez ante parámetros no equivale a validez científica**: indica que un resultado no depende del parámetro, no que mida lo que se pretende medir.

| Familia | Qué se probó | Resultado |
| --- | --- | --- |
| **Recurrencia** (min. eventos 2-5 × min. periodos 1-3) | Con semanas, P/S1/S2: **12 de 12** combinaciones cumplen (10, 11 y 8 eventos en 3 semanas). Con meses: **8 de 12** cumplen y **4 son no evaluables** (min. periodos = 3, la ventana solo tiene 2 meses) | Robusto ante recurrencia **en la parte evaluable**: 12/12 semanales y 8/8 mensuales evaluables. Las 4 mensuales **no evaluables** no cuentan como validación |
| **Segmentación** (hueco 2/6/12 h; ráfaga 120/300/600 s) | Turnos y estados: sin cambios con los tres huecos (63 turnos; 6 sin intervención previa; 1 sin respuesta). Reanudaciones, último mensaje y medianas dentro/entre sí cambian | Robusto ante segmentación **solo** para turnos totales y estados; **sensible** (magnitud) en reanudaciones y en la mediana dentro/entre. Ráfagas: **no evaluable** (este chat no tiene turnos con más de una ráfaga) |
| **Indicadores** (P, S1, S2) | Eventos del patrón: 10, 11 y 8, todos con recurrencia semanal. Categorías de respuesta: no cambian el hecho de que haya 0 `correspondencia_afectiva` y 0 invitaciones aceptadas | Robusto ante indicadores en la **dirección** (recurrente y sin correspondencia explícita); magnitud sensible (8 a 11) |

## Resultados esperados del sistema

Cada hallazgo lleva estado epistémico, suficiencia de datos y robustez **por familia**, sin probabilidades.

**Análisis completo (7/9 a 23/10).**

| Hallazgo | Estado | Suficiencia | Robustez |
| --- | --- | --- | --- |
| Diego envía 10 candidatos en 3 semanas seguidas (3, 4 y 3) y de varios tipos; antes del 22/09 solo hay línea base | Patrón descriptivo | Suficiente | Robusto ante recurrencia (12/12 semanales; mensuales: 8 evaluables cumplen, 4 no evaluables) e indicadores (S1: 11, S2: 8) |
| Evidencia contextual: el 21/09 Diego expresa calidez no específica (fuera del conteo principal) | Observación | Suficiente | Incluida solo en S1 |
| Las respuestas de Sofía no presentan correspondencia afectiva explícita: 0 de 10 `correspondencia_afectiva` y 0 invitaciones aceptadas | Observación (conteo) | Suficiente | No depende de los umbrales de recurrencia; indicadores: mismo resultado en S1 y S2 |
| Sofía declina una invitación, pospone otra y no se compromete en otra; pide que cesen unos apodos | Observación | Suficiente | No depende de parámetros de recurrencia |
| Diego declara su interés el 13/10 y Sofía expresa que lo ve como un amigo | Observación (cita) | Suficiente | No aplica |
| Los candidatos de Diego bajan a 0 tras el 13/10 | Observación temporal; sin atribuir causa | Suficiente | No probada |
| Latencias generales casi iguales (80 y 83.5 min) | Observación; no concluyente como diferencia | Suficiente | No depende del hueco |
| Sofía tarda más dentro de la sesión tras turnos con candidatos | Observación; la interpretación ("prioriza lo académico") es hipótesis | **Insuficiente** para subgrupos (n de 8 a 10 y 17 a 19; mínimo 20) | **Sensible** a la descomposición dentro/entre sesiones; no puede presentarse como patrón |
| Posición afectiva de Sofía | **No concluyente: no se emite hipótesis** | No aplica | No aplica |
| Diego muestra indicadores recurrentes compatibles con interés romántico | Hipótesis, con alternativas (estilo afectuoso nuevo, búsqueda de confianza) | Suficiente | Robusto ante recurrencia e indicadores (en lo evaluable); no equivale a validez |
| Contexto escolar; frecuencia de 26 de 47 días con mensajes; cercanía | Contexto: hipótesis a clasificar en la Fase 8. Frecuencia: observación. Cercanía: no evaluada | Suficiente (frecuencia) | No probada |

**Prueba de truncamiento: solo hasta el 11/10, antes de la declaración.** El resultado esperado es:

> Diego muestra indicadores recurrentes compatibles con interés romántico. Las respuestas de Sofía no presentan correspondencia romántica explícita en la conversación analizada, aunque su posición afectiva no puede determinarse con suficiente evidencia.

Se obtiene de los mismos 10 candidatos y las mismas categorías de respuesta. Antes de la declaración el sistema puede mostrar candidatos recurrentes, ausencia de correspondencia romántica explícita, agradecimientos, respuestas neutrales, aplazamientos y límites sobre expresiones concretas. **No puede determinar que Sofía carezca de interés romántico.** Tras el 13/10 solo se añade como observación, con cita, que Sofía dice que lo ve como un amigo: se reporta lo que expresa, no un sentimiento.

## Casos que siguen siendo ambiguos y por qué

1. **Saludo con deseo (21/09, "que tengas un día increíble ☀️").** Se registra como `calidez_no_especifica`: contexto, no candidato. Con S1 (11 candidatos, 4/4/3) el resultado no cambia, lo que confirma que no sostiene el patrón por sí solo. Dónde termina la calidez no específica y empieza un indicador sigue siendo una pregunta abierta.
2. **"Yo también te tengo confianza" (29/09).** Cordialidad compatible con amistad y con otros vínculos; el texto no permite decidir. Se clasifica `reciprocidad_amistosa_ambigua`, no `correspondencia_afectiva`.
3. **Propuestas no comprometidas o pospuestas (22/09, 30/09 20:46).** "Uy no sé, creo que tengo cosas con mi familia" y "veamos cómo nos va en los exámenes" no son una negativa. Clasificarlas como rechazo sería forzar la conclusión.
4. **Invitación declinada (06/10).** Declina esa cena concreta; no demuestra ausencia de interés romántico ni cierra otras invitaciones.
5. **Límite sobre apodos (07/10 y 08/10).** El alcance es el trato ("no me digas así", "háblame como siempre"); no se extiende al resto de la relación. Que sea suave o explícito, y qué abarca exactamente, sigue siendo interpretable.
6. **Respuesta directa del 30/09 ("no, ahorita estoy enfocada en la escuela").** Contesta lo preguntado. "Ahorita" deja abierto el futuro, así que no es una negativa definitiva.
7. **Respuesta no relacionada o simple ausencia (05/10).** A "buenos días princesa" la siguiente intervención de Sofía llega 390 min después y trata del correo del profe. Se registra como no relacionada y no como indiferencia: no se sabe si vio el mensaje.
8. **Turno sin intervención previa (02/10).** Diego escribe de nuevo el 05/10 antes de que Sofía intervenga. No hay latencia ni lectura de rechazo.
9. **Latencia de Sofía según el tipo de mensaje.** Los candidatos reciben más latencia dentro de la sesión, pero entre sesiones la dirección se invierte y los subgrupos son pequeños. No se concluye nada.
10. **Calidez de Sofía en lo no romántico.** Comparte la noticia de la beca. El sistema no debe resumirla como fría, evasiva o desinteresada.
11. **Declaración y límite del 13/10.** "Te veo como un amigo" es lo que Sofía comunica; el sistema lo reporta como observación, sin afirmar nada más sobre sus sentimientos.

## Lo que el sistema NO debe producir

- "Diego está enamorado de Sofía" o "Sofía carece de interés romántico".
- "Sofía rechazó a Diego" a partir de respuestas pospuestas, no comprometidas o de una invitación declinada.
- "Sofía lo ignora" para mensajes contestados horas después, para el turno del 02/10 o para el último turno del chat.
- Extender el límite sobre apodos a toda la relación, o el límite del 13/10 a la colaboración.
- Un candidato en la semana 4 por el "buenos días 😊" del 28/09, o contar el 21/09 en el conteo principal.
- Un índice romántico, suma ponderada o puntuación que combine frecuencia y especificidad.
- Una etiqueta única de "participación equilibrada" o una afirmación de reciprocidad.
- La palabra "robusto" sin la familia y sin lo que se probó; contar como validación las configuraciones no evaluables.
- Niveles de confianza o probabilidades.
- Presentar como patrón la comparación de latencias por tipo de turno.

## Decisiones incorporadas

- 31/10: latencia hasta la siguiente intervención sin ventana máxima; medianas general, dentro y entre sesiones; registro por turno.
- 01/11: estado "sin intervención previa" independiente; línea base de saludos; 12 categorías de respuesta; interpretación sin determinar la posición afectiva de Sofía; balance separado de reciprocidad; estado epistémico, suficiencia y robustez en lugar de confianza.
- 02/11 (v0.5): 21/09 como `calidez_no_especifica`; participación reportada por unidad; robustez por familia con "no evaluable"; frecuencia y especificidad separadas, sin índice.

# Chat sintético 02: interés romántico unilateral

Archivos: `02_interes_romantico_unilateral.txt` (formato Android, 24 h) y `02_interes_romantico_unilateral.etiquetas.csv` (17 filas: 12 candidatos, incluida la declaración, y 5 casos de línea base que **no** cuentan). Participantes ficticios: Diego y Sofía, compañeros de clase en un proyecto de estadística.

**Para qué sirve.** Probar que definiciones y cálculos se comportan como esperamos, incluido el caso de que una persona exprese indicadores recurrentes y la otra no los corresponda de forma explícita. No demuestra que el sistema identifique relaciones reales: el guion lo escribí yo y sus señales son más nítidas que las de un chat real.

**Cómo se verificaron los números.** Con `tools/referencia/ref_latency.py` y `tools/referencia/ref_indicadores.py`, independientes del código del proyecto, aplicando `docs/definiciones_operativas.md` v0.4:

```bash
python3 -I tools/referencia/ref_latency.py data/synthetic/02_interes_romantico_unilateral.txt detalle
python3 -I tools/referencia/ref_indicadores.py data/synthetic/02_interes_romantico_unilateral.txt data/synthetic/02_interes_romantico_unilateral.etiquetas.csv
```

Las etiquetas del CSV (candidatos, relación semántica y categoría de respuesta) son **juicio mío sobre texto inventado**: los scripts las cuentan, no las comprueban.

## Comportamientos representados

- **Semanas 1 y 2 (7 a 20 de septiembre):** interacción académica. Diego saluda de forma convencional ("buenos días!", "buenas noches"): es su línea base.
- **Semanas 3 a 5 (21 de septiembre a 11 de octubre):** Diego introduce 11 candidatos, de varios tipos: saludos con elemento afectivo, ❤️, un cumplido físico, una pregunta sobre su vida íntima, apodos ("princesa", "linda") y tres propuestas de verse a solas.
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

## Balance de participación y frecuencia (observaciones)

| Concepto | Diego | Sofía |
| --- | --- | --- |
| Mensajes | 36 (50 %) | 36 (50 %) |
| Turnos (6 h) | 33 | 30 |
| Palabras (mensajes de texto) | 204 (51.6 %) | 191 (48.4 %) |
| Días con mensajes | 25 | 22 |

Juntos hay mensajes en 26 de los 47 días del periodo (2.77 mensajes por día activo). **La reciprocidad no se evalúa**: todavía no tiene definición operativa.

## Segmentación: sensibilidad al hueco de sesión

| Hueco | Sesiones | Turnos (Diego / Sofía) | Reanudaciones (Diego / Sofía) | Último mensaje (Diego / Sofía) |
| --- | --- | --- | --- | --- |
| 2 h | 31 | 33 / 30 | 18 / 13 | 16 / 15 |
| **6 h (inicial)** | **28** | **33 / 30** | **18 / 10** | **13 / 15** |
| 12 h | 23 | 33 / 30 | 17 / 6 | 9 / 14 |

Con 6 h: 63 turnos y 63 ráfagas (300 s). Los 9 turnos con más de un mensaje duran 2 minutos o menos y tienen una sola ráfaga: **este chat no ejercita el silencio dentro de un turno**; lo cubren el chat 01 y `00_escenarios_validacion`.

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

**Estados de los turnos** (los mismos con 2, 6 y 12 h): 56 con intervención, 6 **sin intervención previa a su nuevo turno** (Sofía 09/09 18:05 y 19/10 18:04; Diego 10/09 19:42, 18/09 10:16, 22/09 16:00 y 02/10 21:00) y 1 **sin respuesta observada** (Diego, 23/10 13:10, último mensaje). La clasificación de esos 6 turnos no cambia en esa rejilla, pero podría cambiar con otro hueco.

**Lectura.** Las medianas generales son casi iguales (80 y 83.5 min). La diferencia está en la forma: Diego interviene muy rápido dentro de la sesión (2 min), pero 46 % de sus intervenciones ocurren tras un cambio de sesión (mediana de 35 h); Sofía tarda más dentro de la sesión (34.5 min) y retrasa menos entre sesiones (12 h). Es una observación y no se interpreta como diferencia de interés.

### Latencia de Sofía según el turno de Diego

| Turno de Diego | Hueco | n | General | Dentro de sesión (n) | Entre sesiones (n) |
| --- | --- | --- | --- | --- | --- |
| 11 con candidatos (1 sin intervención previa) | 2 h | 10 | 222.5 | 42.5 (4) | 505 (6) |
| | **6 h** | **10** | **222.5** | **62 (6)** | **647.5 (4)** |
| | 12 h | 10 | 222.5 | 165 (9) | 744 (1) |
| Declaración del 13/10 | 6 h | 1 | 88 | 88 (1) | sin casos |
| Resto de turnos | 2 h | 17 | 20 | 7.5 (12) | 1668 (5) |
| | **6 h** | **17** | **20** | **10 (13)** | **1681.5 (4)** |
| | 12 h | 17 | 20 | 10.5 (14) | 1695 (3) |

La mediana general (222.5 contra 20) no depende del hueco. **Dentro de sesión** los candidatos reciben una latencia mayor con los tres huecos (42.5, 62 y 165 contra 7.5, 10 y 10.5); **entre sesiones** la dirección se invierte (505 a 744 contra 1668 a 1695), porque los fines de semana y las pausas retrasan cualquier mensaje. Además, los subgrupos tienen n=10 y 17, menos que el mínimo configurado de 20.

## Candidatos: lo que el sistema debe detectar

11 candidatos antes de la declaración, más la declaración (ver el CSV). Los saludos convencionales y el elogio de habilidad figuran como **no candidatos**.

| Semana (ISO) | Candidatos |
| --- | --- |
| 1 (7/9) | 0 |
| 2 (14/9) | 0: saludos convencionales y un elogio de habilidad |
| 3 (21/9) | 4 |
| 4 (28/9) | 4 (el "buenos días 😊" del 28/09 es línea base, no candidato) |
| 5 (5/10) | 3 |
| 6 (12/10) | 1 (declaración); el "buenos días Sofi" del 12/10 es línea base |
| 7 (19/10) | 0 |

**Categoría de respuesta a los 11 candidatos** (CSV):

| Categoría principal | n | Casos |
| --- | --- | --- |
| `reconocimiento_sin_correspondencia_afectiva` | 3 | 21/09, 23/09, 24/09 |
| `invitacion_pospuesta_o_no_comprometida` | 2 | 22/09, 30/09 20:46 |
| `respuesta_directa` | 1 | 30/09 20:00 |
| `reciprocidad_amistosa_ambigua` | 1 | 29/09 |
| `invitacion_declinada` | 1 | 06/10 |
| `respuesta_no_relacionada` | 1 | 05/10 |
| `limite_interpersonal_suave` (alcance: apodos y trato) | 1 | 07/10, respondido el 08/10 |
| `sin_respuesta_semantica_observable` | 1 | 02/10 (sin intervención previa a su nuevo turno) |

Secundarias: `cambio_de_tema` en 2 casos (22/09 y 24/09) y `reconocimiento_sin_correspondencia_afectiva` en 1 (06/10). **Cero** `correspondencia_afectiva` y cero `invitacion_aceptada`. La declaración del 13/10 recibe `limite_interpersonal_explicito` (alcance: relación romántica; no extiende el límite a la colaboración en el equipo).

## Resultados esperados del sistema

Cada hallazgo lleva estado epistémico, suficiencia de datos y robustez, **sin probabilidades**.

**Análisis completo (7/9 a 23/10).**

| Hallazgo | Estado | Suficiencia | Robustez |
| --- | --- | --- | --- |
| Diego envía 11 candidatos en 3 semanas seguidas (4, 4 y 3) y de varios tipos; ninguno antes del 21/09 (cambio respecto a su línea base) | Patrón descriptivo | Suficiente | Robusto: cumple 12 de 12 combinaciones semanales; con meses 8 de 12, porque el chat solo abarca 2 meses. Sin el caso límite del 21/09 (10 eventos) sigue cumpliendo toda la rejilla semanal |
| Las respuestas de Sofía no presentan correspondencia afectiva explícita: 0 de 11 `correspondencia_afectiva` y 0 invitaciones aceptadas | Observación (conteo) | Suficiente | Los conteos no dependen de los umbrales de recurrencia |
| Sofía declina una invitación, pospone otra y no se compromete en otra; pide que cesen unos apodos | Observación | Suficiente | Robusto |
| Diego declara su interés el 13/10 y Sofía expresa que lo ve como un amigo | Observación (cita) | Suficiente | No aplica |
| Los candidatos de Diego bajan a 0 tras el 13/10 | Observación temporal; sin atribuir causa | Suficiente | No evaluada |
| Latencias generales casi iguales (80 y 83.5 min) | Observación; no concluyente como diferencia | Suficiente | Robusto (no depende del hueco) |
| Sofía tarda más dentro de la sesión tras turnos con candidatos | Observación; la interpretación ("prioriza lo académico") es hipótesis | **Insuficiente** para subgrupos (n=10 y 17; mínimo 20) | **Sensible a umbrales**: entre sesiones invierte la dirección; no puede presentarse como patrón |
| Posición afectiva de Sofía | **No concluyente: no se emite hipótesis** | No aplica | No aplica |
| Diego muestra indicadores recurrentes compatibles con interés romántico | Hipótesis, con alternativas (estilo afectuoso nuevo, búsqueda de confianza) | Suficiente | Robusto en la recurrencia |
| Contexto escolar; frecuencia de 26 de 47 días con mensajes; cercanía | Contexto: hipótesis a clasificar en la Fase 8. Frecuencia: observación. Cercanía: no evaluada | Suficiente (frecuencia) | No evaluada |

**Prueba de truncamiento: solo hasta el 11/10, antes de la declaración.** El resultado esperado es:

> Diego muestra indicadores recurrentes compatibles con interés romántico. Las respuestas de Sofía no presentan correspondencia romántica explícita en la conversación analizada, aunque su posición afectiva no puede determinarse con suficiente evidencia.

Se obtiene de los mismos 11 candidatos y las mismas categorías de respuesta. Antes de la declaración el sistema puede mostrar candidatos recurrentes, ausencia de correspondencia romántica explícita, agradecimientos, respuestas neutrales, aplazamientos y límites sobre expresiones concretas. **No puede determinar que Sofía carezca de interés romántico.** Tras el 13/10 solo se añade como observación, con cita, que Sofía dice que lo ve como un amigo: se reporta lo que expresa, no un sentimiento.

## Casos que siguen siendo ambiguos y por qué

1. **Saludo con deseo (21/09, "que tengas un día increíble ☀️").** Cuenta como candidato de peso bajo por el deseo, que excede la convención; es un caso límite. Si no contara, serían 10 candidatos (3, 4 y 3 por semana) y el resultado no cambia, lo que confirma que no sostiene el patrón por sí solo.
2. **"Yo también te tengo confianza" (29/09).** Cordialidad compatible con amistad y con otros vínculos; el texto no permite decidir. Se clasifica `reciprocidad_amistosa_ambigua`, no `correspondencia_afectiva`.
3. **Propuestas no comprometidas o pospuestas (22/09, 30/09 20:46).** "Uy no sé, creo que tengo cosas con mi familia" y "veamos cómo nos va en los exámenes" no son una negativa. Clasificarlas como rechazo sería forzar la conclusión.
4. **Invitación declinada (06/10).** Declina esa cena concreta; no demuestra ausencia de interés romántico ni cierra otras invitaciones.
5. **Límite sobre apodos (07/10 y 08/10).** El alcance es el trato ("no me digas así", "háblame como siempre"); no se extiende al resto de la relación. Que sea suave o explícito, y qué abarca exactamente, sigue siendo interpretable.
6. **Respuesta directa del 30/09 ("no, ahorita estoy enfocada en la escuela").** Contesta lo preguntado. "Ahorita" deja abierto el futuro, así que no es una negativa definitiva.
7. **Respuesta no relacionada o simple ausencia (05/10).** A "buenos días princesa" la siguiente intervención de Sofía llega 390 min después y trata del correo del profe. Se registra como no relacionada y no como indiferencia: no se sabe si vio el mensaje.
8. **Turno sin intervención previa (02/10).** Diego escribe de nuevo el 05/10 antes de que Sofía intervenga. No hay latencia ni lectura de rechazo.
9. **Latencia de Sofía según el tipo de mensaje.** Los candidatos reciben más latencia dentro de la sesión, pero los saludos suelen contestarse más tarde que las tareas y entre sesiones la dirección se invierte. Con subgrupos pequeños y sensibles a umbrales no se concluye nada.
10. **Calidez de Sofía en lo no romántico.** Comparte la noticia de la beca. El sistema no debe resumirla como fría, evasiva o desinteresada.
11. **Declaración y límite del 13/10.** "Te veo como un amigo" es lo que Sofía comunica; el sistema lo reporta como observación, sin afirmar nada más sobre sus sentimientos.

## Lo que el sistema NO debe producir

- "Diego está enamorado de Sofía" o "Sofía carece de interés romántico".
- "Sofía rechazó a Diego" a partir de respuestas pospuestas, no comprometidas o de una invitación declinada.
- "Sofía lo ignora" para mensajes contestados horas después, para el turno del 02/10 o para el último turno del chat.
- Extender el límite sobre apodos a toda la relación, o el límite del 13/10 a la colaboración.
- Un candidato en la semana 4 por el "buenos días 😊" del 28/09.
- Niveles de confianza o probabilidades.
- Presentar como patrón la comparación de latencias por tipo de turno.

## Decisiones incorporadas

- 31/10: latencia hasta la siguiente intervención sin ventana máxima; medianas general, dentro y entre sesiones; registro por turno.
- 01/11: estado "sin intervención previa" independiente; línea base de saludos (28/09 deja de ser candidato); 12 categorías de respuesta; interpretación sin determinar la posición afectiva de Sofía; balance de participación separado de reciprocidad; estado epistémico, suficiencia y robustez en lugar de confianza.

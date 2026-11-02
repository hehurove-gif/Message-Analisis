# Chat sintético 01: amistad equilibrada

Archivos: `01_amistad_equilibrada.txt` (formato Android, 24 h) y `01_amistad_equilibrada.etiquetas.csv` (6 filas: 4 indicadores candidatos del conteo principal, 2 de ellos marcados como ambiguos, y 2 casos que no cuentan). Participantes ficticios: Lucía y Marco, que el sistema muestra como A y B.

**Para qué sirve.** Probar que las definiciones (mensaje, ráfaga, turno, sesión, reanudación, latencia) y los cálculos se comportan como esperamos, y que el sistema **no fuerza conclusiones** en los casos ambiguos. No demuestra que el sistema identifique relaciones reales.

**Cómo se verificaron los números.** Con `tools/referencia/ref_latency.py` y `tools/referencia/ref_indicadores.py`, independientes del código del proyecto, aplicando `docs/definiciones_operativas.md` v0.5. Cada script imprime un bloque `PARAMETROS`; las cifras corresponden a hueco de sesión 6 h (salvo que se indique), ráfaga 300 s, periodo = semana ISO y variante P (principal) salvo que se indique:

```bash
python3 -I tools/referencia/ref_latency.py data/synthetic/01_amistad_equilibrada.txt detalle
python3 -I tools/referencia/ref_indicadores.py data/synthetic/01_amistad_equilibrada.txt data/synthetic/01_amistad_equilibrada.etiquetas.csv
```

Si el sistema difiere, hay que investigar cuál de los dos tiene el error. Los escenarios de borde de la latencia y de los turnos se prueban con valores conocidos en `00_escenarios_validacion`. Las etiquetas del CSV son juicio mío sobre texto inventado.

## Comportamientos representados

- Conversación de 3 semanas (5 a 26 de octubre de 2026): planes de cine y comida, ayuda con una mudanza, apoyo tras un día largo.
- Ambos proponen planes e intervienen en tiempos parecidos.
- Una pausa de varios días entre sesiones, con distintas personas reanudando.
- Expresiones afectuosas de Marco ("cariño", "corazón", "eres lo máximo", "eres la mejor") en contextos de favor y agradecimiento, sin escalada.

## Parser (Fase 1, referencia)

| Concepto | Esperado |
| --- | --- |
| Mensajes de las personas | 74 (Lucía 39, Marco 35) |
| Mensajes de sistema | 1 (cifrado), no cuenta como mensaje de nadie |
| Multimedia omitida | 1 (`<Multimedia omitido>`, Marco, 06/10 13:20), tipo `media` |
| Mensaje multilínea | 1 (Marco, 14/10 20:45): las 2 líneas sin fecha se anexan a ese mensaje |
| Rango | 05/10/2026 09:12 a 26/10/2026 14:42 |

## Participación y frecuencia (observaciones, cada unidad por separado)

| Unidad | Lucía | Marco |
| --- | --- | --- |
| Mensajes | 39 (52.7 %) | 35 (47.3 %) |
| Turnos (6 h) | 28 (50.0 %) | 28 (50.0 %) |
| Palabras (mensajes de texto) | 154 (46.2 %) | 179 (53.8 %) |
| Días con mensajes | 12 | 12 |

Con 2 h los turnos son 29 / 30 (49.2 % / 50.8 %) y con 12 h 28 / 27 (50.9 % / 49.1 %). Lucía envía más mensajes y Marco más palabras: el resultado depende de la unidad. **No se reporta una etiqueta única** como "participación equilibrada" ni existe un indicador compuesto de equilibrio. Se puede decir, de forma neutra, que la distribución es relativamente cercana en las unidades medidas (46 % a 54 % en cada una). Juntos hay mensajes en 12 de los 22 días del periodo (6.17 mensajes por día activo). **La reciprocidad no se evalúa**: no tiene todavía definición operativa ni métricas propias, y 28 turnos cada uno no la demuestran.

## Segmentación: sensibilidad al hueco de sesión

| Hueco | Sesiones | Turnos (Lucía / Marco) | Reanudaciones (Lucía / Marco) | Último mensaje (Lucía / Marco) |
| --- | --- | --- | --- | --- |
| 2 h | 20 | 29 / 30 | 11 / 9 | 8 / 12 |
| **6 h (inicial)** | **14** | **28 / 28** | **8 / 6** | **6 / 8** |
| 12 h | 11 | 28 / 27 | 7 / 4 | 5 / 6 |

Con 6 h: 56 turnos y 59 ráfagas (300 s). Mensajes por turno: Lucía 1.39, Marco 1.25. **Separación de ráfagas (120, 300 y 600 s):** 59 ráfagas y 3 turnos con más de una ráfaga con los tres umbrales; no cambia en este chat (no ejercita la rejilla; `00_escenarios_validacion` sí).

## Latencia hasta la siguiente intervención del interlocutor

Medianas en minutos. "Lucía" es la latencia con que Lucía interviene tras un turno de Marco, y viceversa. No hay ventana máxima.

| Hueco | Quien interviene | n | General | Dentro de sesión (n) | Entre sesiones (n) | Proporción dentro |
| --- | --- | --- | --- | --- | --- | --- |
| 2 h | Lucía | 25 | 14 | 6 (18) | 1280 (7) | 72 % |
| 2 h | Marco | 25 | 9 | 5 (21) | 668.5 (4) | 84 % |
| **6 h** | **Lucía** | **25** | **14** | **10 (20)** | **1759 (5)** | **80 %** |
| **6 h** | **Marco** | **25** | **9** | **7 (22)** | **735 (3)** | **88 %** |
| **6 h** | **Agregado** | **50** | **12** | **8 (42)** | **1519.5 (8)** | **84 %** |
| 12 h | Lucía | 25 | 14 | 13 (21) | 2159 (4) | 84 % |
| 12 h | Marco | 25 | 9 | 9 (23) | 2919.5 (2) | 92 % |

- La mediana general (14 contra 9 min) **no depende del hueco**. Dentro de sesión Lucía tiene la mayor mediana con los tres huecos; entre sesiones la dirección se invierte con 12 h (2159 contra 2919.5).
- **Estados de los turnos** (6 h): 50 con intervención, 5 **sin intervención previa a su nuevo turno** (Marco 06/10 18:35, 08/10 22:40 y 09/10 10:31; Lucía 13/10 16:50 y 21/10 11:50) y 1 **sin respuesta observada** (Lucía, 26/10 14:42, último mensaje). Con 2 h son 8 y 1; con 12 h, 4 y 1: **esa clasificación depende del hueco**.
- **Intervenciones entre sesiones** (6 h): 8, entre 10 h y 85 h. Las más largas: Marco 14/10 20:45 contestado por Lucía el 17/10 a las 09:55 (61 h 10 min) y Lucía 17/10 22:26 contestada por Marco el 21/10 a las 11:30 (85 h 4 min).

## Registro por turno (6 h)

17 turnos tienen más de un mensaje. 14 duran 2 minutos o menos. Los otros tres tienen varias ráfagas y mucho silencio dentro:

| Turno | Mensajes | Ráfagas | Transcurrido | Silencios (min) | Minutos dentro de ráfagas |
| --- | --- | --- | --- | --- | --- |
| Marco 06/10 08:55 a 13:20 | 2 | 2 | 265 min | 265 | 0 |
| Lucía 06/10 13:22 a 18:10 | 3 | 2 | 288 min | 0, 288 | 0 |
| Marco 13/10 13:12 a 16:45 | 2 | 2 | 213 min | 213 | 0 |

Esos turnos duran horas porque la sesión sigue abierta y la misma persona escribe de nuevo antes de que intervenga la otra. **No son horas de conversación**: el tiempo dentro de ráfagas es cero. Se reportan como fragmentación y hábito de escritura, no como participación o interés.

## Candidatos, recurrencia y sensibilidad por familia

El CSV marca 4 indicadores candidatos (conteo principal, variante P): 3 mensajes de Marco (4 expresiones: "cariño", "corazón", "eres lo máximo", "eres la mejor") y 1 de Lucía ("te quedó genial el corte de pelo"). Se cuenta **un evento por mensaje**. Dos de los de Marco se marcan `ambiguo` (el 07/10 12:31 y el 24/10 19:20) porque son un elogio genérico dentro de un agradecimiento, que podría ser calidez no específica. Especificidad provisional (anotación, no pondera): los 4 candidatos son `baja`.

**Familia indicadores (variantes).** P = 3 eventos de Marco y 1 de Lucía; S1 (P + calidez no específica) = igual que P (este chat no tiene eventos de esa clase); S2 (P sin ambiguos) = 1 de Marco y 1 de Lucía.

**Familia recurrencia** (rejilla de 12 combinaciones: min. eventos 2-5 × min. periodos 1-3), por persona:

| Variante | Persona | Eventos (semanas ISO) | Semanal: cumple / no cumple / no evaluable | Mensual: cumple / no cumple / no evaluable |
| --- | --- | --- | --- | --- |
| P y S1 | Marco | 3 (2 en S41, 1 en S43) | 4 / 8 / 0 | 2 / 2 / 8 |
| P y S1 | Lucía | 1 (S41) | 0 / 12 / 0 | 0 / 4 / 8 |
| S2 | Marco | 1 (S41) | 0 / 12 / 0 | 0 / 4 / 8 |
| S2 | Lucía | 1 (S41) | 0 / 12 / 0 | 0 / 4 / 8 |

La ventana tiene 4 semanas ISO y **1 mes calendario**: con meses, las configuraciones con min. periodos 2 o 3 son **no evaluables** (8 de 12) y no cuentan como cumplidas, incumplidas ni como validación.

Con los umbrales actuales (3 eventos en 2 periodos) Marco cumple **justo el mínimo** con P: un evento menos o un periodo más y deja de cumplirlo, y con S2 no lo cumple en ninguna combinación. **Su resultado depende de la variante de indicadores y de los umbrales de recurrencia: no es patrón.** Es el caso que no debe convertirse en señal romántica.

## Resultados esperados del sistema

Robustez declarada **por familia** (recurrencia, segmentación, indicadores); "robusto" nunca va solo, y **la robustez ante parámetros no equivale a validez científica**.

| Hallazgo | Estado | Suficiencia | Robustez |
| --- | --- | --- | --- |
| Participación por unidad: mensajes 52.7 % / 47.3 %, turnos 50 % / 50 % (6 h), palabras 46.2 % / 53.8 % | Observación: distribución relativamente cercana en las unidades medidas; sin etiqueta compuesta | Suficiente | Mensajes y palabras no dependen del hueco; turnos varían de 49.2 % a 50.9 % con 2, 6 y 12 h |
| Reanudaciones: Lucía ≥ Marco con 2, 6 y 12 h (11/9, 8/6, 7/4) | Observación; no patrón | Suficiente | Robusto ante el hueco de sesión en dirección, magnitud sensible. Ráfagas: no aplica |
| Último mensaje: Marco ≥ Lucía con 2, 6 y 12 h (12/8, 8/6, 6/5) | Observación; no patrón | Suficiente | Robusto ante el hueco de sesión en dirección, magnitud sensible |
| Latencia: medianas generales de 14 y 9 min, mismo orden de magnitud | Observación; no concluyente como diferencia | Suficiente | La mediana general no depende del hueco; las medianas dentro/entre sí varían |
| Marco usa expresiones afectuosas: 3 mensajes en 2 semanas, en favores y agradecimientos | Observación; **no es patrón** | **Insuficiente** para evaluar recurrencia (3 eventos, justo el mínimo experimental) | **Sensible a recurrencia** (4 de 12 semanales; 8 mensuales no evaluables) y **sensible a indicadores** (con S2 solo 1 evento) |
| Interés romántico entre Marco y Lucía | **No sustentado: no se emite hipótesis** | No aplica | No aplica |
| Reciprocidad | **No evaluada** | No aplica | No aplica |
| Vínculo: contexto personal; frecuencia observable de 12 de 22 días | Contexto: hipótesis a clasificar en la Fase 8; frecuencia: observación; cercanía: no evaluada | Suficiente (frecuencia) | No probada |

## Casos ambiguos y por qué siguen siéndolo

1. **Expresiones afectuosas de Marco.** Son 3 mensajes (4 expresiones) en 2 semanas, exactamente el mínimo experimental, y dos de ellos son un elogio genérico que podría ser calidez no específica (S2 los excluye). Aparecen en un favor y en agradecimientos, sin propuestas de verse a solas ni escalada, y Lucía no responde en el mismo registro. El resultado cambia según los umbrales, así que no es patrón. Comprueba que la recurrencia es necesaria pero no suficiente.
2. **Cumplido aislado de Lucía** (08/10). Se registra como evento, sin peso. Marco responde con agradecimiento y una explicación neutral. Un solo evento no permite evaluar nada.
3. **Sarcasmo de Marco** (12/10, "otro lunes de reuniones, qué bien 🙄"). No cuenta como afecto positivo; si se detecta ironía, queda como señal débil. Lucía responde con ánimo, lo que apoya el tono sarcástico pero no lo prueba.
4. **Intervención lenta de Lucía** (12/10, Marco 13:00 y Lucía 15:40: 160 min, dentro de sesión). Ella misma lo explica (estaba en una junta). Es un dato atípico sin lectura de desinterés; hay otras dos latencias dentro de sesión superiores a 200 min (Marco 08/10: 264 min; Lucía 12/10: 209 min).
5. **Queja en broma** (26/10, "tú nunca contestas rápido jaja"). Tiene marcador de broma y se cierra con "te perdono": no es conflicto. Es un comentario sobre latencia que la mediana de Marco (9 min) no respalda.
6. **Pausas largas.** La del 17 al 21 de octubre (85 h 4 min entre el último mensaje de Lucía y la intervención de Marco) y la del 21 al 24 (Lucía escribe dos veces seguidas, tras un cambio de sesión, antes de que intervenga Marco). Se registran como latencia entre sesiones y como "sin intervención previa", sin lectura sobre quién tiene más interés.
7. **Participación dependiente de la unidad.** Lucía envía más mensajes y Marco más palabras. No se elige una unidad como la "correcta" ni se resume en una etiqueta; ninguna de las medidas es reciprocidad.
8. **Elogio genérico.** "Eres la mejor" o "eres lo máximo" en un agradecimiento: ¿calidez no específica o indicador? El texto no lo decide; se mantiene como candidato ambiguo con especificidad baja. Distinguir ambas cosas con fiabilidad es una pregunta abierta.

## Lo que el sistema NO debe producir

- "Marco tiene interés romántico en Lucía" ni cualquier afirmación sobre sentimientos.
- "Lucía es fría" o "desinteresada" por la latencia del 12/10.
- "La relación es recíproca" a partir de los 28 turnos de cada uno.
- "Participación equilibrada" como etiqueta única, o un índice compuesto de equilibrio.
- La palabra "robusto" sin la familia y lo probado; contar como validación las configuraciones no evaluables (mensuales).
- Un índice o puntuación que combine frecuencia de candidatos y especificidad.
- Una diferencia significativa de iniciativa entre los dos.
- Un conflicto detectado en la broma del 26/10.
- Contar como "sin respuesta" los 5 turnos sin intervención previa ni el último turno del chat.
- Presentar los turnos de 213 a 288 min como horas de actividad.
- Niveles de confianza o probabilidades.

## Decisiones incorporadas

- 02/11 (v0.5): participación reportada por unidad sin etiqueta compuesta; robustez por familia con "no evaluable"; candidatos con marca `ambiguo` y sensibilidad S1/S2; frecuencia y especificidad separadas.

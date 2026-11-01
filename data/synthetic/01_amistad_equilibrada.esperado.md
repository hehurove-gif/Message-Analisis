# Chat sintético 01: amistad equilibrada

Archivos: `01_amistad_equilibrada.txt` (formato Android, 24 h) y `01_amistad_equilibrada.etiquetas.csv` (6 filas: 4 candidatos y 2 casos que no cuentan). Participantes ficticios: Lucía y Marco, que el sistema muestra como A y B.

**Para qué sirve.** Probar que las definiciones (mensaje, ráfaga, turno, sesión, reanudación, latencia) y los cálculos se comportan como esperamos, y que el sistema **no fuerza conclusiones** en los casos ambiguos. No demuestra que el sistema identifique relaciones reales.

**Cómo se verificaron los números.** Con `tools/referencia/ref_latency.py` y `tools/referencia/ref_indicadores.py`, independientes del código del proyecto, aplicando `docs/definiciones_operativas.md` v0.4:

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

## Balance de participación y frecuencia (observaciones)

| Concepto | Lucía | Marco |
| --- | --- | --- |
| Mensajes | 39 (52.7 %) | 35 (47.3 %) |
| Turnos (6 h) | 28 | 28 |
| Palabras (mensajes de texto) | 154 (46.2 %) | 179 (53.8 %) |
| Días con mensajes | 12 | 12 |

Marco escribe menos mensajes pero más palabras: el balance depende de la unidad. Juntos hay mensajes en 12 de los 22 días del periodo (6.17 mensajes por día activo). **El resultado esperado es un balance de participación equilibrado.** **La reciprocidad no se evalúa**: no tiene todavía definición operativa ni métricas propias, y 28 turnos cada uno no la demuestran.

## Segmentación: sensibilidad al hueco de sesión

| Hueco | Sesiones | Turnos (Lucía / Marco) | Reanudaciones (Lucía / Marco) | Último mensaje (Lucía / Marco) |
| --- | --- | --- | --- | --- |
| 2 h | 20 | 29 / 30 | 11 / 9 | 8 / 12 |
| **6 h (inicial)** | **14** | **28 / 28** | **8 / 6** | **6 / 8** |
| 12 h | 11 | 28 / 27 | 7 / 4 | 5 / 6 |

Con 6 h: 56 turnos y 59 ráfagas (300 s). Mensajes por turno: Lucía 1.39, Marco 1.25.

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

## Candidatos y recurrencia

El CSV marca 4 candidatos: 3 mensajes de Marco (4 expresiones: "cariño", "corazón", "eres lo máximo", "eres la mejor") y 1 de Lucía ("te quedó genial el corte de pelo"). Se cuenta **un evento por mensaje**.

| Persona | Eventos | Semanas ISO | Combinaciones de la rejilla que cumple |
| --- | --- | --- | --- |
| Marco | 3 (2 en la semana 41, 1 en la 43) | 2 | 4 de 12 (semanal); 2 de 12 (mensual, porque los 3 caen en octubre) |
| Lucía | 1 | 1 | 0 de 12 |

Con los umbrales actuales (3 eventos en 2 periodos) Marco cumple **justo el mínimo**: un evento menos o un periodo más y deja de cumplirlo. Es el caso que no debe convertirse en señal romántica.

## Resultados esperados del sistema

| Hallazgo | Estado | Suficiencia | Robustez |
| --- | --- | --- | --- |
| Participación: 52.7 % / 47.3 % de los mensajes, 28 / 28 turnos y 46.2 % / 53.8 % de las palabras | Observación: balance equilibrado | Suficiente | Robusto |
| Reanudaciones: Lucía ≥ Marco con 2, 6 y 12 h (11/9, 8/6, 7/4) | Observación; no patrón | Suficiente | Robusto en dirección, magnitud sensible |
| Último mensaje: Marco ≥ Lucía con 2, 6 y 12 h (12/8, 8/6, 6/5) | Observación; no patrón | Suficiente | Robusto en dirección, magnitud sensible |
| Latencia: medianas generales de 14 y 9 min, mismo orden de magnitud | Observación; no concluyente como diferencia | Suficiente | Robusto (no depende del hueco) |
| Marco usa expresiones afectuosas: 3 mensajes en 2 semanas, en favores y agradecimientos | Observación; **no es patrón** | **Insuficiente** para evaluar recurrencia (3 eventos, justo el mínimo experimental) | **Sensible a umbrales** (4 de 12 combinaciones) |
| Interés romántico entre Marco y Lucía | **No sustentado: no se emite hipótesis** | No aplica | No aplica |
| Reciprocidad | **No evaluada** | No aplica | No aplica |
| Vínculo: contexto personal; frecuencia observable de 12 de 22 días | Contexto: hipótesis a clasificar en la Fase 8; frecuencia: observación; cercanía: no evaluada | Suficiente (frecuencia) | No evaluada |

## Casos ambiguos y por qué siguen siéndolo

1. **Expresiones afectuosas de Marco.** Son 3 mensajes (4 expresiones) en 2 semanas, exactamente el mínimo experimental. Aparecen en un favor y en agradecimientos, sin propuestas de verse a solas ni escalada, y Lucía no responde en el mismo registro. El resultado cambia según los umbrales, así que no es patrón. Comprueba que la recurrencia es necesaria pero no suficiente.
2. **Cumplido aislado de Lucía** (08/10). Se registra como evento, sin peso. Marco responde con agradecimiento y una explicación neutral. Un solo evento no permite evaluar nada.
3. **Sarcasmo de Marco** (12/10, "otro lunes de reuniones, qué bien 🙄"). No cuenta como afecto positivo; si se detecta ironía, queda como señal débil. Lucía responde con ánimo, lo que apoya el tono sarcástico pero no lo prueba.
4. **Intervención lenta de Lucía** (12/10, Marco 13:00 y Lucía 15:40: 160 min, dentro de sesión). Ella misma lo explica (estaba en una junta). Es un dato atípico sin lectura de desinterés; hay otras dos latencias dentro de sesión superiores a 200 min (Marco 08/10: 264 min; Lucía 12/10: 209 min).
5. **Queja en broma** (26/10, "tú nunca contestas rápido jaja"). Tiene marcador de broma y se cierra con "te perdono": no es conflicto. Es un comentario sobre latencia que la mediana de Marco (9 min) no respalda.
6. **Pausas largas.** La del 17 al 21 de octubre (85 h 4 min entre el último mensaje de Lucía y la intervención de Marco) y la del 21 al 24 (Lucía escribe dos veces seguidas, tras un cambio de sesión, antes de que intervenga Marco). Se registran como latencia entre sesiones y como "sin intervención previa", sin lectura sobre quién tiene más interés.
7. **Balance dependiente de la unidad.** Lucía envía más mensajes y Marco más palabras. Ninguna de las dos medidas es reciprocidad.

## Lo que el sistema NO debe producir

- "Marco tiene interés romántico en Lucía" ni cualquier afirmación sobre sentimientos.
- "Lucía es fría" o "desinteresada" por la latencia del 12/10.
- "La relación es recíproca" a partir de los 28 turnos de cada uno.
- Una diferencia significativa de iniciativa entre los dos.
- Un conflicto detectado en la broma del 26/10.
- Contar como "sin respuesta" los 5 turnos sin intervención previa ni el último turno del chat.
- Presentar los turnos de 213 a 288 min como horas de actividad.
- Niveles de confianza o probabilidades.

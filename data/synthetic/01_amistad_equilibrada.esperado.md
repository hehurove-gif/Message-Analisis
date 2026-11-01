# Chat sintético 01: amistad equilibrada

Archivo: `01_amistad_equilibrada.txt` (formato Android, 24 h). Participantes ficticios: Lucía y Marco, que el sistema muestra como A y B.

**Para qué sirve.** Probar que las definiciones (mensaje, ráfaga, turno, sesión, reanudación, latencia) y los cálculos se comportan como esperamos, y que el sistema **no fuerza conclusiones** en los casos ambiguos. No demuestra que el sistema identifique relaciones reales.

**Cómo se verificaron los números.** Con scripts de referencia independientes del código del proyecto (conteo directo sobre el archivo, aplicando `definiciones_operativas.md` v0.3). Si el sistema difiere, hay que investigar cuál de los dos tiene el error; ninguno se da por correcto de antemano. Los escenarios de borde de la latencia y de los turnos se prueban con valores conocidos en `00_escenarios_validacion`.

## Comportamientos representados

- Conversación equilibrada de 3 semanas (5 a 26 de octubre de 2026): planes de cine y comida, ayuda con una mudanza, apoyo tras un día largo.
- Ambos proponen planes e intervienen en tiempos parecidos.
- Una pausa de varios días entre sesiones, con distintas personas reanudando.
- Estilo afectuoso habitual en Marco ("cariño", "corazón", "eres la mejor") sin escalada ni contexto romántico.

## Parser (Fase 1, referencia)

| Concepto | Esperado |
| --- | --- |
| Mensajes de las personas | 74 (Lucía 39, Marco 35) |
| Mensajes de sistema | 1 (cifrado), no cuenta como mensaje de nadie |
| Multimedia omitida | 1 (`<Multimedia omitido>`, Marco, 06/10 13:20), tipo `media` |
| Mensaje multilínea | 1 (Marco, 14/10 20:45): las 2 líneas sin fecha se anexan a ese mensaje |
| Rango | 05/10/2026 09:12 a 26/10/2026 14:42 |

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

- La mediana general (14 contra 9 min) **no depende del hueco de sesión**. Las demás sí.
- **Estados de los turnos** (6 h): 50 con intervención, 5 **sin intervención previa a su nuevo turno** (Marco 06/10 18:35, 08/10 22:40 y 09/10 10:31; Lucía 13/10 16:50 y 21/10 11:50) y 1 **sin respuesta observada** (Lucía, 26/10 14:42, último mensaje del chat). Con 2 h son 8 y 1; con 12 h, 4 y 1.
- **Intervenciones entre sesiones** (6 h): 8, entre 10 h y 85 h. Las más largas: Marco 14/10 20:45 contestado por Lucía el 17/10 a las 09:55 (61 h 10 min) y Lucía 17/10 22:26 contestada por Marco el 21/10 a las 11:30 (85 h 4 min).

## Registro por turno (6 h)

17 turnos tienen más de un mensaje. 14 duran 2 minutos o menos. Los otros tres tienen varias ráfagas y mucho silencio dentro:

| Turno | Mensajes | Ráfagas | Transcurrido | Silencios (min) | Minutos dentro de ráfagas |
| --- | --- | --- | --- | --- | --- |
| Marco 06/10 08:55 a 13:20 | 2 | 2 | 265 min | 265 | 0 |
| Lucía 06/10 13:22 a 18:10 | 3 | 2 | 288 min | 0, 288 | 0 |
| Marco 13/10 13:12 a 16:45 | 2 | 2 | 213 min | 213 | 0 |

**Lectura.** Esos turnos duran horas porque la sesión sigue abierta y la misma persona escribe de nuevo antes de que intervenga la otra. **No son horas de conversación**: el tiempo dentro de ráfagas es cero. Se reportan como fragmentación y hábito de escritura, no como participación o interés.

## Resultados esperados del sistema

| Hallazgo | Etiqueta esperada |
| --- | --- |
| Participación: 52.7 % / 47.3 % de los mensajes; 28 / 28 turnos | Observación |
| Reanudaciones: Lucía ≥ Marco en los tres huecos, con diferencias de 2 a 3 | Observación; **no** es patrón (diferencia pequeña y sensible al umbral) |
| Último mensaje: Marco ≥ Lucía en los tres huecos, con diferencias de 4, 2 y 1 que se reducen al subir el hueco | Observación; no es patrón (diferencia pequeña y sensible al umbral) y no se interpreta |
| Latencia: medianas generales de 14 y 9 min, mismo orden de magnitud | Observación; **no concluyente** como diferencia |
| Reciprocidad general: equilibrada | Patrón, confianza media |
| Vínculo: contexto personal, cercanía frecuente, amistad | Hipótesis con confianza media; interés romántico **no sustentado** |

## Casos ambiguos (el sistema no debe forzar conclusiones)

1. **Afecto habitual de Marco.** Hay 4 mensajes con vocabulario afectuoso ("cariño", "corazón", "eres lo máximo", "eres la mejor"), en 2 semanas distintas. **Con los umbrales actuales de `config.yaml` esto cumple recurrencia** (3 eventos, 2 periodos). Esperado: se reporta como patrón *descriptivo* de estilo afectuoso, **sin** pasar a interés romántico, porque (a) aparece en contextos de favor y agradecimiento, (b) no hay propuestas de verse a solas ni escalada, (c) Lucía no responde en el mismo registro. Comprueba que la recurrencia es necesaria pero no suficiente.
2. **Cumplido aislado de Lucía** (08/10, "te quedó genial el corte de pelo"). Esperado: se registra como evento, sin peso. Marco interviene con agradecimiento y una explicación neutral.
3. **Sarcasmo de Marco** (12/10, "otro lunes de reuniones, qué bien 🙄"). Esperado: no contar "qué bien" como afecto positivo; si hay detección de ironía, queda con confianza baja. Lucía responde con ánimo, lo que apoya el tono sarcástico pero no lo prueba.
4. **Intervención lenta de Lucía** (12/10, Marco 13:00 y Lucía 15:40: 160 min, dentro de sesión). Ella misma lo explica (estaba en una junta). Esperado: dato atípico que no cambia la mediana, sin lectura de desinterés. Hay otras dos latencias dentro de sesión superiores a 200 min (Marco 08/10: 264 min; Lucía 12/10: 209 min).
5. **Queja en broma** (26/10, "tú nunca contestas rápido jaja"). Esperado: no se clasifica como conflicto; tiene marcador de broma y se cierra con "te perdono". Como mucho, evento de baja confianza. Además, la queja es un comentario sobre latencia: la mediana de Marco (9 min) no la respalda como patrón.
6. **Pausas largas.** La del 17 al 21 de octubre (85 h 4 min entre el último mensaje de Lucía y la intervención de Marco) y la del 21 al 24 (Lucía escribe dos veces seguidas, tras un cambio de sesión, antes de que intervenga Marco). Esperado: se registran como latencia entre sesiones y como estado "sin intervención previa a su nuevo turno", **sin lectura sobre quién tiene más interés**.

## Lo que el sistema NO debe producir

- "Marco tiene interés romántico en Lucía" ni cualquier afirmación sobre sentimientos.
- "Lucía es fría" o "desinteresada" por la latencia del 12/10.
- Una diferencia significativa de iniciativa entre los dos.
- Un conflicto detectado en la broma del 26/10.
- Contar como "sin respuesta" los 5 turnos sin intervención previa ni el último turno del chat.
- Presentar los turnos de 213 a 288 min como horas de actividad.

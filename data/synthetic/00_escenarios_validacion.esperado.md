# Fixture 00: escenarios de validación

Archivo: `00_escenarios_validacion.txt` (21 mensajes, 02/11/2026 10:00 a 06/11/2026 18:01, formato Android 24 h). Participantes ficticios: Ana y Beto.

**Para qué sirve.** No es uno de los seis chats de comportamiento: es un micro-chat construido para ejercitar, con valores conocidos al minuto, los cinco escenarios que definen las métricas de latencia y de duración de turnos. Su contenido es deliberadamente trivial (un reporte de trabajo) para que ningún resultado dependa de interpretar texto.

**Cómo se verificó.** Primero derivé a mano todos los valores de la tabla de 6 h y la sensibilidad agregada; después los comparé con un script de referencia independiente del código del proyecto. Coincidieron en todos los valores (el script además calculó las variantes por participante). Es una verificación doble hecha por mí, no por una segunda persona.

## Segmentación con hueco de 6 h

7 sesiones y 11 turnos (Ana 7, Beto 4).

| # | Turno | Mensajes | Sesión |
| --- | --- | --- | --- |
| 1 | Ana 02/11 10:00 a 10:09 | 5 | 1 |
| 2 | Beto 02/11 10:15 | 1 | 1 |
| 3 | Ana 02/11 23:30 | 1 | 2 |
| 4 | Beto 03/11 08:00 a 16:20 | 6 | 3 |
| 5 | Ana 03/11 16:45 | 1 | 3 |
| 6 | Ana 04/11 09:00 | 1 | 4 |
| 7 | Beto 04/11 15:30 | 1 | 5 |
| 8 | Ana 04/11 21:30 | 1 | 5 |
| 9 | Beto 05/11 09:00 | 1 | 6 |
| 10 | Ana 05/11 09:10 | 1 | 6 |
| 11 | Ana 06/11 18:00 a 18:01 | 2 | 7 |

Los turnos 5 y 6 son de la misma persona pero **no se unen**: entre ambos hay 16 h 15 min, más que el hueco de sesión.

## Los cinco escenarios

| Escenario | Turno | Resultado esperado (6 h) |
| --- | --- | --- |
| 1. Noche contestada por la mañana | #3, Ana 02/11 23:30 | Beto interviene el 03/11 a las 08:00: latencia **510 min (8 h 30 min)**, **entre sesiones**. Ese turno de Beto es además una **reanudación** (primer turno de la sesión 3). Ambas descripciones coexisten. |
| 2. Sin otra intervención | #11, Ana 06/11 18:00 a 18:01 | Estado **sin respuesta observada**. No tiene latencia, no entra en ninguna mediana y no se interpreta como indiferencia. |
| 3. Dos ráfagas separadas por minutos | #1, Ana 02/11 | 5 mensajes en **2 ráfagas** (10:00 a 10:02 y 10:08 a 10:09). Silencios entre mensajes: 1, 1, **6**, 1 min. Transcurrido 9 min; 3 min dentro de ráfagas. Beto interviene a las 10:15: latencia **6 min**, dentro de sesión. Un solo turno de Ana, no dos. |
| 4. Turno con varias ráfagas y silencio largo | #4, Beto 03/11 | 6 mensajes en **4 ráfagas** (08:00; 11:00 a 11:01; 13:30 a 13:31; 16:20). Silencios: 180, 1, 149, 1, 169 min. Transcurrido **500 min (8 h 20 min)**, pero solo **2 min** dentro de ráfagas. Ana interviene a las 16:45: latencia **25 min** desde el último mensaje del turno (no desde el primero). |
| 5. Respuesta tras el límite de 6 h | #6, Ana 04/11 09:00 | Beto interviene a las 15:30: latencia **390 min (6 h 30 min)**, **entre sesiones** con 6 h; con 12 h sería dentro de sesión. |

### Casos de borde adicionales

| Caso | Resultado esperado |
| --- | --- |
| #7, Beto 04/11 15:30, Ana contesta a las 21:30 | Latencia exacta de **360 min = 6 h**. La sesión solo se corta cuando el silencio **supera** el hueco, así que cuenta como **dentro de sesión** con 6 y 12 h, y entre sesiones con 2 h. |
| #5, Ana 03/11 16:45 y #10, Ana 05/11 09:10 | Estado **sin intervención previa a su nuevo turno**: el siguiente mensaje es de la propia Ana tras un cambio de sesión. No tienen latencia ni entran en las medianas. Se registran, sin interpretar. |
| Gap de 6 min entre las ráfagas del turno #1 | 6 min supera los 5 min de la ráfaga, por eso abre una segunda ráfaga sin abrir un turno nuevo. |

## Latencias del hueco de 6 h (min)

Turnos con intervención: 8 de 11. Los otros 3 son los dos de "sin intervención previa" y el "sin respuesta observada".

| Turno | Interviene | Latencia | Sesión |
| --- | --- | --- | --- |
| #1 Ana | Beto | 6 | dentro |
| #2 Beto | Ana | 795 | entre |
| #3 Ana | Beto | 510 | entre |
| #4 Beto | Ana | 25 | dentro |
| #6 Ana | Beto | 390 | entre |
| #7 Beto | Ana | 360 | dentro |
| #8 Ana | Beto | 690 | entre |
| #9 Beto | Ana | 10 | dentro |

### Métricas esperadas por participante que interviene

| Quien interviene | n | Mediana general | Dentro de sesión | Entre sesiones | Proporción dentro |
| --- | --- | --- | --- | --- | --- |
| Ana (tras turnos de Beto) | 4 | 192.5 | 25 (n=3) | 795 (n=1) | 75 % |
| Beto (tras turnos de Ana) | 4 | 450 | 6 (n=1) | 510 (n=3) | 25 % |
| Agregado | 8 | 375 | 17.5 (n=4) | 600 (n=4) | 50 % |

## Sensibilidad al hueco de sesión (agregado)

| Hueco | Sesiones | Turnos | Mediana general | Dentro: mediana (n) | Entre: mediana (n) | Proporción dentro |
| --- | --- | --- | --- | --- | --- | --- |
| 2 h | 11 | 14 | 375 | 10 (3) | 510 (5) | 37.5 % |
| **6 h** | **7** | **11** | **375** | **17.5 (4)** | **600 (4)** | **50 %** |
| 12 h | 4 | 11 | 375 | 360 (7) | 795 (1) | 87.5 % |

- **La mediana general no cambia (375 min)**: no depende del hueco, como exige la definición.
- Las otras dos medianas y la proporción sí cambian mucho; es la razón de reportar las tres.
- Con 2 h el turno #4 de Beto se parte en 4 turnos (la sesión se corta en cada silencio de más de 2 h), lo que muestra cómo la duración y el número de ráfagas por turno dependen del hueco. Con 12 h hay 4 sesiones y el mismo número de turnos que con 6 h.

## Lo que el sistema NO debe producir

- Descartar la latencia de 510 min (o la de 390 min) por exceder una ventana.
- Contar los turnos #5 y #10 de Ana como "sin respuesta" ni como evidencia de rechazo de Beto.
- Interpretar el 06/11 18:00 sin respuesta como indiferencia.
- Reportar el turno de Beto con 500 min transcurridos como "8 horas de actividad" o como señal de participación o de interés.
- Medir la latencia desde el primer mensaje de un turno en vez del último.

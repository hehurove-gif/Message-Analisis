# Reporte de pruebas: cierre de Fases 3 y 4

Versión 0.2 · 2026-11-08 · 635 pruebas pasan (también en el equipo del usuario). Este reporte dice qué se verificó con datos sintéticos, qué queda pendiente con datos reales y qué límites tiene cada verificación. No contiene contenido de conversaciones reales.

## 1. Estado de las fases

| Fase | Contenido | Estado |
| --- | --- | --- |
| 3 | Participación, latencia, hábitos, estilo, contenido de turnos, ritmo, saludos, correspondencia formal (R1–R4) | **Cerrada en código, con verificación sintética y con revisión manual en datos reales (§3.1).** **Congelada:** no se agregan métricas nuevas; los cambios nuevos entran en Fase 5 o posteriores. |
| 4 | Evolución por mes/semana y detección de cambio sostenido | **Cerrada con verificación sintética y con la segunda corrida en datos reales (§3.3).** Sigue siendo provisional: umbrales experimentales. |

## 2. Qué se verificó (sintético)

Los chats se generan con `tests/synth_chats.py` (semilla fija, contenido ficticio). Pruebas en `tests/test_cierre_fase3_4.py`.

### 2.1 Fase 3: el sistema coincide con el lector de referencia

`tools/referencia/ref_latency.py` no comparte código con el sistema. Sobre tres chats (10 meses equilibrado, 10 meses con enfriamiento y 4 meses) coinciden **exactamente**:

- número de turnos y turnos por participante;
- mensajes por participante;
- latencias: n y mediana general, dentro de sesión y entre sesiones, en agregado y por participante que interviene.

Límite: la referencia usa las mismas definiciones (hueco de 6 h, turno = mensajes consecutivos). Detecta errores de implementación, **no** errores de definición.

### 2.2 Fase 4: enfriamiento detectado y sin falsas alarmas

- **Chat equilibrado** (mismo comportamiento los 10 meses, con ruido aleatorio): 0 alarmas en 30 semillas exploradas; 8 semillas quedan fijas como prueba.
- **Chat con enfriamiento** (desde el mes 5: menos días de contacto, B deja de abrir el día y responde en 40–120 min en vez de 1–3): en las 5 semillas de prueba se detecta la baja de `dias_activos` y la subida de la latencia mediana de quien se enfrió. Según la semilla también se detectan `inicia_dia_A` y `cierra_A`.
- El cambio se reporta con retraso (la fecha `desde` cae 1–2 meses después del inicio real) porque usa la mediana móvil de 4 periodos. Está documentado en `metrics/trends.py`.

Límite: el generador produce ruido estacionario y un único tipo de enfriamiento. Que no haya falsas alarmas aquí **no demuestra** que no las haya en chats reales (vacaciones, exámenes, cambios de rutina).

### 2.3 Corrección incluida

`greetings.py` buscaba subcadenas ("descansa" coincidía con "descansar" o "descansado"). Ahora exige palabra completa (definiciones v0.11).

## 3. Pendiente con datos reales (lo hace el usuario, en local)

Estos pasos no pueden hacerse desde el repo ni desde Claude. Sin ellos, ninguna métrica pasa de "implementada" a "validada con datos reales". Pegar solo números, nunca texto.

1. **Revisión manual de 5 sesiones reales** (criterio de salida de la Fase 3) — **HECHA 2026-11-08, ver §3.1**:
   - Elige 5 sesiones de un chat (idealmente de 2 archivos distintos, algunas con ráfagas y alguna con un silencio de varias horas).
   - A mano, en el TXT: cuenta los turnos de A y B, quién abre y quién cierra la sesión, y las latencias (minutos entre el último mensaje de un turno y el primero del siguiente del otro).
   - Compáralo con la salida de `tools/metricas_local.py` y `tools/segmentar_local.py`. Anota solo coincide / no coincide y la diferencia numérica.
2. **Falsos positivos de evolución en datos reales:** corre `metricas_local.py --resumen` (o `--semanal`) y revisa si los cambios sostenidos coinciden con periodos que recuerdas (vacaciones, exámenes, cambios de horario). Un cambio detectado sin causa recordada es una observación, no un error.
3. **Archivo 4:** orden de fecha — ver §3.3 (decidido: dmy).
4. **Timestamps fuera de orden y avisos sin catalogar:** `revisar_avisos_y_orden_local.py` sobre los archivos 0–3 (solo formas enmascaradas y números de línea).

### 3.1 Resultado de la revisión manual (2026-11-08)

Una exportación real (índice 1), 5 sesiones de 4–14 turnos repartidas por el chat, elegidas con `tools/sesiones_para_revisar_local.py` y contadas a mano con un conteo independiente en PowerShell (solo encabezados, sin leer contenido).

- **Mensajes, turnos, quién abre y quién cierra:** coinciden en las 5 sesiones (5/5).
- **Latencias entre turnos:** coinciden todas las comprobadas (≈40 intervalos). El corte de sesión (> 6 h) se comprobó en el lado final de las 5 sesiones; el silencio previo no se contó a mano.
- **Hallazgo 1 (datos):** una sesión contiene un mensaje con hora anterior al que lo precede en el archivo (retroceso de 8 min en el TXT). El sistema lo conserva en el orden del archivo y lo marca como fuera de orden; no reordena. Corregido en v0.12: `segmentar_local` informa también `pares_de_turnos_fuera_de_orden` (retrocesos entre turnos de distinto autor); en esa exportación son 5.
- **Hallazgo 2 (definición):** un turno puede contener pausas largas internas (p. ej. 2 h 41 min entre dos mensajes del mismo autor, dentro del hueco de 6 h). Es coherente con la definición (turno = mensajes consecutivos del mismo autor dentro de la sesión) y su latencia se mide desde el último mensaje del turno; queda documentado como límite.
- Alcance: un solo archivo, 5 sesiones. Valida la implementación, no las definiciones.

### 3.2 Ajustes de la Fase 4 por las primeras corridas reales (definiciones v0.12)

Con exportaciones reales el detector (a) marcaba como "baja de días activos" el final del chat, (b) no podía detectar nada en la latencia porque la mediana vale 0 en todos los meses y (c) detectaba un cambio con la granularidad semanal y no con la mensual. Se agregaron pausas largas fuera de la detección, la serie de respuesta rápida (≤ 5 min) y la etiqueta de sensibilidad a la granularidad, con pruebas sintéticas. Verificado en §3.3.

### 3.3 Segunda corrida en datos reales (2026-11-08)

Cifras relacionales reales no se registran en este repo público; solo si cada comprobación se cumple.

- **Pausa larga:** en la exportación con 3 meses vacíos tras el final de la actividad, esos periodos salen como `pausa` y ya no aparece "baja de días activos" como cambio sostenido. Cumple.
- **Sensibilidad a la granularidad:** dos cambios detectados solo con la granularidad semanal quedan etiquetados `sensible_a_granularidad` y no se reportan como patrón. Cumple.
- **Respuesta rápida (≤ 5 min):** la serie tiene valores informativos en todos los meses con datos, a diferencia de la mediana (0 en todos); no detecta cambios sostenidos en esa exportación.
- **Fuera de orden entre turnos:** `pares_de_turnos_fuera_de_orden` ≠ 0 donde se conocía un caso (5 en la exportación revisada). Cumple.
- **Límite conocido:** al final de un chat con mensajes sueltos (p. ej. 3 mensajes al mes), la frecuencia puede bajar sin ser pausa y producir un "baja" si dura ≥ 3 periodos con datos; aquí no ocurrió porque el último periodo es `parcial`. No se corrige por ahora.
- **Archivo 4:** con orden dmy la importación queda `ok`. La línea 724 (no es un mensaje de persona) está fechada el día de la exportación solo si se lee dmy; eso apoya dmy. Con un solo bloque de 9 días de actividad sus series de evolución quedan sin datos suficientes. **Decisión del usuario (2026-11-08): dmy.** Razón aportada: con mdy los 723 mensajes caerían en seis días 9 de seis meses distintos, lo que no tiene sentido para un chat. Se aplica con `--hint 4=dmy` (el parser no la toma por su cuenta).

**Conclusión:** Fases 3 y 4 cerradas como MVP (código, sintético, referencia independiente, revisión manual y dos corridas reales). Quedan abiertos, sin bloquear la Fase 5: avisos de sistema sin catalogar, timestamps fuera de orden en otros archivos y región/versión de WhatsApp.

## 4. Qué NO afirman estas fases

- Las métricas son descriptivas y los umbrales son experimentales; "robusto" significa estable ante los parámetros probados, no válido científicamente.
- La correspondencia formal mide la forma de los mensajes, no interés ni afecto.
- Los saludos son línea base, no indicadores de interés.
- Un cambio sostenido describe **cuándo** cambia una cifra, no **por qué**.

## 5. Siguiente

Fase 5 (capa léxica y afectiva basada en reglas): primero una propuesta de definiciones operativas para aprobación, después el código.

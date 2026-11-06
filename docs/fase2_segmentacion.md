# Fase 2 — Segmentación (MVP ligero)

Versión 0.1 · 2026-11-05. Implementa las definiciones operativas v0.6 (secciones 1 y 2); no añade definiciones nuevas.

| Módulo | Qué entrega | Qué NO hace |
| --- | --- | --- |
| `segmentation/turns.py` | Turnos con primer/último timestamp, minutos transcurridos, ráfagas, silencios y minutos dentro de ráfagas | Latencias, métricas, interpretación |
| `segmentation/sessions.py` | Sesiones, reanudaciones (primer turno), último mensaje (último turno) y sensibilidad con 2/6/12 h | Atribuir intención; interpretar quién tiene más interés |

**Reglas de borde.** Una sesión se corta solo cuando el silencio **supera** el hueco; con el intervalo exactamente igual continúa. Lo mismo para las ráfagas (300 s).

**Primera y última sesión.** La primera no es una reanudación (es el inicio de los datos) y la última no es un cierre observado (es el fin de los datos): se marcan y no entran en los conteos.

**Fuera de orden.** No se reordena por timestamp. Un retroceso no corta la sesión; el turno queda con `tiene_fuera_de_orden`.

**Robustez** (tres niveles, de `config.yaml` → `evidence_assessment`): `robusto` = el mismo participante lidera con todos los huecos y la diferencia relativa |A−B|/(A+B) es ≥ `segmentation.min_margin_for_robust` (0,10, experimental) en todos; `robusto_en_direccion_magnitud_sensible` = misma dirección pero algún margen menor; `sensible_a_umbrales` = la dirección cambia o hay empate. No es validez científica ni una interpretación. `suficiencia_de_datos` usa `data_sufficiency.min_sessions_for_initiative` (10).

**Candado.** `turns_from_result` y `sensitivity_from_result` solo trabajan con importaciones con el análisis habilitado (tipo de conversación confirmado por el usuario y líneas perdidas resueltas o aceptadas).

**Verificación.** Los tres chats de la Fase 0 coinciden turno por turno y sesión por sesión con el lector de referencia (`tools/referencia/ref_latency.py`) con huecos de 2, 6 y 12 h.

**Pendiente.** No se ha ejecutado sobre exportaciones reales (el análisis de la primera sigue sin habilitar). Los 12 timestamps fuera de orden de esa exportación serán la primera prueba de este módulo.

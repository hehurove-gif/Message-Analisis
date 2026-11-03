# Reporte de pruebas — Fase 1.2 (parser de WhatsApp)

2026-11-03 · Python 3.13 · pytest 9.1 · `python -m pytest -q` desde la raíz del repositorio (dependencias: PyYAML, pytest).

**Resultado: 461 pruebas, 461 aprobadas, 0 fallos.** Todos los fixtures son simulados (ver `limitaciones_y_formatos_pendientes.md`).

| Grupo | Archivo | Pruebas | Qué comprueba |
| --- | --- | --- | --- |
| Fixture vs `.esperado.json` | `test_parser_fixtures.py` | 99 (33 × 3) | Reporte, mensajes y mapa de anonimización de cada fixture coinciden con lo esperado |
| Invariantes 1–10 del contrato | `test_parser_fixtures.py` | 330 (33 × 10) | Una disposición por línea; encabezado ⇒ mensaje; `system` sin participante; `seq` consecutivo; rangos sin solape; ninguna línea desaparece; orden de origen; anonimización fuera del reporte; fechas ambiguas sin normalizar; grupos nunca aprobados |
| Casos adicionales | `test_parser_fixtures.py` | 17 | `FORMAT_AMBIGUOUS` (F03); `ENCODING_ERROR` (F04 y bytes en memoria); D07 pendiente de revisión y sin análisis automático; aceptación expresa de pérdidas línea por línea; C01 bloqueado y C02 rechazado; pista de fecha explícita que no pisa los datos; marcas U+200E/U+200F conservadas en `texto`; U+202F conservado en `timestamp_original`; chats 00 (con `dmy`), 01 y 02 coinciden con el lector de referencia |
| Privacidad | `test_privacy.py` | 8 | Sin escritura a disco; sin red (sockets bloqueados) ni imports de red; `allow_network: true` se rechaza; reportes sin nombres ni contenido; mapa solo en memoria; errores sin fragmentos; nada impreso |
| Lector de referencia | `test_ref_latency.py` | 9 | Continuaciones legítimas, timestamps inválidos, huérfanas, rechazo sin mostrar contenido; resultados de los tres chats sin cambios |

## Problemas encontrados al implementar

1. Los chats de la Fase 0 (`DD/MM/YYYY HH:MM`) no estaban cubiertos por el catálogo (solo año de 2 dígitos). Se amplió `android_24h_sin_coma`; sigue siendo un formato simulado.
2. La heurística de aspecto de timestamp no detectaba minutos de 1 dígito (D07, línea 9): corregida.
3. `rango_fechas` usaba primero/último del archivo; los fixtures esperaban mínimo/máximo: el contrato lo precisa ahora.
4. E01: el contrato decía "no se etiqueta" con más de 2 autores y el fixture esperaba etiqueta C: se alineó el contrato.
5. Un test mío comparaba textos de un carácter (`A`) con reprs; se limitó a textos de ≥ 8 caracteres.

Sin otros fallos. Los tres chats sintéticos se importan sin líneas no procesadas; el 00 queda bloqueado sin pista y se acepta con `date_order_hint=dmy`.

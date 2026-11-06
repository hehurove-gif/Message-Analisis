# Limitaciones y formatos pendientes de observación (Fase 1.2)

Versión 0.1 · 2026-11-03. Acompaña al contrato v0.2 y al catálogo de formatos.

## 1. Qué demuestran (y qué no) las pruebas actuales

- **Todos los fixtures son simulados.** Los escribí yo a partir de la documentación de WhatsApp y de proyectos de terceros (chatpack, whatstk). Ninguno procede de una exportación real observada.
- Que las 486 pruebas pasen demuestra que el parser **cumple el contrato** sobre esos ejemplos. **No demuestra compatibilidad con exportaciones reales de WhatsApp**: si un formato real difiere del simulado, el parser lo rechazará o lo reportará como líneas no procesadas, pero no hay evidencia de que reconozca los reales.
- Las marcas de multimedia, los avisos de cifrado y los avisos de grupo (incluidos los de B01) son hipótesis de catálogo, no observaciones.

## 2. Formatos pendientes de validación con exportaciones reales

| Formato | Estado de evidencia | Qué falta comprobar |
| --- | --- | --- |
| `android_24h_coma` | Documentado por terceros | Variantes regionales, año de 2 dígitos con coma |
| `android_24h_sin_coma` (año de 2 y 4 dígitos) | **Sin respaldo**; es el formato de los chats de la Fase 0 | Que exista en alguna versión real. Ampliado en la Fase 1.2 para aceptar año de 4 dígitos |
| `android_12h_es_nnbsp`, `android_12h_compacto` | Documentado parcialmente | Si el espacio antes de `a. m.`/`p. m.` es U+202F o ordinario según la versión |
| `android_12h_en_mdy` | Documentado por terceros | Orden mes/día real |
| `android_24h_puntos_segundos`, `android_24h_guiones` | **Sin respaldo** | Que existan |
| `ios_24h_corchetes`, `ios_12h_es_corchetes`, `ios_12h_en_mdy_corchetes`, `ios_24h_puntos_corchetes` | Documentado por terceros / simulado | Corchetes, segundos y marcas U+200E reales al inicio de cada línea |
| Marcadores de multimedia omitida y de mensaje eliminado | Simulados | Texto exacto por idioma y versión; adjuntos con nombre de archivo |
| Avisos del sistema y de grupo | Simulados (solo español e inglés) | Texto exacto; otros idiomas (E03 documenta el falso negativo conocido) |

Hasta observar exportaciones reales, ninguno de estos formatos debe describirse como "compatible con WhatsApp".

## 3. Limitaciones que el parser no puede resolver con el TXT

1. **Individual o grupal.** Dos autores no prueban que el chat sea individual: un grupo sin avisos de grupo en el rango exportado es indistinguible de un chat 1-1. El parser devuelve `pending_confirmation` y exige confirmación del usuario. Un aviso de grupo en un idioma no catalogado (E03) no se detecta como evidencia; se cuenta como `sin_catalogar` solo si carece de autor.
2. **Citas pegadas.** Un mensaje que contenga una línea con un encabezado **válido** se leerá como mensaje nuevo (D09). Es indistinguible en el TXT.
3. **Líneas no procesadas.** No se sabe si son texto perdido, ruido del exportador o formato no catalogado. Un texto legítimo que empiece con fecha y hora se reporta y no se anexa (D07, línea 13): se prefiere un aviso visible a una unión silenciosa. No hay umbral tolerable; antes hay que investigar su significado con datos reales.
4. **Zona horaria y precisión.** El TXT no dice la zona horaria; no se asume ninguna. Los timestamps son la hora local escrita. Con precisión de minuto, muchos mensajes comparten timestamp y el orden fiable es el del archivo.
5. **Orden día/mes.** Sin un día > 12 ni una pista explícita, el parser bloquea la importación. Con una pista, el orden queda marcado `*_por_indicacion`, no como dato.
6. **Mensajes eliminados y multimedia.** No se conoce su contenido ni quién eliminó.
7. **Contacto renombrado.** Un cambio de nombre a mitad del chat produce un autor extra y el chat se rechaza (pregunta abierta 2 del contrato).
8. **Marcas de dirección.** `texto` conserva U+200E/U+200F; `texto_normalizado` las elimina. Si un análisis de idiomas RTL las necesita, debe usar `texto`.
9. **Nombres dentro del texto.** El anonimizado cubre a los participantes, no los nombres que aparezcan en el contenido de los mensajes.
10. **Cálculo de `rango_fechas`.** Es el mínimo y el máximo de los mensajes de persona, no el primero y el último del archivo.

### Caso en observación: autor con prefijo extra (1.ª exportación real)

En la primera exportación real (Android) 1 de 27.569 encabezados traía un autor de la forma `<prefijo> - <nombre del otro autor>`, y el parser lo contó como tercer autor. Origen desconocido. Se reporta como `AUTHOR_ALIAS_SUSPECTED`; el usuario puede unirlo con `--unir C=B` o aceptar los sospechosos con `--aceptar-alias-sospechosos` (decisión explícita, registrada en el reporte; nunca por defecto). **Abierto:** con más exportaciones reales hay que ver si es un caso raro o algo normal; si se repite, hay que estudiar su causa antes de cambiar el parser.

## 4. Procedimiento local para contrastar exportaciones propias

Objetivo: comprobar el parser con exportaciones reales **sin subirlas al repositorio ni a ningún servicio**.

1. Exporta el chat desde WhatsApp (sin multimedia) y guarda el TXT **fuera del repositorio** (por ejemplo, `~/exportaciones_reales/`). La herramienta se niega a leer archivos dentro del repositorio; `.gitignore` también excluye `private/`, `exportaciones_reales/` y `*.local.txt` por si acaso.
2. Ejecuta, en tu equipo:
   `python tools/validar_exportacion_local.py ~/exportaciones_reales/chat.txt --formas 10`
   Añade `--date-order-hint dmy` (o `mdy`) solo si el reporte pide `INDICAR_ORDEN_FECHA`.
3. Lee el reporte: formato reconocido, conteos por tipo, `lineas_no_procesadas` con motivo, avisos sin catalogar y evidencias de grupo. No contiene nombres ni texto.
4. Para las líneas no reconocidas, `--formas N` muestra su **forma enmascarada** (dígitos → `9`, letras → `a`, caracteres especiales como `<U+XXXX>`). Con ella puedes describir un formato nuevo **sin copiar contenido privado**. Ojo: conserva la longitud de las palabras; solo debe verse en tu equipo.
5. Si aparece un formato nuevo, abre una nota con: forma enmascarada, plataforma, idioma, versión de la app y región. Con eso se añade una fila al catálogo y un fixture **sintético** (datos ficticios) que reproduzca la forma. **No pegues líneas reales en el repositorio, en issues ni en servicios externos.**
6. Cuando un formato se haya visto en una exportación real, se cambia su nivel de evidencia de "simulado" a "observado" en `formatos_exportacion_whatsapp.md` (sección 9).

La herramienta solo lee el archivo, no escribe nada y no usa la red; las pruebas de privacidad (`tests/test_privacy.py`) lo verifican para el parser.

## 5. Fuera del alcance de la Fase 1.2

Segmentación (ráfagas, turnos, sesiones), métricas de participación, reciprocidad, NLP, análisis sentimental, interés romántico e interfaz gráfica no están implementados. No se avanza a la Fase 2 sin revisión.

# Chat sintético 07: falsos positivos por contexto

Archivos: `07_falsos_positivos_contexto.txt` (formato Android, 24 h) y `07_falsos_positivos_contexto.etiquetas.csv` (16 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que expresiones que **parecen** indicadores pero no lo son (citas, letras de canciones, negadas, preguntas, propuestas grupales, despedidas, acuerdos y fórmulas de cortesía) producen **P = 0** y los descartes esperados por contexto. No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/07_falsos_positivos_contexto.txt data/synthetic/07_falsos_positivos_contexto.etiquetas.csv
```

## Comportamientos representados

- Todas las expresiones etiquetadas son `no_candidato`: parecen afecto, apodo o propuesta pero son **citas** de otra persona o de una canción, formas **negadas** o de **pregunta**, un **acuerdo de trabajo**, una **despedida** ("nos vemos mañana") o una **propuesta grupal** con marcador explícito.
- Los saludos convencionales ("buenos días") son `linea_base`.
- **Nota de diseño:** una **broma** con apodo fuerte ("jaja a sus órdenes, mi reina 😂") sigue en P como `ambiguo` (propuesta §B.2) y por eso **no** está en este fixture, que exige P = 0; ese caso se prueba en pruebas unitarias. Aquí las bromas son quejas sin afecto.
- Las fórmulas de cortesía con apodo ("gracias, corazón") **no se pueden distinguir** de un apodo real (§B.3), por lo que tampoco se incluyen: lo resuelven la recurrencia y la línea base.

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Eventos P (indicador_candidato) | **0 en ambos** |
| Declaraciones | 0 |
| Patrón de expresión | **Ninguno** (no hay eventos que contar) |
| Respuestas | No hay estímulos P: sin categorías de respuesta |
| Descartes y exclusiones | Citas/canción excluidas de P por contexto; negadas y preguntas contadas aparte; propuesta grupal degradada |
| Límites | **Ninguno** |

Eventos etiquetados `no_candidato` por motivo (de las etiquetas):

| Motivo | Eventos |
| --- | --- |
| `acuerdo` | 1 |
| `cancion` | 1 |
| `cita_reportada` | 3 |
| `despedida_cortesia` | 2 |
| `negada` | 1 |
| `negada_infinitivo` | 1 |
| `pregunta_disculpa` | 1 |
| `propuesta_grupal` | 1 |
| `queja_en_broma` | 1 |
| `verse_ambigua` | 2 |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Iván | 0 | 0 | 0 | {} |
| Marina | 0 | 0 | 0 | {} |

Categorías de respuesta etiquetadas: {}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Iván': '18 (54.5 %)', 'Marina': '15 (45.5 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Iván': '125 (58.7 %)', 'Marina': '88 (41.3 %)'}
  turnos con hueco 2 h: {'Iván': '18 (54.5 %)', 'Marina': '15 (45.5 %)'}
  turnos con hueco 6 h: {'Iván': '18 (54.5 %)', 'Marina': '15 (45.5 %)'}
  turnos con hueco 12 h: {'Iván': '18 (54.5 %)', 'Marina': '15 (45.5 %)'}
  días con mensajes (frecuencia observable): 14 de 22; por persona {'Iván': 14, 'Marina': 14}; mensajes por día activo 2.36

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 4, 'mes': 1}

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=0; especificidad provisional (anotación cualitativa)={}
  S1 (P + calidez_no_especifica): frecuencia=0; especificidad provisional (anotación cualitativa)={}
  S2 (P sin candidatos ambiguo=si): frecuencia=0; especificidad provisional (anotación cualitativa)={}
  categorías de respuesta (P): {}
  secundarias (P): {}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO: no hay candidatos P en este chat (no se calcula)
```


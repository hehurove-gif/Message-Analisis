# Chat sintético 04: amistad cálida

Archivos: `04_amistad_calida.txt` (formato Android, 24 h) y `04_amistad_calida.etiquetas.csv` (36 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que una amistad cálida, con "te quiero", "amigo/a" y apodos generales a diario, produce una línea base alta y **simétrica** de calidez (S1) **sin ningún patrón en P**, y que no se confunde con interés romántico. No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/04_amistad_calida.txt data/synthetic/04_amistad_calida.etiquetas.csv
```

## Comportamientos representados

- **Semanas 1 a 6 (7 de septiembre a 12 de octubre):** Andrés y Camila se dicen "amigo/a" casi a diario, usan "te quiero" tras favores, fiestas y exámenes, y añaden 🫶, ❤️ o ☀️ de forma habitual. Es su estilo en todos los temas.
- **Nadie** usa cumplidos físicos, propuestas a solas, vida sentimental ni declaraciones: P = 0 y declaraciones = 0.
- **Respuestas:** devuelven afecto del mismo tipo (reciprocidad amistosa ambigua) o contestan directamente a la pregunta; ninguna respuesta es un límite ni un rechazo.
- **1 de octubre:** una pregunta abierta ("¿qué haces el sábado?") no es una propuesta a solas; la propuesta es para el grupo.

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Asimetría de expresión (P) | **No evaluable** (P = 0 en ambos): no hay nada que comparar |
| Patrón de expresión en P | **Ninguno** |
| Patrón en S1 (calidez no específica) | **Ambos**, simétrico; robusto en la rejilla semanal |
| Línea base | Alta y similar en los dos; el estilo afectuoso es habitual en todos los temas |
| Correspondencia en respuestas | No aplica a P; las respuestas a la calidez son `reciprocidad_amistosa_ambigua` o `respuesta_directa` (familia `acusa_sin_devolver`), no se interpretan como correspondencia romántica |
| Límites | **Ninguno** |
| Declaraciones | 0 |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Andrés | 0 | 0 | 17 | {} |
| Camila | 0 | 0 | 17 | {} |

Categorías de respuesta etiquetadas: {'invitacion_pospuesta_o_no_comprometida': 1, 'reciprocidad_amistosa_ambigua': 21, 'reconocimiento_sin_correspondencia_afectiva': 1, 'respuesta_directa': 11}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Andrés': '26 (51.0 %)', 'Camila': '25 (49.0 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Andrés': '124 (47.1 %)', 'Camila': '139 (52.9 %)'}
  turnos con hueco 2 h: {'Andrés': '24 (49.0 %)', 'Camila': '25 (51.0 %)'}
  turnos con hueco 6 h: {'Andrés': '24 (49.0 %)', 'Camila': '25 (51.0 %)'}
  turnos con hueco 12 h: {'Andrés': '24 (50.0 %)', 'Camila': '24 (50.0 %)'}
  días con mensajes (frecuencia observable): 20 de 36; por persona {'Camila': 20, 'Andrés': 20}; mensajes por día activo 2.55

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 6, 'mes': 2}
  -- variante S1 (P + calidez_no_especifica): eventos por autor {'Andrés': 17, 'Camila': 17}
     Andrés: por semana ISO {'S37': 3, 'S38': 3, 'S39': 4, 'S40': 4, 'S41': 3}
        semana: 17 eventos en 5 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 17 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
     Camila: por semana ISO {'S37': 3, 'S38': 4, 'S39': 4, 'S40': 3, 'S41': 2, 'S42': 1}
        semana: 17 eventos en 6 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 17 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=0; especificidad provisional (anotación cualitativa)={}
  S1 (P + calidez_no_especifica): frecuencia=34; especificidad provisional (anotación cualitativa)={'baja': 34}
  S2 (P sin candidatos ambiguo=si): frecuencia=0; especificidad provisional (anotación cualitativa)={}
  categorías de respuesta (P): {}
  secundarias (P): {}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO: no hay candidatos P en este chat (no se calcula)
```


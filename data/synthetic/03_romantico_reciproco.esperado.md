# Chat sintético 03: romántico recíproco

Archivos: `03_romantico_reciproco.txt` (formato Android, 24 h) y `03_romantico_reciproco.etiquetas.csv` (32 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que, cuando **ambas personas** expresan indicadores recurrentes y se corresponden, el perfil sale simétrico en expresión y con correspondencia en las dos direcciones, con una invitación aceptada y una declaración devuelta. No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/03_romantico_reciproco.txt data/synthetic/03_romantico_reciproco.etiquetas.csv
```

## Comportamientos representados

- **Semanas 1 y 2 (7 a 18 de septiembre):** colaboración académica y saludos convencionales (línea base de ambos). Un elogio de habilidad (18/09) es `no_candidato`.
- **Semanas 3 a 5 (21 de septiembre a 9 de octubre):** ambos usan cumplidos físicos, apodos con ❤️, confidencias afectivas y "te extraño"; los dos preguntan por la vida sentimental del otro (30/09). Mateo propone verse a solas dos veces y Valeria acepta las dos.
- **Correspondencia:** la mayoría de las respuestas devuelve el gesto (cumplido, apodo, confidencia) en pocos minutos. Algunas respuestas son directas (la pregunta de la vida sentimental) y una intervención no se refiere al mensaje anterior (24/09 09:12 → 18:00).
- **9 y 10 de octubre:** Mateo se declara, Valeria le corresponde de forma explícita y propone una relación; Mateo acepta.
- **Calidez no específica:** deseos amables y un ❤️ aislado, solo en la variante S1.

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Asimetría de expresión (P) | **Simétrica**: Mateo 10 y Valeria 9 eventos P; ambos en 3 semanas |
| Patrón de expresión | **Ambos** (3 días con evento en ≥ 2 semanas); robusto en las 12 combinaciones semanales |
| Robustez ante indicadores | P, S1 y S2 mantienen "ambos" |
| Correspondencia en respuestas | **En ambas direcciones**: familia `devuelve_afecto` dominante para los P de los dos: 8 de 10 (80 %) los de Mateo y 7 de 9 (78 %) los de Valeria; ambos cumplen 8 estímulos y 70 % |
| Límites | **Ninguno**; no debe aparecer `declina_o_delimita` |
| Declaraciones | 3 (Mateo 1, Valeria 2, entre el 09 y el 10/10), reportadas como cita y aparte de la recurrencia |
| Estado epistémico | Patrón descriptivo; sin hipótesis automáticas |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Mateo | 10 | 1 | 4 | {'acusa_sin_devolver': 2, 'devuelve_afecto': 8} |
| Valeria | 9 | 2 | 1 | {'acusa_sin_devolver': 2, 'devuelve_afecto': 7} |

Categorías de respuesta etiquetadas: {'correspondencia_afectiva': 15, 'invitacion_aceptada': 4, 'reconocimiento_sin_correspondencia_afectiva': 2, 'respuesta_directa': 6, 'respuesta_no_relacionada': 1}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Mateo': '31 (50.0 %)', 'Valeria': '31 (50.0 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Mateo': '180 (55.9 %)', 'Valeria': '142 (44.1 %)'}
  turnos con hueco 2 h: {'Mateo': '31 (50.8 %)', 'Valeria': '30 (49.2 %)'}
  turnos con hueco 6 h: {'Mateo': '31 (50.8 %)', 'Valeria': '30 (49.2 %)'}
  turnos con hueco 12 h: {'Mateo': '31 (50.8 %)', 'Valeria': '30 (49.2 %)'}
  días con mensajes (frecuencia observable): 24 de 43; por persona {'Mateo': 24, 'Valeria': 24}; mensajes por día activo 2.58

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 7, 'mes': 2}
  -- variante P  (principal: indicador_candidato): eventos por autor {'Mateo': 10, 'Valeria': 9}
     Mateo: por semana ISO {'S39': 6, 'S40': 2, 'S41': 2}
        semana: 10 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 10 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
     Valeria: por semana ISO {'S39': 4, 'S40': 3, 'S41': 2}
        semana: 9 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 9 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S1 (P + calidez_no_especifica): eventos por autor {'Mateo': 14, 'Valeria': 10}
     Mateo: por semana ISO {'S39': 7, 'S40': 4, 'S41': 3}
        semana: 14 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 14 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
     Valeria: por semana ISO {'S39': 5, 'S40': 3, 'S41': 2}
        semana: 10 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 10 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S2 (P sin candidatos ambiguo=si): eventos por autor {'Mateo': 8, 'Valeria': 7}
     Mateo: por semana ISO {'S39': 5, 'S40': 2, 'S41': 1}
        semana: 8 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 8 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
     Valeria: por semana ISO {'S39': 3, 'S40': 3, 'S41': 1}
        semana: 7 eventos en 3 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 7 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=19; especificidad provisional (anotación cualitativa)={'media': 15, 'baja': 4}
  S1 (P + calidez_no_especifica): frecuencia=24; especificidad provisional (anotación cualitativa)={'baja': 9, 'media': 15}
  S2 (P sin candidatos ambiguo=si): frecuencia=15; especificidad provisional (anotación cualitativa)={'media': 15}
  categorías de respuesta (P): {'correspondencia_afectiva': 12, 'respuesta_directa': 4, 'invitacion_aceptada': 3}
  secundarias (P): {'reconocimiento_sin_correspondencia_afectiva': 1}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO DE Mateo (mínimo para comparar: 20 turnos)
  P  (principal: indicador_candidato) | hueco 2 h | candidatos sin intervención previa: 0
     candidatos   n=10 (insuficiente) general=8 dentro=5.5(n=8) entre=636.5(n=2)
     declaracion  n= 1 (insuficiente) general=4 dentro=4(n=1) entre=-(n=0)
     resto        n=17 (insuficiente) general=25 dentro=4(n=9) entre=2065.5(n=8)
  P  (principal: indicador_candidato) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n=10 (insuficiente) general=8 dentro=5.5(n=8) entre=636.5(n=2)
     declaracion  n= 1 (insuficiente) general=4 dentro=4(n=1) entre=-(n=0)
     resto        n=17 (insuficiente) general=25 dentro=4(n=9) entre=2065.5(n=8)
        latencias candidatos: [2, 2, 3, 5, 6, 10, 15, 20, 616, 657]
        latencias resto     : [1, 1, 2, 4, 4, 5, 10, 20, 25, 687, 1495, 1695, 1866, 2265, 2982, 3628, 5038]
  P  (principal: indicador_candidato) | hueco 12 h | candidatos sin intervención previa: 0
     candidatos   n=10 (insuficiente) general=8 dentro=8(n=10) entre=-(n=0)
     declaracion  n= 1 (insuficiente) general=4 dentro=4(n=1) entre=-(n=0)
     resto        n=17 (insuficiente) general=25 dentro=4.5(n=10) entre=2265(n=7)
  S1 (P + calidez_no_especifica) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n=14 (insuficiente) general=12.5 dentro=8(n=10) entre=672(n=4)
     declaracion  n= 1 (insuficiente) general=4 dentro=4(n=1) entre=-(n=0)
     resto        n=13 (insuficiente) general=25 dentro=4(n=7) entre=2623.5(n=6)
        latencias candidatos: [2, 2, 3, 5, 6, 10, 10, 15, 20, 20, 616, 657, 687, 1495]
        latencias resto     : [1, 1, 2, 4, 4, 5, 25, 1695, 1866, 2265, 2982, 3628, 5038]
  S2 (P sin candidatos ambiguo=si) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 8 (insuficiente) general=5.5 dentro=5.5(n=8) entre=-(n=0)
     declaracion  n= 1 (insuficiente) general=4 dentro=4(n=1) entre=-(n=0)
     resto        n=19 (insuficiente) general=616 dentro=4(n=9) entre=1780.5(n=10)
        latencias candidatos: [2, 2, 3, 5, 6, 10, 15, 20]
        latencias resto     : [1, 1, 2, 4, 4, 5, 10, 20, 25, 616, 657, 687, 1495, 1695, 1866, 2265, 2982, 3628, 5038]
```


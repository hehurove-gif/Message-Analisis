# Chat sintético 05: respuestas ambiguas, sin límites

Archivos: `05_ambiguo.txt` (formato Android, 24 h) y `05_ambiguo.etiquetas.csv` (14 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que cuando una persona expresa indicadores recurrentes y la otra responde con aplazamientos, cordialidad amistosa y respuestas que no se pueden clasificar, **el resultado es `no_concluyente`**: nunca se infiere un rechazo ni una correspondencia. Es el fixture que el usuario etiqueta a ciegas (propuesta §G.3). No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/05_ambiguo.txt data/synthetic/05_ambiguo.etiquetas.csv
```

## Comportamientos representados

- **Semanas 1 y 2 (14 a 18 de septiembre):** colaboración académica y saludos convencionales (línea base).
- **Semanas 3 a 6 (21 de septiembre a 17 de octubre):** Ricardo expresa 12 indicadores: cumplidos físicos, apodos con ❤️, tres propuestas a solas, vida sentimental, confidencias y "te extraño".
- **Paola** nunca los corresponde de forma explícita pero tampoco delimita: aplaza las tres propuestas y el "¿cuándo nos vemos?" ("veamos", "luego te aviso"), contesta con cordialidad amistosa ("buenos días Ric 😊"), contesta lo literal de las preguntas y a veces responde algo que no permite clasificar ("ay Ric jaja").
- **Ninguna** frase es un límite ni un rechazo; ninguna es una invitación declinada. Las respuestas lentas o breves no se interpretan como indiferencia.
- **Paola** no usa indicadores P; coopera de forma normal en lo académico y toma la iniciativa en el proyecto final (21/10).

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Asimetría de expresión (P) | **Hacia Ricardo**: 12 eventos P frente a 0 |
| Patrón de expresión | **Solo Ricardo** (3 días con evento en ≥ 2 semanas); robusto en las 12 combinaciones semanales |
| Respuestas de Paola | Ninguna familia alcanza el 70 %: `acusa_sin_devolver` 6 de 12 (50 %; 60 % si se excluyen las 2 `no_evaluable`), `redirige_o_aplaza` 4 de 12 (33 %), `no_evaluable` 2 de 12 |
| Resultado | **`no_concluyente`** en correspondencia; **no** `declina_o_delimita` |
| Límites | **Ninguno**; ni `limite_interpersonal_suave` ni `limite_interpersonal_explicito` |
| Declaraciones | 0 |
| Estado epistémico | Observación de expresión recurrente (patrón); la respuesta no alcanza patrón; sin hipótesis |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Paola | 0 | 0 | 0 | {} |
| Ricardo | 12 | 0 | 0 | {'acusa_sin_devolver': 6, 'no_evaluable': 2, 'redirige_o_aplaza': 4} |

Categorías de respuesta etiquetadas: {'invitacion_pospuesta_o_no_comprometida': 4, 'no_determinada': 2, 'reciprocidad_amistosa_ambigua': 3, 'reconocimiento_sin_correspondencia_afectiva': 1, 'respuesta_directa': 2}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Paola': '20 (47.6 %)', 'Ricardo': '22 (52.4 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Paola': '105 (46.9 %)', 'Ricardo': '119 (53.1 %)'}
  turnos con hueco 2 h: {'Paola': '19 (47.5 %)', 'Ricardo': '21 (52.5 %)'}
  turnos con hueco 6 h: {'Paola': '19 (47.5 %)', 'Ricardo': '21 (52.5 %)'}
  turnos con hueco 12 h: {'Paola': '19 (47.5 %)', 'Ricardo': '21 (52.5 %)'}
  días con mensajes (frecuencia observable): 21 de 38; por persona {'Paola': 18, 'Ricardo': 19}; mensajes por día activo 2.00

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 6, 'mes': 2}
  -- variante P  (principal: indicador_candidato): eventos por autor {'Ricardo': 12}
     Ricardo: por semana ISO {'S39': 4, 'S40': 3, 'S41': 3, 'S42': 2}
        semana: 12 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 12 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S1 (P + calidez_no_especifica): eventos por autor {'Ricardo': 12}
     Ricardo: por semana ISO {'S39': 4, 'S40': 3, 'S41': 3, 'S42': 2}
        semana: 12 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 12 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S2 (P sin candidatos ambiguo=si): eventos por autor {'Ricardo': 11}
     Ricardo: por semana ISO {'S39': 4, 'S40': 3, 'S41': 2, 'S42': 2}
        semana: 11 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 11 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=12; especificidad provisional (anotación cualitativa)={'media': 11, 'baja': 1}
  S1 (P + calidez_no_especifica): frecuencia=12; especificidad provisional (anotación cualitativa)={'media': 11, 'baja': 1}
  S2 (P sin candidatos ambiguo=si): frecuencia=11; especificidad provisional (anotación cualitativa)={'media': 11}
  categorías de respuesta (P): {'reconocimiento_sin_correspondencia_afectiva': 1, 'invitacion_pospuesta_o_no_comprometida': 4, 'reciprocidad_amistosa_ambigua': 3, 'respuesta_directa': 2, 'no_determinada': 2}
  secundarias (P): {'reconocimiento_sin_correspondencia_afectiva': 1}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO DE Ricardo (mínimo para comparar: 20 turnos)
  P  (principal: indicador_candidato) | hueco 2 h | candidatos sin intervención previa: 0
     candidatos   n=12 (insuficiente) general=20 dentro=20(n=9) entre=630(n=3)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 5 (insuficiente) general=20 dentro=15(n=4) entre=3518(n=1)
  P  (principal: indicador_candidato) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n=12 (insuficiente) general=20 dentro=20(n=9) entre=630(n=3)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 5 (insuficiente) general=20 dentro=15(n=4) entre=3518(n=1)
        latencias candidatos: [5, 10, 15, 15, 20, 20, 20, 30, 35, 570, 630, 660]
        latencias resto     : [4, 10, 20, 30, 3518]
  P  (principal: indicador_candidato) | hueco 12 h | candidatos sin intervención previa: 0
     candidatos   n=12 (insuficiente) general=20 dentro=20(n=12) entre=-(n=0)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 5 (insuficiente) general=20 dentro=15(n=4) entre=3518(n=1)
  S1 (P + calidez_no_especifica) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n=12 (insuficiente) general=20 dentro=20(n=9) entre=630(n=3)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 5 (insuficiente) general=20 dentro=15(n=4) entre=3518(n=1)
        latencias candidatos: [5, 10, 15, 15, 20, 20, 20, 30, 35, 570, 630, 660]
        latencias resto     : [4, 10, 20, 30, 3518]
  S2 (P sin candidatos ambiguo=si) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n=11 (insuficiente) general=20 dentro=20(n=9) entre=615(n=2)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 6 (insuficiente) general=25 dentro=15(n=4) entre=2074(n=2)
        latencias candidatos: [5, 10, 15, 15, 20, 20, 20, 30, 35, 570, 660]
        latencias resto     : [4, 10, 20, 30, 630, 3518]
```

Nota: el criterio de la propuesta (8 estímulos, 70 %, 2 periodos) se calcula con las categorías etiquetadas a mano; el usuario etiqueta este fixture a ciegas antes de ver estas etiquetas y se comparan.


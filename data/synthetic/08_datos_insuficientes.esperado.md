# Chat sintético 08: datos insuficientes

Archivos: `08_datos_insuficientes.txt` (formato Android, 24 h) y `08_datos_insuficientes.etiquetas.csv` (6 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que con **pocos eventos** el sistema no declara patrones: todo queda como `aislado` o `insuficiente`, y la recurrencia se marca `no evaluable` donde la ventana no alcanza. No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/08_datos_insuficientes.txt data/synthetic/08_datos_insuficientes.etiquetas.csv
```

## Comportamientos representados

- **Dos semanas y media (14 a 30 de septiembre), 22 mensajes.** Hugo tiene 3 eventos P en 3 días (17/09, 21/09, 28/09; semanas S38, S39 y S40) y Daniela uno ambiguo ("te extraño").
- Las 3 respuestas de Daniela a Hugo son pocas (menos de `min_stimuli` = 8): **no hay patrón de respuesta** aunque sean aplazamientos o cordialidad.
- La ventana tiene solo 1 mes calendario completo: las combinaciones mensuales de la rejilla son `no evaluable`.
- No hay límites, declaraciones ni conflictos.

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Eventos P | Hugo 3 (S38, S39, S40), Daniela 1 (ambiguo) |
| Patrón de expresión de Hugo | Cumple el mínimo base (3 días en ≥ 2 semanas) pero la rejilla semanal da **6 de 12 combinaciones cumplidas**: es **sensible a recurrencia** y no puede presentarse como patrón |
| Patrón de expresión de Daniela | **Insuficiente** (1 evento) |
| Patrón de respuesta | **Insuficiente**: menos de 8 estímulos |
| Rejilla mensual | `no evaluable` donde `min_periodos` supera los meses de la ventana |
| Resultado general | `no_concluyente` / `insuficiente`; ninguna etiqueta de relación |
| Límites | Ninguno |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Daniela | 1 | 0 | 0 | {'acusa_sin_devolver': 1} |
| Hugo | 3 | 0 | 0 | {'acusa_sin_devolver': 2, 'redirige_o_aplaza': 1} |

Categorías de respuesta etiquetadas: {'invitacion_pospuesta_o_no_comprometida': 1, 'reciprocidad_amistosa_ambigua': 1, 'respuesta_directa': 2}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Daniela': '11 (50.0 %)', 'Hugo': '11 (50.0 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Daniela': '46 (50.0 %)', 'Hugo': '46 (50.0 %)'}
  turnos con hueco 2 h: {'Daniela': '10 (50.0 %)', 'Hugo': '10 (50.0 %)'}
  turnos con hueco 6 h: {'Daniela': '10 (50.0 %)', 'Hugo': '10 (50.0 %)'}
  turnos con hueco 12 h: {'Daniela': '10 (50.0 %)', 'Hugo': '10 (50.0 %)'}
  días con mensajes (frecuencia observable): 9 de 17; por persona {'Daniela': 8, 'Hugo': 9}; mensajes por día activo 2.44

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 3, 'mes': 1}
  -- variante P  (principal: indicador_candidato): eventos por autor {'Hugo': 3, 'Daniela': 1}
     Daniela: por semana ISO {'S39': 1}
        semana: 1 eventos en 1 periodos -> cumple 0, no cumple 12, no evaluable 0 (de 12)
        mes: 1 eventos en 1 periodos -> cumple 0, no cumple 4, no evaluable 8 (de 12); no evaluable: min_periodos [2, 3] (la ventana solo tiene 1 mes)
     Hugo: por semana ISO {'S38': 1, 'S39': 1, 'S40': 1}
        semana: 3 eventos en 3 periodos -> cumple 6, no cumple 6, no evaluable 0 (de 12)
        mes: 3 eventos en 1 periodos -> cumple 2, no cumple 2, no evaluable 8 (de 12); no evaluable: min_periodos [2, 3] (la ventana solo tiene 1 mes)
  -- variante S1 (P + calidez_no_especifica): eventos por autor {'Hugo': 3, 'Daniela': 1}
     Daniela: por semana ISO {'S39': 1}
        semana: 1 eventos en 1 periodos -> cumple 0, no cumple 12, no evaluable 0 (de 12)
        mes: 1 eventos en 1 periodos -> cumple 0, no cumple 4, no evaluable 8 (de 12); no evaluable: min_periodos [2, 3] (la ventana solo tiene 1 mes)
     Hugo: por semana ISO {'S38': 1, 'S39': 1, 'S40': 1}
        semana: 3 eventos en 3 periodos -> cumple 6, no cumple 6, no evaluable 0 (de 12)
        mes: 3 eventos en 1 periodos -> cumple 2, no cumple 2, no evaluable 8 (de 12); no evaluable: min_periodos [2, 3] (la ventana solo tiene 1 mes)
  -- variante S2 (P sin candidatos ambiguo=si): eventos por autor {'Hugo': 3}
     Hugo: por semana ISO {'S38': 1, 'S39': 1, 'S40': 1}
        semana: 3 eventos en 3 periodos -> cumple 6, no cumple 6, no evaluable 0 (de 12)
        mes: 3 eventos en 1 periodos -> cumple 2, no cumple 2, no evaluable 8 (de 12); no evaluable: min_periodos [2, 3] (la ventana solo tiene 1 mes)

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=4; especificidad provisional (anotación cualitativa)={'media': 3, 'baja': 1}
  S1 (P + calidez_no_especifica): frecuencia=4; especificidad provisional (anotación cualitativa)={'media': 3, 'baja': 1}
  S2 (P sin candidatos ambiguo=si): frecuencia=3; especificidad provisional (anotación cualitativa)={'media': 3}
  categorías de respuesta (P): {'reciprocidad_amistosa_ambigua': 1, 'respuesta_directa': 2, 'invitacion_pospuesta_o_no_comprometida': 1}
  secundarias (P): {}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO DE Hugo (mínimo para comparar: 20 turnos)
  P  (principal: indicador_candidato) | hueco 2 h | candidatos sin intervención previa: 0
     candidatos   n= 3 (insuficiente) general=30 dentro=30(n=2) entre=600(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 4 (insuficiente) general=6.5 dentro=3(n=3) entre=3385(n=1)
  P  (principal: indicador_candidato) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 3 (insuficiente) general=30 dentro=30(n=2) entre=600(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 4 (insuficiente) general=6.5 dentro=3(n=3) entre=3385(n=1)
        latencias candidatos: [30, 30, 600]
        latencias resto     : [1, 3, 10, 3385]
  P  (principal: indicador_candidato) | hueco 12 h | candidatos sin intervención previa: 0
     candidatos   n= 3 (insuficiente) general=30 dentro=30(n=3) entre=-(n=0)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 4 (insuficiente) general=6.5 dentro=3(n=3) entre=3385(n=1)
  S1 (P + calidez_no_especifica) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 3 (insuficiente) general=30 dentro=30(n=2) entre=600(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 4 (insuficiente) general=6.5 dentro=3(n=3) entre=3385(n=1)
        latencias candidatos: [30, 30, 600]
        latencias resto     : [1, 3, 10, 3385]
  S2 (P sin candidatos ambiguo=si) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 3 (insuficiente) general=30 dentro=30(n=2) entre=600(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 4 (insuficiente) general=6.5 dentro=3(n=3) entre=3385(n=1)
        latencias candidatos: [30, 30, 600]
        latencias resto     : [1, 3, 10, 3385]
```


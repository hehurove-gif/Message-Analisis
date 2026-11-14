# Chat sintético 06: límite con alcance acotado

Archivos: `06_limite_con_alcance.txt` (formato Android, 24 h) y `06_limite_con_alcance.etiquetas.csv` (11 filas). Todo inventado; nombres, textos y fechas no corresponden a ninguna persona real.

**Para qué sirve.** Probar que un límite de **alcance acotado** (apodos y forma de tratamiento) se registra con su alcance y **no se extiende automáticamente** a otros aspectos: Lucía pide que no la llamen "linda" y después acepta otra invitación. No demuestra que el sistema identifique relaciones reales (definiciones §9.5).

**Cómo se generó y verificó.** Las etiquetas del CSV (clase de evento, categoría de respuesta, especificidad provisional) son **juicio mío sobre texto inventado**, escrito **antes** de las reglas de la Fase 6 (test-first, propuesta §G.3). Las latencias, el estado del turno y `dentro/entre` se calcularon a partir de las marcas de tiempo del `.txt` (latencia = desde el último mensaje del turno hasta la siguiente intervención del otro; `dentro` si ≤ 6 h). Los números de abajo los imprime `tools/referencia/ref_indicadores.py`, independiente del código del proyecto:

```bash
python3 -I tools/referencia/ref_indicadores.py data/synthetic/06_limite_con_alcance.txt data/synthetic/06_limite_con_alcance.etiquetas.csv
```

## Comportamientos representados

- **Semanas 1 y 2 (7 a 14 de septiembre):** colaboración académica y saludos convencionales.
- **Semana 3 y 4 (21 a 27 de septiembre):** Ernesto usa "linda" con ❤️ y un cumplido físico; Lucía responde con cordialidad. El 25/09 Lucía pone un **límite suave** ("jaja no me digas así") y el 27/09, tras otro "linda", un **límite explícito** ("prefiero que me llames Lucía"), ambos con alcance `apodos_y_forma_de_tratamiento`.
- **Después del límite:** Ernesto la llama por su nombre y no usa más apodos. El 02/10 la invita a un concierto a solas y **Lucía acepta**: el límite no cubría las invitaciones. El 12/10 otra invitación es **declinada con motivo** ("mañana no puedo"): solo esa invitación.
- Ninguna respuesta se interpreta como rechazo general ni como indiferencia.

## Perfil descriptivo esperado (Fase 6, propuesta §G.2)

| Dimensión | Esperado |
| --- | --- |
| Asimetría de expresión (P) | **Hacia Ernesto**: 7 eventos P frente a 0 |
| Patrón de expresión | **Solo Ernesto**: 7 días con evento en 4 semanas (S39 a S42); robusto en la rejilla semanal |
| Límites | **2**: 1 suave y 1 explícito, **ambos con alcance `apodos_y_forma_de_tratamiento`** |
| Alcance del límite | No se aplica a las invitaciones: 1 `invitacion_aceptada` posterior al límite y 1 `invitacion_declinada` (esa invitación concreta) |
| Familia `declina_o_delimita` | Aparece (2 límites + 1 invitación declinada), pero **sin extender** el alcance; el informe debe mostrar el alcance junto a cada límite |
| Declaraciones | 0 |
| Estado epistémico | Observaciones con cita; sin hipótesis sobre interés o ausencia de interés |

## Eventos etiquetados y respuestas por familia (de las etiquetas, no del código)

| Autor del indicador | Eventos P | Declaraciones | Calidez (S1) | Respuestas por familia (a sus P) |
| --- | --- | --- | --- | --- |
| Ernesto | 7 | 0 | 0 | {'acusa_sin_devolver': 3, 'declina_o_delimita': 3, 'devuelve_afecto': 1} |
| Lucía | 0 | 0 | 0 | {} |

Categorías de respuesta etiquetadas: {'invitacion_aceptada': 1, 'invitacion_declinada': 1, 'limite_interpersonal_explicito': 1, 'limite_interpersonal_suave': 1, 'reciprocidad_amistosa_ambigua': 1, 'reconocimiento_sin_correspondencia_afectiva': 2}

Familias según `config.yaml` (`romantic_interest.response.families`). Las categorías sin familia aparecen como `sin_familia` y se revisan.

## Salida de la referencia independiente

```text
PARAMETROS (segmentación): hueco de sesión en horas = [2, 6, 12] (inicial 6; la sesión se corta cuando el silencio SUPERA el hueco); ráfaga = intervalo <= 300 s; rejilla de ráfaga = [120, 300, 600] s; latencia sin ventana máxima; latencia dentro de sesión = latencia <= hueco
PARAMETROS (indicadores): periodo = semana ISO (lunes a domingo) o mes calendario; evento = una fila del CSV (un mensaje); rejilla de recurrencia: min_eventos [2, 3, 4, 5] x min_periodos [1, 2, 3]; una configuración es "no evaluable" si la ventana del chat tiene menos periodos que min_periodos; variantes: P  (principal: indicador_candidato); S1 (P + calidez_no_especifica); S2 (P sin candidatos ambiguo=si); columnas usadas: clase_evento, ambiguo, categoria_candidata, categoria_respuesta, categoria_secundaria; especificidad_provisional solo se cuenta, no pondera; mínimo de turnos para comparar latencias: 20

== BALANCE DE PARTICIPACIÓN (unidades por separado; sin etiqueta compuesta)
  mensajes: {'Ernesto': '19 (54.3 %)', 'Lucía': '16 (45.7 %)'}
  palabras (mensajes de texto; separadas por espacios): {'Ernesto': '88 (55.7 %)', 'Lucía': '70 (44.3 %)'}
  turnos con hueco 2 h: {'Ernesto': '18 (52.9 %)', 'Lucía': '16 (47.1 %)'}
  turnos con hueco 6 h: {'Ernesto': '18 (52.9 %)', 'Lucía': '16 (47.1 %)'}
  turnos con hueco 12 h: {'Ernesto': '18 (52.9 %)', 'Lucía': '16 (47.1 %)'}
  días con mensajes (frecuencia observable): 15 de 43; por persona {'Lucía': 14, 'Ernesto': 14}; mensajes por día activo 2.33

== SENSIBILIDAD DE LA RECURRENCIA (rejilla 4 x 3 por granularidad)
  periodos disponibles en la ventana del chat: {'semana': 7, 'mes': 2}
  -- variante P  (principal: indicador_candidato): eventos por autor {'Ernesto': 7}
     Ernesto: por semana ISO {'S39': 4, 'S40': 1, 'S41': 1, 'S42': 1}
        semana: 7 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 7 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S1 (P + calidez_no_especifica): eventos por autor {'Ernesto': 7}
     Ernesto: por semana ISO {'S39': 4, 'S40': 1, 'S41': 1, 'S42': 1}
        semana: 7 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 7 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)
  -- variante S2 (P sin candidatos ambiguo=si): eventos por autor {'Ernesto': 7}
     Ernesto: por semana ISO {'S39': 4, 'S40': 1, 'S41': 1, 'S42': 1}
        semana: 7 eventos en 4 periodos -> cumple 12, no cumple 0, no evaluable 0 (de 12)
        mes: 7 eventos en 2 periodos -> cumple 8, no cumple 0, no evaluable 4 (de 12); no evaluable: min_periodos [3] (la ventana solo tiene 2 meses)

== FRECUENCIA Y ESPECIFICIDAD PROVISIONAL (dimensiones separadas; sin índice ni ponderación)
  P  (principal: indicador_candidato): frecuencia=7; especificidad provisional (anotación cualitativa)={'media': 7}
  S1 (P + calidez_no_especifica): frecuencia=7; especificidad provisional (anotación cualitativa)={'media': 7}
  S2 (P sin candidatos ambiguo=si): frecuencia=7; especificidad provisional (anotación cualitativa)={'media': 7}
  categorías de respuesta (P): {'reciprocidad_amistosa_ambigua': 1, 'reconocimiento_sin_correspondencia_afectiva': 2, 'limite_interpersonal_suave': 1, 'limite_interpersonal_explicito': 1, 'invitacion_aceptada': 1, 'invitacion_declinada': 1}
  secundarias (P): {}

== LATENCIA DEL INTERLOCUTOR SEGÚN EL TIPO DE TURNO DE Ernesto (mínimo para comparar: 20 turnos)
  P  (principal: indicador_candidato) | hueco 2 h | candidatos sin intervención previa: 0
     candidatos   n= 7 (insuficiente) general=20 dentro=15(n=6) entre=570(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 7 (insuficiente) general=4 dentro=4(n=7) entre=-(n=0)
  P  (principal: indicador_candidato) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 7 (insuficiente) general=20 dentro=15(n=6) entre=570(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 7 (insuficiente) general=4 dentro=4(n=7) entre=-(n=0)
        latencias candidatos: [5, 10, 10, 20, 20, 30, 570]
        latencias resto     : [1, 3, 4, 4, 5, 15, 25]
  P  (principal: indicador_candidato) | hueco 12 h | candidatos sin intervención previa: 0
     candidatos   n= 7 (insuficiente) general=20 dentro=20(n=7) entre=-(n=0)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 7 (insuficiente) general=4 dentro=4(n=7) entre=-(n=0)
  S1 (P + calidez_no_especifica) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 7 (insuficiente) general=20 dentro=15(n=6) entre=570(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 7 (insuficiente) general=4 dentro=4(n=7) entre=-(n=0)
        latencias candidatos: [5, 10, 10, 20, 20, 30, 570]
        latencias resto     : [1, 3, 4, 4, 5, 15, 25]
  S2 (P sin candidatos ambiguo=si) | hueco 6 h | candidatos sin intervención previa: 0
     candidatos   n= 7 (insuficiente) general=20 dentro=15(n=6) entre=570(n=1)
     declaracion  n= 0 (insuficiente) general=- dentro=-(n=0) entre=-(n=0)
     resto        n= 7 (insuficiente) general=4 dentro=4(n=7) entre=-(n=0)
        latencias candidatos: [5, 10, 10, 20, 20, 30, 570]
        latencias resto     : [1, 3, 4, 4, 5, 15, 25]
```


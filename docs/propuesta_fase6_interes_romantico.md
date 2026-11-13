# Propuesta: interés romántico expresado y respuesta de la otra persona (Fase 6) — v0.1

> Estado: **BORRADOR para aprobación. No hay código ni cambios en `config.yaml`.** Todo lo que aparece como "valor" es una propuesta experimental.
> Complementa `definiciones_operativas.md` §4 (clases de evento), §5 (respuesta a un indicador), §8 (evidencia) y §9 (reglas generales), y se apoya en `propuesta_fase5_lexico.md` (conteo bruto). No redefine esas secciones salvo donde §0.3 y §I.3 lo indican.
> Todos los ejemplos son inventados. El repositorio puede ser público (ver §0.3): nada de chats reales ni de sus resultados entra en este documento.

## 0. Punto de partida

### 0.1 Estado verificado

HEAD `950af0d`; la suite completa pasa (**721 pruebas**, Python 3.13.18 en Linux sobre un clon del repo). El usuario debe repetir la comprobación en Windows (§I.2, paso 0).

### 0.2 Qué se reutiliza y qué falta

| Ya existe | Falta para la Fase 6 |
| --- | --- |
| Eventos léxicos con regla, forma (afirmativa / negada / pregunta) y `ambiguo` (Fase 5) | Asignar **clase de evento** (`indicador_candidato`, `calidez_no_especifica`, `declaracion_explicita`, …) |
| Clases, recurrencia, 12 categorías de respuesta y alcance de límites (definiciones §4–§5; `romantic_interest` en `config.yaml`) | Reglas observables para decidir cada categoría de respuesta |
| Turnos, sesiones, latencia, reanudaciones, correspondencia R1–R4, series por periodo con cambio sostenido | Unir un estímulo con la intervención siguiente y clasificarla |
| Rejilla de robustez (recurrencia × segmentación × indicadores), suficiencia, Wilson, muestreo y hoja de revisión (5.4) | Reutilizarlos para clases y respuestas |
| Chats sintéticos 01 y 02 con etiquetas escritas a mano (clase, categoría de respuesta, alcance del límite) | Fixtures nuevos y una comparación automática contra esas etiquetas |

### 0.3 Hallazgos de factibilidad (solo con datos sintéticos) y correcciones a documentos

**Cobertura del léxico actual.** Ejecuté las reglas de Fase 5, sin cambios, sobre el chat sintético 02. De los **11** estímulos etiquetados (10 candidatos y 1 declaración):

- 4 producen un evento equivalente (emoji afectivo en saludo ×2, cumplido, apodo ambiguo).
- 1 queda parcial: "buenas noches, linda ❤️" detecta el emoji pero no el apodo, porque los adjetivos solos se quitaron en v0.17.
- **6 no producen ningún evento**: las 3 propuestas de verse, la pregunta sobre la vida sentimental, la confidencia afectiva y la declaración.

Conclusión: la Fase 6 **no es solo clasificar eventos que ya existen**; necesita reglas nuevas (§A.2). El chat 02 es un conjunto de desarrollo escrito por el mismo autor que las reglas: sus señales son más nítidas que las de un chat real y no prueba nada sobre chats reales (definiciones §9.5).

**Ventana de respuesta.** En ese mismo chat, 4 de las 9 respuestas etiquetadas llegan más de 6 h después del estímulo (5 con 2 h; 1 con 12 h): contestar de mañana a un "buenas noches". Una ventana "misma sesión" las perdería (§D.1).

**Correcciones propuestas a documentos existentes** (se aplicarían en §I.3):

1. `definiciones_operativas.md`: el encabezado dice "Versión 0.6" y el registro llega a v0.22.
2. Unidad de recurrencia: definiciones §4 habla de **eventos (mensajes)** y `propuesta_fase5_lexico.md` §3 dice que los **días con evento** son la unidad. Hay que elegir una (decisión 3).
3. El Plan de desarrollo (Fase 6, punto 4) pide un "índice de asimetría"; definiciones §4/§9 y esta tarea prohíben índices compuestos. Se sustituye por descriptores separados (§E).
4. Visibilidad del repo: `propuesta_fase5_lexico.md` dice "El repo es público"; `00_LEEME` dice "privado". Hay que comprobarlo en GitHub (si es público, nunca debe haber datos reales; si es privado, corregir `propuesta_fase5`).
5. `romantic_interest.response_categories` tiene 12 valores; falta uno para "hubo intervención pero ningún criterio observable se cumple" (decisión 7).

### 0.4 Dependencia de Fase 5

Ninguna decisión de esta propuesta depende de `disculpa.ambigua`: `disculpa` no es indicador de interés y solo se usa, si acaso, como marcador secundario de respuesta (§D.3). Su cierre puede hacerse en paralelo.

## 1. Principios de diseño

1. **Se describe lo comunicado y cómo se respondió.** Nunca sentimientos, intención ni "interés de X".
2. **Cada decisión deja rastro**: evento → regla → `motivos` (contexto) → clase. Todo se puede reproducir abriendo una línea del `.txt`.
3. **Ante la duda, `no_determinada`**, visible en el informe. Sin criterio observable no hay etiqueta, y "ambigua" nunca se convierte en "rechazo" (definiciones §5).
4. **Los criterios se fijan antes de ver datos reales** (pre-registro): esta propuesta, los fixtures y las pruebas se congelan antes de ejecutar nada sobre los chats reales.
5. **Un indicador léxico no es interés romántico.** Exige recurrencia, línea base, contexto y respuesta (definiciones §4); y aun así describe expresiones, no a la persona.

## A. Indicadores de interés por persona

### A.1 De `pendiente_fase_6` a clase de evento

La asignación se guarda en un archivo nuevo, `lexicon/clases_fase6.yaml` (regla → clase, especificidad provisional, marca de ambigüedad). No se tocan las reglas `.v1` de Fase 5, para conservar la reproducibilidad de sus conteos. Las reglas del léxico local (`lexicon_local.yaml`) toman por defecto la clase que su categoría indique y se pueden sobrescribir en ese mismo archivo local.

| Regla (Fase 5) | Clase propuesta | Especificidad provisional | `ambiguo` | Por qué |
| --- | --- | --- | --- | --- |
| `afecto.te_quiero.v1` | `calidez_no_especifica` | baja | no | "Te quiero" es habitual entre amistades y familia |
| `afecto.mucho_carino.v1` | `calidez_no_especifica` | baja | no | Aprecio general |
| `afecto.te_amo.v1` | `indicador_candidato` | media | **sí** | Más específico, pero también se usa fuera de lo romántico |
| `afecto.te_extrano.v1` | `indicador_candidato` | baja | **sí** | Echar de menos cabe en muchos vínculos |
| `apodo.fuerte.v1` | `indicador_candidato` | media | no | Vocativo estricto ("mi amor", "mi vida"…) |
| `apodo.general.v1` | `calidez_no_especifica` | baja | sí | Uso general ("amor", "cielo", "princesa") |
| `cumplido.aspecto.v1` | `indicador_candidato` | media | no | Cumplido personal o físico (definiciones §4) |
| `cumplido.cualidad.v1` | `calidez_no_especifica` | baja | no | Elogio de cualidad; el de habilidad es `no_candidato` |
| `verse.plan.v1` | `indicador_candidato` | baja (alta con marcador "a solas") | no | Ver contexto B.2 |
| `verse.ambigua.v1` | `no_candidato` | — | — | Son despedidas ("nos vemos mañana") |
| `emoji.afectivo.v1` | `calidez_no_especifica`; **sube a `indicador_candidato` ambiguo** si va en un saludo o co-ocurre en el turno con apodo, afecto o cumplido | baja | sí al subir | "Saludos con elemento afectivo" (definiciones §4, `config`) |
| `emoji.risa`, `emoji.base`, `gratitud`, `risa.texto` | `linea_base` | — | — | Ya lo son |
| `emoji.tristeza*`, `emoji.enojo`, `emoji.otro` | `no_candidato` | — | — | No son indicadores |
| `emoji.posible_ironia` | `no_candidato` y **marca de contexto** (§B.2) | — | — | Sigue siendo solo "posibilidad" |
| `apoyo.*`, `conflicto.*`, `disculpa.*` | `no_candidato` como indicador | — | — | Pertenecen a otras dimensiones; se usan como marcadores de respuesta (§D) |
| Saludo convencional (`greetings`) | `linea_base` | — | — | Solo cuenta con un elemento afectivo añadido |

### A.2 Reglas nuevas necesarias (ids nuevos; no se modifican las `.v1`)

Se redactan **a partir de la definición**, no del texto de los fixtures (§G.3).

| Regla nueva | Categoría / clase | Qué recoge (ejemplos inventados) |
| --- | --- | --- |
| `declaracion.romantica.v1` | `declaracion_explicita` | "me gustas", "estoy enamorado de ti", "quieres ser mi novia", "siento algo por ti" |
| `vida_sentimental.v1` | `indicador_candidato` (media) | "¿tienes novio?", "¿andas saliendo con alguien?", "¿estás soltera?" |
| `verse.plan_ampliado.v1` | `indicador_candidato` | Construcciones que hoy no se detectan: "¿vamos tú y yo el sábado?", "podríamos salir a cenar", "déjame invitarte a…", "invitarte a…" |
| `apodo.adjetivo_vocativo.v1` | `calidez_no_especifica`, `ambiguo` | "linda", "hermosa", "guapo"… solo como vocativo tras saludo o despedida ("buenas noches, linda") |
| `contexto.a_solas.v1` / `contexto.grupal.v1` | marcadores, no eventos | "tú y yo", "nosotros dos", "solos" / "todos", "el grupo", "los demás" |

`confidencia afectiva` (etiqueta que existe en el fixture 02) **no se automatiza**: depende de la semántica ("me siento tranquilo contigo") y cualquier regla léxica sería ajustada al ejemplo. Queda para revisión manual y Fase 9.

Las reglas nuevas pasan por la misma validación 5.4 antes de entrar al informe.

### A.3 Variantes y qué cuenta

Se conservan las de definiciones §4 y `config.robustness.indicators`:

- **P (principal):** eventos de clase `indicador_candidato`, afirmativos, sin cita ni reportado.
- **S1:** P + `calidez_no_especifica`.
- **S2:** P sin eventos `ambiguo`.
- **Aparte, sin sumarse:** `declaracion_explicita` (se reporta como cita con línea), formas `negada` y `pregunta` de las categorías de afecto, y los descartes por contexto (§B).

Frecuencia y especificidad siguen siendo dimensiones separadas: la especificidad es una anotación (distribución por persona) que no pondera ni altera ningún conteo.

### A.4 Línea base individual (operativa)

`require_individual_baseline: true` se traduce, con las herramientas que ya existen, en cuatro lecturas lado a lado por persona (sin etiqueta compuesta):

1. Tasa de P por 100 mensajes de texto y **% de días activos con ≥1 evento P**.
2. Serie de P por periodo con **línea base propia** (mediana de los 4 primeros periodos) y cambio sostenido (Fase 4): "sin cambio respecto a su propia línea base" es una observación válida.
3. P frente a S1 de la misma persona (cuánto de su calidez es específica y cuánto general).
4. Dónde ocurren sus eventos: reanudación, saludo, franja horaria, comparados con la distribución de **todos** sus mensajes.

Límite: solo hay datos de este chat; no se sabe cómo habla esa persona con otras.

## B. Contexto del mensaje

### B.1 Unidades

Evento (mensaje) → **turno** (se evalúan co-ocurrencias) → sesión (reanudación, latencia). El contexto describe; **no crea ni borra** una expresión salvo en los dos casos marcados "excluye".

### B.2 Señales de contexto

| Señal | Cómo se detecta (regla transparente) | Efecto |
| --- | --- | --- |
| Forma negada / pregunta | Ya existe (Fase 5) | Fuera de P; se cuentan aparte |
| **Cita o discurso reportado** | Comillas alrededor de la coincidencia, o verbo de decir / de cita (`dijo`, `dice`, `me dijo`, `como dice`, `canción`, `letra`, `frase`) en las N palabras anteriores | **Excluye** de P; se cuenta como `descarte_contexto` |
| **Marca de broma o ironía** | El mismo mensaje contiene `risa_texto`, `emoji_risa` o `emoji_posible_ironia` | Sigue en P con `ambiguo` (S2 lo excluye). No se infiere sarcasmo |
| **Saludo** | El mensaje trae un saludo/despedida de `config.greetings` | Saludo solo = `linea_base`; saludo + apodo fuerte o emoji afectivo = candidato `ambiguo` (motivo `saludo_afectivo`) |
| **Co-ocurrencia en el turno** | ≥2 categorías de afecto/candidato en el mismo turno | Descriptivo: "turnos con ≥2 categorías". No pondera |
| **Iniciado / devuelto** | El turno va justo después de un turno de la otra persona con evento afectivo (misma sesión): `devuelto`; si no, `iniciado` | Descriptivo; separa expresar de corresponder (§E) |
| **Reanudación** | Primer turno de la sesión (definiciones §2) | Descriptivo; no es interés |
| **Franja horaria** | `habits.day_parts` | Descriptivo, frente a la distribución propia de esa persona |
| **A solas / grupal** | Marcadores explícitos (A.2). `a_solas_explicito` sube la especificidad provisional a alta; `grupal_explicito` degrada la propuesta a `no_candidato`; sin marcador, `no_determinado` (lo habitual) | Se reporta la distribución de los tres valores |
| **Tipo de mensaje** | Solo `texto` se analiza | Media y stickers son `intervencion_sin_texto` |

Cada evento guarda la lista `motivos` (`regla_ambigua`, `saludo_afectivo`, `marca_de_broma`, `cita_excluida`, …) para poder auditar por qué quedó en cada variante.

### B.3 Errores conocidos de Fase 5 y cómo se evitan

| Error conocido | Medida |
| --- | --- |
| Sustantivos tomados por apodos ("de mi vida", "el cariño") | Se conserva el vocativo estricto de v0.19 |
| Adjetivos sueltos ("bonita", "linda") | Solo con "mi" (apodo fuerte) o como vocativo tras saludo (regla ambigua nueva) |
| Acuerdos y despedidas como propuestas ("quedamos en que…", "nos vemos mañana") | `verse.ambigua` → `no_candidato`; las invitaciones salen de reglas explícitas |
| Patrones con negador propio ("ya **no** estás sola") frente a la ventana de negación | Los **marcadores de límite** son una lista positiva aparte; no se derivan de reglas negadas |
| Fórmulas de cortesía ("gracias, corazón") | No se pueden distinguir de un apodo real; lo resuelven recurrencia, línea base y el contexto del vínculo que aporte el usuario (Fase 8) |
| Preguntas retóricas ("¿perdón?") | Siguen como `forma: pregunta`; fuera de P |
| Citas y discurso reportado (no se detectaban) | Señal nueva (B.2) |
| Bromas | Señal nueva; no se descartan, se marcan |

### B.4 Lo que el contexto no puede ver

Quién es la otra persona, si una invitación es "a solas" sin marcador, tono, sarcasmo, conversaciones fuera del chat, reacciones y stickers (no salen en la exportación).

## C. Recurrencia y consistencia

- **Unidad:** **día lógico con ≥1 evento** de la variante (`habits.day_start_hour`), de modo que ráfagas, mensajes fragmentados o varios eventos el mismo día cuenten una vez (decisión 3).
- **Periodo:** semana ISO (`romantic_interest.period_unit`), con el mes como sensibilidad.
- **Niveles** (por persona, variante y categoría; son etiquetas descriptivas):

| Nivel | Condición | Se reporta como |
| --- | --- | --- |
| `aislado` | Menos de `min_events_for_pattern` días con evento, o menos de `min_distinct_periods` periodos | Observación: fecha y línea, sin conclusión |
| `recurrente` | ≥3 días con evento en ≥2 periodos (valores actuales, experimentales) | Observación con recurrencia descriptiva (necesaria, no suficiente) |
| `patron` | `recurrente` **y** robusto ante recurrencia en toda la parte evaluable de la rejilla (`min_events` 2–5 × `min_periods` 1–3 × semana/mes), **y** suficiencia de datos | Patrón (descriptivo: dice qué se repite, no por qué) |

- Las configuraciones que la ventana no permite probar se marcan `no_evaluable` y no cuentan como cumplidas (definiciones §8). Un hallazgo `sensible a recurrencia` no se presenta como patrón.
- Se reporta además la **persistencia** como conteo ("evento en 7 de 12 semanas"), sin umbral.
- La serie por periodo y los cambios sostenidos reutilizan `lexical_series` y `trends` (≥5 eventos por periodo, diferencia ≥25 %, líder dominante ≥75 %, repetido con la otra granularidad).
- **Comparación entre personas:** misma regla del 25 % y la etiqueta `sensible_a_granularidad`; sin umbrales nuevos.
- Tres eventos en dos semanas no validan nada sobre interés (definiciones §4): `patron` significa "se repite de forma estable", no "hay interés".

## D. Respuesta de la otra persona

### D.1 Estímulo, respuesta y ventana

- **Estímulo:** un turno de X con ≥1 evento de P o `declaracion_explicita` (sensibilidad: S1). Un turno es un solo estímulo aunque tenga varios eventos; se guardan sus categorías.
- **Respuesta:** el **turno completo** de Y que sigue (definiciones §3: "siguiente intervención del interlocutor"). No se asume que conteste el estímulo; se asume que es lo siguiente que Y escribe.
- **Ventana (recomendada):** sin límite máximo, coherente con §3. Cada respuesta se marca `dentro_de_sesion` o `entre_sesiones` (hueco 2/6/12 h) y se reporta con su **latencia**. Los patrones se prueban con todas las respuestas y solo con `dentro_de_sesion` (familia segmentación). Razón: con 6 h se perderían 4 de las 9 respuestas del fixture 02 (§0.3). Una respuesta tras un corte de sesión tiene **menos evidencia de vínculo con el estímulo** y se muestra aparte. Alternativa: solo misma sesión.
- **Estados sin respuesta evaluable** (subtipos de `sin_respuesta_semantica_observable`): `sin_respuesta_observada` (último turno del chat), `sin_intervencion_previa` (X vuelve a escribir en otra sesión sin que Y intervenga) e `intervencion_sin_texto` (Y responde con multimedia, sticker o mensaje eliminado). Ninguno es indiferencia ni rechazo.

### D.2 Latencia

La latencia de la respuesta es un dato propio (definiciones §5a): mediana dentro/entre sesiones, comparada **con la propia mediana de Y en turnos sin estímulo**, con los mismos mínimos de suficiencia (20 turnos). No genera etiquetas ni se usa para clasificar la respuesta.

### D.3 Categorías, criterios observables y qué se automatiza

La respuesta se clasifica con **marcadores léxicos** en el turno de Y, definidos en un archivo nuevo, `lexicon/respuestas_es_mx.yaml`. "Parcial" significa alta precisión y recall bajo: lo no detectado queda en `no_determinada`.

| Categoría | Criterio operativo (observable) | Se automatiza |
| --- | --- | --- |
| `correspondencia_afectiva` | El turno de Y contiene un evento afectivo propio (afecto explícito afirmativo, apodo fuerte, cumplido, emoji afectivo) **o** un eco explícito ("yo también te quiero/te extraño", "y yo a ti") cuando el estímulo era afecto explícito. **"igual/igualmente" no es eco**: es cortesía devuelta. Se anota `encuadre_amistad` si aparece "amiga/o" | Sí |
| `reconocimiento_sin_correspondencia_afectiva` | Acuse explícito (`gracias`, `qué lindo/amable`, `igualmente/igual`, `aww`) sin evento afectivo propio ni eco | Sí |
| `reciprocidad_amistosa_ambigua` | Devuelve confianza o cordialidad: "te tengo confianza", "cuenta conmigo", eventos de `apoyo`, sin afecto de P | Sí (lista corta) |
| `respuesta_directa` | Estímulo con pregunta **polar** y Y contesta con "sí/no/claro/ajá/pues sí/pues no" como cláusula propia en su primer mensaje | Parcial (solo polares) |
| `invitacion_aceptada` | Estímulo con propuesta de verse; marcador de aceptación (`sí`, `claro`, `va`, `sale`, `dale`, `me encantaría`, `con gusto`…) sin marcador de rechazo ni aplazamiento | Sí |
| `invitacion_declinada` | Marcador de rechazo de **esa** invitación (`no puedo`, `no podré`, `no gracias`, `estoy ocupada`) sin alternativa | Parcial |
| `invitacion_pospuesta_o_no_comprometida` | `veamos`, `a ver`, `ya veremos`, `no sé`, `tal vez`, `depende`, `luego te aviso`, `otro día`, `cuando pueda`. Un rechazo con "otro día" cae aquí (definiciones §5: la ambigüedad no es rechazo) | Sí |
| `cambio_de_tema` | Solo con marcador explícito (`por cierto`, `cambiando de tema`, `a todo esto`). "oye" solo no basta | Parcial; casi siempre **secundaria** |
| `respuesta_no_relacionada` | "La siguiente intervención no hace referencia al mensaje" | **No** (exige semántica): `no_determinada` con la nota `sustantiva_sin_marcadores`; solo etiquetas manuales y Fase 9 |
| `limite_interpersonal_suave` / `limite_interpersonal_explicito` | Ver D.5 | Sí (lista corta, recall bajo) |
| `sin_respuesta_semantica_observable` | Estados de D.1 | Sí |
| **`no_determinada` (nueva)** | Hay un turno de Y con texto y ningún criterio se cumple | Por definición |

Si en una invitación el turno de Y trae marcadores de grupos excluyentes (aceptación con rechazo o con aplazamiento), el resultado es `no_determinada` con la nota `marcadores_en_conflicto`.

### D.4 Precedencia y categoría secundaria

Principal: límite explícito → límite suave → invitación (si el estímulo era propuesta de verse) → correspondencia afectiva → reciprocidad amistosa ambigua → reconocimiento → respuesta directa → cambio de tema → `no_determinada`. **Secundaria (máximo una):** la siguiente de esa lista que también se cumpla. Mismo orden en todas las ejecuciones; el orden vive en `config.yaml`.

### D.5 Límites: suave frente a explícito, y alcance

- **Explícito:** enunciado que **delimita el vínculo** o rechaza expresamente lo expresado ("te veo como amiga/o", "solo amigos", "no siento lo mismo", "no me gustas", "no quiero nada contigo") o exige cesar el contacto (reutiliza `conflicto.ruptura`).
- **Suave:** pide cesar o cambiar **una conducta concreta** o expresa reserva sin delimitar el vínculo ("no me digas así", "prefiero que me hables como siempre", "me incomoda", "ahorita no").
- **Alcance** (se registra siempre y **no se extiende**): `relacion_romantica`, `apodos_o_trato`, `contacto`, `encuentros`, `no_determinado`.
- El sistema solo puede decir "no se detectó correspondencia romántica explícita con las reglas actuales"; **no** puede decir que la otra persona no tenga interés (definiciones §5).

### D.6 Familias de respuesta (solo para agregar; las 13 categorías siempre se muestran)

`devuelve_afecto` (correspondencia, invitación aceptada) · `acusa_sin_devolver` (reconocimiento, amistosa ambigua, directa) · `redirige_o_aplaza` (cambio de tema, no relacionada, pospuesta) · `declina_o_delimita` (declinada, límites) · `no_evaluable` (sin respuesta, `no_determinada`). Nombres neutros; no son una escala ni un índice.

### D.7 Patrón de respuesta

Hay `patron_de_respuesta` si, para un estímulo de un tipo y una dirección, hay ≥8 estímulos con respuesta evaluable en ≥2 periodos y una misma familia reúne ≥70 % de ellos. Valores experimentales con rejilla (6/8/10 estímulos × 60/70/80 %) y la sensibilidad de ventana (todas / solo dentro de sesión). Debajo de 8 estímulos: `insuficiente`. Alternativa: usar la cota inferior de Wilson ≥0,50 (decisión 10).

## E. Expresar, reconocer y corresponder

| Eje | Qué se observa | Unidad | Quién |
| --- | --- | --- | --- |
| **Expresar** | X emite P o declaración en un turno `iniciado` | Turno de X | X |
| **Reconocer** | La intervención siguiente de Y trae un acuse explícito del estímulo: categorías `reconocimiento…`, `correspondencia…`, `invitacion_*` y `limite_*` | Par estímulo→respuesta | Y |
| **Corresponder** | La intervención siguiente de Y devuelve afecto propio (`correspondencia_afectiva`). `invitacion_aceptada` se reporta aparte | Par | Y |

- "Reconocer" mide **acuse explícito en el texto**, no que Y haya notado o entendido la señal: "no se detectó acuse" no equivale a "no lo notó".
- **Expresar por iniciativa propia** (eventos de Y `iniciado`) se separa de **corresponder** (eventos de Y `devuelto`): quien nunca devuelve en el turno siguiente pero expresa por su cuenta es otra cosa.
- **Lectura en dos sentidos:** `A→B` (A expresa; B reconoce y corresponde) y `B→A` (al revés), cada uno con su n, su suficiencia y la tabla de categorías.
- **Asimetrías, como descriptores separados (sin índice):**
  - `asimetria_de_expresion`: quién tiene más días con P por 100 mensajes (regla del 25 %, `dominante` entre periodos, robustez a la granularidad).
  - `asimetria_de_correspondencia`: proporción de estímulos con `correspondencia_afectiva` en cada dirección, con las etiquetas de R1–R3 (`simetrica`, `asimetrica_hacia_X`, `insuficiente`, `sensible_a_umbrales`) y `reciprocity.max_symmetric_diff`.
  - Ambas se muestran lado a lado y **no se combinan**.

## F. Salidas y lenguaje

### F.1 Qué se reporta (por chat, local, sin texto de mensajes)

1. Por persona: clases de evento por regla (mensajes, turnos, días con evento y por 100 mensajes), variantes P/S1/S2, nivel (`aislado` / `recurrente` / `patron`) y persistencia.
2. Contexto: distribución iniciado/devuelto, reanudación, saludo, franja, a solas/grupal, descartes por contexto.
3. Por dirección: estímulos, estados sin respuesta, tabla de 13 categorías (principal y secundaria), familias y alcance de los límites.
4. Latencia de las respuestas con su comparación y suficiencia.
5. Evolución por periodo (expresión y correspondencia) con cambios sostenidos como **observación**.
6. Cada hallazgo con estado epistémico, suficiencia y robustez por familia (recurrencia, segmentación, indicadores y umbrales de respuesta).
7. Las líneas del `.txt` que respaldan cada hallazgo (no el texto). Las tarjetas con mensajes son Fase 7.

### F.2 Estado epistémico

La Fase 6 emite **observación** y **patrón**. No emite hipótesis automáticas: cada informe lleva un bloque fijo de "límites de la interpretación" (el chat es una muestra; no se ven reacciones, stickers ni la vida fuera del chat; las reglas detectan solo lo listado). Las hipótesis llegan con la Fase 7/8 y con el contexto del usuario (decisión 12).

### F.3 Plantillas (los ejemplos son inventados)

- ✔ "A envió al menos un apodo de la regla estricta en 14 de 63 días activos (22 %); B, en 2 de 71 (3 %)."
- ✔ "Ante los 18 turnos de A con indicadores y respuesta evaluable, B respondió con reconocimiento sin correspondencia afectiva en 7, con correspondencia afectiva en 5, con invitación pospuesta en 2 y sin criterio observable en 4. Suficiencia: suficiente."
- ✔ "No se detectó correspondencia afectiva explícita con las reglas actuales (precisión validada: …; la ausencia de detección no es ausencia de expresión)."
- ✘ Nunca: "A está enamorado/a", "le gusta", "lo/la rechaza", "ignora", "indiferente", "fría/o", "no le interesa", "interés romántico de A", ni un porcentaje presentado como probabilidad.

### F.4 Sin índices ni probabilidades

No hay puntuación, ponderación por especificidad, "nivel de interés" ni "probabilidad". Los intervalos de Wilson describen la precisión de las **reglas** en la revisión, no el interés de nadie.

## G. Validación

### G.1 Fixtures sintéticos nuevos (6)

Mismo formato que los existentes (`.txt`, `.etiquetas.csv`, `.esperado.md` con parámetros impresos):

| Fixture | Qué ejercita |
| --- | --- |
| `03_romantico_reciproco` | Ambos expresan P de forma recurrente y se corresponden; invitación aceptada |
| `04_amistad_calida` | Ambos usan "te quiero", apodos generales y "amigo/a" a diario: línea base alta y simétrica; sin patrón en P |
| `05_ambiguo` | A expresa P de forma recurrente; B responde con pospuesta, amistosa ambigua y `no_determinada`, sin límites: debe salir `no_concluyente`, nunca rechazo |
| `06_limite_con_alcance` | B pide no usar un apodo (alcance `apodos_o_trato`) y luego acepta otra invitación: el límite no se extiende |
| `07_falsos_positivos_contexto` | Citas, canciones, bromas, negadas, preguntas, grupo, despedidas, fórmulas de cortesía |
| `08_datos_insuficientes` | Pocos eventos: todo `aislado`/`insuficiente` |

Los chats 01 (amistad equilibrada) y 02 (unilateral con límite explícito) cubren los otros dos casos del Plan y son el **conjunto de desarrollo**.

### G.2 Criterio de salida

El Plan pide "distinguir unilateral, recíproco y amistad". Como el sistema **no emite esas etiquetas** (no hay clasificación hasta la Fase 8), el criterio se define sobre **perfiles descriptivos** y se prueba por fixture:

| Perfil | Asimetría de expresión | Patrón de expresión | Correspondencia en respuestas | Límites |
| --- | --- | --- | --- | --- |
| 02 unilateral | hacia A | solo A (P) | A→B: sin correspondencia | explícito (relación) |
| 03 recíproco | simétrica | A y B | en ambas direcciones | ninguno |
| 04 amistad | simétrica | ninguno en P; ambos en S1 | no evaluable o simétrica | ninguno |

Los tres perfiles deben ser distintos entre sí y coincidir con su `.esperado.md`. Además, 05 no debe producir ningún `limite_*` ni la familia `declina_o_delimita`, y 07 debe producir P=0 y los descartes esperados.

### G.3 Riesgo de circularidad y mitigación

Los fixtures los escribo yo y las reglas también: pueden coincidir por construcción. Mitigación:

1. **Test-first:** se confirman fixtures, etiquetas y `.esperado.md` (03–08) **antes** de escribir las reglas; 01 y 02 se usan para desarrollo y 03–08 como reserva.
2. Las reglas se redactan desde la definición (A.2, D.3), no desde el texto.
3. **Tú etiquetas a ciegas un fixture** (por ejemplo, 05) antes de ver mis etiquetas: es la única comprobación independiente antes de datos reales.
4. La comparación automática contra etiquetas se reporta como precisión/recall por categoría, **sin exigir coincidencia total** (que sería señal de sobreajuste).
5. Los fixtures prueban cálculos y definiciones; no demuestran nada sobre chats reales (definiciones §9.5).

### G.4 Revisión manual con datos reales

`revisar_eventos_local.py` ganaría dos modos, sin veredictos pre-llenados (tu revisión es la validación independiente):

- `--fase6 eventos`: muestra de eventos de clase P/declaración (n por la fórmula de 5.4, repartida por regla × persona). Veredicto c/i/a: "la expresión es de esa clase, dirigida a la otra persona, no es cita, broma evidente ni cortesía".
- `--fase6 respuestas`: muestra de pares estímulo→respuesta estratificada por categoría asignada (incluidas `no_determinada` y los estados sin respuesta). La hoja trae líneas, categoría automática, alcance, latencia y `dentro/entre`; tú pones c/i/a y, si i, la categoría correcta. Para `no_determinada` también se mide el recall: "escapó: categoría X".
- `--resumir` imprime precisión con Wilson por clase/categoría y una matriz de confusión **solo con códigos**; nunca texto.
- **Política de entrada al informe** (misma que 5.4): `valida` entra; `baja_precision` se reporta como `no_validada` y no cuenta para patrones; `no_validada` (<10 revisados) muestra solo el conteo bruto con esa etiqueta.

## H. Lo que la Fase 6 no hace

- Detección de ironía o sarcasmo (solo la marca de posible ironía como señal descriptiva).
- Modelos de PLN (`pysentimiento`, etc.), clasificación de intención o de "tono".
- Clasificación del vínculo (contexto, cercanía, naturaleza, componente instrumental): Fase 8.
- Cualquier afirmación sobre sentimientos, intenciones o conocimiento de la otra persona.
- Seguimiento de temas, reciprocidad semántica, confidencias, `respuesta_no_relacionada` automática.
- Reacciones y stickers (no están en la exportación), tarjetas con texto de mensajes (Fase 7), comparación entre chats, consulta en lenguaje natural.

## I. Decisiones y plan

### I.1 Decisiones que necesito de ti

| # | Decisión | Recomendación | Alternativas |
| --- | --- | --- | --- |
| 1 | Mapa regla → clase (A.1) y archivo `lexicon/clases_fase6.yaml` | Aprobar la tabla: `te_quiero`, aprecio y apodos generales a S1; `te_amo`, `te_extraño` y emoji en saludo a P ambiguo | `te_amo` como declaración; `te_quiero` a P |
| 2 | Reglas nuevas (A.2) con ids nuevos, sin tocar las `.v1` | Aprobar | Solo en `lexicon_local.yaml`; o modificar `.v1` |
| 3 | Unidad de recurrencia | Día lógico con evento | Mensaje (definiciones actuales) o turno |
| 4 | Umbral de patrón | 3 días en ≥2 semanas + robustez en toda la rejilla evaluable | 4 días en ≥3 semanas |
| 5 | Señales de contexto v0.1 (B.2), incluidos marcadores "a solas/grupal" | Todas | Sin "a solas" (sigue como dato abierto) |
| 6 | Ventana de respuesta | Siguiente intervención sin límite, con `dentro/entre sesiones` y sensibilidad 2/6/12 h | Solo misma sesión |
| 7 | Categoría `no_determinada` y subtipos de "sin respuesta" | Añadir | Dejar sin categoría |
| 8 | Qué respuestas se automatizan (D.3) | Las observables; `respuesta_no_relacionada` solo manual | Proxies léxicos para todo; o todo manual |
| 9 | Suave frente a explícito y alcance (D.5) | Aprobar | Dejar a revisión manual |
| 10 | Familias y umbral de patrón de respuesta (8 estímulos, 70 %, 2 periodos) | Aprobar | Criterio por cota de Wilson |
| 11 | Expresar/reconocer/corresponder y descriptores separados; se retira el "índice de asimetría" del Plan | Aprobar | Mantener un índice (contradice definiciones §4) |
| 12 | Fase 6 sin hipótesis automáticas, con bloque fijo de límites | Aprobar | Plantillas de hipótesis con alternativas |
| 13 | Validación: fixtures 03–08 antes de las reglas, criterio por perfiles y tú etiquetas uno a ciegas | Aprobar | Etiquetas solo mías |
| 14 | Higiene documental (§0.3): encabezado de definiciones y visibilidad del repo | Corregir | Dejar |

### I.2 Plan de implementación (un commit por archivo nuevo o al tocar más de 3)

| Paso | Contenido | Archivos | Verificación |
| --- | --- | --- | --- |
| 0 | Confirmar estado en Windows y subir esta propuesta | 1 nuevo | `git log`, `pytest` ≥721 |
| 1 | `definiciones_operativas.md` v0.23 y claves nuevas en `config.yaml` (§I.3) | 2 | pruebas |
| 2 | `lexicon/clases_fase6.yaml` y su prueba de completitud | 2 nuevos (commits separados) | cada regla tiene clase |
| 3 | Fixtures 03–08 con etiquetas y `.esperado.md` | 3 por fixture (un commit por fixture) | `tools/referencia` los recalcula |
| 4 | Reglas nuevas (`es_mx.yaml`, `nlp/lexicon.py`) y pruebas | 3 | pruebas de cada regla (≥6 positivas y 6 negativas) |
| 5 | `lexicon/respuestas_es_mx.yaml` | 1 nuevo | pruebas |
| 6 | `metrics/romantic_context.py` y pruebas | 2 nuevos | fixture 07 |
| 7 | `metrics/romantic_indicators.py` (clases, recurrencia, niveles, rejilla) y pruebas | 2 nuevos | fixtures 02, 04, 08 |
| 8 | `metrics/romantic_response.py` (estímulo, ventana, categorías, descriptores) y pruebas | 2 nuevos | fixtures 02, 03, 05, 06 |
| 9 | Comparación automática con etiquetas y `tools/referencia/ref_fase6.py` independiente | 2 nuevos | perfiles de G.2 |
| 10 | `revisar_eventos_local.py`: modos `--fase6` y `--resumir` | 1 (+ pruebas) | pruebas de privacidad: sin texto |
| 11 | Integración en `informe_local.py` / `informe_visual_local.py` | 3 | informe `--anonimo` en sintéticos |
| 12 | Tú ejecutas en local con datos reales y revisas | — | tus comandos, tus resultados |
| 13 | `docs/reporte_pruebas_fase_6.md` (sin cifras reales), cierre en definiciones v0.24 y `00_LEEME` | 3 | revisión final |

Estimación realista: 2 semanas (el Plan decía 1–1,5; el trabajo adicional son los 6 fixtures, las reglas nuevas y la ampliación de la revisión manual). Después de cada paso: `python -m pytest -q` y se reporta el número de pruebas.

### I.3 Cambios previstos (borrador; **no aplicados**)

`config.yaml`, dentro de `romantic_interest:` (las claves existentes se conservan):

```yaml
  recurrence:                      # NUEVO · experimental
    unit: logical_day              # día lógico con >=1 evento (habits.day_start_hour)
    # min_events_for_pattern (3) y min_distinct_periods (2) se reutilizan
  context:                         # NUEVO · experimental
    reported_speech_window_tokens: 4
    joke_markers_categories: [risa_texto, emoji_risa, emoji_posible_ironia]
    # las listas de marcadores viven en lexicon/ (cita, a solas, grupal)
  response:                        # NUEVO · experimental
    window: next_intervention      # sin límite máximo (definiciones §3)
    mark_between_sessions: true
    default_category: no_determinada
    no_semantic_subtypes: [sin_respuesta_observada, sin_intervencion_previa, intervencion_sin_texto]
    precedence: [limite_interpersonal_explicito, limite_interpersonal_suave, invitacion, correspondencia_afectiva,
                 reciprocidad_amistosa_ambigua, reconocimiento_sin_correspondencia_afectiva, respuesta_directa, cambio_de_tema]
    families: {devuelve_afecto: [correspondencia_afectiva, invitacion_aceptada],
               acusa_sin_devolver: [reconocimiento_sin_correspondencia_afectiva, reciprocidad_amistosa_ambigua, respuesta_directa],
               redirige_o_aplaza: [cambio_de_tema, respuesta_no_relacionada, invitacion_pospuesta_o_no_comprometida],
               declina_o_delimita: [invitacion_declinada, limite_interpersonal_suave, limite_interpersonal_explicito],
               no_evaluable: [sin_respuesta_semantica_observable, no_determinada]}
  response_pattern:                # NUEVO · experimental
    min_stimuli: 8
    min_share: 0.70
    min_distinct_periods: 2
    sensitivity: {min_stimuli: [6, 8, 10], min_share: [0.60, 0.70, 0.80]}
```

Se añade `no_determinada` a `response_categories`, y `lexicon.validation` se reutiliza sin cambios.

`definiciones_operativas.md` v0.23: encabezado corregido; §4 con la unidad de recurrencia, las clases asignadas por `clases_fase6.yaml` y las variantes; §5 con la ventana, `no_determinada`, los subtipos, la precedencia, suave/explícito y el alcance; §8 con la robustez del umbral de respuesta; §10 con lo que sigue abierto (equivalencia del afecto devuelto, `confidencia`, "a solas" sin marcador).

# Propuesta: capa léxica y afectiva basada en reglas (Fase 5) — v0.1, BORRADOR PARA APROBACIÓN

> Estado: **sin implementar**. Nada de esto entra en `definiciones_operativas.md` ni en el código hasta que el usuario lo apruebe (checklist en §10).
> Complementa `definiciones_operativas.md` §4 (eventos léxicos y clases de evento), §8 (evaluación de la evidencia) y §9 (reglas generales). No redefine esas secciones: las usa.
> Todos los ejemplos son inventados. El repo es público: no se versionan apodos, frases ni mensajes reales (ver §7).

## 1. Qué es y qué no es la Fase 5

Detectar, con reglas transparentes y editables, **expresiones** en el texto de cada mensaje (afecto, apodos, cumplidos, propuestas de verse, apoyo, conflicto, disculpa, emojis) y guardar cada coincidencia como un **evento con evidencia**. Medirlos por persona y por periodo, en proporción al volumen de cada una.

- Un evento es un **dato sobre el texto**, no sobre la persona ni sobre la relación (definiciones §4).
- **No** decide si algo es interés romántico. Eso exige recurrencia, línea base, contexto y respuesta del otro (Fase 6). La Fase 5 solo entrega materia prima verificable.
- **No** usa modelos. Los modelos (Fase 9) se comparan después contra estas reglas y contra la validación manual.
- Una regla que no supera la validación (§8) no entra al reporte.

## 2. Categorías léxicas (qué se busca)

Cada regla pertenece a **una** categoría. Las categorías son independientes y no se suman.

| Código | Qué recoge | Ejemplos inventados (sí) | Ejemplos inventados (no) |
|---|---|---|---|
| `afecto_explicito` | Expresión directa de cariño o de echar de menos | "te quiero mucho", "te extraño", "te adoro", "tqm" | "te quiero decir algo", "no te quiero molestar" |
| `apodo_carinoso` | Apelativo afectivo dirigido al otro | "hola mi vida", "gracias, corazón", "descansa, amor" | "el amor propio es importante", "mi amor por el café" |
| `cumplido` | Elogio a la persona (aspecto o cualidades) | "te ves hermosa hoy", "eres muy lista", "qué guapo saliste en la foto" | "qué bonito está el parque" |
| `propuesta_de_verse` | Invitación o plan para coincidir en persona | "¿nos vemos mañana?", "¿quieres ir al cine?", "salimos el viernes" | "nos vemos" como despedida simple; "ya salí del trabajo" |
| `apoyo` | Ofrecimiento de ayuda o consuelo | "ánimo", "aquí estoy para lo que necesites", "cuenta conmigo" | "ánimo" dentro de una burla evidente (no detectable: límite) |
| `conflicto` | Reclamo, enojo expreso, ruptura de contacto, insulto | "me molesta que no avises", "ya basta", "no me hables", "eres un idiota" | "me molesta el ruido de la calle" (queja no dirigida; ver §4.4) |
| `disculpa` | Reconocimiento de falta o petición de perdón | "perdón por lo de ayer", "fue mi culpa", "disculpa que te grité" | "¿perdón?" como "¿cómo?"; "disculpa, ¿a qué hora es?" |
| `emoji_*` | Emojis por clase: `afectivo`, `risa`, `tristeza`, `enojo`, `marca_de_posible_ironia`, `base` | ❤️ 😘 🥰 · 😂 🤣 · 😢 · 😡 · 🙄 🙃 · 😊 👍 | — |

Notas por categoría:

- **`afecto_explicito`**: en español de México "te quiero" es habitual entre amistades y familia. La categoría **no** significa interés romántico. La regla excluye "te quiero + verbo en infinitivo" (decir, preguntar, pedir, invitar…): la heurística es que la palabra siguiente termine en *-ar/-er/-ir* y no sea una de las de intensidad (*mucho, tanto, demasiado, así, de verdad*).
- **`apodo_carinoso`**: solo cuenta como **vocativo**: pegado a un signo de puntuación o a un inicio/fin de mensaje, o precedido de "mi". Los apodos específicos de cada pareja de chat viven en el archivo local (§7), no en el repo.
- **`cumplido`**: en Fase 5 se distingue solo `cumplido_aspecto` / `cumplido_cualidad` como subetiqueta informativa. No se decide si es amistoso o romántico.
- **`propuesta_de_verse`**: la Fase 5 **no puede saber si es "a solas"**. Solo marca marcadores explícitos (`tu_y_yo`, `los_dos`, `solos`) como subetiqueta. Que sea a solas o en grupo se queda como dato abierto (definiciones §10).
- **`conflicto`**: el insulto y el reclamo se separan en subetiquetas (`insulto`, `reclamo`, `ruptura_de_contacto`). Sin lista exhaustiva de groserías: una lista corta y editable; lo coloquial entre amistades ("cabrón" en broma) produce falsos positivos **conocidos** y se cuenta como ambiguo (§4.5).
- **`disculpa`**: "lo siento" puede ser disculpa **o** condolencia. Se registra como `disculpa` con `ambiguo: true` y su compañero natural ("lo siento mucho" tras una mala noticia) queda como falso positivo conocido.
- **Emojis**: 😭 se usa también para risa ("me muero 😭") y 🥺 para ternura o súplica: ambos `ambiguo: true`. 🙄 🙃 son **marcas de posible ironía**, no detección de sarcasmo.

## 3. Registro de un evento (evidencia)

Un evento guarda, solo en memoria durante el análisis:

| Campo | Contenido |
|---|---|
| `seq`, `linea` | Posición del mensaje en el archivo (para localizarlo a mano) |
| `timestamp`, `participante` | A o B |
| `categoria`, `subetiqueta` | Una categoría (§2); subetiqueta opcional |
| `regla` | Identificador estable de la regla (`afecto.te_quiero.v1`) |
| `forma` | `afirmativa`, `negada` o `pregunta` (ver §4.3) |
| `ambiguo` | Verdadero si la regla está marcada como discutible (§4.5) |
| `clase_provisional` | `linea_base` (saludos, emojis base) o `pendiente_fase_6` para todo lo demás. **La Fase 5 no asigna `indicador_candidato`, `declaracion_explicita` ni `calidez_no_especifica`**: esas clases dependen de contexto y de respuesta |
| `texto` | El texto del mensaje. **No sale a la consola ni a disco**: las herramientas imprimen línea, categoría y regla (§8) |

Reglas de conteo (**propuesta de aclaración a definiciones §4**, que fija "un evento por mensaje"):

1. Un mensaje puede producir **un evento por categoría** (un mensaje con "te quiero" y "perdón" aporta a `afecto_explicito` y a `disculpa`), pero **no más de uno por categoría**, aunque contenga varias coincidencias.
2. Como los mensajes de una persona se fragmentan, la medida principal por persona no es el conteo de mensajes sino la **tasa**: eventos por 100 turnos de esa persona, y **días con al menos un evento** (unidad para la recurrencia). El conteo de mensajes se reporta como dato secundario.
3. Los eventos `negada` y los de `forma: pregunta` se reportan aparte y **no** entran al conteo principal.

## 4. Reglas de coincidencia

### 4.1 Normalización (solo para comparar; el texto original no se altera)
- minúsculas y sin acentos; espacios y signos colapsados;
- letras repetidas colapsadas (`te quieroooo` → `te quiero`; `holaaa`);
- abreviaturas y grafías habituales como variantes de la **misma** regla: `tq`, `tqm`, `tkm`, `te kiero`, `te amoo`;
- los emojis se comparan sobre el texto original (con y sin selector de variación).

### 4.2 Límites de palabra
La coincidencia es de **palabra(s) completa(s)**, nunca subcadena (lección del error de saludos v0.11: "descansa" ≠ "descansar").

### 4.3 Negación y pregunta
- **Negada**: un negador (`no`, `nunca`, `jamás`, `ni`, `tampoco`) en las 3 palabras anteriores a la coincidencia → `forma: negada`. Ej.: "no te quiero ver" → `negada`.
- **Pregunta**: el mensaje contiene `?` y la coincidencia está en la oración interrogativa → `forma: pregunta`. Ej.: "¿me quieres?", "¿perdón?".
- Citas y discurso reportado ("me dijo 'te quiero'") **no se detectan**: límite conocido.

### 4.4 Dirigido al otro
Se prefiere la coincidencia con segunda persona o vocativo. Las quejas no dirigidas ("me molesta el ruido") no cuentan como `conflicto` salvo que haya segunda persona o un verbo de reclamo hacia el otro ("me molesta que *no avises*" cuenta; "me molesta *el calor*" no).

### 4.5 Ambiguas
Reglas con alta tasa conocida de falsos positivos (`lo siento`, 😭, 🥺, 😏, apodos de uso muy general como "amor" suelto) llevan `ambiguo: true`. Se **cuentan en la variante amplia y se excluyen en la estricta** (§6).

### 4.6 Lo que no se intenta
Sarcasmo, ironía contextual, mensajes en otro idioma, jergas locales no listadas, texto dentro de imágenes y stickers. Los emojis 🙄 🙃 solo marcan **posibilidad** de ironía.

## 5. Qué se mide (por persona y por periodo)

Para cada categoría, A y B por separado y, después, su comparación:

- eventos (mensajes), **turnos con evento**, **días con evento**;
- **tasa por 100 turnos** de esa persona (cada quien frente a su propio volumen);
- reparto A/B de los **días con evento** (comparación principal);
- serie por mes/semana con el mismo detector de cambios sostenidos de la Fase 4 (sobre días con evento y tasa), con sus etiquetas de pausa y de granularidad;
- suficiencia de datos: `min_events_for_pattern` y `min_distinct_periods` (definiciones §4, config actual); por debajo → `insuficiente` o `no_concluyente`, nunca cero engañoso.

**No hay índice compuesto** ("nivel de afecto" o "calidez total"). **Comparar A con B no es interpretar**: que A use más apodos no dice nada de interés; la línea base individual es la unidad de lectura (definiciones §9.3).

## 6. Sensibilidad

Familia **Indicadores** (definiciones §8), aplicada a la Fase 5:

| Variante | Qué incluye |
|---|---|
| Estricta | solo reglas no ambiguas y solo `forma: afirmativa` |
| Amplia | estricta + reglas ambiguas |

Cada hallazgo declara si la **dirección** (quién tiene más) se mantiene en ambas variantes: `robusto ante indicadores` o `sensible a indicadores` (este último no se reporta como patrón). Las variantes S1/S2 de §4 se reservan para la Fase 6.

## 7. Diccionarios: formato y privacidad

- `lexicon/es_mx.yaml` (en el repo, **genérico**): reglas con `id`, `categoria`, `patrones`, `excepciones`, `ambiguo`, `nota`. Español con variantes mexicanas. Editable.
- `lexicon_local.yaml` (**fuera del repo / ignorado por git**): apodos y frases propias de un chat concreto. Nunca se versiona ni se imprime su contenido.
- Cada regla lleva versión (`.v1`): cambiar una regla genera una versión nueva para que los resultados sean reproducibles.
- Parámetros en `config.yaml` (`lexicon:`), nada fijo en el código.
- Un evento imprime línea, categoría y regla; el texto solo lo ve el usuario al abrir su propio archivo.

## 8. Validación (criterio de salida de la Fase 5)

1. **Pruebas sintéticas**: ≥ 6 ejemplos positivos y ≥ 6 negativos por categoría, incluidos los casos de §2 (infinitivo, vocativo, negación, pregunta, "¿perdón?", "lo siento" ambiguo, 😭 como risa).
2. **Precisión en datos reales** (solo la hace el usuario): `tools/revisar_eventos_local.py` elegirá hasta **100 eventos por categoría**, repartidos entre reglas y entre A y B, e imprimirá línea, categoría y regla. El usuario abre cada línea y marca `correcto` / `incorrecto` / `ambiguo`; se reportan solo los conteos por regla.
3. **Recuperación aproximada**: la herramienta también elige **200 mensajes sin evento**; el usuario cuenta cuántos contenían una expresión de alguna categoría. Solo da una cota inferior de lo que se escapa.
4. **Umbrales propuestos (experimentales)**: una categoría entra al reporte con precisión ≥ **0,80**; una regla con ≥ 10 revisados y precisión < **0,60** se elimina o pasa a ambigua; categorías entre 0,60 y 0,80 se reportan marcadas `baja_precision`. Con menos de 30 revisados la categoría queda `no_validada`.
5. Resultado en un reporte `reporte_pruebas_fase_5.md` con conteos, sin texto real y **sin cifras relacionales reales** (repo público).

## 9. Plan de entrega (un commit por parte)

| Parte | Contenido |
|---|---|
| 5.1 | Esquema de evento, normalización, límites de palabra, negación/pregunta, `lexicon/es_mx.yaml` con `afecto_explicito` y emojis, pruebas sintéticas |
| 5.2 | Categorías restantes (apodos, cumplidos, propuestas de verse, apoyo, conflicto, disculpa) y sus pruebas |
| 5.3 | Métricas por persona y periodo (tasa, turnos y días con evento), sensibilidad estricta/amplia, integración con `metricas_local` y `comparar_local` |
| 5.4 | `revisar_eventos_local.py`, protocolo de validación y reporte |

## 10. Decisiones que necesito de ti

1. ¿Aceptas la **aclaración de conteo** de §3: un evento por categoría y mensaje (no por mensaje), con tasa por 100 turnos y días con evento como medidas principales?
2. ¿Aceptas que la Fase 5 **no asigne** las clases `indicador_candidato`, `declaracion_explicita` ni `calidez_no_especifica` y las deje para la Fase 6 (`pendiente_fase_6`)?
3. ¿Aceptas el archivo **local** de apodos fuera del repo (§7)?
4. ¿Aceptas los umbrales de validación de §8 (0,80 / 0,60 / 30 revisados) como valores experimentales?
5. ¿Alguna categoría que quieras añadir, quitar o priorizar (por ejemplo, empezar por `apodo_carinoso` y `propuesta_de_verse` por la Fase 6)?

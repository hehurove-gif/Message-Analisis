# Propuesta: definición operativa de reciprocidad (v0.1, APROBADA E IMPLEMENTADA 2026-11-07)

> Estado: **implementada** en `metrics/correspondence.py` (`reciprocity.defined: true`). Decisiones: 4 dimensiones; pares solo en la misma sesión; 30 pares / 10 estímulos / 0.10 (ρ 0.15); Spearman en R1; nombre en reportes: **correspondencia**.
> Complementa `definiciones_operativas.md` §6 (Balance de participación y reciprocidad).

## 1. Problema

Hoy "reciprocidad" significa "correspondencia en la interacción (respuestas, seguimiento de temas, preguntas,
iniciativas y apoyo)", pero no tiene ninguna medida. Las métricas existentes no la cubren:

- Turnos: se alternan por definición y quedan cerca de 50/50 siempre.
- Participación (mensajes, palabras): mide **cuánto** escribe cada uno, no **si uno corresponde a lo que hace el otro**.
- Contenido de turnos: mide la extensión de los turnos de cada uno, pero no la relación entre un turno y el turno del otro que le sigue.

La reciprocidad es **relacional**: compara lo que hace X con lo que hace Y **a continuación**, en ambas direcciones (A→B y B→A).

## 2. Definición propuesta

**Reciprocidad observable**: grado en que la siguiente intervención de cada participante corresponde, en forma
medible, a la intervención anterior del otro. Se mide en **cuatro dimensiones separadas**, cada una en las dos
direcciones, **sin índice compuesto**.

Unidad base: **par de turnos** = turno de X (estímulo) seguido del siguiente turno de Y (respuesta) dentro de la
**misma sesión** (latencia ≤ hueco de sesión). Los pares entre sesiones se excluyen: retomar horas después no es responder.
Solo se usan pares en estado `con_intervencion` (no fuera de orden).

### R1. Correspondencia de extensión
¿La extensión de la respuesta sigue a la extensión del estímulo?

- Medida: correlación de Spearman entre las palabras sustantivas del turno de X y las del turno de Y que le sigue (ρ, de −1 a 1).
- Se reporta además la mediana de palabras de Y según el estímulo: tras un turno mínimo, uno breve y uno desarrollado de X.
- Lectura: ρ alto = las respuestas largas siguen a los mensajes largos. ρ ≈ 0 = la extensión de Y no depende de la de X.
- Dirección A→B: estímulo de A, respuesta de B (y al revés).

### R2. Respuesta a preguntas
¿Las preguntas reciben una intervención con contenido?

- Estímulo: un turno de X que contiene al menos una pregunta (definiciones §4).
- Medida: proporción de esos turnos cuyo siguiente turno de Y (en la misma sesión) **no es mínimo**.
- Comparación: la misma proporción tras turnos de X **sin** pregunta (línea base de Y). Se reporta la diferencia.
- Límite explícito: no verifica que Y **conteste** la pregunta (eso es respuesta semántica, Fase 6).

### R3. Correspondencia ante turnos desarrollados
¿Un turno elaborado recibe algo más que un acuse?

- Estímulo: un turno desarrollado de X (≥ `turn_content.developed_min_words`).
- Medida: distribución del siguiente turno de Y en mínimo / breve / desarrollado, comparada con la de Y tras turnos breves de X (línea base).
- Se recalcula con los umbrales 10 / 15 / 25 (sensibilidad, igual que el contenido de turnos).

### R4. Correspondencia de iniciativa
¿La iniciativa de retomar está repartida?

- Usa métricas ya existentes, sin redefinirlas: reanudaciones de sesión (hueco 2/6/12 h) e inicio del día lógico.
- Medida: proporción de cada uno y su margen |A−B|/(A+B), con las etiquetas de robustez actuales.
- No es relacional par a par: describe el reparto a lo largo de todo el chat.

## 3. Asimetría por dimensión

En R1–R3, cada dimensión se reporta en ambas direcciones y con su **diferencia** (A→B menos B→A):

| Etiqueta | Regla (umbrales experimentales en config) |
|---|---|
| `simetrica` | las dos direcciones difieren menos que `reciprocity.max_symmetric_diff` (propuesto: 0.10 en proporciones; 0.15 en ρ) |
| `asimetrica_hacia_A` / `asimetrica_hacia_B` | una dirección supera a la otra por al menos ese umbral; "hacia A" = A recibe más correspondencia de la que da |
| `insuficiente` | menos de `reciprocity.min_pairs` pares (propuesto: 30) o menos de 10 estímulos en R2/R3 |

La dirección se prueba con la sensibilidad de hueco (2/6/12 h) y de umbral (10/15/25). Si cambia de dirección, la
etiqueta es `sensible_a_umbrales` y no se reporta como patrón.

## 4. Qué NO es (reglas)

1. No es interés, afecto, cercanía ni calidad de la relación. Es correspondencia **formal** observable.
2. No hay índice global de reciprocidad: las 4 dimensiones pueden contradecirse y se reportan por separado.
3. No incluye seguimiento de temas ni apoyo: requieren análisis semántico (Fase 6) y quedan fuera de v0.1.
4. Hábitos individuales primero (§9.3): quien siempre escribe corto tendrá respuestas cortas a todo. Por eso R2 y R3 comparan contra la **línea base de esa persona**, no contra la otra.
5. Un chat exportado es una muestra parcial: la reciprocidad describe ese historial, no la relación completa.

## 5. Salida propuesta (por chat)

```
reciprocidad:
  pares_misma_sesion: n
  R1_extension:    {A_a_B: {rho, n, mediana_tras_minimo/breve/desarrollado}, B_a_A: {...}, etiqueta}
  R2_preguntas:    {A_a_B: {con_pregunta, sin_pregunta, diferencia, n}, B_a_A: {...}, etiqueta}
  R3_desarrollados:{A_a_B: {tras_desarrollado: {minimo, breve, desarrollado}, tras_breve: {...}, n}, ..., etiqueta, sensibilidad}
  R4_iniciativa:   {reanudaciones, inicia_dia, margenes, robustez}
  nota: "correspondencia formal observable; no mide interés ni afecto"
```

En `--resumen`: una línea por dimensión con las dos direcciones y la etiqueta. En `comparar_local`: una columna por dimensión con la etiqueta.

## 6. Decisiones que necesito de ti

1. **¿Apruebas las 4 dimensiones** o quitas o agregas alguna?
2. **Pares solo dentro de la misma sesión** (propuesta) o también entre sesiones.
3. **Umbrales**: 30 pares mínimos y diferencia de 0.10 (ρ: 0.15) para llamarla asimétrica.
4. **Spearman en R1** (robusto a valores extremos y sin dependencias externas) o una medida más simple: la proporción de respuestas "de tamaño similar" (±50% de palabras).
5. ¿Se llama **reciprocidad** en los reportes, o prefieres **correspondencia** para no sugerir más de lo que mide?

Al aprobarla: `reciprocity.defined: true`, se agregan los umbrales a config y se crean `metrics/reciprocity.py`,
las pruebas con fixtures sintéticos (una conversación con correspondencia simétrica, otra asimétrica y otra con
datos insuficientes) y esta sección en `definiciones_operativas.md`.

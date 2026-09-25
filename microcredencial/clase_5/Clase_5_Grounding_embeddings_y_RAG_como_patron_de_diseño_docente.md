# Machete Docente — Clase 5: Grounding, Embeddings y RAG como Patrón de Diseño

**Microcredencial #2 · Unidad 2 · Clase 5 de 8**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 20 min | Por qué el modelo necesita contexto externo |
| Bloque 2 | 45 min | Embeddings y similitud semántica (conceptual, sin matemática completa) |
| Bloque 3 | 45 min | Arquitectura RAG: chunking, recuperación, generación con contexto |
| Bloque 4 | 55 min | Laboratorio: prototipo enriquecido + comparación antes/después |
| Cierre | 15 min | Entrega, repaso, conexión con Clase 6 |

---

## Bloque 1 — Guion rápido (20 min)

- Retomar el taller express de Clase 1 (el mensaje del "Proveedor Enojado") como gancho: "esa alucinación de la Clase 1 la resolvemos hoy."
- Nombrar los tres factores de alucinación (desactualización, falta de especificidad, presión conversacional) con un ejemplo de Ortelana cada uno.

---

## Bloque 2 — Embeddings (45 min)

- Usar la analogía del mapa/barrios como eje central — es la más efectiva para que el grupo entienda sin necesitar álgebra lineal.
- Mostrar el contraejemplo de SQL: "busco algo fresco" no encuentra nada por `LIKE`, pero un embedding sí. Es el momento de mayor impacto de la clase — no apurarlo.
- Similitud coseno: explicar solo la idea (ángulo = dirección = significado), **no** es necesario resolver la fórmula a mano en esta microcredencial — eso queda para cursos más extensos.

---

## Bloque 3 — Arquitectura RAG (45 min)

Orden sugerido:

1. Diagrama offline/online en el pizarrón (10 min).
2. Chunking — por qué no meter el catálogo entero, usando el ejemplo de `descripcion_semantica` (10 min).
3. Recuperación con filtrado híbrido — remarcar que el valor real está en combinar semántica + metadatos (15 min).
4. El prompt de grounding ("ÚNICAMENTE el contexto") — leerlo en voz alta y explicar por qué esa frase es la primera capa de guardrail (10 min).

**No profundizar** en `IndexIVFFlat`, reranking ni estrategias de solapamiento de chunks — quedan fuera de alcance. Si preguntan, responder que son optimizaciones para escala mayor, no necesarias para el prototipo de esta microcredencial.

---

## Bloque 4 — Laboratorio (55 min)

- Dar 25 minutos para que cada grupo arme (o adapte de una plantilla) su corpus de 10-15 documentos con `descripcion_semantica` y metadatos.
- 20 minutos para conectar la recuperación con el LLM usando el prompt de grounding.
- 10 minutos finales: cada grupo corre al menos 2 preguntas comparando respuesta sin contexto vs. con RAG y anota el resultado en la tabla del teórico.

**Si el grupo tiene bajo dominio técnico:** proveer el dataset de telas de Ortelana ya vectorizado (usar `clase_5_pre-telas.json` u homólogo) para que practiquen la conexión con el LLM sin perder tiempo armando el corpus desde cero, y que apliquen el mismo patrón después a su caso propio como tarea.

---

## Cierre (15 min)

- Repasar el resumen de la clase.
- Confirmar entrega: prototipo enriquecido + tabla de comparación antes/después.
- Anticipar Clase 6: "el RAG de hoy responde bien preguntas de un solo paso. La próxima clase el sistema empieza a decidir por sí mismo qué hacer — eso son los agentes."

---

## Notas para el docente

- El momento de mayor impacto pedagógico de la clase es la comparación en vivo "sin contexto vs. con RAG" — si el tiempo aprieta, priorizar este momento sobre profundizar la teoría de embeddings.
- Recordar que el foco evaluable es el **patrón de diseño** (por qué y cuándo usar RAG) más que la implementación exhaustiva — un prototipo funcional simple vale más que uno incompleto por intentar cubrir demasiado.

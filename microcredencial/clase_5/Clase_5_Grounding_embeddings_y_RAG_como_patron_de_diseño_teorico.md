# Clase 5: Grounding, Embeddings y RAG como Patrón de Diseño

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 2 · Herramientas y Prototipado con IA**

**Objetivo técnico:** Entender por qué un modelo necesita contexto externo para no alucinar, comprender qué son los embeddings y la búsqueda semántica a nivel conceptual, y construir o adaptar una arquitectura RAG básica (ingesta, recuperación, generación) sobre un corpus propio.

**Origen reutilizado:** Síntesis de IADS 3, Unidades 3 y 4; clases 4 a 6 (embeddings, bases vectoriales y RAG básico). Se omiten deliberadamente reranking, chunking avanzado con solapamiento fino y evaluación con RAGAS — quedan fuera del alcance de esta microcredencial.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | Por qué un modelo necesita contexto externo |
| **Bloque 2** | Embeddings y similitud semántica — la geometría del significado |
| **Bloque 3** | Arquitectura RAG básica: ingesta, chunking, recuperación y generación |
| **Bloque 4** | Laboratorio: enriquecer el prototipo con una fuente de conocimiento |
| **Cierre** | Entrega del prototipo enriquecido y conexión con Clase 6 |

---

## Bloque 1: Por qué un modelo necesita contexto externo

Desde la Clase 1 venimos viendo el mismo problema en distintas formas: un modelo sin datos reales inventa algo que *suena* correcto. Eso se llama **alucinación**, y crece con tres factores:

- **Conocimiento desactualizado:** el modelo fue entrenado con datos hasta cierta fecha — no sabe el stock de hoy ni la normativa que se actualizó la semana pasada.
- **Falta de especificidad:** el modelo no conoce los datos internos y privados de Ortelana Textil — su catálogo, su reglamento comercial.
- **Presión conversacional:** ante un input asertivo o ambiguo, el modelo prioriza sonar convincente por sobre decir "no sé" (como vimos en el laboratorio de Clase 2).

**La solución de diseño:** en lugar de confiar en la memoria del modelo, le damos **contexto externo verificable en el momento de la consulta**. Eso se llama **grounding** (anclaje), y su implementación más extendida es **RAG** (Retrieval-Augmented Generation).

---

## Bloque 2: Embeddings y similitud semántica

### ¿Qué es un embedding?

Un **embedding** es la representación numérica de un texto en un espacio de múltiples dimensiones. El modelo convierte cualquier texto —una palabra, una oración, un párrafo— en un vector de números. Textos con significados similares producen vectores cercanos en ese espacio.

```
"Denim pesado, tacto rústico, alta resistencia"  → vector A
"Lona industrial impermeable, muy resistente"    → vector B (cercano a A)
"Seda natural satinada, caída fluida, liviana"   → vector C (lejano de A y B)
```

> **La analogía del mapa:** cada tela del catálogo de Ortelana ocupa una posición en un mapa según sus propiedades. El denim y la lona industrial están en el "barrio de los materiales resistentes"; la seda y la gasa están en el "barrio de los materiales delicados". Buscar semánticamente es preguntar: "¿qué está más cerca de esta coordenada?"

### Por qué esto resuelve lo que SQL no resuelve

Si un cliente pregunta "busco algo fresco para un vestido de verano", un `WHERE descripcion LIKE '%fresco%'` no encuentra nada — ninguna tela tiene esa palabra exacta. Los embeddings buscan por **significado**: "fresco", "liviano" y "transpirable" están cerca en el espacio vectorial aunque sean palabras distintas. Eso es lo que hace posible recuperar la tela correcta sin que el cliente use la jerga técnica exacta.

### Similitud coseno — la idea, sin la matemática completa

La similitud entre dos vectores se mide por el ángulo entre ellos: cuanto más alineados apuntan, más similares son en significado (un resultado cercano a 1). No importa tanto la magnitud (el largo del texto) sino la dirección (el significado).

**El umbral de aceptación:** no alcanza con traer "lo más parecido" — hay que decidir si ese resultado es lo bastante parecido como para usarlo. En el backend se define un umbral (ej. "si el score supera 0.80, lo recuperamos; si no, asumimos que no está en catálogo"). Sin ese umbral el sistema siempre devuelve *algo* — aunque sea una tela que no tiene nada que ver — porque matemáticamente siempre existe un "más cercano".

---

## Bloque 3: Arquitectura RAG básica

RAG tiene tres pasos, dos de ellos offline (se hacen una vez) y uno online (se ejecuta en cada consulta):

```
[OFFLINE — una vez, al construir la base]
Documentos → Chunking → Embeddings → Base vectorial

[ONLINE — en cada consulta]
Pregunta → Embedding → Base vectorial busca los más similares → Contexto + pregunta al LLM → Respuesta
```

### Paso 1 — Ingesta y chunking

Antes de indexar, los documentos largos se dividen en fragmentos (chunks). Meter un catálogo entero en el contexto del modelo es costoso, satura la atención del modelo ("lost in the middle") y no escala si el catálogo cambia constantemente.

Para un catálogo como el de Ortelana, cada tela se describe en un campo rico llamado `descripcion_semantica` — cuanto más detallado (textura, usos, tacto, sinónimos), mejor calidad tiene el embedding resultante:

```json
{
  "id": "TELA-001",
  "descripcion_semantica": "Denim pesado de 12 oz, 100% algodón rígido con teñido índigo intenso. Tacto rústico, alta resistencia al roce. Ideal para camperas y pantalones de trabajo.",
  "metadatos": {
    "linea_textil": "indumentaria",
    "sucursal_disponible": "central_buenos_aires",
    "en_stock": true,
    "tags_regionales": ["jean", "vaquero", "mezclilla"]
  }
}
```

> **Regla práctica para decidir qué es metadato y qué es texto:** todo campo sobre el que alguien vaya a necesitar filtrar de forma dura (sucursal, stock, categoría) va como metadato. Lo puramente descriptivo (textura, usos, sensaciones) queda dentro del texto, para que lo procese la búsqueda semántica. Nunca al revés — meter un dato de filtro dentro del texto obliga al sistema a "adivinarlo" semánticamente en vez de simplemente comparar un valor.

### Paso 2 — Recuperación (retrieval)

La consulta del usuario se convierte a embedding y la base vectorial devuelve los *k* documentos más similares. Herramientas típicas: **FAISS** (librería local, rápida para prototipos) o **ChromaDB** (base vectorial con persistencia real en disco y filtrado por metadatos combinado con búsqueda semántica).

```python
resultados = coleccion.query(
    query_texts=["Necesito una tela abrigada y gruesa para camperas de invierno"],
    n_results=2,
    where={"en_stock": True}   # filtro por metadato, combinado con la búsqueda semántica
)
```

> **Filtrado híbrido:** lo más valioso de una base vectorial en producción no es solo "buscar por significado" — es poder combinar esa búsqueda con condiciones duras de negocio (solo con stock, solo en cierta sucursal). Eso evita que el sistema recomiende algo que no existe o no está disponible.

> **Una variante simple para reducir resultados repetidos:** si varios documentos del corpus son casi idénticos entre sí, una búsqueda por similitud pura puede traer 3 fragmentos que dicen casi lo mismo. Algunas bases vectoriales ofrecen un modo de búsqueda (MMR — Maximum Marginal Relevance) que prioriza, además de la similitud con la consulta, que los resultados recuperados sean distintos entre sí. No hace falta implementarlo hoy — alcanza con saber que existe si el corpus tiene mucha redundancia.

> **Un límite importante para el diseño:** que la base vectorial permita actualizar un metadato como `en_stock` en caliente no la convierte en el sistema de gestión del negocio. Sirve para descartar productos agotados al buscar, pero no reemplaza al sistema real (ERP, base transaccional) cuando hace falta confirmar una cantidad exacta o una reserva — ahí la respuesta depende de consultar esa fuente real, no solo la base vectorial.

### Paso 3 — Generación con contexto (grounding real)

El LLM recibe la pregunta **junto con** los documentos recuperados, y se le instruye explícitamente a usar únicamente ese contexto:

```
Sos el asistente de ventas de Ortelana Textil.
Usá ÚNICAMENTE los fragmentos del catálogo provistos para recomendar telas.
Si la respuesta no puede deducirse del contexto, respondé:
"No poseo información oficial sobre esa consulta."

Contexto del catálogo:
{contexto_recuperado}

Consulta del cliente:
{pregunta}
```

> **Por qué esto reduce la alucinación:** la instrucción "únicamente el contexto" ancla al modelo a los datos reales en lugar de dejarlo completar con su conocimiento general. Es la primera capa de un guardrail — el diseño responsable del sistema se profundiza en la Clase 7.

---

## Bloque 4: Laboratorio — Prototipo enriquecido con RAG

### Consigna

1. Preparar un corpus breve (mínimo 10-15 documentos) vinculado al caso propio de cada grupo, con una `descripcion_semantica` rica y al menos dos metadatos útiles para filtrar.
2. Construir o adaptar una recuperación semántica con FAISS o ChromaDB.
3. Conectar la recuperación con un LLM usando una plantilla de prompt que exija usar únicamente el contexto recuperado.
4. Comparar, con al menos 2 preguntas, la respuesta **sin contexto** (Clase 1-3) vs. **con grounding** (hoy).

### Criterio de comparación

| Pregunta | Respuesta sin grounding | Respuesta con RAG | ¿Mejoró fidelidad? |
|---|---|---|---|
| ... | (el modelo inventa o generaliza) | (responde con datos reales o dice "no sé") | |

---

## Cierre y entrega

### Resumen de la clase

- La **alucinación** se reduce dándole al modelo contexto externo real en el momento de la consulta — eso es **grounding**.
- Un **embedding** representa el significado de un texto como vector; textos similares quedan cerca en ese espacio.
- **RAG** tiene tres pasos: chunking (offline), recuperación (retrieval) y generación con contexto.
- El **filtrado híbrido** (semántica + metadatos) evita recomendar algo que no existe o no está disponible.

### Evidencia / entrega de la clase

**Prototipo enriquecido** con una fuente de conocimiento propia, y evidencia de comparación antes/después (sin contexto vs. con grounding), sobre el caso propio de cada grupo.

### Herramientas usadas

FAISS o ChromaDB · LangChain · Colab

### Conexión con Clase 6

El RAG de hoy responde bien preguntas de un solo paso. Pero si la consulta requiere **combinar varias fuentes de información y ejecutar acciones** —no solo recuperar texto— el sistema necesita decidir por sí mismo qué hacer en cada momento. En la Clase 6 damos ese salto: agentes con estado y decisiones controladas.

---

## Bibliografía de la clase

- Lewis, M., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* (El paper fundacional de RAG).
- Alammar, J., & Grootendorst, M. (2024). *Hands-On Large Language Models.* O'Reilly. Capítulos 5 y 7.
- Documentación oficial de ChromaDB — docs.trychroma.com
- Documentación oficial de LangChain — python.langchain.com (RAG, LCEL).

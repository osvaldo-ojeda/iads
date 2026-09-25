# Clase 8: Evaluación de Sistemas RAG con RAGAS

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Implementar un framework de evaluación automática sobre el pipeline RAG de Ortelana usando RAGAS, comprender las cuatro métricas core (Faithfulness, Answer Relevancy, Context Precision, Context Recall) y construir un dataset de evaluación reproducible que permita detectar regresiones cuando el sistema cambia.

> **Para quienes vienen de las Microcredenciales**
> En las microcredenciales evaluaban los sistemas "a ojo" — la respuesta se ve bien o no. En producción eso no escala. Hoy construimos el equivalente de un suite de tests automatizados, pero para sistemas de IA: métricas que corren solas y te dicen con números si el sistema mejoró o empeoró.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 30 min | El problema de evaluar a ojo — debate con la tarea asincrónica |
| **Bloque 2** | 50 min | Las cuatro métricas de RAGAS — qué miden y cómo se interpretan |
| **Bloque 3** | 70 min | Laboratorio: correr RAGAS sobre el pipeline de Ortelana |
| **Bloque 4** | 50 min | LangSmith + RAGAS integrados — monitoreo continuo |
| **Cierre** | 20 min | Resumen, tarea asincrónica y conexión con Clase 9 |

---

## Bloque 1: El Problema de Evaluar a Ojo (30 min)

### Arranque con la tarea asincrónica

Cada grupo llegó con la comparación RAG básico vs RAG avanzado — las mismas 5 consultas corridas en los dos pipelines. Pedir que compartan sus conclusiones.

**Lo que va a pasar:** grupos distintos van a tener conclusiones distintas sobre cuál pipeline fue mejor. Algunos van a decir que el avanzado ganó en 4 de 5 preguntas, otros en 3 de 5. Y van a estar en desacuerdo sobre qué significa "mejor".

**Preguntar al grupo:**
- ¿Cómo decidieron cuál respuesta era mejor? ¿Qué criterios usaron?
- ¿Dos personas del mismo grupo llegaron a la misma conclusión siempre?
- ¿Qué pasa cuando el sistema cambia el chunk_size de 300 a 500 — cómo saben si mejoró?

---

### Los tres problemas de evaluar a ojo

**Problema 1 — No es reproducible**
Si hoy decís "esta respuesta está bien" y mañana alguien del equipo dice "está mal", no hay forma de resolver el desacuerdo. No hay una fuente de verdad.

**Problema 2 — No detecta regresiones**
Si cambiás el modelo de `gpt-4o-mini` a otro más barato, ¿cómo sabés si la calidad bajó? ¿Tenés que leer todas las respuestas de nuevo a mano? En producción eso es inviable.

**Problema 3 — No escala**
El sistema de Ortelana puede recibir 1.000 consultas por día. No podés revisar 1.000 respuestas manualmente para saber si el sistema está funcionando bien.

> **La solución**
> Un **dataset de evaluación** con preguntas, respuestas esperadas y contexto correcto, más un framework que corre automáticamente y devuelve métricas numéricas. Eso es RAGAS. Cada vez que cambiás algo del sistema, corrés el dataset y comparás los números.

---

## Bloque 2: Las Cuatro Métricas de RAGAS (50 min)

### El triángulo de la evaluación RAG

Un sistema RAG tiene tres componentes evaluables:

```
        Pregunta del usuario
               │
               ▼
        ┌─────────────┐
        │  RETRIEVER  │ ← ¿Recuperó los chunks correctos?
        └─────────────┘
               │
        chunks recuperados
               │
               ▼
        ┌─────────────┐
        │     LLM     │ ← ¿Usó bien los chunks para responder?
        └─────────────┘
               │
          respuesta final
```

RAGAS mide cada flecha y cada componente con una métrica distinta.

### LLM-as-a-Judge — ¿cómo un LLM puede evaluar a otro LLM?

A primera vista suena contradictorio: si estamos evaluando la calidad de las respuestas de un modelo, ¿cómo puede otro modelo hacer esa evaluación?

La clave es que el LLM evaluador **no necesita conocer de antemano cuál es "la" respuesta correcta**. Recibe tres elementos — la consulta, el contexto recuperado y la respuesta generada — y verifica si esa respuesta está respaldada por el contexto, si responde lo que se preguntó y si el contexto recuperado alcanzaba para responder. En ese momento deja de actuar como asistente conversacional y pasa a actuar como **auditor** del pipeline.

> Esto es lo que hace posible que RAGAS funcione sin comparar texto contra texto: dos respuestas distintas ("aceptamos transferencia, tarjeta o cheque" vs. "podés pagar con tarjeta, cheque o transferencia") pueden ser igual de correctas aunque no coincidan palabra por palabra. Un test tradicional de `assert respuesta == esperado` marcaría una de las dos como error; el LLM-as-a-Judge evalúa el significado, no la cadena de texto exacta.

---

### Métrica 1 — Faithfulness (Fidelidad) 🎯

**¿Qué mide?** Si cada afirmación de la respuesta del LLM puede rastrearse al contexto recuperado. Detecta alucinaciones.

**Escala:** 0 a 1. Más cercano a 1 = el LLM respondió usando solo lo que estaba en los chunks.

**Ejemplo en Ortelana:**

```
Pregunta: "¿Cuánto tiempo tengo para devolver material con defecto?"

Contexto recuperado:
"Las devoluciones por defecto de fabricación se aceptan dentro de los
30 días corridos desde la recepción del pedido."

Respuesta del LLM (faithfulness ALTA):
"Tenés 30 días corridos desde que recibís el pedido para hacer la devolución."
→ Faithfulness: 0.95 ✅ Todo está en el contexto.

Respuesta del LLM (faithfulness BAJA):
"Tenés 30 días corridos. Además, podés pedir extensión de 15 días adicionales
contactando al área comercial."
→ Faithfulness: 0.50 ❌ La extensión de 15 días no está en el contexto — el LLM la inventó.
```

> **Pregunta #1**
> Si el faithfulness es bajo, ¿el problema es el retriever o el LLM?
>
> **Análisis:** El LLM. El retriever ya hizo su trabajo — trajo los chunks. El LLM es el que agrega información que no estaba en el contexto. La solución es reforzar el System Prompt: "respondé ÚNICAMENTE con lo que está en el contexto" y bajar la temperature a 0.

---

### Métrica 2 — Answer Relevancy (Relevancia de la Respuesta) 🎯

**¿Qué mide?** Si la respuesta realmente responde la pregunta que se hizo. Un sistema puede ser fiel al contexto pero igualmente divagante o incompleto.

**Escala:** 0 a 1. Más cercano a 1 = la respuesta es directa y completa para la pregunta.

**Ejemplo en Ortelana:**

```
Pregunta: "¿Puedo devolver material si simplemente no me gustó?"

Respuesta (relevancy ALTA):
"No. Las devoluciones solo se aceptan por defecto de fabricación, no por
cambio de opinión o preferencia."
→ Answer Relevancy: 0.92 ✅ Responde directamente con sí/no y la razón.

Respuesta (relevancy BAJA):
"Ortelana Textil tiene una política de devoluciones que cubre los casos
de defecto de fabricación dentro de los 30 días. El material debe estar
sin uso y en su embalaje original. Los distribuidores Categoría A y B
tienen flete cubierto para devoluciones."
→ Answer Relevancy: 0.45 ❌ Técnicamente correcto pero no responde la pregunta.
   El cliente preguntó si PUEDE devolver — no cómo funciona la política.
```

> **Pregunta #2**
> Un sistema puede tener faithfulness alta y answer relevancy baja al mismo tiempo. ¿Cómo?
>
> **Análisis:** Si el LLM copia información correcta del contexto pero no la que responde la pregunta específica. El contexto tenía la respuesta pero el LLM eligió hablar de otra cosa. Eso se resuelve mejorando el prompt de generación — siendo más explícito sobre responder la pregunta puntual.

---

### Métrica 3 — Context Precision (Precisión Contextual) 🎯

**¿Qué mide?** De todos los chunks que el retriever recuperó, ¿cuántos eran realmente necesarios para responder? Mide la calidad del retriever — si trae ruido o no.

**Escala:** 0 a 1. Más cercano a 1 = el retriever trajo solo chunks relevantes, sin ruido.

**Ejemplo en Ortelana:**

```
Pregunta: "¿Qué documentos necesito para pedir financiación?"

Retriever recuperó 3 chunks:
Chunk 1: "Para acceder a financiación debe presentar certificado de
          habilitación municipal vigente y constancia de ingresos brutos."  → RELEVANTE ✅
Chunk 2: "Los distribuidores Categoría A tienen derecho a financiación
          en 3 cuotas sin interés para órdenes superiores a $500.000."     → RELEVANTE ✅
Chunk 3: "El horario de atención del área comercial es de lunes a
          viernes de 9 a 17hs."                                             → IRRELEVANTE ❌

Context Precision: 0.67 (2 de 3 chunks fueron útiles)
```

> **Context Precision bajo → revisar el retriever**
> Si el retriever trae mucho ruido, el LLM tiene más probabilidades de alucinar o de ignorar los chunks relevantes. La solución puede ser ajustar el chunk_size, mejorar los metadatos para filtrado, o revisar el reranking.

---

### Métrica 4 — Context Recall (Cobertura Contextual) 🎯

**¿Qué mide?** Si el retriever encontró **todos** los chunks necesarios para responder bien. Requiere tener una "respuesta de referencia" (ground truth) para comparar.

**Escala:** 0 a 1. Más cercano a 1 = el retriever no se perdió ningún chunk importante.

**Ejemplo en Ortelana:**

```
Pregunta: "¿Qué condiciones necesito cumplir para pedir financiación?"

Respuesta de referencia (ground truth):
"Para pedir financiación necesitás: ser Categoría A, orden mayor a $500.000,
certificado de habilitación vigente, constancia de ingresos brutos y
no tener deuda con Ortelana en los últimos 6 meses."

Retriever recuperó chunks que cubren:
✅ Ser Categoría A
✅ Orden mayor a $500.000
✅ Certificado de habilitación
❌ No menciona la constancia de ingresos brutos
❌ No menciona la condición de sin deuda

Context Recall: 0.60 (cubrió 3 de 5 condiciones necesarias)
```

> **Context Recall bajo → revisar el chunking**
> Si la información necesaria está en la base pero el retriever no la encuentra, el problema puede ser que esa información quedó en un chunk que no se recupera bien. Solución: ajustar chunk_size, mejorar el overlap, o enriquecer la descripción semántica.

---

### Resumen de las cuatro métricas

| Métrica | ¿Qué evalúa? | Si es baja, revisar... |
|---|---|---|
| **Faithfulness** | ¿El LLM alucinó? | El System Prompt y la temperature |
| **Answer Relevancy** | ¿Respondió la pregunta? | El prompt de generación |
| **Context Precision** | ¿El retriever trajo ruido? | El retrieval y el reranking |
| **Context Recall** | ¿El retriever se perdió algo? | El chunking y el indexado |

### Error compuesto — por qué las 4 métricas no se promedian, se multiplican

Un pipeline RAG no es un componente — son varios en cadena, y cada consulta atraviesa todos. Eso significa que pequeñas pérdidas de precisión en cada etapa **se multiplican**, no se suman ni se promedian.

Supongamos un pipeline donde el retriever recupera correctamente el 90% de las veces, el reranker selecciona bien el 85%, y el LLM genera una respuesta correcta el 92% de las veces cuando recibe el contexto adecuado:

```
0.90 × 0.85 × 0.92 = 0.7038
```

> Aunque cada componente individual tiene un desempeño superior al 85%, la probabilidad de que **todo el pipeline junto** produzca una respuesta correcta es de apenas ~70%. Por eso mejorar un solo componente (por ejemplo, agregar reranking) no garantiza por sí solo un sistema confiable — hay que medir el pipeline completo, no cada pieza por separado. Es también la razón por la que no alcanza con probar unas pocas consultas sueltas: se necesita una batería representativa y repetible — el dataset de evaluación que armamos a continuación.

---

## Bloque 3: Laboratorio — RAGAS sobre el Pipeline de Ortelana (70 min)

### Instalación y configuración

```python
!pip install ragas langchain-openai langchain-chroma --quiet
```

```python
import os
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

load_dotenv()
```

---

### El dataset de evaluación — La fuente de verdad

Ese conjunto de casos de prueba tiene nombre propio: **Golden Dataset** (o dataset de evaluación). Es la fuente de verdad (*source of truth*) contra la que se corre RAGAS cada vez que algo del pipeline cambia — igual que una suite de tests de regresión, pero para un sistema probabilístico.

Un Golden Dataset útil no se arma solo con preguntas fáciles — si todas las consultas fueran triviales, las métricas darían una imagen demasiado optimista del sistema. Conviene mezclar cuatro tipos de consulta:

- **Simples:** la respuesta sale de un único fragmento recuperado.
- **Complejas:** requieren combinar información de varios chunks distintos.
- **De escape:** preguntan por algo que no existe en la base — el criterio de éxito es que el sistema diga honestamente "no tengo esa información" en vez de alucinar.
- **Informales o ambiguas:** lenguaje coloquial, abreviaturas, errores de tipeo — para probar la robustez semántica del pipeline.

RAGAS necesita un dataset con cuatro columnas:

```python
# Dataset de evaluación para el sistema RAG de Ortelana
# Construido a partir del reglamento comercial

dataset_evaluacion = {
    "question": [
        "¿Cuánto tiempo tengo para devolver material con defecto de fábrica?",
        "¿Qué documentos necesito para pedir financiación en cuotas?",
        "¿Cuál es la diferencia entre un distribuidor Categoría A y uno Categoría B?",
        "¿Ortelana cubre el flete de devolución para todos los distribuidores?",
        "¿Puedo pedir financiación si tengo deuda pendiente con Ortelana?",
    ],
    "answer": [
        # Respuestas que generó el pipeline RAG (completar en el laboratorio)
        "",  # ← completar corriendo el pipeline
        "",
        "",
        "",
        "",
    ],
    "contexts": [
        # Chunks que recuperó el retriever para cada pregunta (completar en el laboratorio)
        [],  # ← completar corriendo el pipeline
        [],
        [],
        [],
        [],
    ],
    "ground_truth": [
        # La respuesta correcta según el reglamento — escrita por el docente/equipo
        "Las devoluciones por defecto de fabricación se aceptan dentro de los 30 días corridos desde la recepción del pedido.",
        "Certificado de habilitación municipal vigente, constancia de inscripción en ingresos brutos y no registrar deuda con Ortelana en los últimos 6 meses.",
        "Categoría A: facturación anual mayor a $5.000.000 y antigüedad mínima de 2 años. Categoría B: facturación entre $1.000.000 y $5.000.000.",
        "No. Ortelana cubre el flete de devolución solo para distribuidores Categoría A y B.",
        "No. Una de las condiciones para acceder a financiación es no registrar deuda con Ortelana en los últimos 6 meses.",
    ]
}
```

---

### Función para poblar el dataset con el pipeline

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Conectar con la base de ChromaDB de las clases anteriores
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(
    collection_name="reglamento_ortelana_v2",
    embedding_function=embeddings,
    persist_directory="./ortelana_vectordb"
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

PROMPT_RAG = ChatPromptTemplate.from_template("""
Sos el asistente comercial de Ortelana Textil.
Respondé la pregunta basándote ÚNICAMENTE en el siguiente contexto.
Si la respuesta no está en el contexto, decí: "No tengo esa información."

Contexto:
{context}

Pregunta: {question}
Respuesta:
""")

def formatear_contexto(docs):
    return "\n\n---\n\n".join(doc.page_content for doc in docs)

chain_rag = (
    {"context": retriever | formatear_contexto, "question": RunnablePassthrough()}
    | PROMPT_RAG
    | llm
    | StrOutputParser()
)

# Poblar el dataset con respuestas y contextos reales del pipeline
print("Corriendo el pipeline sobre el dataset de evaluación...")
answers = []
contexts = []

for pregunta in dataset_evaluacion["question"]:
    # Recuperar chunks
    docs = retriever.invoke(pregunta)
    chunks = [doc.page_content for doc in docs]
    contexts.append(chunks)

    # Generar respuesta
    respuesta = chain_rag.invoke(pregunta)
    answers.append(respuesta)

    print(f"✅ '{pregunta[:50]}...'")

dataset_evaluacion["answer"] = answers
dataset_evaluacion["contexts"] = contexts
```

---

### Correr RAGAS y analizar los resultados

```python
# Convertir a Dataset de HuggingFace (formato que usa RAGAS)
dataset_ragas = Dataset.from_dict(dataset_evaluacion)

# Evaluar con las cuatro métricas
print("\nEvaluando con RAGAS...")
resultados = evaluate(
    dataset=dataset_ragas,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]
)

print("\n=== RESULTADOS RAGAS — Pipeline Ortelana ===")
print(resultados)
df_resultados = resultados.to_pandas()
print(df_resultados[["question", "faithfulness", "answer_relevancy",
                       "context_precision", "context_recall"]])
```

**Output esperado (valores de referencia):**

```
=== RESULTADOS RAGAS — Pipeline Ortelana ===

question                                    faithful  ans_rel  ctx_prec  ctx_rec
¿Cuánto tiempo tengo para devolver...?        0.95     0.88      0.80      0.90
¿Qué documentos necesito para...?            0.72     0.91      0.67      0.75
¿Cuál es la diferencia entre Cat A y B?      0.88     0.85      0.90      0.85
¿Ortelana cubre el flete de devolución?      0.90     0.79      0.75      0.80
¿Puedo pedir financiación si tengo deuda?    0.65     0.88      0.70      0.70

PROMEDIO:                                    0.82     0.86      0.76      0.80
```

---

### Diagnosticar a partir de los números

Con los resultados en la tabla, hacer el análisis en clase:

```python
# Identificar las preguntas con peor performance
umbral_alerta = 0.75

print("\n=== ALERTAS — Preguntas que requieren atención ===")
for _, row in df_resultados.iterrows():
    alertas = []
    if row["faithfulness"] < umbral_alerta:
        alertas.append(f"❌ Faithfulness baja ({row['faithfulness']:.2f}) → revisar System Prompt")
    if row["answer_relevancy"] < umbral_alerta:
        alertas.append(f"❌ Relevancy baja ({row['answer_relevancy']:.2f}) → revisar prompt de generación")
    if row["context_precision"] < umbral_alerta:
        alertas.append(f"❌ Precision baja ({row['context_precision']:.2f}) → revisar retrieval/reranking")
    if row["context_recall"] < umbral_alerta:
        alertas.append(f"❌ Recall bajo ({row['context_recall']:.2f}) → revisar chunking")

    if alertas:
        print(f"\nPregunta: {row['question'][:60]}...")
        for alerta in alertas:
            print(f"  {alerta}")
```

> **Pregunta #3**
> Si la pregunta "¿Qué documentos necesito para financiación?" tiene faithfulness de 0.72 y context_recall de 0.75, ¿qué deberían cambiar primero?
>
> **Análisis:** El context_recall bajo indica que el retriever no está encontrando todos los chunks necesarios — probablemente la condición de "sin deuda" está en un chunk que no se recupera. Primero arreglan el retrieval (chunk_size, overlap) y después ven si el faithfulness sube solo. Atacar el LLM antes de arreglar el retriever es como cambiar el motor cuando el problema es la nafta.

---

## Bloque 4: LangSmith + RAGAS — Monitoreo Continuo (50 min)

### El concepto de test suite de regresión para RAG

En desarrollo de software tradicional, cada vez que cambiás código corrés los tests automáticos para verificar que nada se rompió. Para sistemas RAG, el dataset de evaluación + RAGAS cumple ese mismo rol.

**El flujo de trabajo en producción:**

```
Cambio en el sistema
(nuevo chunk_size, nuevo modelo, nuevo prompt)
        │
        ▼
Correr dataset de evaluación con RAGAS
        │
        ▼
Comparar métricas vs. baseline
        │
        ├── Métricas mejoraron → deployar el cambio ✅
        └── Métricas empeoraron → revertir el cambio ❌
```

---

### Comparar RAG básico vs RAG avanzado con números

```python
# Baseline: resultados del RAG básico (Clase 6)
baseline = {
    "faithfulness": 0.71,
    "answer_relevancy": 0.78,
    "context_precision": 0.58,
    "context_recall": 0.65,
}

# Actual: resultados del RAG avanzado (Clase 7 + hoy)
actual = {
    "faithfulness": 0.82,
    "answer_relevancy": 0.86,
    "context_precision": 0.76,
    "context_recall": 0.80,
}

print("=== COMPARACIÓN: RAG Básico vs RAG Avanzado ===\n")
print(f"{'Métrica':<25} {'Básico':>8} {'Avanzado':>10} {'Delta':>8}")
print("-" * 55)

for metrica in baseline:
    delta = actual[metrica] - baseline[metrica]
    emoji = "✅" if delta > 0 else "❌"
    print(f"{metrica:<25} {baseline[metrica]:>8.2f} {actual[metrica]:>10.2f} {emoji} {delta:>+6.2f}")
```

**Output:**
```
=== COMPARACIÓN: RAG Básico vs RAG Avanzado ===

Métrica                   Básico   Avanzado    Delta
-------------------------------------------------------
faithfulness               0.71       0.82  ✅  +0.11
answer_relevancy           0.78       0.86  ✅  +0.08
context_precision          0.58       0.76  ✅  +0.18
context_recall             0.65       0.80  ✅  +0.15
```

Ahora la mejora no es "a ojo" — es +18 puntos en context_precision y +15 en context_recall. Eso se puede reportar, defender y monitorear.

---

### LangSmith para ver el pipeline de evaluación

Con LangSmith activo, cada corrida del dataset de RAGAS queda registrada:

```python
# En .env agregar:
# LANGCHAIN_PROJECT=ortelana-rag-evaluacion

# Ahora cada evaluate() de RAGAS aparece en LangSmith como una traza
# Se puede ver pregunta por pregunta qué chunks recuperó y por qué
```

**Lo que permite LangSmith en evaluación:**
- Ver qué preguntas tienen peor performance consistentemente
- Comparar trazas de RAG básico vs avanzado lado a lado
- Detectar si una pregunta específica siempre falla (problema de chunking) vs si falla aleatoriamente (problema de temperatura del LLM)

> **La combinación LangSmith + RAGAS**
> LangSmith muestra el **cómo** (qué pasó en cada paso del pipeline). RAGAS muestra el **qué** (qué tan bueno fue el resultado). Juntos dan el diagnóstico completo: sabés que falló (RAGAS) y sabés exactamente dónde falló (LangSmith).

---

## Cierre y Material Asincrónico (20 min)

### Resumen de la clase

| Métrica RAGAS | ¿Qué evalúa? | Si es baja, atacar... |
|---|---|---|
| **Faithfulness** | ¿El LLM alucinó? | System Prompt + temperature=0 |
| **Answer Relevancy** | ¿Respondió la pregunta? | Prompt de generación |
| **Context Precision** | ¿El retriever trajo ruido? | Retrieval + reranking |
| **Context Recall** | ¿Se perdió información? | Chunking + overlap |

- El **dataset de evaluación** es la fuente de verdad del sistema — sin él, cualquier cambio es a ciegas.
- **RAGAS + LangSmith** juntos dan el diagnóstico completo: qué falló y dónde.
- El flujo de trabajo correcto: cambio → correr dataset → comparar métricas → decidir.

---

### Material asincrónico — Entre Clase 8 y Clase 9

> **Entregable del TP1 — Dataset de evaluación propio**

Cada grupo construye el dataset de evaluación de su sistema del TP1. Este dataset los acompaña hasta el final de la cursada — cada vez que cambian algo del pipeline, lo corren para ver si mejoraron o empeoraron.

**Estructura requerida — mínimo 10 preguntas:**

```python
dataset_tp1 = {
    "question": [
        # 10 preguntas reales que un usuario de su sistema haría
    ],
    "ground_truth": [
        # La respuesta correcta para cada pregunta
        # Basada en los documentos reales de su base de conocimiento
    ]
}
```

**Criterios de calidad del dataset:**
- Al menos 3 preguntas donde la respuesta está en un solo chunk
- Al menos 3 preguntas donde la respuesta requiere información de múltiples chunks
- Al menos 2 preguntas trampa donde el sistema debería decir "no tengo esa información"
- Al menos 2 preguntas con lenguaje informal o ambiguo

**Correr RAGAS sobre su pipeline y documentar el baseline:**
```
faithfulness:      X.XX  (este es su punto de partida)
answer_relevancy:  X.XX
context_precision: X.XX
context_recall:    X.XX
```

En Clase 9 arrancamos con agentes — y ese baseline queda como referencia de qué tan bien funciona el RAG antes de agregarle agentes encima.

---

### Conexión con Clase 9

Hasta ahora el sistema de Ortelana recibe una pregunta y la responde. Pero ¿qué pasa cuando la respuesta requiere múltiples pasos? "Quiero saber si califico para financiación" — el sistema tiene que consultar el CUIT en la API fiscal, verificar el historial de deuda en la BD y recuperar la normativa del RAG. Eso no es una cadena simple — es un **agente**. En Clase 9 construimos el primer agente de Ortelana con LangGraph.

---

## Bibliografía de la Clase

- **Es, S., et al. (2023).** *RAGAS: Automated Evaluation of Retrieval Augmented Generation.* arXiv:2309.15217.
- **Documentación oficial RAGAS** — docs.ragas.io
- **Documentación oficial LangSmith** — smith.langchain.com
- **Alammar, J., & Grootendorst, M. (2024).** *Hands-On Large Language Models.* O'Reilly. Capítulo 7.
- **Lewis, M., et al. (2020).** *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.*

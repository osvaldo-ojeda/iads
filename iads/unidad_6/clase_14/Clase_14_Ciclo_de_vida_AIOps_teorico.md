# Clase 14: AIOps — Ciclo de Vida de Sistemas de IA en Producción

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Implementar el ciclo de vida operativo de un sistema de IA usando versionado de prompts con PromptLayer, registro de experimentos con MLflow, A/B testing de configuraciones del pipeline RAG, y detección de data drift — convirtiendo el sistema de Ortelana en uno que puede evolucionar en producción de forma controlada y reproducible.

> **Conexión con clases anteriores**
> En Clases 11, 12 y 13 desplegamos, monitoreamos y aseguramos el sistema. Hoy cerramos el ciclo operativo: cómo mejoramos el sistema en el tiempo sin romper lo que ya funciona. Es la diferencia entre un sistema que se despliega una vez y uno que evoluciona con el negocio.

---

## Estructura de la Clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | Por qué los sistemas de IA se degradan solos |
| **Bloque 2** | Versionado de prompts con PromptLayer y A/B Testing |
| **Bloque 3** | MLflow — registrar y comparar experimentos del RAG |
| **Bloque 4** | Data drift y pipeline de actualización de ChromaDB |
| **Cierre** | Resumen, tarea asincrónica y conexión con Clase 15 |

---

## Bloque 1: Por Qué los Sistemas de IA Se Degradan Solos

### El problema de la estática en sistemas dinámicos

El sistema de Ortelana funciona perfecto el día del deploy. Tres meses después, el equipo comercial empieza a recibir quejas: "el bot no sabe nada del catálogo nuevo". ¿Qué pasó?

**Nada se rompió. El mundo cambió.**

```
Día 0 del deploy:
  Catálogo: 120 telas → ChromaDB indexado ✅
  ROUTING_PROMPT: ajustado para 3 subagentes ✅
  Modelo: gpt-4o-mini versión X ✅
  Métricas RAGAS: faithfulness 0.89 ✅

3 meses después:
  Catálogo: 180 telas (+60 nuevas, -20 descontinuadas) → ChromaDB desactualizado ❌
  ROUTING_PROMPT: el negocio agregó un 4to subagente (logística) → routing falla ❌
  Modelo: OpenAI deprecó la versión X, ahora corre versión Y → comportamiento distinto ❌
  Métricas RAGAS: faithfulness 0.61 → degradación silenciosa ❌
```

**Los tres tipos de drift que afectan sistemas de IA:**

**Data Drift** — los datos de entrada cambian. Los distribuidores de Ortelana empezaron a escribir en un registro más informal, con más jerga regional que antes. El sistema fue entrenado (vía embeddings) con el lenguaje formal del catálogo.

**Concept Drift** — el significado de los conceptos cambia. "Tela premium" antes significaba seda y lino. Ahora el mercado usa "premium" para cualquier tela con certificación orgánica.

**Model Drift** — el LLM subyacente se actualiza sin aviso. OpenAI, Anthropic y Google actualizan sus modelos periódicamente. El comportamiento cambia sutilmente pero las métricas caen.

> **La solución no es "no cambiar nada"**
> Es tener el sistema de control para detectar cuándo algo cambió, medir si el cambio es bueno o malo, y poder revertir si es necesario. Eso es AIOps.

---

### El ciclo de vida AIOps

```
┌─────────────────────────────────────────────────────────┐
│                  CICLO DE VIDA AIOps                    │
│                                                         │
│  Deploy → Monitorear → Detectar degradación             │
│     ↑                        │                          │
│     │                        ▼                          │
│  Rollback ←── Evaluar ←── Experimentar                  │
│  (si empeora)  (RAGAS)    (A/B Testing)                 │
└─────────────────────────────────────────────────────────┘
```

---

## Bloque 2: Versionado de Prompts y A/B Testing

### El problema de cambiar prompts sin control

```python
# Sin versionado — lo que hace todo el mundo al principio
ROUTING_PROMPT = """Sos el orquestador del sistema de Ortelana Textil.
Analizá la consulta y decidí qué agente debe manejarla..."""

# Alguien lo "mejora" un martes a las 11pm
ROUTING_PROMPT = """Sos el orquestador MEJORADO del sistema de Ortelana.
Analizá la consulta con más cuidado y decidí..."""

# El miércoles el routing falla en el 30% de los casos
# ¿Cuál era la versión anterior? ¿Cuándo se cambió? ¿Quién lo cambió?
# → Nadie sabe. Hay que reescribir el prompt de memoria.
```

**PromptLayer** resuelve esto: cada versión del prompt queda registrada con timestamp, autor, métricas de performance y la posibilidad de hacer rollback en un click.

---

### Instalación y configuración

```bash
pip install promptlayer langchain-community
```

```python
# .env
PROMPTLAYER_API_KEY=pl__XXXXXXXXXXXXXXXX
```

```python
# prompt_manager.py
import promptlayer
from promptlayer import PromptLayer
import os
from dotenv import load_dotenv

load_dotenv()
promptlayer.api_key = os.getenv("PROMPTLAYER_API_KEY")
pl_client = PromptLayer()
```

---

### Registrar y versionar el ROUTING_PROMPT

```python
# Subir la versión actual del ROUTING_PROMPT a PromptLayer
def registrar_prompt_v1():
    pl_client.templates.publish(
        name="ortelana_routing_prompt",
        prompt_template={
            "messages": [
                {
                    "role": "system",
                    "content": """Sos el orquestador del sistema de Ortelana Textil.
Analizá la consulta del distribuidor y decidí qué agente especializado debe manejarla.

Agentes disponibles:
- "catalogo": preguntas sobre telas, stock, disponibilidad, materiales
- "credito": alta de distribuidores, validación de CUIT, financiación
- "reclamos": defectos de material, problemas con pedidos, devoluciones
- "general": consultas que no encajan en ninguna categoría

Respondé SOLO con el nombre del agente (una sola palabra)."""
                }
            ]
        },
        tags=["v1", "produccion", "ortelana"],
        metadata={"autor": "equipo_dsi", "fecha": "2026-05-15"}
    )
    print("✅ ROUTING_PROMPT v1 registrado en PromptLayer")


# Usar el prompt desde PromptLayer — no hardcodeado en el código
def obtener_routing_prompt(version: str = "produccion") -> str:
    template = pl_client.templates.get(
        "ortelana_routing_prompt",
        label=version  # "produccion", "staging", "experimental"
    )
    return template.prompt_template["messages"][0]["content"]


# En el nodo orquestador — leer desde PromptLayer
def nodo_orquestador(estado):
    routing_prompt = obtener_routing_prompt(version="produccion")
    respuesta = llm.invoke([
        SystemMessage(content=routing_prompt),
        HumanMessage(content=estado["messages"][-1].content)
    ])
    agente_elegido = respuesta.content.strip().lower()
    return {"messages": [AIMessage(content=f"[ROUTING: {agente_elegido}]")]}
```

---

### A/B Testing del ROUTING_PROMPT

El equipo quiere mejorar el routing agregando ejemplos Few-shot. Antes de exponerlo a todos los distribuidores, lo prueban con el 20% del tráfico:

```python
# Registrar la versión mejorada como "experimental"
def registrar_prompt_v2():
    pl_client.templates.publish(
        name="ortelana_routing_prompt",
        prompt_template={
            "messages": [
                {
                    "role": "system",
                    "content": """Sos el orquestador del sistema de Ortelana Textil.
Analizá la consulta y decidí qué agente debe manejarla.

Ejemplos:
Input: "¿Tienen seda natural?" → catalogo
Input: "Quiero abrir cuenta corriente, CUIT 30-XX" → credito
Input: "El jersey vino manchado" → reclamos
Input: "Hola, buenas tardes" → general

Agentes: catalogo | credito | reclamos | general
Respondé SOLO con el nombre del agente."""
                }
            ]
        },
        tags=["v2", "experimental", "few-shot"],
        metadata={"autor": "equipo_dsi", "mejora": "agregado few-shot examples"}
    )
    print("✅ ROUTING_PROMPT v2 (experimental) registrado")


# Router A/B — 20% del tráfico va a la versión experimental
import random

def obtener_prompt_ab(thread_id: str) -> tuple[str, str]:
    """
    Asigna consistentemente la misma versión al mismo distribuidor.
    Usa hash del thread_id para que el mismo distribuidor siempre
    vea la misma versión durante el experimento.
    """
    hash_val = hash(thread_id) % 100

    if hash_val < 20:  # 20% al experimento
        version = "experimental"
        variante = "v2_few_shot"
    else:              # 80% a producción
        version = "produccion"
        variante = "v1_baseline"

    return obtener_routing_prompt(version), variante


# Registrar el resultado del A/B en PromptLayer
def registrar_resultado_ab(
    thread_id: str,
    variante: str,
    routing_correcto: bool,
    herramientas_usadas: list
):
    pl_client.log_request(
        function_name="routing_ab_test",
        kwargs={"thread_id": thread_id, "variante": variante},
        tags=[variante, "ab_test"],
        metadata={
            "routing_correcto": routing_correcto,
            "herramientas": herramientas_usadas,
        }
    )
```

**Analizar los resultados del A/B después de 48 horas:**

```python
def analizar_ab_testing(horas: int = 48) -> dict:
    """
    Compara el performance de las dos variantes del A/B test.
    """
    # En PromptLayer: filtrar por tag "ab_test" en las últimas N horas
    requests_v1 = pl_client.requests.filter(tags=["v1_baseline"])
    requests_v2 = pl_client.requests.filter(tags=["v2_few_shot"])

    def calcular_metricas(requests):
        total = len(requests)
        correctos = sum(1 for r in requests if r.metadata.get("routing_correcto"))
        return {
            "total": total,
            "tasa_correcta": correctos / max(total, 1),
            "latencia_promedio": sum(r.latency for r in requests) / max(total, 1)
        }

    metricas_v1 = calcular_metricas(requests_v1)
    metricas_v2 = calcular_metricas(requests_v2)

    print("\n=== RESULTADOS A/B TESTING — ROUTING PROMPT ===")
    print(f"v1 (baseline): {metricas_v1['tasa_correcta']:.1%} correctos | "
          f"{metricas_v1['latencia_promedio']:.0f}ms")
    print(f"v2 (few-shot): {metricas_v2['tasa_correcta']:.1%} correctos | "
          f"{metricas_v2['latencia_promedio']:.0f}ms")

    if metricas_v2["tasa_correcta"] > metricas_v1["tasa_correcta"] + 0.05:
        print("✅ v2 es significativamente mejor → promover a producción")
        recomendacion = "promover_v2"
    elif metricas_v2["tasa_correcta"] < metricas_v1["tasa_correcta"] - 0.02:
        print("❌ v2 es peor → hacer rollback")
        recomendacion = "rollback_v1"
    else:
        print("⚠️  Sin diferencia significativa → continuar el experimento")
        recomendacion = "continuar"

    return {"v1": metricas_v1, "v2": metricas_v2, "recomendacion": recomendacion}
```

> **Pregunta #1**
> ¿Por qué usamos el hash del `thread_id` para asignar variantes en lugar de random puro?
>
> **Análisis:** Porque un distribuidor que empieza una conversación con la versión v1 debe seguir con v1 en los turnos siguientes. Si asignáramos random en cada request, el mismo distribuidor podría cambiar de versión a mitad de conversación — lo que contaminaría las métricas y daría una experiencia inconsistente. El hash garantiza consistencia: mismo thread_id, siempre la misma variante.

---

## Bloque 3: MLflow — Registrar Experimentos del RAG

### Por qué MLflow

En Clases 7 y 8 ajustaron `chunk_size`, `chunk_overlap`, `k` del retriever y el modelo de embeddings. Cada combinación produce métricas RAGAS distintas. Sin MLflow, esa información vive en comentarios del notebook — imposible de comparar y reproducir.

MLflow registra cada experimento con sus parámetros, métricas y artefactos. En cualquier momento podés ver qué configuración produjo el mejor resultado y reproducirla exactamente.

```bash
pip install mlflow
```

```bash
# Levantar la UI de MLflow localmente
mlflow ui --port 5000
# → http://localhost:5000
```

---

### Registrar experimentos del pipeline RAG

```python
# experiments.py
import mlflow
import mlflow.langchain
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from datasets import Dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

mlflow.set_experiment("ortelana_rag_optimization")

def experimento_rag(
    chunk_size: int,
    chunk_overlap: int,
    k_retriever: int,
    modelo_llm: str,
    temperatura: float,
    nombre_run: str
) -> dict:
    """
    Corre un experimento completo del pipeline RAG de Ortelana
    y registra todo en MLflow.
    """
    with mlflow.start_run(run_name=nombre_run):

        # ── Registrar parámetros del experimento ─────────────────────────────
        mlflow.log_params({
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "k_retriever": k_retriever,
            "modelo_llm": modelo_llm,
            "temperatura": temperatura,
            "embedding_model": "text-embedding-3-small",
        })

        # ── Construir el pipeline con estos parámetros ────────────────────────
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". "]
        )

        # Usar el reglamento comercial de Ortelana
        reglamento = """
Artículo 1 — Categorías de Distribuidores
Ortelana Textil reconoce tres categorías de distribuidores mayoristas:
Categoría A: facturación anual superior a $5.000.000 y antigüedad mínima de 2 años.
Categoría B: facturación anual entre $1.000.000 y $5.000.000.
Categoría C: distribuidores nuevos o con facturación menor a $1.000.000.

Artículo 2 — Condiciones de Financiación
Los distribuidores Categoría A acceden a financiación en 3 cuotas sin interés
para órdenes superiores a $500.000. Para acceder deben presentar certificado
de habilitación municipal vigente y constancia de ingresos brutos. No deben
registrar deuda con Ortelana en los últimos 6 meses.

Artículo 3 — Política de Devoluciones
Las devoluciones por defecto de fabricación se aceptan dentro de los 30 días
corridos desde la recepción del pedido. Ortelana cubre el flete de devolución
solo para distribuidores Categoría A y B.
        """

        chunks = splitter.split_text(reglamento)
        mlflow.log_metric("num_chunks", len(chunks))

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vectorstore = Chroma.from_texts(
            texts=chunks,
            embedding=embeddings,
            collection_name=f"exp_{nombre_run}"
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": k_retriever})
        llm = ChatOpenAI(model=modelo_llm, temperature=temperatura)

        PROMPT = ChatPromptTemplate.from_template("""
Sos el asistente comercial de Ortelana Textil.
Respondé ÚNICAMENTE con información del contexto provisto.
Si la respuesta no está: "No tengo esa información."

Contexto: {context}
Pregunta: {question}
Respuesta:
""")

        def fmt(docs): return "\n\n---\n\n".join(d.page_content for d in docs)

        chain = (
            {"context": retriever | fmt, "question": RunnablePassthrough()}
            | PROMPT | llm | StrOutputParser()
        )

        # ── Correr el dataset de evaluación ──────────────────────────────────
        preguntas = [
            "¿Cuánto tiempo tengo para devolver material con defecto?",
            "¿Qué documentos necesito para pedir financiación en cuotas?",
            "¿Cuál es la diferencia entre Categoría A y Categoría B?",
            "¿Ortelana cubre el flete de devolución para todos los distribuidores?",
            "¿Puedo pedir financiación si tengo deuda con Ortelana?",
        ]
        ground_truths = [
            "Las devoluciones se aceptan dentro de los 30 días corridos desde la recepción.",
            "Certificado de habilitación municipal vigente y constancia de ingresos brutos.",
            "Categoría A: facturación mayor a $5.000.000 y 2 años de antigüedad. Categoría B: entre $1.000.000 y $5.000.000.",
            "No. Solo para distribuidores Categoría A y B.",
            "No. No deben registrar deuda en los últimos 6 meses.",
        ]

        answers, contexts = [], []
        for pregunta in preguntas:
            docs = retriever.invoke(pregunta)
            contexts.append([d.page_content for d in docs])
            answers.append(chain.invoke(pregunta))

        dataset = Dataset.from_dict({
            "question": preguntas,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths,
        })

        # ── Evaluar con RAGAS ─────────────────────────────────────────────────
        resultados_ragas = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall]
        )

        # ── Registrar métricas en MLflow ──────────────────────────────────────
        df = resultados_ragas.to_pandas()
        mlflow.log_metrics({
            "faithfulness_mean": df["faithfulness"].mean(),
            "answer_relevancy_mean": df["answer_relevancy"].mean(),
            "context_precision_mean": df["context_precision"].mean(),
            "context_recall_mean": df["context_recall"].mean(),
            "score_compuesto": df[["faithfulness", "answer_relevancy",
                                    "context_precision", "context_recall"]].mean().mean(),
        })

        # Guardar el DataFrame completo como artefacto
        df.to_csv("ragas_results.csv", index=False)
        mlflow.log_artifact("ragas_results.csv")

        print(f"✅ Experimento '{nombre_run}' registrado en MLflow")
        return resultados_ragas
```

---

### Correr la grilla de experimentos

```python
# Comparar distintas configuraciones del pipeline
configuraciones = [
    {"chunk_size": 300, "chunk_overlap": 60,  "k": 3, "modelo": "gpt-4o-mini", "temp": 0, "nombre": "baseline_300_60_k3"},
    {"chunk_size": 500, "chunk_overlap": 100, "k": 3, "modelo": "gpt-4o-mini", "temp": 0, "nombre": "medium_500_100_k3"},
    {"chunk_size": 500, "chunk_overlap": 100, "k": 5, "modelo": "gpt-4o-mini", "temp": 0, "nombre": "medium_500_100_k5"},
    {"chunk_size": 800, "chunk_overlap": 160, "k": 3, "modelo": "gpt-4o-mini", "temp": 0, "nombre": "large_800_160_k3"},
]

for config in configuraciones:
    experimento_rag(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        k_retriever=config["k"],
        modelo_llm=config["modelo"],
        temperatura=config["temp"],
        nombre_run=config["nombre"]
    )

print("\n✅ Todos los experimentos registrados. Ver resultados en http://localhost:5000")
```

> **Pregunta #2**
> Mirando los experimentos en la UI de MLflow, ¿qué configuración esperan que tenga el mayor `context_recall`? ¿Y el mayor `context_precision`?
>
> **Análisis:** Mayor `k` y chunks más grandes → mayor context_recall (encuentra más información relevante). Menor `k` y chunks más pequeños → mayor context_precision (lo que recupera es más relevante). El `score_compuesto` muestra el equilibrio óptimo entre las cuatro métricas para el caso de uso específico de Ortelana.

---

## Bloque 4: Data Drift y Pipeline de Actualización

### Detectar data drift en la base vectorial

```python
# drift_detector.py
import numpy as np
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

def detectar_drift_consultas(
    vectorstore: Chroma,
    consultas_recientes: list[str],
    umbral_distancia: float = 0.4
) -> dict:
    """
    Detecta si las consultas recientes de los distribuidores están
    lejos de los documentos indexados — señal de que el catálogo
    o el reglamento necesitan actualizarse.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    distancias_promedio = []

    for consulta in consultas_recientes:
        resultados = vectorstore.similarity_search_with_score(consulta, k=1)
        if resultados:
            _, distancia = resultados[0]
            distancias_promedio.append(distancia)

    if not distancias_promedio:
        return {"drift_detectado": False, "mensaje": "Sin consultas para analizar"}

    distancia_media = np.mean(distancias_promedio)
    distancia_p90 = np.percentile(distancias_promedio, 90)

    drift_detectado = distancia_p90 > umbral_distancia

    resultado = {
        "drift_detectado": drift_detectado,
        "distancia_media": round(distancia_media, 4),
        "distancia_p90": round(distancia_p90, 4),
        "umbral": umbral_distancia,
        "num_consultas_analizadas": len(distancias_promedio),
    }

    if drift_detectado:
        print(f"⚠️  DRIFT DETECTADO: p90 de distancia = {distancia_p90:.4f} "
              f"(umbral: {umbral_distancia})")
        print("   Recomendación: revisar si el catálogo o el reglamento necesitan actualización")
    else:
        print(f"✅ Sin drift. Distancia p90 = {distancia_p90:.4f}")

    return resultado
```

---

### Pipeline de actualización de ChromaDB

Cuando el catálogo cambia, necesitamos actualizar ChromaDB sin bajar el sistema:

```python
# update_pipeline.py
import json
from pathlib import Path
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from logger_config import logger

def actualizar_catalogo_ortelana(
    path_catalogo_nuevo: str,
    vectorstore: Chroma
) -> dict:
    """
    Actualiza la base vectorial de Ortelana con el nuevo catálogo.
    Estrategia:
    - Telas nuevas → agregar
    - Telas modificadas → upsert
    - Telas descontinuadas → eliminar
    Sin downtime: upsert es atómico en ChromaDB.
    """
    with open(path_catalogo_nuevo) as f:
        catalogo_nuevo = json.load(f)

    ids_nuevos = {t["id"] for t in catalogo_nuevo}

    # Obtener IDs actuales en la base
    todos_los_docs = vectorstore.get()
    ids_actuales = set(todos_los_docs["ids"])

    # Calcular diferencias
    ids_a_agregar = ids_nuevos - ids_actuales
    ids_a_actualizar = ids_nuevos & ids_actuales
    ids_a_eliminar = ids_actuales - ids_nuevos

    logger.info(
        "Inicio actualización catálogo",
        extra={
            "a_agregar": len(ids_a_agregar),
            "a_actualizar": len(ids_a_actualizar),
            "a_eliminar": len(ids_a_eliminar),
        }
    )

    # Agregar y actualizar (upsert)
    telas_a_upsert = [t for t in catalogo_nuevo if t["id"] in ids_a_agregar | ids_a_actualizar]
    if telas_a_upsert:
        vectorstore.upsert(
            documents=[t["descripcion_semantica"] for t in telas_a_upsert],
            metadatas=[t["metadatos"] for t in telas_a_upsert],
            ids=[t["id"] for t in telas_a_upsert]
        )

    # Eliminar descontinuadas
    if ids_a_eliminar:
        vectorstore.delete(ids=list(ids_a_eliminar))

    resumen = {
        "agregadas": len(ids_a_agregar),
        "actualizadas": len(ids_a_actualizar),
        "eliminadas": len(ids_a_eliminar),
        "total_actual": vectorstore._collection.count(),
    }

    logger.info("Actualización completada", extra=resumen)
    print(f"✅ Catálogo actualizado: +{resumen['agregadas']} "
          f"~{resumen['actualizadas']} -{resumen['eliminadas']} "
          f"| Total: {resumen['total_actual']} telas")

    return resumen
```

> **¿Por qué upsert y no delete + recrear todo?**
> Recrear el índice completo requiere regenerar todos los embeddings — costoso en tokens y tiempo. Con upsert solo se generan embeddings para los documentos nuevos o modificados. En un catálogo de 500 telas donde cambian 20 por semana, upsert consume el 4% de los tokens que consumiría una recreación completa.

---

### El endpoint de actualización en la API

```python
# api.py — endpoint administrativo para actualizaciones
from fastapi import Header, HTTPException

@app.post("/admin/actualizar-catalogo")
async def actualizar_catalogo(
    path_catalogo: str,
    admin_token: str = Header(alias="X-Admin-Token")
):
    """
    Endpoint administrativo para actualizar el catálogo sin downtime.
    Requiere header de autenticación X-Admin-Token.
    """
    # Verificar token de administrador
    if admin_token != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=403, detail="Token inválido")

    resumen = actualizar_catalogo_ortelana(path_catalogo, vectorstore)
    return {"mensaje": "Catálogo actualizado exitosamente", "resumen": resumen}
```

---

## Cierre y Material Asincrónico

### Resumen de la clase

- **Los tres tipos de drift:** data drift (cambian las consultas), concept drift (cambia el significado), model drift (cambia el LLM). Los tres degradan el sistema silenciosamente.
- **PromptLayer:** versionado de prompts con historial, métricas y rollback. Los prompts son código — necesitan control de versiones.
- **A/B Testing:** exponer el cambio al 20% del tráfico, medir con métricas objetivas, decidir basado en datos. Hash del thread_id para consistencia.
- **MLflow:** registrar cada experimento del pipeline RAG (parámetros → métricas RAGAS → artefactos). Hace reproducible cualquier configuración.
- **Pipeline de actualización:** upsert para cambios incrementales, detección de drift para saber cuándo actualizar, endpoint administrativo para hacerlo sin downtime.

---

### Material asincrónico — Entre Clase 14 y Clase 15

> **Entregable para la defensa final — ciclo de vida del TP1**

Correr la grilla de experimentos MLflow sobre el pipeline del TP1 con al menos 3 configuraciones distintas:

```python
# Configuraciones mínimas a comparar
configuraciones_tp1 = [
    {"chunk_size": 300, "chunk_overlap": 60,  "k": 3, "nombre": "tp1_baseline"},
    {"chunk_size": 500, "chunk_overlap": 100, "k": 3, "nombre": "tp1_medium"},
    {"chunk_size": 500, "chunk_overlap": 100, "k": 5, "nombre": "tp1_medium_k5"},
]
```

**Documentar para la defensa:**
- ¿Qué configuración obtuvo el mejor score compuesto RAGAS?
- ¿Hubo algún trade-off entre context_precision y context_recall?
- ¿Detectaron drift en su base de conocimiento?
- ¿Qué cambio en el sistema haría A/B testing antes de deployar?

---

### Conexión con Clase 15

En Clase 15 es la **clínica de proyecto final** — soporte técnico al TP con el sistema completo integrado. Llegar con: API desplegada, guardrails activos, métricas de observabilidad funcionando, experimentos MLflow documentados y el dataset de evaluación RAGAS del sistema final.

---

## Bibliografía de la Clase

- **Documentación oficial MLflow** — mlflow.org/docs
- **Documentación oficial PromptLayer** — docs.promptlayer.com
- **Sculley, D., et al. (2015).** *Hidden Technical Debt in Machine Learning Systems.* NeurIPS. (El paper que define los problemas de operar ML en producción).
- **Huyen, C. (2025).** *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulo 10: Monitoring y Chapter 12: Continual Learning.
- **Kleppmann, M. (2017).** *Designing Data-Intensive Applications.* O'Reilly. Capítulo 11: Stream Processing (conceptos de drift).

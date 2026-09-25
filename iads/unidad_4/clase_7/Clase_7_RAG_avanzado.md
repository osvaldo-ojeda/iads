# Clase 7: RAG Avanzado — Chunking, Reranking y Ventana de Contexto

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Identificar y resolver las tres fallas estructurales del RAG básico implementando chunking con solapamiento, reranking de documentos recuperados y estrategias de ventana de contexto, usando LangSmith para observar el pipeline por dentro y diagnosticar dónde falla el sistema.

> **Para quienes vienen de las Microcredenciales**
> En las microcredenciales mencionaron RAG como arquitectura para reducir alucinaciones. En Clase 6 lo construyeron con LangChain LCEL sobre el catálogo y el reglamento comercial de Ortelana — incluyendo el prompt blindado con guardrails comerciales. Hoy tomamos ese sistema y lo rompemos en vivo para entender sus límites estructurales, y lo reconstruimos con las técnicas que usan los sistemas en producción real.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 30 min | Autopsia del RAG básico — los tres escenarios donde falla |
| **Bloque 2** | 50 min | Chunking con solapamiento — cómo y por qué |
| **Bloque 3** | 60 min | Reranking — recuperar más, pasar solo lo mejor |
| **Bloque 4** | 50 min | Ventana de contexto y LangSmith como rayos X del pipeline |
| **Cierre** | 30 min | Pipeline RAG avanzado completo, tarea asincrónica y conexión con Clase 8 |

---

## Bloque 1: Autopsia del RAG Básico (30 min)

### El sistema de Clase 6 funciona... hasta que no funciona

En Clase 6 construyeron el `chain_blindado` de Ortelana: ChromaDB + LangChain LCEL + prompt con guardrails comerciales + `temperature=0`. De tarea lo corrieron con 5 consultas sobre el reglamento comercial y documentaron los resultados.

Hoy arrancamos con esas 5 consultas en la mano y las sometemos a tres escenarios donde el pipeline falla — no por el prompt ni por el LLM, sino por limitaciones estructurales del RAG básico que ningún guardrail puede resolver.

**Arranque — mostrar los resultados de la tarea asincrónica (5 min)**

Pedir a dos o tres grupos que compartan sus resultados. La pregunta disparadora:

> *"¿Cuál de las 5 consultas dio una respuesta incompleta o incorrecta aunque el prompt blindado estuviera activo?"*

Lo que debería surgir: la consulta sobre financiación devolvió una respuesta parcial (le faltaron condiciones), o la de flete de devolución alucinó o dijo "no tengo información". Eso es exactamente lo que vamos a diseccionar.

---

**Reproducir en vivo las tres fallas con el `chain_blindado` de Clase 6:**

**Falla 1 — El chunk cortado**

El reglamento comercial que cargaron en Clase 6 con `chunk_size=500, chunk_overlap=50` puede haber partido el Artículo 2 a la mitad. Reproducir con `chunk_size=200, overlap=0` para que la falla sea visible:

```
Artículo 2 con chunking sin solapamiento:

Chunk A (recuperado):
"Los distribuidores Categoría A acceden a financiación en 3 cuotas sin interés
para órdenes superiores a $500.000. Para acceder deben presentar certificado
de habilitación municipal vigente, constancia de ingresos brutos"

Chunk B (NO recuperado — queda aislado):
"y no registrar deuda con Ortelana en los últimos 6 meses. La solicitud
debe realizarse con 48 horas de anticipación al despacho."
```

Consulta: *"¿Qué necesito para pedir financiación en cuotas?"*

La respuesta del `chain_blindado`: correcta pero **incompleta** — le falta la condición de sin deuda y el plazo de 48hs. El guardrail funciona (no inventa), pero el retriever no encontró toda la información porque estaba partida.

**Falla 2 — El ruido en el contexto**

Consulta: *"¿Cuánto cuesta el flete para distribuidores de Córdoba?"*

El retriever recupera los 3 chunks semánticamente más cercanos. Uno habla de "distribuidores", otro menciona "Córdoba" — pero ninguno habla de flete. El `chain_blindado` responde correctamente "No tengo esa información" — pero el dato **sí existe** en el reglamento. El problema no es el LLM ni el prompt: es que el retriever trajo los 3 chunks equivocados.

**Falla 3 — Lost in the Middle**

Consulta con múltiples condiciones: *"¿Cuáles son todas las condiciones para calificar como Categoría A y acceder a financiación?"*

El retriever devuelve 5 chunks. La condición de antigüedad mínima está en el chunk 3 — el del medio. El LLM responde usando chunks 1, 2, 4 y 5, ignorando el 3. La respuesta parece completa pero le falta un requisito.

> **La conclusión que tiene que surgir**
> El `chain_blindado` de Clase 6 resuelve la alucinación — el LLM no inventa. Pero no puede resolver lo que el retriever no le trae. El RAG básico falla en tres niveles: cómo divide los documentos (chunking), qué documentos elige pasar al LLM (retrieval + reranking) y cómo organiza lo que le pasa (ventana de contexto). Hoy resolvemos los tres.

---

## Bloque 2: Chunking con Solapamiento (50 min)

### El problema del corte abrupto

Cuando dividimos un documento sin solapamiento, los chunks son islas de información. Una idea que empieza al final del chunk 1 y termina al inicio del chunk 2 queda partida — y el retriever solo puede recuperar una de las dos mitades.

**Visualización del problema:**

```
Documento original:
"...califica para cuenta corriente. El plazo de pago es de 30 días desde
la fecha de factura. Para solicitar extensión a 60 días debe presentar..."

Sin solapamiento (chunk_size=80):
Chunk A: "...califica para cuenta corriente. El plazo de pago es de 30 días desde"
Chunk B: "la fecha de factura. Para solicitar extensión a 60 días debe presentar..."

Con solapamiento (chunk_size=80, overlap=20):
Chunk A: "...califica para cuenta corriente. El plazo de pago es de 30 días desde"
Chunk B: "30 días desde la fecha de factura. Para solicitar extensión a 60 días..."
          ↑ estas 20 palabras se repiten → el contexto nunca se pierde
```

---

### Estrategias de chunking — cuándo usar cada una

**Estrategia 1 — Tamaño fijo sin solapamiento**
```python
from langchain.text_splitter import CharacterTextSplitter

splitter = CharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=0,
    separator="\n"
)
# ✅ Uso: documentos muy estructurados con párrafos independientes
# ❌ Evitar: reglamentos, contratos, textos narrativos continuos
```

**Estrategia 2 — Recursivo con solapamiento (recomendado para Ortelana)**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,      # 20% de solapamiento — regla práctica
    separators=["\n\n", "\n", ". ", " ", ""]
)
# ✅ Uso: reglamentos comerciales, normativas, fichas técnicas
# El separador intenta respetar párrafos → oraciones → palabras
```

**Estrategia 3 — Por estructura semántica (avanzado)**
```python
# Dividir por secciones del documento: artículos, títulos, cláusulas
# Requiere más lógica pero produce chunks más coherentes
# Ideal cuando el documento tiene estructura clara (Artículo 1, Artículo 2...)
```

> **El trade-off central del chunking**
> - Chunks pequeños → más precisión en la recuperación, menos contexto para el LLM
> - Chunks grandes → más contexto para el LLM, menor precisión en la recuperación
> - Solapamiento → resuelve la pérdida de contexto en los bordes, a costo de redundancia

**Cuadro comparativo de las tres estrategias:**

| Estrategia | Ventaja | Desventaja | Caso de uso óptimo |
|---|---|---|---|
| Tamaño fijo | Simple, predecible, muy bajo costo de cómputo | Corta oraciones o conceptos por la mitad | Logs estructurados, textos de formato uniforme |
| Recursivo con solapamiento | Mantiene coherente oraciones y párrafos enteros | Genera chunks de tamaño variable | Reglamentos, catálogos, informes normativos — **la que usamos con Ortelana** |
| Semántico / estructural | Preserva la estructura lógica original (artículos, secciones) | Requiere lógica de *parsing* personalizada | Documentos ya estructurados en secciones rígidas |

> **Si el documento está en Markdown o HTML** (por ejemplo, un manual interno con títulos `#`, `##`, `###`), LangChain ofrece `MarkdownHeaderTextSplitter`: corta respetando la jerarquía de encabezados y cada chunk retiene en sus metadatos la sección a la que pertenece (ej: `{"Categoría": "Telas Pesadas", "Producto": "Gabardina"}`) — facilita mucho el filtrado posterior en ChromaDB. Y si el documento original es un PDF complejo con tablas y columnas, herramientas de *Document Parsing* como **LlamaParse** interpretan esa estructura antes de fragmentar, evitando que una tabla de composiciones y recomendaciones de lavado pierda su significado al perder el encabezado que la explica.

---

### Aplicado a Ortelana — Reglamento Comercial

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# Documento real: reglamento comercial de Ortelana
reglamento_ortelana = """
Artículo 1 — Categorías de Distribuidores
Ortelana Textil reconoce tres categorías de distribuidores mayoristas:
Categoría A: facturación anual superior a $5.000.000 y antigüedad mínima de 2 años.
Categoría B: facturación anual entre $1.000.000 y $5.000.000.
Categoría C: distribuidores nuevos o con facturación menor a $1.000.000.

Artículo 2 — Condiciones de Financiación
Los distribuidores Categoría A acceden a financiación en 3 cuotas sin interés
para órdenes superiores a $500.000. Para acceder deben presentar certificado
de habilitación municipal vigente, constancia de ingresos brutos y no registrar
deuda con Ortelana en los últimos 6 meses. La solicitud debe realizarse con
48 horas de anticipación al despacho.

Artículo 3 — Política de Devoluciones
Las devoluciones por defecto de fabricación se aceptan dentro de los 30 días
corridos desde la recepción del pedido. El material debe estar sin uso y en su
embalaje original. Ortelana cubre el costo de flete de devolución solo para
distribuidores Categoría A y B.
"""

# Chunking con solapamiento
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=60,
    separators=["\n\n", "\n", ". "]
)

chunks = splitter.split_text(reglamento_ortelana)

print(f"Total de chunks generados: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"\n--- Chunk {i+1} ({len(chunk)} chars) ---")
    print(chunk)
```

> **Pregunta #1**
> Con chunk_size=300 y overlap=60, ¿cuántos chunks esperan que genere este reglamento? ¿Qué pasa si aumentan el overlap a 150?
>
> **Análisis:** Más overlap = más chunks redundantes = más tokens en el índice = mayor costo de embeddings. Pero también menor riesgo de perder contexto en los bordes. El 20% de overlap es la regla práctica de la industria para textos normativos.

---

### Cargar los chunks en ChromaDB

```python
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Crear colección con los chunks del reglamento
vectorstore = Chroma.from_texts(
    texts=chunks,
    embedding=embeddings,
    collection_name="reglamento_ortelana_v2",
    metadatas=[{"fuente": "reglamento_comercial", "chunk_id": i} for i in range(len(chunks))]
)

print(f"✅ {vectorstore._collection.count()} chunks indexados en ChromaDB")
```

---

### Parent Document Retriever — precisión chica, contexto grande

El chunking con solapamiento reduce el efecto guillotina, pero no resuelve del todo la tensión del trade-off: chunks chicos recuperan con precisión pero le dan poco contexto al LLM; chunks grandes le dan contexto pero pierden precisión de búsqueda.

El patrón **Parent Document Retriever (PDR)** separa el proceso de recuperación del de generación:

- Para **buscar**, el retriever sigue trabajando sobre fragmentos pequeños (**child chunks**) — mayor precisión semántica.
- Una vez identificado el fragmento relevante, el sistema recupera el **documento padre completo** (parent document) al que pertenece ese chunk, y ese contenido más amplio es el que recibe el LLM como contexto.

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore, LocalFileStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

parent_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)

# InMemoryStore alcanza para prototipos; en producción conviene LocalFileStore
# (persiste en disco, no se pierde si el servidor se reinicia)
docstore = InMemoryStore()

retriever_pdr = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=docstore,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)
```

> **Cuándo vale la pena en Ortelana:** en el reglamento comercial, el Artículo 2 completo (condiciones de financiación) puede necesitarse entero para responder bien — pero buscar con chunks de 1500 caracteres perdería precisión si la consulta es puntual. Con PDR, el retriever busca por el chunk chico ("no registrar deuda en los últimos 6 meses") y le entrega al LLM el Artículo 2 completo, evitando que la respuesta quede huérfana de contexto (el mismo problema que las "cláusulas huérfanas" en contratos, donde la sanción aparece lejos de la condición que la origina).

---

## Bloque 3: Reranking — Recuperar Más, Pasar Solo lo Mejor (60 min)

### El problema del retriever ingenuo

El retriever básico de Clase 6 hace esto:
1. Convierte la consulta a embedding
2. Busca los k=3 chunks más cercanos en ChromaDB
3. Pasa esos 3 chunks al LLM

El problema: **similitud semántica ≠ relevancia para responder la pregunta**. Un chunk puede estar cerca en el espacio vectorial pero no contener la respuesta. Y el chunk que sí la contiene puede quedar en el puesto 4 o 5.

**La solución — Recuperar más, filtrar mejor:**

```
Sin reranking:
Consulta → ChromaDB recupera top-3 → LLM recibe 3 chunks (pueden ser irrelevantes)

Con reranking:
Consulta → ChromaDB recupera top-10 → Reranker evalúa relevancia → LLM recibe top-3 reales
```

---

### Implementación con reranking manual por LLM

La forma más accesible de reranking sin librerías externas — usamos Claude o GPT para evaluar la relevancia de cada chunk:

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def rerankear_chunks(consulta: str, chunks: list[str], top_k: int = 3) -> list[str]:
    """
    Evalúa la relevancia de cada chunk para la consulta
    y devuelve solo los top_k más relevantes.
    """
    prompt_rerank = ChatPromptTemplate.from_template("""
Evaluá si el siguiente fragmento de documento contiene información
útil para responder la pregunta. Respondé solo con un número del 0 al 10.
0 = completamente irrelevante, 10 = responde directamente la pregunta.

Pregunta: {consulta}

Fragmento:
{chunk}

Puntuación (solo el número):
""")

    chain_rerank = prompt_rerank | llm | StrOutputParser()

    chunks_con_score = []
    for chunk in chunks:
        score_str = chain_rerank.invoke({"consulta": consulta, "chunk": chunk})
        try:
            score = float(score_str.strip())
        except ValueError:
            score = 0.0
        chunks_con_score.append((score, chunk))

    # Ordenar por score descendente y devolver top_k
    chunks_con_score.sort(key=lambda x: x[0], reverse=True)

    print("\n--- SCORES DE RERANKING ---")
    for score, chunk in chunks_con_score:
        print(f"[{score:.1f}] {chunk[:80]}...")

    return [chunk for _, chunk in chunks_con_score[:top_k]]
```

---

### Pipeline RAG con reranking integrado

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Recuperar más candidatos de lo necesario
retriever_amplio = vectorstore.as_retriever(search_kwargs={"k": 8})

def pipeline_rag_con_reranking(consulta: str) -> dict:
    # Paso 1: Recuperar candidatos
    docs_candidatos = retriever_amplio.invoke(consulta)
    textos_candidatos = [doc.page_content for doc in docs_candidatos]

    print(f"Candidatos recuperados: {len(textos_candidatos)}")

    # Paso 2: Rerankear
    textos_relevantes = rerankear_chunks(consulta, textos_candidatos, top_k=3)

    print(f"Chunks seleccionados tras reranking: {len(textos_relevantes)}")

    # Paso 3: Construir contexto y generar respuesta
    contexto = "\n\n---\n\n".join(textos_relevantes)

    PROMPT_RAG = ChatPromptTemplate.from_template("""
Sos el asistente comercial de Ortelana Textil.
Respondé la pregunta basándote ÚNICAMENTE en el siguiente contexto.
Si la respuesta no está en el contexto, decí: "No tengo esa información en mi base de conocimiento."

Contexto:
{context}

Pregunta: {question}

Respuesta:
""")

    chain = PROMPT_RAG | llm | StrOutputParser()
    respuesta = chain.invoke({"context": contexto, "question": consulta})

    return {
        "respuesta": respuesta,
        "chunks_usados": textos_relevantes,
        "candidatos_totales": len(textos_candidatos)
    }

# Test
resultado = pipeline_rag_con_reranking(
    "¿Qué documentos necesito para pedir financiación en cuotas?"
)
print(f"\nRESPUESTA:\n{resultado['respuesta']}")
```

> **Pregunta #2**
> ¿Por qué el reranking con LLM es más preciso que el retriever vectorial solo?
>
> **Análisis:** El retriever vectorial mide similitud semántica entre la consulta y el chunk — qué tan "parecidos" son como textos. El LLM reranker evalúa relevancia para responder — qué tan útil es ese chunk para dar una respuesta correcta. Son dos preguntas distintas. Un chunk sobre "distribuidores categoría A" es semánticamente cercano a cualquier consulta sobre distribuidores, pero solo es relevante si la pregunta toca específicamente esa categoría.

---

## Bloque 4: Ventana de Contexto y LangSmith (50 min)

### Gestión de la ventana de contexto

El LLM tiene un límite de tokens que puede procesar en una sola llamada. Más contexto no siempre es mejor — el fenómeno Lost in the Middle dice que los modelos prestan menos atención al contenido en el medio de contextos muy largos.

**Tres estrategias para gestionar el contexto:**

**Estrategia 1 — Límite fijo de chunks**
```python
# Simple: siempre pasar exactamente k chunks
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
# ✅ Predecible, ✅ costo controlado
# ❌ No adapta según la longitud de los chunks
```

**Estrategia 2 — Límite por tokens**
```python
import tiktoken

def construir_contexto_con_limite(chunks: list[str], max_tokens: int = 2000) -> str:
    """
    Agrega chunks al contexto hasta alcanzar el límite de tokens.
    Prioriza los chunks mejor rankeados (primeros en la lista).
    """
    enc = tiktoken.encoding_for_model("gpt-4o-mini")
    contexto_final = []
    tokens_usados = 0

    for chunk in chunks:
        tokens_chunk = len(enc.encode(chunk))
        if tokens_usados + tokens_chunk > max_tokens:
            print(f"⚠️ Límite alcanzado en chunk {len(contexto_final)+1} ({tokens_usados} tokens)")
            break
        contexto_final.append(chunk)
        tokens_usados += tokens_chunk

    print(f"✅ Contexto final: {len(contexto_final)} chunks, {tokens_usados} tokens")
    return "\n\n---\n\n".join(contexto_final)
```

**Estrategia 3 — Posicionamiento estratégico**
```python
def posicionar_chunks(chunks_rankeados: list[str]) -> list[str]:
    """
    Coloca los chunks más relevantes al principio y al final del contexto.
    El modelo presta más atención a los extremos que al medio.
    (Técnica: Lost in the Middle mitigation)
    """
    if len(chunks_rankeados) <= 2:
        return chunks_rankeados

    # El mejor chunk al inicio, el segundo mejor al final
    mejor = chunks_rankeados[0]
    segundo_mejor = chunks_rankeados[1]
    resto = chunks_rankeados[2:]

    return [mejor] + resto + [segundo_mejor]
```

> **Pregunta #3**
> ¿Por qué importa el orden en que le pasamos los chunks al LLM si de todas formas los lee todos?
>
> **Análisis:** Los modelos transformer tienen un sesgo de atención hacia el inicio y el final del contexto. Si el chunk más importante queda en el medio de un contexto largo, el modelo puede ignorarlo o subponderarlo. Posicionar los chunks más relevantes en los extremos mejora la calidad de la respuesta sin cambiar nada del retrieval.

---

### LangSmith — Los rayos X del pipeline

Hasta ahora, cuando el RAG falla, no sabemos exactamente dónde: ¿el retriever recuperó mal? ¿el reranker eligió los chunks equivocados? ¿el LLM ignoró el contexto correcto?

**LangSmith** es la herramienta de observabilidad de LangChain. Registra cada paso del pipeline — qué entró, qué salió, cuántos tokens costó, cuánto tardó — y lo muestra en una interfaz visual.

**Configuración — solo dos líneas:**

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Agregar al .env:
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls__XXXXXXXXXXXXXXXX
# LANGCHAIN_PROJECT=ortelana-rag

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = "ortelana-rag-avanzado"

# A partir de acá, cualquier chain de LangChain se registra automáticamente
# No hay que cambiar nada más del código
```

**Lo que LangSmith muestra de cada consulta:**

```
Traza de: "¿Qué documentos necesito para pedir financiación?"

├── retriever (0.43s)
│   ├── Input: "¿Qué documentos necesito para pedir financiación?"
│   ├── Output: 8 documentos recuperados
│   └── Tokens: 0 (búsqueda vectorial, sin LLM)
│
├── reranker_llm (2.1s)
│   ├── Input: consulta + 8 chunks
│   ├── Output: scores [9.0, 8.5, 7.0, 4.0, 3.5, 2.0, 1.5, 0.5]
│   └── Tokens: 1.240 prompt + 16 completion
│
├── prompt_builder (0.001s)
│   ├── Contexto: 3 chunks seleccionados (847 tokens)
│   └── Pregunta: "¿Qué documentos necesito...?"
│
└── llm_response (1.8s)
    ├── Input: 1.100 tokens
    ├── Output: "Para solicitar financiación en cuotas necesitás..."
    └── Tokens: 1.100 prompt + 89 completion — Costo: $0.0012
```

> **¿Por qué LangSmith en esta clase y no antes?**
> Porque recién ahora tienen algo suficientemente complejo para que valga la pena inspeccionar. Un pipeline de 4 pasos (retriever → reranker → prompt → LLM) es imposible de debuggear sin trazabilidad. A partir de hoy, LangSmith es parte del flujo de desarrollo — no un extra opcional.

---

### Ejercicio en vivo — Diagnosticar una falla con LangSmith

1. Activar LangSmith con las variables de entorno
2. Ejecutar el pipeline con esta consulta que debería fallar:

```python
resultado = pipeline_rag_con_reranking(
    "¿Cuánto cuesta el flete para devoluciones de distribuidores de Mendoza?"
)
```

3. Abrir LangSmith y analizar la traza:
   - ¿Qué chunks recuperó el retriever?
   - ¿El reranker los descartó o los pasó igual?
   - ¿La respuesta del LLM fue correcta o alucinó?

4. Discutir: ¿el problema es el chunking, el retrieval, el reranking o el LLM?

---

## Cierre — Pipeline RAG Avanzado Completo (30 min)

### El pipeline completo de hoy

```python
def rag_avanzado_ortelana(consulta: str) -> dict:
    """
    Pipeline RAG avanzado para Ortelana Textil.
    Integra: chunking con solapamiento + retrieval amplio +
    reranking por LLM + gestión de ventana de contexto +
    trazabilidad con LangSmith.
    """
    # 1. Recuperar candidatos (más de los necesarios)
    docs = retriever_amplio.invoke(consulta)
    chunks_candidatos = [doc.page_content for doc in docs]

    # 2. Rerankear por relevancia real
    chunks_relevantes = rerankear_chunks(consulta, chunks_candidatos, top_k=3)

    # 3. Posicionar para mitigar Lost in the Middle
    chunks_posicionados = posicionar_chunks(chunks_relevantes)

    # 4. Construir contexto con límite de tokens
    contexto = construir_contexto_con_limite(chunks_posicionados, max_tokens=2000)

    # 5. Generar respuesta
    PROMPT = ChatPromptTemplate.from_template("""
Sos el asistente comercial de Ortelana Textil.
Respondé basándote ÚNICAMENTE en el contexto provisto.
Si la respuesta no está, decí: "No tengo esa información."
Citá el artículo o sección cuando sea posible.

Contexto:
{context}

Pregunta: {question}
Respuesta:
""")

    chain = PROMPT | llm | StrOutputParser()
    respuesta = chain.invoke({"context": contexto, "question": consulta})

    return {
        "respuesta": respuesta,
        "chunks_usados": chunks_posicionados,
        "candidatos_evaluados": len(chunks_candidatos)
    }
```

---

### Resumen de la clase

| Problema del RAG básico | Solución aplicada hoy |
|---|---|
| Chunks que cortan ideas a la mitad | `chunk_overlap=100` — solapamiento del 20% |
| Retriever recupera chunks irrelevantes | Reranking por LLM — recuperar 8, pasar los 3 mejores |
| Lost in the Middle en el contexto | Posicionamiento estratégico + límite de tokens |
| No sé dónde falla el pipeline | LangSmith — trazabilidad de cada paso |

---

### Material asincrónico — Entre Clase 7 y Clase 8

> **La Clase 8 arranca con estos resultados**

**Actividad — Comparar RAG básico vs RAG avanzado con las mismas consultas:**

Usar las **mismas 5 consultas** que documentaron de tarea en Clase 6 y correrlas ahora con el pipeline RAG avanzado de hoy. Para cada consulta completar esta tabla:

```python
consultas_evaluacion = [
    "¿Qué documentos necesito para pedir financiación en cuotas?",
    "¿Qué pasa si devuelvo material con defecto de fábrica?",
    "¿Cuál es la diferencia entre categoría A y categoría B?",
    "¿Puedo pedir extensión del plazo de pago?",
    "¿Qué pasa si no tengo la habilitación municipal vigente?"
]

# Para cada consulta documentar:
# - Respuesta RAG básico (Clase 6) — ya la tienen documentada
# - Respuesta RAG avanzado (hoy)
# - ¿Cuál fue más completa? ¿Por qué?
# - Screenshot de la traza en LangSmith mostrando los chunks usados
```

> **¿Por qué las mismas consultas y no nuevas?**
> Porque la comparación solo tiene sentido si el input es idéntico. Cambiar las preguntas haría imposible saber si la mejora viene del pipeline avanzado o de que las preguntas nuevas son más fáciles. Este es el principio de cualquier experimento controlado — y en Clase 8 lo formalizamos con RAGAS.

En Clase 8 vamos a medir esto con métricas objetivas usando **RAGAS** — en lugar de evaluar "a ojo", tendremos números: fidelidad, relevancia contextual y precisión de la respuesta. Los resultados de esta tarea son el insumo directo para ese análisis.

---

### Conexión con Clase 8

Hoy mejoramos el RAG y pudimos ver el pipeline con LangSmith. Pero seguimos evaluando la calidad "a ojo" — una respuesta se ve bien o no se ve bien. En Clase 8 introducimos **RAGAS**: el framework de evaluación automática de sistemas RAG. Vamos a poder medir con números si el chunking con solapamiento realmente mejoró la fidelidad, si el reranking aumentó la precisión contextual, y dónde el sistema sigue fallando.

---

## Bibliografía de la Clase

- **Lewis, M., et al. (2020).** *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* (El paper fundacional de RAG).
- **Alammar, J., & Grootendorst, M. (2024).** *Hands-On Large Language Models.* O'Reilly. Capítulo 7: RAG.
- **Liu, N., et al. (2023).** *Lost in the Middle: How Language Models Use Long Contexts.* (El paper que documenta el fenómeno de atención en contextos largos).
- **Documentación oficial LangSmith** — smith.langchain.com
- **Documentación oficial LangChain** — python.langchain.com (Text Splitters, Retrievers).
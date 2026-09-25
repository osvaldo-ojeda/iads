"""
Clase 7 — RAG Avanzado: Chunking, Reranking y Ventana de Contexto
=================================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Demostrar las fallas del Chunking Fijo sin solapamiento (Lost in the Middle / Fragmentación).
  PASO 2: Implementar RecursiveCharacterTextSplitter con solapamiento (Overlap 20%).
  PASO 3: Indexar fragmentos en ChromaDB con metadatos de trazabilidad.
  PASO 4: Implementar Reranking utilizando un LLM como juez para filtrar ruido (Top-K candidatos -> Top-3 reales).
  PASO 5: Gestionar la Ventana de Contexto: límite por tokens (tiktoken) y posicionamiento
          estratégico de chunks (mejor chunk al inicio y al final, mitigación Lost in the Middle).
  PASO 6: Activar trazabilidad LangSmith (LANGCHAIN_TRACING_V2) sobre el pipeline.
  PASO 7: Construir el Pipeline RAG Avanzado y ejecutar Stress Queries para validación.
---------------------------------------------------------------------
"""

import os
import tiktoken
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

# PASO 6 — LangSmith: dos líneas activan el tracing automático de cualquier chain de LangChain
if os.getenv("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "ortelana-rag-avanzado"

RUTA_VECTORDB = "./ortelana_vectordb_c7"

REGLAMENTO_ORTELANA = """
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
distribuidores Categoría A y B. Los cortes a medida no admiten devolución.

Artículo 4 — Plazos y Envíos
Envío gratuito para órdenes superiores a $300.000. Plazo de entrega: 3-5 días
hábiles para AMBA, 7-10 días para interior. Se envía por transporte propio o
por Andreani según el destino y el volumen del pedido.
"""


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Demostrar la Falla del Chunking Fijo sin Solapamiento
# ══════════════════════════════════════════════════════════════════════════════

def demo_falla_chunk_cortado():
    print("\n" + "=" * 60)
    print("PASO 1 — Demostración: El chunk cortado (sin solapamiento)")
    print("=" * 60)

    splitter_sin_overlap = CharacterTextSplitter(chunk_size=250, chunk_overlap=0, separator="\n")
    chunks = splitter_sin_overlap.split_text(REGLAMENTO_ORTELANA)

    print(f"Chunks generados con overlap=0: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  [Chunk {i+1}] {chunk[:80]}...")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 & 3 — Chunking Recursivo con Solapamiento e Indexación
# ══════════════════════════════════════════════════════════════════════════════

def indexar_con_solapamiento() -> Chroma:
    print("\n📦 PASO 2 & 3 — Indexando reglamento con solapamiento 20%...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=60,
        separators=["\n\n", "\n", ". "],
    )
    chunks = splitter.split_text(REGLAMENTO_ORTELANA)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        collection_name="reglamento_ortelana_v2",
        persist_directory=RUTA_VECTORDB,
        metadatas=[{"fuente": "reglamento_comercial", "chunk_id": i} for i in range(len(chunks))],
    )
    print(f"✅ {vectorstore._collection.count()} chunks indexados correctamente.")
    return vectorstore


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Reranking de Chunks con LLM como Juez
# ══════════════════════════════════════════════════════════════════════════════

def rerankear_chunks(consulta: str, chunks: list[str], top_k: int = 3) -> list[str]:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt_rerank = ChatPromptTemplate.from_template("""
Evaluá si el siguiente fragmento contiene información útil para responder.
Devolvé solo un número de 0 a 10.
Pregunta: {consulta}
Fragmento: {chunk}
Puntuación:
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

    chunks_con_score.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in chunks_con_score[:top_k]]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Ventana de Contexto: límite por tokens y posicionamiento estratégico
# ══════════════════════════════════════════════════════════════════════════════

def construir_contexto_con_limite(chunks: list[str], max_tokens: int = 2000) -> str:
    """Agrega chunks al contexto hasta alcanzar el límite de tokens, priorizando
    los mejor rankeados (primeros en la lista)."""
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
    return contexto_final


def posicionar_chunks(chunks_rankeados: list[str]) -> list[str]:
    """Coloca el chunk mejor rankeado al inicio y el segundo mejor al final —
    mitigación de Lost in the Middle (los extremos reciben más atención)."""
    if len(chunks_rankeados) <= 2:
        return chunks_rankeados

    mejor = chunks_rankeados[0]
    segundo_mejor = chunks_rankeados[1]
    resto = chunks_rankeados[2:]

    return [mejor] + resto + [segundo_mejor]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 7 — Pipeline RAG Avanzado y Stress Queries
# ══════════════════════════════════════════════════════════════════════════════

def pipeline_rag_con_reranking(vectorstore: Chroma, consulta: str) -> dict:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 1. Recuperación amplia (top 8)
    retriever_amplio = vectorstore.as_retriever(search_kwargs={"k": 8})
    candidatos = [doc.page_content for doc in retriever_amplio.invoke(consulta)]

    # 2. Reranking
    chunks_relevantes = rerankear_chunks(consulta, candidatos, top_k=3)

    # 3. Ventana de contexto: límite por tokens + posicionamiento estratégico
    chunks_dentro_del_limite = construir_contexto_con_limite(chunks_relevantes, max_tokens=2000)
    chunks_posicionados = posicionar_chunks(chunks_dentro_del_limite)
    contexto = "\n\n---\n\n".join(chunks_posicionados)

    # 4. Generación
    prompt = ChatPromptTemplate.from_template("""
Sos el asistente de ventas de Ortelana Textil.
Responde usando ÚNICAMENTE el contexto provisto.
Contexto: {context}
Consulta: {question}
Respuesta:
""")
    chain = prompt | llm | StrOutputParser()
    respuesta = chain.invoke({"context": contexto, "question": consulta})

    return {"consulta": consulta, "respuesta": respuesta}


if __name__ == "__main__":
    demo_falla_chunk_cortado()
    vectorstore = indexar_con_solapamiento()
    resultado = pipeline_rag_con_reranking(
        vectorstore,
        "¿Qué documentos necesito para pedir financiación en cuotas?"
    )
    print(f"\n✅ PASO 7 — Respuesta RAG con Reranking:\n{resultado['respuesta']}")

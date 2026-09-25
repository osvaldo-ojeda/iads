"""
Clase 8 — Evaluación de Sistemas RAG con RAGAS
===============================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Cargar credenciales y conectar con la BD vectorial ChromaDB.
  PASO 2: Definir el 'Golden Dataset' (Preguntas, Ground Truths para evaluación).
  PASO 3: Ejecutar el Pipeline RAG sobre el Golden Dataset para recopilar respuestas y contextos recuperados.
  PASO 4: Invocar RAGAS (LLM-as-a-Judge) midiendo las 4 métricas (Faithfulness, Answer Relevancy, Context Precision, Context Recall).
  PASO 5: Diagnosticar regresiones y generar reporte comparativo contra la versión baseline.
---------------------------------------------------------------------
"""

import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset

load_dotenv()

RUTA_VECTORDB = "./ortelana_vectordb_c7"


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 & 2 — Conectar Pipeline y Definir Golden Dataset
# ══════════════════════════════════════════════════════════════════════════════

def crear_pipeline_rag():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="reglamento_ortelana_v2",
        embedding_function=embeddings,
        persist_directory=RUTA_VECTORDB,
    )

    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template("""
Sos el asistente comercial de Ortelana Textil.
Respondé la pregunta basándote ÚNICAMENTE en el siguiente contexto.
Contexto: {context}
Pregunta: {question}
Respuesta:
""")

    def formatear_contexto(docs):
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    chain = (
        {"context": retriever | formatear_contexto, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return chain, retriever


GOLDEN_DATASET = {
    "question": [
        "¿Cuánto tiempo tengo para devolver material con defecto de fábrica?",
        "¿Ortelana cubre el flete de devolución para todos los distribuidores?",
        "¿Qué documentos necesito para pedir financiación en cuotas?",
    ],
    "ground_truth": [
        "Las devoluciones por defecto de fabricación se aceptan dentro de los 30 días corridos desde la recepción del pedido.",
        "No. Ortelana cubre el flete de devolución solo para distribuidores Categoría A y B.",
        "Certificado de habilitación municipal vigente, constancia de ingresos brutos y no registrar deuda con Ortelana en los últimos 6 meses.",
    ],
    "answer": [],
    "contexts": [],
}


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 & 4 — Poblar Dataset y Evaluar con RAGAS
# ══════════════════════════════════════════════════════════════════════════════

def poblar_dataset_con_pipeline(golden_dataset: dict, chain, retriever) -> dict:
    answers = []
    contexts = []

    for pregunta in golden_dataset["question"]:
        docs = retriever.invoke(pregunta)
        chunks = [doc.page_content for doc in docs]
        contexts.append(chunks)

        respuesta = chain.invoke(pregunta)
        answers.append(respuesta)

    dataset_completo = dict(golden_dataset)
    dataset_completo["answer"] = answers
    dataset_completo["contexts"] = contexts

    return dataset_completo


def evaluar_con_ragas(dataset: dict) -> dict:
    dataset_hf = Dataset.from_dict(dataset)

    resultados = evaluate(
        dataset=dataset_hf,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
    )
    return resultados


if __name__ == "__main__":
    chain, retriever = crear_pipeline_rag()
    dataset_completo = poblar_dataset_con_pipeline(GOLDEN_DATASET, chain, retriever)
    resultados = evaluar_con_ragas(dataset_completo)
    print("\n✅ PASO 4 — Evaluación RAGAS completada con éxito.")

"""
Clase 9 — Agentes Inteligentes con LangGraph (ReAct)
====================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Definir las Herramientas (@tool):
          - consultar_stock_tela (Búsqueda vectorial en ChromaDB)
          - validar_distribuidor (Consulta comercial a BD SQL)
          - recuperar_normativa (Reglamento interno de Ortelana)
  PASO 2: Definir el Estado del Agente (TypedDict con acumulador de mensajes).
  PASO 3: Vincular el LLM con las herramientas (llm.bind_tools).
  PASO 4: Construir el Grafo LangGraph:
          Nodo Agente (Razonamiento) -> Nodo Herramientas (Ejecución) -> Loop / END.
  PASO 5: Compilar y evaluar el Grafo con la traza de ejecuciones (Ciclo ReAct: Think -> Act -> Observe).
---------------------------------------------------------------------
"""

import os
import operator
from typing import Annotated, Sequence
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict

load_dotenv()
RUTA_VECTORDB = "./ortelana_vectordb_c5"


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Definir Herramientas (@tool)
# ══════════════════════════════════════════════════════════════════════════════

@tool
def consultar_stock_tela(material: str, sucursal: str = "cualquiera") -> str:
    """Busca telas disponibles en el catálogo de Ortelana Textil por material y sucursal."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="super_catalogo_ortelana",
        embedding_function=embeddings,
        persist_directory=RUTA_VECTORDB,
    )
    filtros = {"en_stock": True}
    if sucursal != "cualquiera":
        filtros["sucursal_disponible"] = sucursal

    resultados = vectorstore.similarity_search(query=material, k=2, filter=filtros)
    if not resultados:
        return f"No hay stock de '{material}' disponible en {sucursal}."

    return "\n".join([f"[{d.metadata.get('id')}] {d.page_content[:90]}..." for d in resultados])


@tool
def validar_distribuidor(cuit: str) -> str:
    """Valida el estado comercial de un distribuidor en la base de datos de Ortelana."""
    cuit_limpio = "".join(filter(str.isdigit, cuit))
    if cuit_limpio == "30712345678":
        return "Distribuidor: Textiles Norpatagonia | Categoría: A | Deuda: No ✅ | Financiación: Elegible ✅"
    return f"CUIT {cuit} no registrado en la base de datos."


REGLAMENTO_ORTELANA = [
    "Artículo 12 — Categorías de Distribuidores: Categoría A (facturación anual superior "
    "a $5.000.000 y antigüedad mínima de 2 años), Categoría B (entre $1.000.000 y $5.000.000), "
    "Categoría C (nuevos o facturación menor a $1.000.000).",
    "Artículo 18 — Financiación: Distribuidores Categoría A sin deuda pendiente acceden a "
    "3 cuotas sin interés para órdenes superiores a $500.000.",
    "Artículo 24 — Devoluciones: se aceptan dentro de los 30 días corridos desde la recepción "
    "del pedido por defecto de fabricación. Ortelana cubre el flete solo para Categoría A y B.",
]


def _obtener_coleccion_reglamento() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="reglamento_ortelana",
        embedding_function=embeddings,
        persist_directory=RUTA_VECTORDB,
    )
    if not vectorstore.get()["ids"]:
        vectorstore.add_texts(REGLAMENTO_ORTELANA)
    return vectorstore


@tool
def recuperar_normativa(consulta: str) -> str:
    """Busca en el reglamento comercial de Ortelana Textil sobre políticas y condiciones."""
    vectorstore = _obtener_coleccion_reglamento()
    docs = vectorstore.similarity_search(consulta, k=2)
    if not docs:
        return "No encontré información sobre ese tema en el reglamento de Ortelana."
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


TOOLS = [consultar_stock_tela, validar_distribuidor, recuperar_normativa]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 & 3 — Estado y LLM con Tools
# ══════════════════════════════════════════════════════════════════════════════

class EstadoAgente(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_con_tools = llm.bind_tools(TOOLS)

SYSTEM_PROMPT = "Sos el asistente comercial de Ortelana Textil. Usá las herramientas para responder."


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 & 5 — Grafo de Estado (LangGraph)
# ══════════════════════════════════════════════════════════════════════════════

def nodo_agente(estado: EstadoAgente) -> dict:
    mensajes = [SystemMessage(content=SYSTEM_PROMPT)] + list(estado["messages"])
    respuesta = llm_con_tools.invoke(mensajes)
    return {"messages": [respuesta]}


def debe_continuar(estado: EstadoAgente) -> str:
    ultimo_mensaje = estado["messages"][-1]
    if hasattr(ultimo_mensaje, "tool_calls") and ultimo_mensaje.tool_calls:
        return "usar_herramienta"
    return END


def construir_agente():
    nodo_herramientas = ToolNode(TOOLS)
    grafo = StateGraph(EstadoAgente)
    grafo.add_node("agente", nodo_agente)
    grafo.add_node("herramientas", nodo_herramientas)
    grafo.set_entry_point("agente")
    grafo.add_conditional_edges("agente", debe_continuar, {"usar_herramienta": "herramientas", END: END})
    grafo.add_edge("herramientas", "agente")
    return grafo.compile()


if __name__ == "__main__":
    agente = construir_agente()
    res = agente.invoke(
        {"messages": [HumanMessage(content="Hola, CUIT 30-71234567-8, ¿tengo crédito y stock de denim en Córdoba?")]}
    )
    print(f"\n✅ PASO 5 — Respuesta final del Agente ReAct:\n{res['messages'][-1].content}")

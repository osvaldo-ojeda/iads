"""
Clase 10 — Orquestación de Agentes con Estado y Memoria
========================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Definir la estructura de Estado Global enriquecido (EstadoOrtelana: mensajes, cuit, sucursal, etc.).
  PASO 2: Construir el Subagente de Catálogo, Crédito y Reclamos con sus herramientas específicas.
  PASO 3: Construir el Nodo Extraer Contexto (parsea CUIT/sucursal en cada turno y lo persiste).
  PASO 4: Implementar el Nodo Orquestador Router (LLM + ROUTING_PROMPT clasifica intención ->
          agente_catalogo | agente_credito | agente_reclamos | agente_general).
  PASO 5: Compilar el Grafo Multiagente adjuntando el Checkpointer SqliteSaver (disco) para
          persistencia por `thread_id` entre sesiones.
  PASO 6: Demostrar la memoria entre sesiones multi-turno.
---------------------------------------------------------------------
"""

import operator
import re
from typing import Annotated, Sequence, Optional
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from typing import TypedDict

load_dotenv()
RUTA_MEMORIA_DB = "./ortelana_memoria_c10.db"
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Estado Enriquecido
# ══════════════════════════════════════════════════════════════════════════════

class EstadoOrtelana(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    cuit_identificado: Optional[str]
    sucursal_preferida: Optional[str]
    categoria_distribuidor: Optional[str]
    herramientas_usadas: Annotated[list, operator.add]
    iteraciones: int


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Herramientas Específicas por Subagente
# ══════════════════════════════════════════════════════════════════════════════

@tool
def consultar_stock_tela(material: str, sucursal: str = "cualquiera") -> str:
    """Busca telas en el catálogo."""
    return f"Stock de '{material}' verificado en {sucursal}."

@tool
def validar_distribuidor(cuit: str) -> str:
    """Valida distribuidor por CUIT."""
    return f"CUIT {cuit} validado: Categoría A sin deuda."

@tool
def recuperar_normativa(consulta: str) -> str:
    """Consulta reglamento."""
    return "Normativa: 3 cuotas sin interés para Categoría A."

@tool
def abrir_ticket_reclamo(cuit: str, descripcion: str) -> str:
    """Abre un ticket de reclamo por defecto de material o problema de pedido."""
    return f"Ticket #ORN-2847 creado para CUIT {cuit}: {descripcion[:60]}..."


PROMPT_CATALOGO = (
    "Sos el especialista en catálogo y stock de Ortelana Textil. "
    "Tu expertise es buscar telas, verificar disponibilidad y recomendar materiales. "
    "Si el cliente pregunta algo fuera de tu dominio (crédito, reclamos), decile que "
    "lo vas a derivar al área correspondiente."
)

PROMPT_CREDITO = (
    "Sos el especialista en crédito y onboarding de Ortelana Textil. "
    "Tu expertise es validar distribuidores, evaluar financiación y gestionar altas. "
    "Siempre verificá el CUIT antes de dar información de crédito."
)

PROMPT_RECLAMOS = (
    "Sos el especialista en reclamos y calidad de Ortelana Textil. "
    "Tu expertise es gestionar devoluciones, abrir tickets y escalar problemas de calidad. "
    "Siempre pedí el CUIT y una descripción detallada del problema antes de abrir un ticket."
)

agente_catalogo = create_react_agent(model=llm, tools=[consultar_stock_tela], state_modifier=PROMPT_CATALOGO)
agente_credito = create_react_agent(model=llm, tools=[validar_distribuidor, recuperar_normativa], state_modifier=PROMPT_CREDITO)
agente_reclamos = create_react_agent(model=llm, tools=[abrir_ticket_reclamo, recuperar_normativa], state_modifier=PROMPT_RECLAMOS)


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Nodo Extraer Contexto
# ══════════════════════════════════════════════════════════════════════════════

def nodo_extraer_contexto(estado: EstadoOrtelana) -> dict:
    msg = estado["messages"][-1].content
    actualizaciones = {}
    if "30-71234567-8" in msg or "30712345678" in msg:
        actualizaciones["cuit_identificado"] = "30712345678"
    if "Córdoba" in msg or "córdoba" in msg.lower():
        actualizaciones["sucursal_preferida"] = "filial_cordoba"
    return actualizaciones


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Nodo Orquestador Router (LLM, no keywords)
# ══════════════════════════════════════════════════════════════════════════════

ROUTING_PROMPT = """Sos el orquestador del sistema de Ortelana Textil.
Analizá la consulta del distribuidor y decidí qué agente especializado debe manejarla.

Agentes disponibles:
- "catalogo": preguntas sobre telas, stock, disponibilidad, características de materiales
- "credito": alta de distribuidores, validación de CUIT, financiación, cuenta corriente
- "reclamos": defectos de material, problemas con pedidos, devoluciones, quejas
- "general": saludos, consultas que no encajan en ninguna categoría anterior

Respondé SOLO con el nombre del agente (una sola palabra).
"""


def nodo_orquestador(estado: EstadoOrtelana) -> dict:
    ultimo_mensaje = estado["messages"][-1].content

    respuesta = llm.invoke([
        SystemMessage(content=ROUTING_PROMPT),
        HumanMessage(content=ultimo_mensaje),
    ])

    agente_elegido = respuesta.content.strip().lower()
    print(f"\n🔀 Router → Derivando a: [{agente_elegido}]")

    return {"messages": [AIMessage(content=f"[ROUTING: {agente_elegido}]")]}


def decidir_subagente(estado: EstadoOrtelana) -> str:
    ultimo = estado["messages"][-1].content
    if "[ROUTING: catalogo]" in ultimo:
        return "agente_catalogo"
    elif "[ROUTING: credito]" in ultimo:
        return "agente_credito"
    elif "[ROUTING: reclamos]" in ultimo:
        return "agente_reclamos"
    return "agente_general"


# ══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Grafo Multiagente con Checkpointer en Disco (SqliteSaver)
# ══════════════════════════════════════════════════════════════════════════════

def nodo_catalogo(estado: EstadoOrtelana) -> dict:
    resultado = agente_catalogo.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["catalogo"]}

def nodo_credito(estado: EstadoOrtelana) -> dict:
    resultado = agente_credito.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["credito"]}

def nodo_reclamos(estado: EstadoOrtelana) -> dict:
    resultado = agente_reclamos.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["reclamos"]}

def nodo_general(estado: EstadoOrtelana) -> dict:
    respuesta = llm.invoke([
        SystemMessage(content="Sos el asistente general de Ortelana Textil. "
                              "Respondé amablemente y derivá a quien corresponda."),
        *estado["messages"],
    ])
    return {"messages": [respuesta]}


def construir_sistema_multiagente():
    grafo = StateGraph(EstadoOrtelana)
    grafo.add_node("extraer_contexto", nodo_extraer_contexto)
    grafo.add_node("orquestador", nodo_orquestador)
    grafo.add_node("agente_catalogo", nodo_catalogo)
    grafo.add_node("agente_credito", nodo_credito)
    grafo.add_node("agente_reclamos", nodo_reclamos)
    grafo.add_node("agente_general", nodo_general)

    grafo.set_entry_point("extraer_contexto")
    grafo.add_edge("extraer_contexto", "orquestador")
    grafo.add_conditional_edges("orquestador", decidir_subagente, {
        "agente_catalogo": "agente_catalogo",
        "agente_credito": "agente_credito",
        "agente_reclamos": "agente_reclamos",
        "agente_general": "agente_general",
    })
    for n in ["agente_catalogo", "agente_credito", "agente_reclamos", "agente_general"]:
        grafo.add_edge(n, END)

    checkpointer_disco = SqliteSaver.from_conn_string(RUTA_MEMORIA_DB)
    return grafo.compile(checkpointer=checkpointer_disco)


if __name__ == "__main__":
    sistema = construir_sistema_multiagente()
    cfg = {"configurable": {"thread_id": "sesion_001"}}
    estado_inicial_extra = {
        "cuit_identificado": None,
        "sucursal_preferida": None,
        "categoria_distribuidor": None,
        "herramientas_usadas": [],
        "iteraciones": 0,
    }

    # Turno 1
    sistema.invoke(
        {"messages": [HumanMessage(content="Hola, CUIT 30-71234567-8 en Córdoba")], **estado_inicial_extra},
        config=cfg,
    )

    # Turno 2 (Memoria del turno anterior)
    res2 = sistema.invoke({"messages": [HumanMessage(content="¿Tienen denim disponible acá?")]}, config=cfg)
    print(f"\n✅ PASO 6 — Respuesta con Memoria:\n{res2['messages'][-1].content}")
    print(f"🔧 Herramientas usadas: {res2.get('herramientas_usadas', [])}")

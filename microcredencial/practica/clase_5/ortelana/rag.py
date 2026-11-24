"""
RAG sobre la normativa comercial, armado como una CADENA de LangChain (LCEL).

    pregunta ──┬──────────────────────────────────────────────┐
               └─▶ recuperar (embedding + ChromaDB + umbral) ─┤
                                                              ▼
               ¿algún fragmento supera el umbral?
                 ├─ NO → "No tengo información oficial sobre esa consulta."   (el LLM ni se llama)
                 └─ SÍ → plantilla (contexto + pregunta) | modelo | parser  → respuesta citando la regla

Es la misma idea de la Clase 4 (plantilla | modelo | parser) con un paso nuevo adelante:
RECUPERAR el contexto. Eso es la "R" de RAG (Retrieval-Augmented Generation).

Sin API key, el "modelo" es una SIMULACIÓN: devuelve el fragmento recuperado tal cual.
La recuperación (embeddings, búsqueda, filtro y umbral) corre de verdad igual.
"""

import os
from typing import Optional

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables import RunnableBranch, RunnableLambda, RunnableParallel, RunnablePassthrough

from .base_conocimiento import abrir, buscar
from .config import RAIZ_PROYECTO, detectar_proveedor

SIN_INFORMACION = "No tengo información oficial sobre esa consulta."
SOLO_VIGENTES = {"vigente": True}   # filtrado híbrido: nunca responder con una regla derogada


def _leer_prompt(nombre: str) -> str:
    return (RAIZ_PROYECTO / "prompts" / f"{nombre}.txt").read_text(encoding="utf-8")


# 1) PLANTILLA: instrucciones de grounding + el contexto recuperado + la pregunta
PLANTILLA_RAG = ChatPromptTemplate.from_messages([
    ("system", _leer_prompt("rag_v1")),
    ("human", "Contexto recuperado de la normativa:\n{contexto}\n\n"
              "Consulta del distribuidor:\n<consulta>\n{pregunta}\n</consulta>"),
])

# Para comparar: la misma pregunta SIN contexto (como en las Clases 1 a 3)
PLANTILLA_SIN_GROUNDING = ChatPromptTemplate.from_messages([
    ("system", _leer_prompt("sin_grounding_v1")),
    ("human", "{pregunta}"),
])


# 2) MODELO: el real si hay API key; si no, una simulación ──────────────────

def _modelo_simulado(prompt: ChatPromptValue) -> str:
    """Sin API key: devuelve el primer fragmento del contexto, sin redactar nada."""
    consulta_usuario = prompt.messages[-1].content
    for linea in consulta_usuario.splitlines():
        if linea.startswith("["):                      # "[NOR-ZONA] Cobertura geográfica..."
            codigo, texto = linea[1:].split("] ", 1)
            return f"Según la normativa vigente ({codigo}): {texto}"
    return SIN_INFORMACION


def crear_modelo(temperatura: float = 0):
    """Devuelve (modelo, origen). Cualquier chat model de LangChain encaja en la cadena."""
    proveedor = detectar_proveedor()
    if proveedor is None:
        return RunnableLambda(_modelo_simulado), "SIMULACIÓN (sin API key)"

    nombre, key = proveedor
    try:
        if nombre == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            modelo = ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                                            temperature=temperatura, google_api_key=key)
        else:
            from langchain_openai import ChatOpenAI  # OpenAI y Groq usan el mismo formato
            if nombre == "openai":
                modelo = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                                    temperature=temperatura, api_key=key)
            else:
                modelo = ChatOpenAI(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                                    temperature=temperatura, api_key=key,
                                    base_url="https://api.groq.com/openai/v1")
    except ImportError as e:
        return RunnableLambda(_modelo_simulado), f"SIMULACIÓN (falta instalar {e.name})"
    return modelo, f"LLM ({nombre})"


# 3) La cadena completa ──────────────────────────────────────────────────────

def formatear_contexto(documentos) -> str:
    """Solo los fragmentos que superan el umbral, cada uno con su código para poder citarlo."""
    return "\n".join(f"[{d.metadata['id']}] {d.page_content}" for d in documentos if d.metadata["supera_umbral"])


def _hay_contexto(entrada: dict) -> bool:
    return any(d.metadata["supera_umbral"] for d in entrada["documentos"])


def crear_cadena_rag(base=None, filtro: Optional[dict] = SOLO_VIGENTES):
    """Devuelve (cadena, origen del modelo). `filtro=None` desactiva el filtrado híbrido (para la demo)."""
    base = base if base is not None else abrir("normativa")
    modelo, origen = crear_modelo()

    recuperar = RunnableLambda(lambda pregunta: buscar(base, pregunta, filtro=filtro))

    generar = RunnableBranch(
        (lambda x: not _hay_contexto(x), RunnableLambda(lambda x: SIN_INFORMACION)),  # ✋ umbral
        RunnablePassthrough.assign(contexto=lambda x: formatear_contexto(x["documentos"]))
        | PLANTILLA_RAG | modelo | StrOutputParser(),
    )

    cadena = RunnableParallel(pregunta=RunnablePassthrough(), documentos=recuperar).assign(respuesta=generar)
    return cadena, origen


_cadena = None


def responder_consulta(pregunta: str) -> dict:
    """
    Lo que usa el workflow. Devuelve:
        texto       → la respuesta (o SIN_INFORMACION)
        origen      → quién la escribió: LLM, SIMULACIÓN o "nada supera el umbral"
        fuentes     → códigos de las reglas usadas como contexto
        candidatos  → los k recuperados con su similitud (para la traza)
    """
    global _cadena
    if _cadena is None:
        _cadena = crear_cadena_rag()
    cadena, origen = _cadena

    try:
        r = cadena.invoke(pregunta)
    except Exception as e:  # la API falló: no inventamos, derivamos
        return {"texto": None, "origen": f"falló el LLM ({type(e).__name__})", "fuentes": [], "candidatos": []}

    fuentes = [d.metadata["id"] for d in r["documentos"] if d.metadata["supera_umbral"]]
    return {
        "texto": r["respuesta"],
        "origen": origen if fuentes else "nada supera el umbral: el LLM no se llama",
        "fuentes": fuentes,
        "candidatos": [(d.metadata["id"], d.metadata["similitud"], d.metadata["supera_umbral"]) for d in r["documentos"]],
    }


def responder_sin_grounding(pregunta: str, simulacion: str) -> dict:
    """La misma pregunta, sin contexto. Sin API key, usa la respuesta de ejemplo (`simulacion`)."""
    modelo, origen = crear_modelo()
    if origen.startswith("SIMULACIÓN"):
        return {"texto": simulacion, "origen": "SIMULACIÓN (respuesta de ejemplo de un LLM sin contexto)"}
    try:
        texto = (PLANTILLA_SIN_GROUNDING | modelo | StrOutputParser()).invoke({"pregunta": pregunta})
        return {"texto": texto.strip(), "origen": origen}
    except Exception as e:
        return {"texto": f"(falló la API: {type(e).__name__})", "origen": origen}

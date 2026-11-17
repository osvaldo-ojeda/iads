"""
OPCIONAL — El paso 2 (extraer + validar) escrito como una CADENA de LangChain (LCEL).

Hace exactamente lo mismo que extractor.py de la Clase 3, pero con el patrón del teórico:

    cadena = plantilla | modelo | parser

Sirve para comparar: ¿qué nos ahorra el framework y qué no?
    ✅ Ahorra la "plomería": armar los mensajes, llamar a la API, sacar el texto de la respuesta.
    ❌ NO ahorra la validación ni las reglas: el parser sigue siendo NUESTRO código (validar_respuesta).

Requiere:  pip install langchain-core
Con API real además:  pip install langchain-google-genai   (o langchain-openai)
Sin eso, usa un modelo FALSO de LangChain que devuelve las respuestas de ejemplo del lote.
"""

import os

from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from .config import detectar_proveedor
from .extractor import aplicar_reglas, cargar_prompt, validar_respuesta

# 1) PLANTILLA: la estructura del mensaje, con espacios para las variables.
#    Ojo: el prompt de extracción tiene llaves { } en los ejemplos JSON, y LangChain usa
#    las llaves para marcar variables. Por eso el prompt entra como VALOR de {instrucciones}
#    y no escrito directamente en la plantilla.
plantilla = ChatPromptTemplate.from_messages([
    ("system", "{instrucciones}"),
    ("user", "Mensaje del distribuidor (entre <mensaje> y </mensaje>):\n<mensaje>\n{mensaje}\n</mensaje>"),
])


def crear_modelo(respuestas_simuladas: list[str]):
    """2) MODELO: el real si hay key y la integración instalada; si no, uno falso de LangChain."""
    proveedor = detectar_proveedor()
    if proveedor:
        nombre, key = proveedor
        try:
            if nombre == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                return ChatGoogleGenerativeAI(model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
                                              temperature=0, google_api_key=key), f"LangChain + {nombre}"
            if nombre == "openai":
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                                  temperature=0, api_key=key), f"LangChain + {nombre}"
        except ImportError:
            pass
    return FakeListChatModel(responses=respuestas_simuladas), "LangChain + modelo FALSO (simulación)"


def _validar_y_aplicar_reglas(texto: str) -> dict:
    """3) PARSER: json.loads + Pydantic + regla del CUIT. Es el mismo código de la Clase 3."""
    resultado = validar_respuesta(texto)
    if not resultado["ok"]:
        return resultado
    return {**resultado, **aplicar_reglas(resultado["extraccion"])}


parser = StrOutputParser() | RunnableLambda(_validar_y_aplicar_reglas)


def crear_cadena(respuestas_simuladas: list[str]):
    modelo, origen = crear_modelo(respuestas_simuladas)
    return plantilla | modelo | parser, origen


def extraer(cadena, mensaje: str) -> dict:
    return cadena.invoke({"instrucciones": cargar_prompt(), "mensaje": mensaje})

"""
El componente completo: pasos 2, 4 y 5 del user journey de la Entrega 1.

    Mensaje → [LLM + prompt] → texto → json.loads() → Pydantic → regla CUIT → extracción validada
     paso 2                            ¿es JSON?      ¿cumple el   ¿el CUIT es
                                                       contrato?    válido?
                                       └──────────── paso 4 ──────┘ └─ paso 5 ─┘

Cada etapa puede fallar, y cada falla se informa por separado:
    COMUNICACION → el modelo no respondió (red, key, saturación)
    FORMATO      → respondió algo que no es JSON
    CONTRATO     → es JSON pero no cumple el contrato
    REGLA        → cumple el contrato pero un dato no es válido para el negocio
"""

import json
import urllib.error
from typing import Optional

from pydantic import ValidationError

from .config import RAIZ_PROYECTO, detectar_proveedor
from .contrato import ExtraccionOrtelana
from .llm import llamar_con_reintentos
from .reglas import validar_cuit

PROMPT_VERSION = "v1"


def cargar_prompt(version: str = PROMPT_VERSION) -> str:
    """El prompt vive en un archivo aparte: así se puede comparar v1 con v2 sin tocar el código."""
    return (RAIZ_PROYECTO / "prompts" / f"extraccion_{version}.txt").read_text(encoding="utf-8")


def armar_mensaje_usuario(mensaje: str) -> str:
    """Delimita el mensaje del distribuidor para que el modelo lo trate como dato, no como instrucción."""
    return f"Mensaje del distribuidor (entre <mensaje> y </mensaje>):\n<mensaje>\n{mensaje.strip()}\n</mensaje>"


def validar_respuesta(texto: str) -> dict:
    """
    Paso 4 — validación en dos niveles.
    No limpiamos bloques ```json: si el modelo los agrega, rompió la regla del prompt
    y queremos verlo como error de FORMATO.
    """
    try:
        datos = json.loads(texto)                       # Nivel 1: ¿es JSON?
    except json.JSONDecodeError as e:
        return {"ok": False, "error": "FORMATO", "detalle": f"No es JSON válido ({e.msg})"}

    if not isinstance(datos, dict):
        return {"ok": False, "error": "CONTRATO", "detalle": "El JSON no es un objeto {...}"}

    try:
        extraccion = ExtraccionOrtelana(**datos)        # Nivel 2: ¿cumple el contrato?
    except ValidationError as e:
        errores = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        return {"ok": False, "error": "CONTRATO", "detalle": errores}

    return {"ok": True, "extraccion": extraccion.model_dump()}


def aplicar_reglas(extraccion: dict) -> dict:
    """Paso 5 — reglas de negocio. Hoy: dígito verificador del CUIT (si el mensaje trajo uno)."""
    cuit = extraccion.get("cuit")
    if cuit is None:
        return {"ok": True, "regla_cuit": "Sin CUIT en el mensaje: no hay nada que validar"}
    valido, motivo = validar_cuit(cuit)
    if not valido:
        return {"ok": False, "error": "REGLA", "detalle": f"CUIT {cuit}: {motivo}"}
    return {"ok": True, "regla_cuit": motivo}


def procesar_mensaje(mensaje: str, simulacion: Optional[str] = None, version: str = PROMPT_VERSION) -> dict:
    """
    Flujo completo del componente. Nunca rompe el programa: siempre devuelve un dict
    con "ok" y, si falló, en qué etapa ("error") y por qué ("detalle").
    Si no hay API key en el .env, usa `simulacion` como si fuera la respuesta del modelo.
    """
    proveedor = detectar_proveedor()
    if proveedor is None:
        origen, texto = "SIMULACIÓN (sin API key en .env)", simulacion or ""
    else:
        nombre, key = proveedor
        origen = f"API REAL — {nombre}"
        try:
            texto = llamar_con_reintentos(cargar_prompt(version), armar_mensaje_usuario(mensaje), nombre, key)
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
            # URLError incluye HTTPError (key inválida, límite de uso, servidor caído).
            return {"origen": origen, "ok": False, "error": "COMUNICACION", "detalle": f"{type(e).__name__}: {e}"}

    resultado = {"origen": origen, "prompt": version, "respuesta_cruda": texto, **validar_respuesta(texto)}
    if not resultado["ok"]:
        return resultado
    return {**resultado, **aplicar_reglas(resultado["extraccion"])}

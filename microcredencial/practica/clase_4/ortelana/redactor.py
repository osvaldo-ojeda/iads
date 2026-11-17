"""
Paso 11 del journey: el LLM redacta la respuesta al distribuidor.

Es el camino inverso al paso 2:
    paso 2  : lenguaje natural   → datos estructurados   (el LLM extrae)
    paso 11 : decisión estructurada → lenguaje natural   (el LLM redacta)

El LLM COMUNICA la decisión, no la toma: recibe un JSON con la decisión ya resuelta
por las reglas (y por la persona que aprueba) y solo le pone palabras.

Si no hay API key, o la API falla, se usa una PLANTILLA FIJA: el workflow nunca se cae
por la redacción, porque la decisión ya está tomada y se puede comunicar igual.
"""

import json
import urllib.error

from .config import RAIZ_PROYECTO, detectar_proveedor
from .llm import llamar_con_reintentos

PROMPT_REDACCION = "redaccion_v1"

NOMBRES_FALTANTES = {
    "razon_social": "razón social de la empresa o taller",
    "cuit": "CUIT",
    "facturacion_anual": "facturación anual aproximada",
    "CONSTANCIA_ARCA": "constancia de inscripción en ARCA",
    "HABILITACION": "habilitación municipal vigente",
    "INGRESOS_BRUTOS": "constancia de inscripción en Ingresos Brutos",
}


def formatear_pesos(monto: float) -> str:
    """150000000 → "$150.000.000" (formato argentino)."""
    return "$" + f"{monto:,.0f}".replace(",", ".")


def plantilla_fija(decision: dict) -> str:
    """Respuesta determinista: la usa el sistema cuando no puede (o no debe) llamar al LLM."""
    saludo = f"Hola, {decision['razon_social']}." if decision.get("razon_social") else "Hola."
    tipo = decision["tipo"]

    if tipo == "PENDIENTE":
        faltantes = "\n".join(f"  - {NOMBRES_FALTANTES.get(f, f)}" for f in decision["faltantes"])
        return (f"{saludo} Recibimos tu solicitud de alta como distribuidor. Para poder evaluarla "
                f"necesitamos lo siguiente:\n{faltantes}\nLa solicitud queda pendiente hasta recibirlo.")

    if tipo == "RECHAZADA":
        return f"{saludo} Revisamos tu solicitud y no pudimos aprobarla. Motivo: {decision['motivo']}."

    reglas = ", ".join(decision["reglas_aplicadas"])
    if decision["cuenta_corriente"]:
        condiciones = (f"cuenta corriente a {decision['plazo_dias']} días con un límite de "
                       f"{formatear_pesos(decision['limite_credito'])}")
    else:
        condiciones = "operación al contado"
    return (f"{saludo} Tu solicitud fue aprobada en categoría {decision['categoria']}, con "
            f"{condiciones}. Esta decisión se basa en la normativa comercial ({reglas}).")


def redactar_respuesta(decision: dict) -> dict:
    """Devuelve {"texto": ..., "origen": "LLM" | "PLANTILLA"}."""
    proveedor = detectar_proveedor()
    if proveedor is None:
        return {"texto": plantilla_fija(decision), "origen": "PLANTILLA (sin API key)"}

    nombre, key = proveedor
    system = (RAIZ_PROYECTO / "prompts" / f"{PROMPT_REDACCION}.txt").read_text(encoding="utf-8")
    usuario = f"<decision>\n{json.dumps(decision, ensure_ascii=False, indent=2)}\n</decision>"
    try:
        texto = llamar_con_reintentos(system, usuario, nombre, key, json_mode=False, temperatura=0.3)
        return {"texto": texto.strip(), "origen": f"LLM ({nombre})"}
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError) as e:
        return {"texto": plantilla_fija(decision), "origen": f"PLANTILLA (falló la API: {type(e).__name__})"}

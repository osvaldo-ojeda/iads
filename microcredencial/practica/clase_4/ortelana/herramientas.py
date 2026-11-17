"""
Herramientas (tools): funciones de código que el sistema EJECUTA para hacer algo real.

Hoy hay una sola: consultar el sistema de gestión de Ortelana (paso 7 del journey).

    ¿Quién decide cuándo se llama?  → EL DESARROLLADOR. Está en un paso fijo del workflow.
    En la Clase 6 (agentes), es el MODELO el que decide qué herramienta usar y cuándo.

El sistema de gestión real sería una base de datos o una API del ERP. Para la práctica
lo simulamos con un archivo JSON (datos/sistema_gestion.json): la función se usa igual.
"""

import json

from .config import RAIZ_PROYECTO

ARCHIVO_SISTEMA_GESTION = RAIZ_PROYECTO / "datos" / "sistema_gestion.json"


def consultar_sistema_gestion(cuit: str) -> dict:
    """
    Busca un distribuidor por CUIT en el sistema de gestión de Ortelana.
    Devuelve si ya es cliente, su antigüedad en meses y los días de deuda vencida.

    Tipo: SENSOR (solo lee, no modifica nada) → riesgo bajo.
    La base de datos es la AUTORIDAD: el LLM no puede "saber" si alguien debe plata.
    """
    base = json.loads(ARCHIVO_SISTEMA_GESTION.read_text(encoding="utf-8"))
    registro = base.get(cuit)
    if registro is None:
        return {"es_cliente": False, "antiguedad_meses": 0, "dias_deuda_vencida": 0}
    return {"es_cliente": True, **registro}

"""
Microcredencial Entrega 1 — Solución de Referencia
===================================================
Consolida los aprendizajes de las Clases 1, 2 y 3.

Componentes:
  1. Ficha PEAS y Diagnóstico de Oportunidad.
  2. Validación Determinista de CUIT.
  3. Contrato Técnico Pydantic (SolicitudDistribuidorSchema).
  4. Extracción de Structured Outputs.
"""

import json
import re
from typing import Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError


# 1. Contrato Técnico Pydantic
class SolicitudDistribuidorSchema(BaseModel):
    razon_social: str = Field(description="Razón social del distribuidor")
    cuit: str = Field(description="CUIT en formato XX-XXXXXXXX-X")
    categoria: str = Field(description="Categoría A, B o C")
    facturacion_anual: float = Field(ge=0, description="Facturación anual en ARS")
    tiene_habilitacion: bool = Field(description="Si posee habilitación municipal")


# 2. Lógica Determinista
def validar_cuit_checksum(cuit: str) -> bool:
    digits = [int(c) for c in re.sub(r"\D", "", cuit)]
    if len(digits) != 11:
        return False
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(d * m for d, m in zip(digits[:10], multiplicadores))
    verificador = 11 - (suma % 11)
    if verificador == 11: verificador = 0
    elif verificador == 10: verificador = 9
    return digits[10] == verificador


# 3. Pipeline de la Entrega 1
def procesar_entrega_1(datos: dict) -> dict:
    try:
        solicitud = SolicitudDistribuidorSchema(**datos)
    except ValidationError as e:
        return {"aprobado": False, "error": f"Error de contrato Pydantic: {e}"}

    if not validar_cuit_checksum(solicitud.cuit):
        return {"aprobado": False, "error": "CUIT inválido según algoritmo determinista Módulo 11"}

    return {
        "aprobado": True,
        "mensaje": "Solicitud validada correctamente para el Pipeline de la Entrega 2",
        "datos": solicitud.model_dump()
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL — SOLUCIÓN INTEGRAL ENTREGA 1")
    print("="*70)

    datos = {
        "razon_social": "Textiles Norpatagonia",
        "cuit": "30-71234567-8",
        "categoria": "A",
        "facturacion_anual": 180000000.0,
        "tiene_habilitacion": True
    }
    resultado = procesar_entrega_1(datos)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))

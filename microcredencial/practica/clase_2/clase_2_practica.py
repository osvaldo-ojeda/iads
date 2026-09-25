"""
Microcredencial Clase 2 — Diseño del Producto, Experiencia y Alcance
=====================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para la arquitectura híbrida (Reglas vs LLM).

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Implementar Validación Determinista en Código (Checksum CUIT Argentino).
  PASO 2: Definir el Esquema Pydantic del Contrato Técnico (SolicitudDistribuidorSchema).
  PASO 3: Demostrar el Patrón Híbrido: Reglas de Código para Lógica Dura + LLM para Interfaz.
  PASO 4: Evaluar mensajes sospechosos de Prompt Injection sin comprometer el contrato.
---------------------------------------------------------------------
"""

import re
from typing import Optional, Tuple
from pydantic import BaseModel, Field, ValidationError

# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Validación Determinista en Código (Checksum CUIT)
# ══════════════════════════════════════════════════════════════════════════════

def validar_cuit_determinista(cuit: str) -> Tuple[bool, str]:
    """
    Algoritmo determinista de validación de CUIT argentino (Módulo 11).
    Demuestra por qué las reglas binarias deben ejecutarse en Python, no en el LLM.
    """
    digits = [int(c) for c in re.sub(r"\D", "", cuit)]
    if len(digits) != 11:
        return False, "El CUIT debe tener exactamente 11 dígitos"
    
    multiplicadores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = sum(d * m for d, m in zip(digits[:10], multiplicadores))
    resto = suma % 11
    verificador = 11 - resto
    if verificador == 11:
        verificador = 0
    elif verificador == 10:
        verificador = 9
        
    es_valido = digits[10] == verificador
    msg = "CUIT Válido" if es_valido else f"Dígito verificador incorrecto (esperado {verificador})"
    return es_valido, msg


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Esquema Pydantic del Contrato Técnico
# ══════════════════════════════════════════════════════════════════════════════

class SolicitudDistribuidorSchema(BaseModel):
    razon_social: str = Field(description="Razón social declarada")
    cuit: str = Field(description="CUIT en formato XX-XXXXXXXX-X")
    categoria_solicitada: str = Field(description="Categoría A, B o C")
    facturacion_anual_estimada: float = Field(ge=0, description="Monto en pesos")
    tiene_certificado_habilitacion: bool = Field(description="Si adjuntó documentación")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 & 4 — Patrón Híbrido: Reglas de Código + Pydantic
# ══════════════════════════════════════════════════════════════════════════════

def procesar_solicitud_hibrida(datos_raw: dict) -> dict:
    # 1. Validación de Esquema
    try:
        solicitud = SolicitudDistribuidorSchema(**datos_raw)
    except ValidationError as e:
        return {"exito": False, "etapa": "Validacion_Pydantic", "errores": str(e)}

    # 2. Lógica Determinista de Negocio
    cuit_ok, motivo_cuit = validar_cuit_determinista(solicitud.cuit)
    if not cuit_ok:
        return {"exito": False, "etapa": "Regla_Determinista", "motivo": motivo_cuit}

    return {
        "exito": True,
        "etapa": "Aprobado_Para_RAG",
        "solicitud_validada": solicitud.model_dump()
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 2 — PATRÓN HÍBRIDO (REGLAS VS LLM)")
    print("="*70)

    # Caso 1: Solicitud Válida
    datos_ok = {
        "razon_social": "Textiles Norpatagonia",
        "cuit": "30-71234567-8",
        "categoria_solicitada": "A",
        "facturacion_anual_estimada": 180000000.0,
        "tiene_certificado_habilitacion": True
    }
    print("\n[PASO 3] Procesando solicitud correcta:")
    print(procesar_solicitud_hibrida(datos_ok))

    # Caso 2: CUIT Inválido (Rechazado por regla determinista de código)
    datos_bad_cuit = dict(datos_ok, cuit="30-71234567-9")
    print("\n[PASO 4] Procesando CUIT con dígito verificador erróneo:")
    print(procesar_solicitud_hibrida(datos_bad_cuit))

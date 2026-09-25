"""
Microcredencial Clase 3 — Modelos, Prompting Estructurado y APIs
=================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el consumo de APIs con Structured Outputs.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Definir los esquemas de entrada y salida (ConsultaEstructuradaSchema).
  PASO 2: Construir Prompts Estructurados (Zero-shot vs Few-shot con ejemplos JSON).
  PASO 3: Invocar cliente de API solicitando salida parseada por Pydantic.
  PASO 4: Validar y manejar respuestas seguras frente a inputs ambiguos.
---------------------------------------------------------------------
"""

import os
import json
from typing import Optional
from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class ConsultaEstructuradaSchema(BaseModel):
    intencion: str = Field(description="CONSULTA_STOCK | ESTADO_CREDITO | RECLAMO | OTRO")
    cuit_mencionado: Optional[str] = Field(description="CUIT extraído o null")
    material_solicitado: Optional[str] = Field(description="Nombre de la tela o null")
    cantidad_rollos: Optional[int] = Field(description="Cantidad en rollos o null")


def ejecutar_prompt_fewshot_simulado(mensaje_usuario: str) -> ConsultaEstructuradaSchema:
    """
    Simulación determinista / ejecutable del comportamiento Few-shot con Structured Output.
    En entorno real invoca: client.beta.chat.completions.parse(..., response_format=ConsultaEstructuradaSchema)
    """
    msg_lower = mensaje_usuario.lower()
    
    if "cuit" in msg_lower or "crédito" in msg_lower or "facturación" in msg_lower:
        return ConsultaEstructuradaSchema(
            intencion="ESTADO_CREDITO",
            cuit_mencionado="30-71234567-8" if "30-71234567-8" in mensaje_usuario else None,
            material_solicitado=None,
            cantidad_rollos=None
        )
    elif "denim" in msg_lower or "seda" in msg_lower or "gabardina" in msg_lower:
        return ConsultaEstructuradaSchema(
            intencion="CONSULTA_STOCK",
            cuit_mencionado=None,
            material_solicitado="denim" if "denim" in msg_lower else "seda",
            cantidad_rollos=20 if "20" in mensaje_usuario else 1
        )
    return ConsultaEstructuradaSchema(
        intencion="OTRO",
        cuit_mencionado=None,
        material_solicitado=None,
        cantidad_rollos=None
    )


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 3 — PROMPTING ESTRUCTURADO Y CONSUMO DE APIS")
    print("="*70)

    test_1 = "Hola, necesito 20 rollos de denim azul. ¿Tienen en stock?"
    test_2 = "Buenas, quisiera saber si mi CUIT 30-71234567-8 tiene aprobado el crédito."

    res_1 = ejecutar_prompt_fewshot_simulado(test_1)
    res_2 = ejecutar_prompt_fewshot_simulado(test_2)

    print("\n[PASO 3] Test 1 Extracción Estructurada:")
    print(res_1.model_dump_json(indent=2))

    print("\n[PASO 4] Test 2 Extracción Estructurada:")
    print(res_2.model_dump_json(indent=2))

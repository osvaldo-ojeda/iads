"""
Clase 3 — Normalización del Caos y Pydantic (Laboratorio Práctico)
===================================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Este bloque explica la lógica completa paso a paso para el desarrollo.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Cargar credenciales (.env) y esquemas Pydantic de validación.
  PASO 2: Recibir texto no estructurado (ej. correo de un cliente).
  PASO 3: Configurar el cliente del LLM (OpenAI / Anthropic / Gemini).
  PASO 4: Formular System Prompt con el contrato estricto de extracción.
  PASO 5: Invocar el modelo solicitando 'Structured Output' (Pydantic).
  PASO 6: Parsear y validar la respuesta contra el modelo Pydantic.
  PASO 7: Capturar errores de esquema (ValidationError) o fallos de red.
---------------------------------------------------------------------
"""

import os
from dotenv import load_dotenv
from pydantic import ValidationError
from schemas import ConsultaClienteSchema

# PASO 1: Cargar credenciales desde entorno seguro
load_dotenv()

# ── PASO 2: Input no estructurado de prueba ──────────────────────────────
correo = """
Buenas! Soy de Textiles Norpatagonia, CUIT 30-71234567-8.
Necesitamos jersey 40/60 algodón-poliéster en gris melange,
unos 25 rollos. ¿Tienen en filial Córdoba?
"""

# ── PASO 3: Prompt del Sistema (Instrucción de extracción) ────────────────
system_prompt = (
    "Sos un agente de clasificación semántica para Ortelana Textil. "
    "Tu único objetivo es extraer datos estructurados conforme al esquema proporcionado."
)

# ── PASO 4: Configuración del proveedor LLM y Structured Outputs ─────────
#
# Pseudocódigo de invocación a API:
# LLM.generar_con_esquema(
#     mensajes=[system_prompt, correo],
#     esquema_salida=ConsultaClienteSchema
# )

datos_validados = None  # Reemplazar con la llamada al proveedor elegido


# ── PASO 5 y 6: Validación y Procesamiento de Resultados ──────────────────
try:
    if datos_validados is None:
        # Simulación de respuesta para demostración si no hay API key
        print("⚠️ [Modo Explicación] Simulación de respuesta Pydantic validada:")
        datos_validados = ConsultaClienteSchema(
            intencion_principal="stock_sucursal",
            identificador_fiscal="30-71234567-8",
            razon_social_declarada="Textiles Norpatagonia",
            tipo_tela="jersey 40/60",
            color="gris melange",
            filial_mencionada="Córdoba",
            cantidad_estimada=25.0,
            confianza_clasificacion=0.98
        )

    print("\n--- PASO 5: RESULTADO PIPELINE VALIDADO POR PYDANTIC ---")
    print(f"Intención:            {datos_validados.intencion_principal}")
    print(f"Identificador fiscal: {datos_validados.identificador_fiscal}")
    print(f"Razón social:         {datos_validados.razon_social_declarada}")
    print(f"Tipo de tela:         {datos_validados.tipo_tela}")
    print(f"Color:                {datos_validados.color}")
    print(f"Confianza:            {datos_validados.confianza_clasificacion:.2f}")

except ValidationError as e:
    print(f"❌ PASO 6: ERROR — Los datos violaron el schema de Ortelana. Detalles: {e}")
except Exception as e:
    print(f"❌ PASO 6: Falla operativa: {e}")

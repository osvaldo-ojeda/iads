"""
Microcredencial Clase 1 — De una Necesidad a una Oportunidad de Valor
=====================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el diagnóstico de oportunidad de IA.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Capturar mensaje no estructurado del cliente (WhatsApp / Email).
  PASO 2: Simular 'Alucinación en Vivo' (Prompt Ingenuo sin Grounding ni Reglas).
  PASO 3: Auditar la respuesta: identificar alucinaciones factuales de precios/normativas.
  PASO 4: Mapear la Oportunidad de Valor (Estructura PEAS: Performance, Environment, Actuators, Sensors).
  PASO 5: Definir las 3 Señales de Viabilidad para automatizar con IA.
---------------------------------------------------------------------
"""

import json

# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Captura de Mensaje No Estructurado
# ══════════════════════════════════════════════════════════════════════════════

MENSAJE_CLIENTE_ORTELANA = """
Buen día. Soy distribuidor mayorista de Rosario. Mando mis datos:
CUIT 20-12345678-9, categoría B, facturación anual $180M.
Quiero saber si califico para cuenta corriente a 60 días según la
normativa interna de Ortelana. Adjunto certificado de habilitación.
"""

# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 & 3 — Simulación del "Prompt Ingenuo" y Auditoría de Alucinación
# ══════════════════════════════════════════════════════════════════════════════

def simular_alucinacion_llm_sin_grounding(mensaje: str) -> dict:
    """
    Simula la respuesta típica de un LLM aislado (sin RAG ni base de conocimiento)
    al que se le pide responder según la 'normativa interna de Ortelana'.
    """
    # El LLM predecirá texto plausible pero 100% inventado
    respuesta_alucinada = (
        "Estimado cliente de Rosario, según la normativa interna de Ortelana Textil "
        "para distribuidores Categoría B con facturación de $180M, informamos que "
        "la cuenta corriente a 60 días se encuentra APROBADA con un límite de crédito de $5.000.000."
    )
    
    auditoria = {
        "mensaje_recibido": mensaje.strip(),
        "respuesta_generada": respuesta_alucinada,
        "diagnostico_alucinacion": {
            "normativa_verificada": False,
            "motivo": "El LLM no posee la normativa real en su ventana de contexto. Inventó la aprobación.",
            "riesgo_comercial": "ALTO (Se aprobó un crédito sin respaldo documental)"
        }
    }
    return auditoria


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 & 5 — Mapeo PEAS y Ficha de Oportunidad de Valor
# ══════════════════════════════════════════════════════════════════════════════

def generar_ficha_peas_ortelana() -> dict:
    """
    Genera la Ficha PEAS del sistema inteligente de Ortelana Textil.
    
    ¿Qué es PEAS y cómo se relaciona con el Mapa Conceptual de 6 Piezas de la Teoría?
    --------------------------------------------------------------------------------
    PEAS es la sigla académica clásica de IA (Performance, Environment, Actuators, Sensors).
    En el material teórico de la microcredencial, se aborda de forma aplicada mediante
    el 'Mapa Conceptual de 6 Piezas':

    • Performance (Métricas)  ---> Corresponde a 'Salida' y criterios de rendimiento/éxito.
    • Environment (Entorno)   ---> Corresponde a 'Usuario' y 'Entorno operativo' (WhatsApp, ERP).
    • Actuators (Actuadores)  ---> Corresponde a 'Herramientas' (acciones que ejecuta el sistema).
    • Sensors (Sensores)     ---> Corresponde a 'Datos' (información de entrada, CUITs, PDFs).
    """
    return {
        "sistema": "Asistente de Atención Comercial de Ortelana Textil",
        "mapa_conceptual_6_piezas": {
            "1_Usuario (Entorno / Environment)": "Distribuidor mayorista / Equipo administrativo (Canales: WhatsApp/Email/ERP)",
            "2_Datos (Sensores / Sensors)": "Mensajes desestructurados (WhatsApp/Mail), CUITs, PDFs",
            "3_Modelo": "LLM (Simulado)",
            "4_Herramientas (Actuadores / Actuators)": "Respuestas automáticas de chat, Creación de Tickets en ERP",
            "5_Reglas": "Normativa comercial interna y validación de crédito",
            "6_Salida (Performance)": "Respuesta libre de alucinación (Tasa de respuesta < 5 seg)"
        },
        "PEAS_clasico": {
            "Performance (Métricas)": "Tasa de respuesta < 5 seg, 0% alucinación en condiciones comerciales",
            "Environment (Entorno)": "WhatsApp, Correos entrantes, Sistema ERP/SQL de Ortelana",
            "Actuators (Actuadores)": "Respuestas automáticas de chat, Creación de Tickets en ERP",
            "Sensors (Sensores)": "Texto de clientes, CUITs, Fichas de productos, Base ChromaDB"
        },
        "señales_oportunidad": [
            "1. Alto volumen de mensajes no estructurados diarios",
            "2. Reglas de negocio claras pero enterradas en reglamentos",
            "3. Dolor directo de cuello de botella en el equipo administrativo"
        ]
    }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 1 — DIAGNÓSTICO DE OPORTUNIDAD DE IA")
    print("="*70)
    
    res = simular_alucinacion_llm_sin_grounding(MENSAJE_CLIENTE_ORTELANA)
    print("\n[PASO 2 & 3] Auditoría del Prompt Ingenuo:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    peas = generar_ficha_peas_ortelana()
    print("\n[PASO 4 & 5] Ficha PEAS de Oportunidad:")
    print(json.dumps(peas, indent=2, ensure_ascii=False))

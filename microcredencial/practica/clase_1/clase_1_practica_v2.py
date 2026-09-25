"""
Microcredencial Clase 1 (v2 — Conexión Real a API / .env)
=====================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

📌 PASOS Y OBJETIVO DE ESTA VERSIÓN V2:
---------------------------------------------------------------------
1. Lee las llaves de API desde el archivo `.env` (Gemini, OpenAI o Groq).
2. Si encuentra una API Key real, realiza la consulta en vivo al modelo de IA.
3. Si no encuentra API Key en el entorno, ejecuta el modo simulación 
   sin romper el código y explicando cómo configurar el archivo `.env`.
4. Audita la respuesta obtenida (detectando alucinaciones por falta de grounding).
5. Genera la Ficha PEAS de oportunidad de valor.
---------------------------------------------------------------------
"""

import os
import json
import ssl
import urllib.request
import urllib.error

# Contexto SSL sin verificación estricta para prevenir errores de certificados en macOS
try:
    ssl_context = ssl._create_unverified_context()
except AttributeError:
    ssl_context = ssl.create_default_context()

# ══════════════════════════════════════════════════════════════════════════════
# CARGA AUTOMÁTICA DE ARCHIVO .ENV (Sin librerías externas obligatorias)
# ══════════════════════════════════════════════════════════════════════════════

def cargar_env_local():
    """
    Lee el archivo .env de la carpeta actual y carga las variables en os.environ
    usando Python nativo (100% estándar, sin requerir librerías externas ni pip).
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

# Cargar variables de entorno al iniciar
cargar_env_local()

# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Mensaje de prueba no estructurado
# ══════════════════════════════════════════════════════════════════════════════

MENSAJE_CLIENTE_ORTELANA = """
Buen día. Soy distribuidor mayorista de Rosario. Mando mis datos:
CUIT 20-12345678-9, categoría B, facturación anual $180M.
Quiero saber si califico para cuenta corriente a 60 días según la
normativa interna de Ortelana. Adjunto certificado de habilitación.
"""

# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 & 3 — Conexión a APIs Reales (Gemini / OpenAI) y Auditoría
# ══════════════════════════════════════════════════════════════════════════════

def llamar_gemini_api(prompt: str, api_key: str) -> str:
    """Invoca la API gratuita de Google Gemini usando urllib (nativo en Python)."""
    modelos = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
    
    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req, context=ssl_context) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue
            
    raise RuntimeError("No se pudo conectar con los servidores de Google Gemini.")


def llamar_openai_api(prompt: str, api_key: str) -> str:
    """Invoca la API de OpenAI usando urllib (nativo en Python)."""
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    })
    
    with urllib.request.urlopen(req, context=ssl_context) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"]


def ejecutar_prompt_ingenuo_con_llm(mensaje: str) -> dict:
    """
    Envía el mensaje del cliente a un LLM real (si hay API Key en .env)
    o ejecuta la simulación si no hay API Key configurada.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    prompt_ingenuo = f"""
    Sos el asistente de atención comercial de la empresa Ortelana Textil.
    Un cliente te envía este mensaje:
    "{mensaje}"

    Por favor, respondé indicando si califica o no a la cuenta corriente a 60 días
    según la normativa interna de Ortelana Textil.
    """

    origen_respuesta = "SIMULACIÓN (Sin API Key)"
    respuesta_texto = ""

    try:
        if gemini_key and gemini_key != "tu_api_key_de_gemini_aqui":
            origen_respuesta = "API REAL — Google Gemini (gemini-2.0-flash)"
            respuesta_texto = llamar_gemini_api(prompt_ingenuo, gemini_key)
        elif openai_key and openai_key != "sk-tu_api_key_de_openai_aqui":
            origen_respuesta = "API REAL — OpenAI (gpt-4o-mini)"
            respuesta_texto = llamar_openai_api(prompt_ingenuo, openai_key)
        else:
            origen_respuesta = "SIMULACIÓN (No se encontró API Key válida en el archivo .env)"
            respuesta_texto = (
                "Estimado cliente de Rosario, según la normativa interna de Ortelana Textil "
                "para distribuidores Categoría B con facturación de $180M, informamos que "
                "la cuenta corriente a 60 días se encuentra APROBADA con un límite de crédito de $5.000.000."
            )
    except Exception as e:
        origen_respuesta = f"ERROR AL LLAMAR A LA API ({type(e).__name__}): {e}"
        respuesta_texto = "Error de conexión con el proveedor de IA."

    return {
        "mensaje_recibido": mensaje.strip(),
        "proveedor_ejecutado": origen_respuesta,
        "respuesta_generada_por_llm": respuesta_texto.strip(),
        "diagnostico_alucinacion": {
            "normativa_verificada": False,
            "motivo": "El LLM no posee el reglamento real de Ortelana en su ventana de contexto. Inventó o supuso la regla.",
            "riesgo_comercial": "ALTO (Riesgo de aprobar/rechazar créditos sin sustento documental)"
        }
    }


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 & 5 — Mapeo PEAS y Ficha de Oportunidad de Valor
# ══════════════════════════════════════════════════════════════════════════════

def generar_ficha_peas_ortelana() -> dict:
    """
    Genera la Ficha PEAS del sistema inteligente de Ortelana Textil.
    
    ¿Qué es PEAS y cómo se relaciona con el Mapa Conceptual de 6 Piezas de la Teoría?
    --------------------------------------------------------------------------------
    PEAS es la sigla académica clásica de IA (Performance, Environment, Actuators, Sensors).
    En la teoría de la microcredencial se presenta de forma aplicada como el 'Mapa Conceptual de 6 Piezas':

    • Performance (Métricas)  ---> Corresponde a 'Salida' y criterios de éxito.
    • Environment (Entorno)   ---> Corresponde a 'Usuario' y entorno (WhatsApp, ERP).
    • Actuators (Actuadores)  ---> Corresponde a 'Herramientas' (crear tickets, responder).
    • Sensors (Sensores)     ---> Corresponde a 'Datos' (mensajes, CUITs, PDFs).
    """
    return {
        "sistema": "Asistente de Atención Comercial de Ortelana Textil",
        "mapa_conceptual_6_piezas": {
            "1_Usuario (Entorno / Environment)": "Distribuidor mayorista / Equipo administrativo (Canales: WhatsApp/Email/ERP)",
            "2_Datos (Sensores / Sensors)": "Mensajes desestructurados (WhatsApp/Mail), CUITs, PDFs",
            "3_Modelo": "LLM (Simulado o Gemini/OpenAI)",
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
    print("MICROCREDENCIAL CLASE 1 v2 — CONSUMO DE API REAL Y DIAGNÓSTICO")
    print("="*70)
    
    # 1. Auditoría
    res = ejecutar_prompt_ingenuo_con_llm(MENSAJE_CLIENTE_ORTELANA)
    print("\n[PASO 2 & 3] Auditoría del Prompt (Conexión / Simulación):")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    
    # Aviso si está corriendo en modo simulación
    if "SIMULACIÓN" in res["proveedor_ejecutado"]:
        print("\n" + "⚠️ "*25)
        print("NOTA DOCENTE / ALUMNO: Actualmente estás corriendo en MODO SIMULACIÓN.")
        print("Para conectar una IA real (ej: Gemini gratis):")
        print("  1. Duplicá el archivo '.env.example' y renombralo a '.env'")
        print("  2. Colocá tu GEMINI_API_KEY obtenida gratis en https://aistudio.google.com")
        print("⚠️ "*25)

    # 2. PEAS
    peas = generar_ficha_peas_ortelana()
    print("\n[PASO 4 & 5] Ficha PEAS de Oportunidad:")
    print(json.dumps(peas, indent=2, ensure_ascii=False))

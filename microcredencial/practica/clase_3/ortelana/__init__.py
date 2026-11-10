"""
Ortelana Textil — componente de extracción del onboarding de distribuidores.

Módulos (uno por responsabilidad):
    config.py     → variables de entorno (.env) y proveedor de LLM disponible
    contrato.py   → contrato de datos (Pydantic): qué debe devolver el LLM
    llm.py        → llamada a la API real (Gemini / OpenAI / Groq) con reintentos
    reglas.py     → reglas de negocio deterministas (dígito verificador del CUIT)
    extractor.py  → el flujo completo: mensaje → LLM → json.loads → Pydantic → reglas
"""

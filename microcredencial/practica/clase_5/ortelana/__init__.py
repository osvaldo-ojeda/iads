"""
Ortelana Textil — workflow de onboarding de distribuidores (Clase 4).

Módulos (uno por responsabilidad):
    config.py       → variables de entorno (.env) y proveedor de LLM disponible     (Clase 3)
    contrato.py     → contrato de datos (Pydantic): qué debe devolver el LLM          (Clase 3)
    llm.py          → llamada a la API real, ahora con modo JSON o texto              (Clase 3 + cambio)
    extractor.py    → pasos 2, 4 y 5: mensaje → LLM → json.loads → Pydantic → CUIT    (Clase 3)
    reglas.py       → reglas de negocio: CUIT + NOR-DOC, NOR-CAT, NOR-NUEVO, NOR-DEUDA (Clase 3 + nuevas)
    herramientas.py → paso 7: consultar el sistema de gestión (una tool)              (nuevo)
    redactor.py     → paso 11: el LLM redacta la respuesta (con plantilla de respaldo) (nuevo)
    workflow.py     → la secuencia completa, con los puntos de control                (nuevo)
    cadena_lcel.py  → OPCIONAL: el paso 2 como cadena de LangChain                   (nuevo)
"""

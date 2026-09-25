"""
Clase 11 — Despliegue de Sistemas de IA con FastAPI
====================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Configurar Formateador de Logs Estructurados (JSONFormatter) para auditoría de requests HTTP.
  PASO 2: Definir Esquemas Pydantic de Contrato de API (ConsultaRequest, ConsultaResponse, HealthResponse).
  PASO 3: Inicializar servidor FastAPI con Middleware de Tracing y captura de tiempos (duracion_ms).
  PASO 4: Definir Endpoints de la API:
          - GET /health (Health Check de servicio)
          - POST /consultar (Invocación al Agente Multiagente con thread_id)
          - GET /estado/{thread_id} (Inspección de memoria de sesión)
  PASO 5: Desplegar el servidor HTTP mediante Uvicorn.
---------------------------------------------------------------------
"""

import time
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Optional, List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

try:
    from clase_10_practica import construir_sistema_multiagente, EstadoOrtelana
    _sistema = construir_sistema_multiagente()
    SISTEMA_ACTIVO = True
except ImportError:
    _sistema = None
    SISTEMA_ACTIVO = False

load_dotenv()


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Logger Estructurado en JSON
# ══════════════════════════════════════════════════════════════════════════════

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        return json.dumps(log_data, ensure_ascii=False)


def crear_logger(nombre: str) -> logging.Logger:
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    return logger


logger = crear_logger("ortelana_api")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Schemas Pydantic de Contrato
# ══════════════════════════════════════════════════════════════════════════════

class ConsultaRequest(BaseModel):
    pregunta: str = Field(description="Consulta del cliente")
    thread_id: str = Field(description="ID de sesión para memoria persistente")

class ConsultaResponse(BaseModel):
    respuesta: str
    thread_id: str
    herramientas_usadas: List[str]
    duracion_ms: int
    exito: bool = True

class EstadoResponse(BaseModel):
    thread_id: str
    mensajes: List[dict]
    cuit_identificado: Optional[str]
    sucursal_preferida: Optional[str]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — FastAPI App y Middleware de Tracing
# ══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="Ortelana Textil — API Agente IA", version="1.0.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    inicio = time.time()
    response = await call_next(request)
    duracion_ms = int((time.time() - inicio) * 1000)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duracion_ms}ms)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url.path}: {exc}")
    return JSONResponse(status_code=500, content={"error": "Error interno del servidor", "detalle": str(exc)})


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    return {"status": "ok", "sistema_activo": SISTEMA_ACTIVO}

@app.post("/consultar", response_model=ConsultaResponse)
async def consultar_agente(request: ConsultaRequest):
    inicio = time.time()
    if not SISTEMA_ACTIVO or _sistema is None:
        raise HTTPException(status_code=503, detail="Sistema multiagente no activo")

    config = {"configurable": {"thread_id": request.thread_id}}
    resultado = _sistema.invoke({"messages": [HumanMessage(content=request.pregunta)]}, config=config)
    duracion = int((time.time() - inicio) * 1000)

    return ConsultaResponse(
        respuesta=resultado["messages"][-1].content,
        thread_id=request.thread_id,
        herramientas_usadas=resultado.get("herramientas_usadas", []),
        duracion_ms=duracion
    )


@app.get("/estado/{thread_id}", response_model=EstadoResponse)
async def obtener_estado(thread_id: str):
    if not SISTEMA_ACTIVO or _sistema is None:
        raise HTTPException(status_code=503, detail="Sistema multiagente no activo")

    config = {"configurable": {"thread_id": thread_id}}
    estado = _sistema.get_state(config)

    if not estado or not estado.values:
        raise HTTPException(status_code=404, detail=f"No se encontró sesión con thread_id: {thread_id}")

    valores = estado.values
    mensajes = [{"rol": type(m).__name__, "contenido": m.content} for m in valores.get("messages", [])]

    return EstadoResponse(
        thread_id=thread_id,
        mensajes=mensajes,
        cuit_identificado=valores.get("cuit_identificado"),
        sucursal_preferida=valores.get("sucursal_preferida"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

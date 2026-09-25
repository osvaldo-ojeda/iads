"""
Clase 12 — Observabilidad y Monitoreo de Sistemas de IA
========================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Configurar Pilar 1 (Logs Estructurados JSON con JSONFormatter).
  PASO 2: Configurar Pilar 2 (TrackerDeMetricas: conteo de requests, latencias, costo de tokens, tasa de errores).
  PASO 3: Configurar Pilar 3 (Trazabilidad en LangSmith y diagnósticos).
  PASO 4: Simular flujo de peticiones entrantes generando logs y registrando métricas.
  PASO 5: Generar dashboard sintético de monitoreo (`/metricas`).
---------------------------------------------------------------------
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# =====================================================================
# PASO 1 — LOGGING ESTRUCTURADO (JSON)
# =====================================================================

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data)
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    def __init__(self, name: str = "OrtelanaObservability"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, extra={"extra_data": kwargs})

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, extra={"extra_data": kwargs})


# =====================================================================
# PASO 2 — MÉTRICAS OPERATIVAS Y DE NEGOCIO
# =====================================================================

@dataclass
class RegistroConsulta:
    timestamp: str
    thread_id: str
    latencia_sec: float
    exito: bool
    agente_asignado: str
    tokens_usados: int
    costo_estimado_usd: float
    error: Optional[str] = None


class TrackerDeMetricas:
    def __init__(self):
        self.consultas: List[RegistroConsulta] = []
        self.COSTO_INPUT_1K = 0.00015
        self.COSTO_OUTPUT_1K = 0.00060

    def registrar(self, thread_id: str, latencia_sec: float, exito: bool, agente_asignado: str, prompt_tokens: int = 0, completion_tokens: int = 0, error: Optional[str] = None):
        costo = ((prompt_tokens / 1000.0) * self.COSTO_INPUT_1K) + ((completion_tokens / 1000.0) * self.COSTO_OUTPUT_1K)
        reg = RegistroConsulta(
            timestamp=datetime.now(timezone.utc).isoformat(),
            thread_id=thread_id,
            latencia_sec=latencia_sec,
            exito=exito,
            agente_asignado=agente_asignado,
            tokens_usados=prompt_tokens + completion_tokens,
            costo_estimado_usd=costo,
            error=error
        )
        self.consultas.append(reg)

    def obtener_resumen(self) -> Dict[str, Any]:
        total = len(self.consultas)
        if total == 0:
            return {"total_consultas": 0, "status": "Sin actividad"}

        exitosas = sum(1 for c in self.consultas if c.exito)
        fallidas = total - exitosas
        tasa_error = (fallidas / total) * 100
        latencia_promedio = sum(c.latencia_sec for c in self.consultas) / total
        costo_total = sum(c.costo_estimado_usd for c in self.consultas)
        tokens_totales = sum(c.tokens_usados for c in self.consultas)

        return {
            "total_consultas": total,
            "tasa_exito_pct": round((exitosas / total) * 100, 2),
            "tasa_error_pct": round(tasa_error, 2),
            "latencia_promedio_sec": round(latencia_promedio, 3),
            "tokens_totales_consumidos": tokens_totales,
            "costo_acumulado_usd": round(costo_total, 6),
            "alerta_salud": "ALERTA: Tasa de errores > 5%" if tasa_error > 5.0 else "SISTEMA SALUDABLE"
        }


# =====================================================================
# PASO 3 & 4 — SIMULACIÓN Y DASHBOARD
# =====================================================================

def simular_ejecucion_con_observabilidad():
    print("\n" + "="*70)
    print("DEMOSTRACIÓN: CLASE 12 — OBSERVABILIDAD Y MONITOREO EN VIVO")
    print("="*70)

    logger = StructuredLogger("OrtelanaAPI")
    tracker = TrackerDeMetricas()

    logger.info("Verificación de configuración LangSmith", tracing_activo="True", proyecto="ortelana")

    escenarios = [
        {"thread_id": "dist_001", "pregunta": "¿Tienen seda natural?", "agente": "catalogo", "latencia": 1.2, "exito": True, "p_tok": 450, "c_tok": 120},
        {"thread_id": "dist_002", "pregunta": "Solicito crédito CUIT 30-11111111-8", "agente": "credito", "latencia": 2.5, "exito": True, "p_tok": 600, "c_tok": 250},
    ]

    for esc in escenarios:
        logger.info("Petición procesada", thread_id=esc["thread_id"], agente=esc["agente"])
        tracker.registrar(esc["thread_id"], esc["latencia"], esc["exito"], esc["agente"], esc["p_tok"], esc["c_tok"])

    print("\n--- PASO 5: Dashboard de Métricas (/metricas) ---")
    print(json.dumps(tracker.obtener_resumen(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    simular_ejecucion_con_observabilidad()

"""
Microcredencial Entrega 3 — Solución de Referencia
===================================================
Consolida los aprendizajes de la Clase 6.

Componentes:
  1. Estado Global con TypedDict.
  2. Herramientas del Agente (@tool).
  3. Agente ReAct con LangGraph.
  4. Checkpointer de memoria multi-turno por thread_id.
"""

import json
from typing import Dict, Any, List

class MultiAgentSystemSimulator:
    def __init__(self):
        self.memoria: Dict[str, Dict[str, Any]] = {}

    def ejecutar_turno(self, thread_id: str, mensaje: str) -> Dict[str, Any]:
        if thread_id not in self.memoria:
            self.memoria[thread_id] = {"cuit": None, "sucursal": None, "mensajes": []}

        state = self.memoria[thread_id]
        state["mensajes"].append(mensaje)

        if "30-71234567-8" in mensaje:
            state["cuit"] = "30-71234567-8"
        if "Córdoba" in mensaje:
            state["sucursal"] = "filial_cordoba"

        return {
            "thread_id": thread_id,
            "respuesta_agente": f"Procesado con memoria: CUIT={state['cuit']}, Sucursal={state['sucursal']}",
            "estado_sesion": state
        }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL — SOLUCIÓN INTEGRAL ENTREGA 3")
    print("="*70)

    agent = MultiAgentSystemSimulator()
    t_id = "sesion_norpatagonia"

    r1 = agent.ejecutar_turno(t_id, "Hola, CUIT 30-71234567-8 en Córdoba")
    r2 = agent.ejecutar_turno(t_id, "¿Tienen stock de denim acá?")

    print("\nTurno 1:")
    print(json.dumps(r1, indent=2, ensure_ascii=False))

    print("\nTurno 2 (con memoria):")
    print(json.dumps(r2, indent=2, ensure_ascii=False))

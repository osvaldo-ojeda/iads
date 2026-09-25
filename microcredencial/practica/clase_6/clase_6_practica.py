"""
Microcredencial Clase 6 — Agentes, Estado y Decisiones Controladas
=====================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el control de estado y memoria en Agentes.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Definir el Estado Global Persistente por Thread ID (Messages, CUIT, Sucursal).
  PASO 2: Implementar el Ciclo ReAct (Thought -> Tool Execution -> Observation).
  PASO 3: Mantener Memoria Multi-turno usando Checkpointer de Estado.
  PASO 4: Demostrar que el agente recuerda preferencias en mensajes subsecuentes.
---------------------------------------------------------------------
"""

from typing import Dict, Any, List

class AgentStateMemorySimulator:
    """
    Simulador de memoria de estado persistente por thread_id (LangGraph Pattern).
    """
    def __init__(self):
        self.sesiones: Dict[str, Dict[str, Any]] = {}

    def procesar_mensaje(self, thread_id: str, mensaje: str) -> str:
        if thread_id not in self.sesiones:
            self.sesiones[thread_id] = {
                "historial": [],
                "cuit": None,
                "sucursal": None
            }

        sesion = self.sesiones[thread_id]
        sesion["historial"].append(mensaje)

        # Detectar CUIT
        if "30-71234567-8" in mensaje:
            sesion["cuit"] = "30-71234567-8"
        if "Córdoba" in mensaje:
            sesion["sucursal"] = "filial_cordoba"

        # Respuesta usando memoria
        if "acá" in mensaje or "stock" in mensaje:
            sucursal_str = sesion["sucursal"] if sesion["sucursal"] else "todas las filiales"
            cuit_str = f" para el CUIT {sesion['cuit']}" if sesion['cuit'] else ""
            return f"Verificando stock en {sucursal_str}{cuit_str}. ¡Stock disponible de denim!"

        return f"Hola, recibí tu mensaje. CUIT registrado: {sesion['cuit']} | Sucursal: {sesion['sucursal']}"


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 6 — AGENTES Y MEMORIA DE ESTADO PERSISTENTE")
    print("="*70)

    sim = AgentStateMemorySimulator()
    t_id = "sesion_distribuidor_001"

    print("\n[Turno 1] Presentación:")
    print(sim.procesar_mensaje(t_id, "Hola, soy de Textiles Norpatagonia, CUIT 30-71234567-8 en Córdoba."))

    print("\n[Turno 2] Pregunta usando contexto previo ('acá'):")
    print(sim.procesar_mensaje(t_id, "¿Tienen stock de denim disponible acá?"))

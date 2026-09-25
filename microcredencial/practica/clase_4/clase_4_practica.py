"""
Microcredencial Clase 4 — Diseño de Workflows y Orquestación Básica
=====================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el ensamble de flujos de trabajo (LCEL).

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Diseñar las etapas del Workflow: Clasificación -> Enrutamiento -> Formateo.
  PASO 2: Construir el Prompt del Orquestador LCEL.
  PASO 3: Definir la cadena secuencial con componentes Runnable.
  PASO 4: Ejecutar pipeline simulando entradas de clientes para validar la orquestación.
---------------------------------------------------------------------
"""

from typing import Dict, Any

class LCELWorkflowPipeline:
    """
    Simulación conceptual de un pipeline de orquestación LCEL.
    Conecta el paso de clasificación con el motor de generación.
    """
    def __init__(self):
        self.rutas = {
            "CONSULTA_STOCK": "Agente_Catalogo",
            "ESTADO_CREDITO": "Agente_Financiero",
            "RECLAMO": "Agente_Calidad"
        }

    def procesar(self, entrada: Dict[str, Any]) -> Dict[str, Any]:
        intencion = entrada.get("intencion", "OTRO")
        agente_destino = self.rutas.get(intencion, "Agente_General")
        
        # Generar respuesta según la ruta asignada
        if agente_destino == "Agente_Catalogo":
            respuesta = f"Verificando stock para {entrada.get('material_solicitado', 'material')} ({entrada.get('cantidad_rollos', 1)} rollos)..."
        elif agente_destino == "Agente_Financiero":
            respuesta = f"Consultando estado de cuenta para CUIT {entrada.get('cuit_mencionado')}..."
        else:
            respuesta = "Derivando su mensaje a un representante general."

        return {
            "intencion_detectada": intencion,
            "agente_asignado": agente_destino,
            "respuesta_generada": respuesta
        }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 4 — DISEÑO DE WORKFLOWS Y ORQUESTACIÓN BÁSICA")
    print("="*70)

    pipeline = LCELWorkflowPipeline()

    input_1 = {"intencion": "CONSULTA_STOCK", "material_solicitado": "denim", "cantidad_rollos": 25}
    input_2 = {"intencion": "ESTADO_CREDITO", "cuit_mencionado": "30-71234567-8"}

    print("\n[PASO 4] Resultado Ejecución Workflow 1:")
    print(pipeline.procesar(input_1))

    print("\n[PASO 4] Resultado Ejecución Workflow 2:")
    print(pipeline.procesar(input_2))

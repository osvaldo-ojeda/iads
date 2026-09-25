"""
Clase 14 — Ciclo de Vida de Sistemas de IA (AIOps, MLflow, Drift)
===============================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para el análisis y ejecución del script.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Implementar Registro A/B Testing de Prompts (PromptRegistryAB por hash de thread_id).
  PASO 2: Implementar Wrapper MLflow real (mlflow.start_run / log_params / log_metrics)
          para el RAG Grid Search (Tracking de métricas RAGAS).
  PASO 3: Implementar Detector de Data Drift real: embebe la consulta con OpenAI y mide
          la distancia contra la colección ChromaDB del Súper-Catálogo (Clase 5).
  PASO 4: Demostrar pipeline de optimización AIOps y prevención de degradación.
---------------------------------------------------------------------
"""

import os
import json
from typing import Dict, List, Any, Tuple

import mlflow
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

RUTA_VECTORDB = "./ortelana_vectordb_c5"
COLECCION_ORTELANA = "super_catalogo_ortelana"


# =====================================================================
# PASO 1 — VERSIONADO DE PROMPTS Y A/B TESTING
# =====================================================================

class PromptRegistryAB:
    PROMPTS = {
        "v1_baseline": """Sos el orquestador de Ortelana Textil. Decidí el subagente: catalogo | credito | reclamos | general.""",
        "v2_fewshot": """Sos el orquestador de Ortelana Textil.
Ejemplos:
- '¿Tienen lino?' -> catalogo
- 'CUIT 30-11111111-8 saldo' -> credito
Agentes: catalogo | credito | reclamos | general."""
    }

    @classmethod
    def obtener_prompt_ab(cls, thread_id: str) -> Tuple[str, str]:
        hash_val = abs(hash(thread_id)) % 100
        if hash_val < 20:
            return cls.PROMPTS["v2_fewshot"], "v2_fewshot"
        return cls.PROMPTS["v1_baseline"], "v1_baseline"


# =====================================================================
# PASO 2 — EXPERIMENTACIÓN CON MLFLOW (RAG GRID SEARCH)
# =====================================================================

class MLflowRAGTracker:
    def __init__(self, experiment_name: str = "Ortelana_RAG_Optimization"):
        self.experiment_name = experiment_name
        mlflow.set_experiment(experiment_name)

    def log_experiment(self, run_name: str, params: Dict[str, Any], metrics: Dict[str, float]):
        with mlflow.start_run(run_name=run_name):
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)

    def obtener_tabla_comparativa(self) -> List[Dict[str, Any]]:
        experimento = mlflow.get_experiment_by_name(self.experiment_name)
        runs_df = mlflow.search_runs(experiment_ids=[experimento.experiment_id])
        columnas = [c for c in runs_df.columns if c.startswith("params.") or c.startswith("metrics.") or c == "tags.mlflow.runName"]
        return runs_df[columnas].to_dict("records")


# =====================================================================
# PASO 3 — DETECTOR DE DATA DRIFT EN CONSULTAS (distancia vectorial real)
# =====================================================================

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-3-small",
)


class DataDriftDetector:
    @staticmethod
    def calcular_distancia_coleccion(consulta: str) -> float:
        """Distancia real (L2/coseno según config de la colección) entre la
        consulta y el vecino más cercano del Súper-Catálogo de Clase 5."""
        cliente = chromadb.PersistentClient(path=RUTA_VECTORDB)
        coleccion = cliente.get_collection(COLECCION_ORTELANA, embedding_function=openai_ef)
        resultado = coleccion.query(query_texts=[consulta], n_results=1)
        return resultado["distances"][0][0]

    @classmethod
    def evaluar_batch_consultas(cls, consultas: List[str], umbral: float = 0.4) -> Dict[str, Any]:
        distancias = [cls.calcular_distancia_coleccion(c) for c in consultas]
        distancia_media = sum(distancias) / len(distancias) if distancias else 0.0
        distancias_sorted = sorted(distancias)
        p90_idx = int(0.9 * len(distancias_sorted))
        distancia_p90 = distancias_sorted[min(p90_idx, len(distancias_sorted) - 1)]

        drift_detectado = distancia_p90 > umbral

        return {
            "num_consultas": len(consultas),
            "distancia_media": round(distancia_media, 3),
            "distancia_p90": round(distancia_p90, 3),
            "umbral": umbral,
            "drift_detectado": drift_detectado,
            "recomendacion": "ALERTA: Actualizar catálogo vectorizado" if drift_detectado else "OK: Base en rango"
        }


# =====================================================================
# PASO 4 — DEMOSTRACIÓN DEL PIPELINE AIOPS
# =====================================================================

def ejecutar_demo_aiops():
    print("\n" + "="*70)
    print("DEMOSTRACIÓN: CLASE 14 — CICLO DE VIDA AIOps Y MLFLOW")
    print("="*70)

    # 1. A/B Testing
    print("\n--- PASO 1: A/B Testing por Hash ---")
    p, var = PromptRegistryAB.obtener_prompt_ab("dist_001")
    print(f"Thread dist_001 asignado a [{var}]")

    # 2. MLflow Experiments
    print("\n--- PASO 2: Experimentos MLflow ---")
    tracker = MLflowRAGTracker()
    tracker.log_experiment("exp_medium_chunks", {"chunk_size": 500, "k": 3}, {"score_compuesto": 0.84})
    print(json.dumps(tracker.obtener_tabla_comparativa(), indent=2, ensure_ascii=False, default=str))

    # 3. Data Drift (requiere el índice de Clase 5 ya construido)
    print("\n--- PASO 3: Detección de Data Drift ---")
    res_drift = DataDriftDetector.evaluar_batch_consultas(["¿Venden tela elastizada de lycra para trajes de baño?"])
    print("Resultado:", json.dumps(res_drift, ensure_ascii=False))


if __name__ == "__main__":
    ejecutar_demo_aiops()

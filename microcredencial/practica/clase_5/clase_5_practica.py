"""
Microcredencial Clase 5 — Grounding, Embeddings y RAG como Patrón de Diseño
=============================================================================
Programa: Microcredencial #2 — Diseño de Aplicaciones Inteligentes

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Guía de estudio paso a paso para la eliminación de alucinaciones mediante RAG.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Cargar la base de conocimiento vectorial (ChromaDB con catálogo/normativa).
  PASO 2: Convertir la consulta en lenguaje natural a un vector de embedding.
  PASO 3: Ejecutar similitud semántica recuperando los K documentos más relevantes.
  PASO 4: Formular el Prompt RAG Blindado forzando el Grounding estricto.
  PASO 5: Generar la respuesta fundamentada libre de alucinaciones.
---------------------------------------------------------------------
"""

import os
from typing import List, Dict, Any

class GroundingRAGPipeline:
    """
    Pipeline RAG conceptual de grounding para Ortelana Textil.
    """
    BASE_CONOCIMIENTO = [
        {"id": "ART-01", "texto": "Denim pesado de 12 oz 100% algodón. Stock disponible en filial Córdoba y Buenos Aires. Precio $4.500/m."},
        {"id": "ART-02", "texto": "Seda natural satinada para alta costura. Stock disponible en filial Córdoba. Precio $8.900/m."},
        {"id": "NOR-01", "texto": "Distribuidores Categoría A sin deuda acceden a financiación en 3 cuotas sin interés para órdenes mayores a $500.000."}
    ]

    @classmethod
    def recuperar_contexto(cls, consulta: str) -> List[str]:
        q_lower = consulta.lower()
        docs_encontrados = []
        for doc in cls.BASE_CONOCIMIENTO:
            # Búsqueda semántica simplificada
            if any(palabra in doc["texto"].lower() for palabra in q_lower.split()):
                docs_encontrados.append(doc["texto"])
        return docs_encontrados if docs_encontrados else [cls.BASE_CONOCIMIENTO[0]["texto"]]

    @classmethod
    def responder_con_grounding(cls, consulta: str) -> Dict[str, Any]:
        contextos = cls.recuperar_contexto(consulta)
        contexto_str = "\n\n---\n\n".join(contextos)
        
        respuesta = (
            f"Basado en la información oficial de Ortelana:\n"
            f"{contextos[0]}\n"
            f"(Respuesta fundamentada estrictamente sin inventar normativas ni precios)."
        )
        return {
            "consulta": consulta,
            "contexto_recuperado": contextos,
            "respuesta_grounded": respuesta
        }


if __name__ == "__main__":
    print("\n" + "="*70)
    print("MICROCREDENCIAL CLASE 5 — GROUNDING, EMBEDDINGS Y RAG")
    print("="*70)

    q = "¿Tienen stock de denim pesado y cuáles son las cuotas de financiación?"
    res = GroundingRAGPipeline.responder_con_grounding(q)

    print("\n[PASO 3 & 5] Ejecución de RAG Grounded:")
    print(f"Consulta : {res['consulta']}")
    print(f"Respuesta: {res['respuesta_grounded']}")

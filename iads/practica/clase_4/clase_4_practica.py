"""
Clase 4 — Embeddings y Búsqueda Semántica (Práctica Guiada)
===========================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 PSEUDOCÓDIGO Y PASOS DEL ALGORITMO
=====================================================================
Este bloque explica el flujo conceptual de la búsqueda vectorial.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Calcular la Similitud Coseno entre dos vectores en 2D (Demostración).
  PASO 2: Cargar el Catálogo de Telas con sus 'descripciones semánticas'.
  PASO 3: Convertir las descripciones textuales a Embeddings mediante OpenAI.
  PASO 4: Indexar la matriz de embeddings en una estructura FAISS (IndexFlatL2).
  PASO 5: Recibir una consulta del cliente (ej: "tela impermeable para camión").
  PASO 6: Vectorizar la consulta y buscar las K coincidencias más cercanas en FAISS.
  PASO 7: Demostrar las limitaciones de FAISS (falta de pre-filtering nativo).
---------------------------------------------------------------------
"""

import os
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Similitud coseno manual (del pizarrón al código)
# ══════════════════════════════════════════════════════════════════════════════

def similitud_coseno(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    producto_escalar = np.dot(vec_a, vec_b)
    magnitud_a = np.linalg.norm(vec_a)
    magnitud_b = np.linalg.norm(vec_b)
    return producto_escalar / (magnitud_a * magnitud_b)


def demo_pizarron():
    print("=" * 60)
    print("DEMO — Similitud coseno en 2D")
    print("=" * 60)

    lona_alta_densidad = np.array([5, 1])   # resistente, rígida
    consulta_cliente   = np.array([4, 2])   # "lona rígida para toldos"
    seda_natural       = np.array([1, 8])   # delicada, muy flexible

    sim_lona_consulta = similitud_coseno(lona_alta_densidad, consulta_cliente)
    sim_seda_consulta = similitud_coseno(seda_natural,       consulta_cliente)

    print(f"\nConsulta: 'Busco lona rígida para toldos' → vector {consulta_cliente.tolist()}")
    print(f"\n  Lona Alta Densidad  {lona_alta_densidad.tolist()} → similitud = {sim_lona_consulta:.3f}")
    print(f"  Seda Natural        {seda_natural.tolist()} → similitud = {sim_seda_consulta:.3f}")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — El catálogo de Ortelana Textil
# ══════════════════════════════════════════════════════════════════════════════

CATALOGO_ORTELANA = [
    {
        "id": "TELA-001",
        "descripcion_semantica": (
            "Denim pesado de 12 oz, 100% algodón rígido con teñido índigo intenso. "
            "Tacto rústico, alta resistencia al roce y cuerpo firme. "
            "Ideal para camperas y pantalones de trabajo."
        ),
        "metadatos": {
            "linea_textil": "indumentaria",
            "sucursal": "central_bsas",
            "en_stock": True,
            "tags_regionales": ["jean", "vaquero", "mezclilla", "ropa de trabajo"],
        },
    },
    {
        "id": "TELA-002",
        "descripcion_semantica": (
            "Seda natural con acabado satinado, caída fluida y brillo sofisticado. "
            "Tejido muy liviano y fresco al tacto, diseñado para vestidos de gala."
        ),
        "metadatos": {
            "linea_textil": "alta_costura",
            "sucursal": "filial_cordoba",
            "en_stock": True,
            "tags_regionales": ["seda", "satén", "vestido de fiesta"],
        },
    },
    {
        "id": "TELA-003",
        "descripcion_semantica": (
            "Lona cobertora industrial con recubrimiento de PVC impermeable. "
            "Entramado de poliéster de alta tenacidad, nula flexibilidad y máxima resistencia al agua."
        ),
        "metadatos": {
            "linea_textil": "industrial",
            "sucursal": "central_bsas",
            "en_stock": False,
            "tags_regionales": ["toldo", "carpa", "pvc", "camión"],
        },
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 & 4 — Generar embeddings con OpenAI y construir el índice FAISS
# ══════════════════════════════════════════════════════════════════════════════

INDEX_FILE = "ortelana_catalogo_c4.index"


def obtener_embeddings(textos: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=textos,
    )
    return [item.embedding for item in response.data]


def construir_o_cargar_indice() -> faiss.IndexFlatL2:
    textos = [art["descripcion_semantica"] for art in CATALOGO_ORTELANA]

    if not os.path.exists(INDEX_FILE):
        embeddings = obtener_embeddings(textos)
        matriz = np.array(embeddings, dtype="float32")

        dimension = matriz.shape[1]
        indice = faiss.IndexFlatL2(dimension)
        indice.add(matriz)

        faiss.write_index(indice, INDEX_FILE)
        print(f"✅ Índice guardado en '{INDEX_FILE}' ({indice.ntotal} artículos)")
    else:
        print(f"\n💾 Cargando índice desde '{INDEX_FILE}' (0 tokens consumidos)")
        indice = faiss.read_index(INDEX_FILE)

    return indice


# ══════════════════════════════════════════════════════════════════════════════
# PASO 5 & 6 — Búsqueda Semántica
# ══════════════════════════════════════════════════════════════════════════════

def buscar_semantico(indice: faiss.IndexFlatL2, consulta: str, k: int = 2) -> None:
    print(f"\n🔍 Consulta: '{consulta}'")
    vector_consulta = np.array(obtener_embeddings([consulta]), dtype="float32")
    distancias, indices = indice.search(vector_consulta, k)

    for i, (dist, idx) in enumerate(zip(distancias[0], indices[0])):
        art = CATALOGO_ORTELANA[idx]
        stock = "✅ En stock" if art["metadatos"]["en_stock"] else "❌ Sin stock"
        print(f"\n  {i+1}. [{art['id']}] Distancia L2: {dist:.4f}")
        print(f"     {art['descripcion_semantica'][:90]}...")


if __name__ == "__main__":
    demo_pizarron()
    indice = construir_o_cargar_indice()
    buscar_semantico(indice, "Necesito una tela abrigada y gruesa para camperas")

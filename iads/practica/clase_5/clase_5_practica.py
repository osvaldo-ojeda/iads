"""
Clase 5 — Persistencia y Bases de Datos Vectoriales con ChromaDB
================================================================
Desarrollo de Sistemas de Inteligencia Artificial (IADS 3)

=====================================================================
📌 GUÍA DOCENTE: PSEUDOCÓDIGO Y EXPLICACIÓN PASO A PASO
=====================================================================
Este bloque permite al docente explicar la arquitectura de persistencia
y filtrado híbrido en ChromaDB sin necesidad de hacer live coding.

ALGORITMO EN PSEUDOCÓDIGO:
---------------------------------------------------------------------
  PASO 1: Ejecutar ETL sobre catálogos JSON para normalizar esquemas e IDs.
  PASO 2: Realizar Purga Semántica eliminando duplicados mediante distancia coseno.
  PASO 3: Inicializar cliente ChromaDB (PersistentClient) en ruta local.
  PASO 4: Cargar o actualizar (upsert) el Súper-Catálogo en la colección.
  PASO 5: Demostrar actualización en caliente de metadatos (ej: cambio de stock).
  PASO 6: Ejecutar Motor de Búsqueda Híbrida (Pre-filtering por Metadatos + Similitud).
  PASO 7: Evaluar 'Killer Queries' simulando consultas reales de clientes por WhatsApp.
---------------------------------------------------------------------
"""

import json
import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ── Función de embeddings compartida ──────────────────────────────────────────
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-3-small",
)

RUTA_VECTORDB = "./ortelana_vectordb_c5"


# ══════════════════════════════════════════════════════════════════════════════
# PASO 1 — ETL: unificar catálogos con inconsistencias
# ══════════════════════════════════════════════════════════════════════════════

def etl_unificar_catalogos(directorio_entregas: str) -> list[dict]:
    """
    Lee todos los JSON del directorio, normaliza estructuras y resuelve
    la colisión de IDs prefijando con el ID del grupo.
    """
    catalogo_unificado = []
    archivos = list(Path(directorio_entregas).glob("*.json"))

    for i, archivo in enumerate(archivos, start=1):
        grupo_id = f"G{i}"
        with open(archivo, encoding="utf-8") as f:
            telas = json.load(f)

        for tela in telas:
            tela["id"] = f"{grupo_id}-{tela['id']}"
            meta = tela.get("metadatos", {})

            if isinstance(meta.get("en_stock"), str):
                meta["en_stock"] = meta["en_stock"].strip().lower() == "true"

            if "sucursal" in meta and "sucursal_disponible" not in meta:
                meta["sucursal_disponible"] = meta.pop("sucursal")
            if "stock_disponible" in meta:
                meta["en_stock"] = meta.pop("stock_disponible")
            if "tags" in meta and "tags_regionales" not in meta:
                meta["tags_regionales"] = meta.pop("tags")

            catalogo_unificado.append(tela)

    print(f"✅ ETL completado: {len(catalogo_unificado)} telas unificadas")
    return catalogo_unificado


# ══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Purga semántica de casi-duplicados
# ══════════════════════════════════════════════════════════════════════════════

def purgar_duplicados_semanticos(
    catalogo: list[dict],
    umbral_duplicado: float = 0.08,
) -> list[dict]:
    """
    Detecta y elimina casi-duplicados usando similitud semántica.
    """
    client_purga = chromadb.Client()
    col_purga = client_purga.create_collection(
        "purga_tmp",
        embedding_function=openai_ef,
    )

    textos = [t["descripcion_semantica"] for t in catalogo]
    ids = [t["id"] for t in catalogo]

    col_purga.add(documents=textos, ids=ids)
    ids_a_eliminar: set[str] = set()

    for tela in catalogo:
        if tela["id"] in ids_a_eliminar:
            continue

        resultados = col_purga.query(
            query_texts=[tela["descripcion_semantica"]],
            n_results=3,
        )

        for id_similar, distancia in zip(
            resultados["ids"][0][1:],
            resultados["distances"][0][1:],
        ):
            if distancia < umbral_duplicado:
                print(f"🔍 Casi-duplicado detectado (dist={distancia:.4f}): {id_similar}")
                ids_a_eliminar.add(id_similar)

    super_catalogo = [t for t in catalogo if t["id"] not in ids_a_eliminar]
    return super_catalogo


# ══════════════════════════════════════════════════════════════════════════════
# PASO 3 — El Súper-Catálogo de Ortelana (Estructura con Metadatos)
# ══════════════════════════════════════════════════════════════════════════════

SUPER_CATALOGO_ORTELANA = [
    {
        "id": "TELA-001",
        "descripcion_semantica": (
            "Denim pesado de 12 oz, 100% algodón rígido con teñido índigo intenso. "
            "Tacto rústico, alta resistencia al roce y cuerpo firme. "
            "Ideal para camperas y pantalones de trabajo."
        ),
        "metadatos": {
            "linea_textil": "indumentaria",
            "sucursal_disponible": "central_buenos_aires",
            "en_stock": True,
            "tags_regionales": ["jean", "vaquero", "mezclilla"],
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
            "sucursal_disponible": "filial_cordoba",
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
            "sucursal_disponible": "central_buenos_aires",
            "en_stock": False,
            "tags_regionales": ["toldo", "carpa", "pvc", "camión"],
        },
    },
    {
        "id": "TELA-004",
        "descripcion_semantica": (
            "Gabardina elastizada de 8 oz. Mezcla de algodón y spandex que otorga "
            "comodidad sin perder estructura. Textura diagonal clásica, ideal para pantalones de vestir."
        ),
        "metadatos": {
            "linea_textil": "indumentaria",
            "sucursal_disponible": "filial_cordoba",
            "en_stock": True,
            "tags_regionales": ["pantalón de vestir", "uniforme", "elastizado"],
        },
    },
    {
        "id": "TELA-005",
        "descripcion_semantica": (
            "Gasa de algodón translúcida y ultra respirable. "
            "Ideal para prendas de verano muy sueltas y superposiciones. Requiere lavado a mano."
        ),
        "metadatos": {
            "linea_textil": "alta_costura",
            "sucursal_disponible": "central_buenos_aires",
            "en_stock": False,
            "tags_regionales": ["transparencia", "verano", "liviano", "velo"],
        },
    },
    {
        "id": "TELA-006",
        "descripcion_semantica": (
            "Chenille de tapicería aterciopelado. Tejido grueso con tratamiento antimanchas, "
            "diseñado para soportar el roce constante en muebles de interior."
        ),
        "metadatos": {
            "linea_textil": "tapiceria",
            "sucursal_disponible": "filial_cordoba",
            "en_stock": True,
            "tags_regionales": ["sillón", "funda", "terciopelo", "decoración"],
        },
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# PASO 4 & 5 — Crear la colección ChromaDB y Actualizaciones en Caliente
# ══════════════════════════════════════════════════════════════════════════════

def inicializar_chromadb() -> chromadb.Collection:
    chroma_client = chromadb.PersistentClient(path=RUTA_VECTORDB)

    coleccion = chroma_client.get_or_create_collection(
        name="super_catalogo_ortelana",
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"},
    )

    if coleccion.count() == 0:
        print("Cargando el Súper-Catálogo en ChromaDB...")
        coleccion.upsert(
            documents=[t["descripcion_semantica"] for t in SUPER_CATALOGO_ORTELANA],
            metadatas=[t["metadatos"] for t in SUPER_CATALOGO_ORTELANA],
            ids=[t["id"] for t in SUPER_CATALOGO_ORTELANA],
        )
        print(f"✅ Súper-Catálogo cargado: {coleccion.count()} telas indexadas")
    else:
        print(f"✅ Colección ya existente: {coleccion.count()} telas (0 tokens)")

    return coleccion


def actualizar_stock(coleccion: chromadb.Collection, tela_id: str, nuevo_stock: bool) -> None:
    actual = coleccion.get(ids=[tela_id])
    doc_actual = actual["documents"][0]
    meta_actual = actual["metadatas"][0]
    meta_actual["en_stock"] = nuevo_stock

    coleccion.upsert(
        ids=[tela_id],
        documents=[doc_actual],
        metadatas=[meta_actual],
    )
    print(f"✅ [{tela_id}] stock actualizado a {nuevo_stock}")


# ══════════════════════════════════════════════════════════════════════════════
# PASO 6 & 7 — Motor de búsqueda híbrida y Killer Queries
# ══════════════════════════════════════════════════════════════════════════════

def buscar_tela(
    coleccion: chromadb.Collection,
    query_semantica: str,
    filtro_sucursal: str = "cualquiera",
    solo_con_stock: bool = True,
    n_resultados: int = 2,
) -> None:
    condiciones = []
    if solo_con_stock:
        condiciones.append({"en_stock": {"$eq": True}})
    if filtro_sucursal != "cualquiera":
        condiciones.append({"sucursal_disponible": {"$eq": filtro_sucursal}})

    where = None if not condiciones else (condiciones[0] if len(condiciones) == 1 else {"$and": condiciones})

    resultados = coleccion.query(
        query_texts=[query_semantica],
        n_results=n_resultados,
        where=where,
    )

    print(f"\n🔍 Búsqueda: '{query_semantica}' (sucursal={filtro_sucursal}, solo_stock={solo_con_stock})")
    if not resultados["documents"][0]:
        print("❌ Sin resultados con estos filtros.")
        return

    for doc, dist, meta, id_ in zip(
        resultados["documents"][0],
        resultados["distances"][0],
        resultados["metadatas"][0],
        resultados["ids"][0],
    ):
        stock_emoji = "✅" if meta["en_stock"] else "❌"
        print(f"  [{id_}] dist={dist:.4f} {stock_emoji} | {doc[:80]}...")


if __name__ == "__main__":
    coleccion = inicializar_chromadb()
    actualizar_stock(coleccion, "TELA-001", nuevo_stock=False)
    buscar_tela(coleccion, "Busco algo fresco para vestido en Córdoba", filtro_sucursal="filial_cordoba")
    actualizar_stock(coleccion, "TELA-001", nuevo_stock=True)

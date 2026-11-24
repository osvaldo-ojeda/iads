"""
La base de conocimiento: embeddings + base vectorial (ChromaDB), armada con LangChain.

RAG tiene dos momentos:

    [OFFLINE · una vez]   corpus JSON → Document → embedding → ChromaDB (se guarda en disco)
                          indexar()

    [ONLINE · cada vez]   consulta → embedding → los k más parecidos → ¿superan el umbral?
                          buscar()

Se usa para dos bases distintas:
    "normativa" → datos/corpus_normativa.json   (la usa el workflow para CONSULTA_NORMATIVA)
    "telas"     → datos/catalogo_telas.json     (demo del teórico: el stock está fuera del MVP)

Los embeddings se calculan EN LA COMPU, sin API key, con un modelo entrenado para español
(jina-embeddings-v2-base-es). La primera vez se descarga (~640 MB) y queda guardado.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from .config import RAIZ_PROYECTO

MODELO_EMBEDDINGS = os.getenv("EMBEDDINGS_MODEL", "jinaai/jina-embeddings-v2-base-es")
CACHE_MODELOS = Path.home() / ".cache" / "fastembed"
CARPETA_INDICE = RAIZ_PROYECTO / "indice_chroma"

K = 3                   # cuántos fragmentos se recuperan
UMBRAL_SIMILITUD = 0.35  # por debajo de esto, "no tenemos información oficial"
# Calibrado con este corpus y este modelo: lo que SÍ está en la normativa da 0.38 o más; lo que no
# está (criptomonedas, horarios) da 0.30-0.32. Si se cambia el modelo de embeddings, hay que recalibrarlo.

CORPUS = {
    "normativa": RAIZ_PROYECTO / "datos" / "corpus_normativa.json",
    "telas": RAIZ_PROYECTO / "datos" / "catalogo_telas.json",
}

logging.getLogger("chromadb").setLevel(logging.ERROR)


# ── Embeddings: texto → vector ───────────────────────────────────────────────

class EmbeddingsLocales(Embeddings):
    """
    Convierte texto en un vector de 768 números. Textos con significado parecido → vectores cercanos.
    Implementa la interfaz Embeddings de LangChain: así ChromaDB (o cualquier base de LangChain) lo puede usar.
    Con API key se podría cambiar por GoogleGenerativeAIEmbeddings sin tocar el resto del código.
    """

    def __init__(self, modelo: str = MODELO_EMBEDDINGS):
        from fastembed import TextEmbedding  # import acá: solo se carga si se usa
        self.modelo = modelo
        self._modelo = TextEmbedding(modelo, cache_dir=str(CACHE_MODELOS))

    def embed_documents(self, textos: list[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self._modelo.embed(textos)]

    def embed_query(self, texto: str) -> list[float]:
        return self.embed_documents([texto])[0]


_embeddings: Optional[EmbeddingsLocales] = None


def obtener_embeddings() -> EmbeddingsLocales:
    """El modelo tarda unos segundos en cargar: se carga una sola vez y se reutiliza."""
    global _embeddings
    if _embeddings is None:
        _embeddings = EmbeddingsLocales()
    return _embeddings


# ── OFFLINE: del corpus a la base vectorial ─────────────────────────────────

def cargar_corpus(nombre: str) -> list[Document]:
    """
    Cada elemento del JSON pasa a ser un Document de LangChain:
        page_content → descripcion_semantica  (lo que se convierte en embedding)
        metadata     → metadatos              (lo que se filtra de forma exacta)
    El "chunking" ya está hecho: cada documento del corpus es una unidad de sentido (una regla, una tela).
    """
    corpus = json.loads(CORPUS[nombre].read_text(encoding="utf-8"))
    return [
        Document(
            id=doc["id"],
            page_content=doc["descripcion_semantica"],
            metadata={"id": doc["id"], "titulo": doc["titulo"], **doc["metadatos"]},
        )
        for doc in corpus
    ]


def _huella(nombre: str) -> str:
    """Si el corpus o el modelo cambian, la huella cambia y hay que volver a indexar."""
    contenido = CORPUS[nombre].read_bytes() + MODELO_EMBEDDINGS.encode()
    return hashlib.sha256(contenido).hexdigest()[:16]


def _cliente(en_memoria: bool):
    ajustes = Settings(anonymized_telemetry=False)
    if en_memoria:
        return chromadb.EphemeralClient(settings=ajustes)
    return chromadb.PersistentClient(path=str(CARPETA_INDICE), settings=ajustes)


def indexar(nombre: str, en_memoria: bool = False) -> Chroma:
    """PASO OFFLINE: calcula el embedding de cada documento y lo guarda en ChromaDB."""
    cliente = _cliente(en_memoria)
    try:
        cliente.delete_collection(nombre)
    except Exception:
        pass  # no existía
    base = Chroma(
        client=cliente,
        collection_name=nombre,
        embedding_function=obtener_embeddings(),
        collection_metadata={"hnsw:space": "cosine", "huella": _huella(nombre)},  # similitud coseno
    )
    base.add_documents(cargar_corpus(nombre))
    return base


def abrir(nombre: str, en_memoria: bool = False) -> Chroma:
    """
    Abre la base guardada en disco. Si no existe, o si el corpus cambió, la indexa primero.
    En la vida real la indexación es un proceso aparte (`python app.py indexar`).
    """
    if not en_memoria:
        cliente = _cliente(en_memoria=False)
        try:
            coleccion = cliente.get_collection(nombre)
            if (coleccion.metadata or {}).get("huella") == _huella(nombre):
                return Chroma(client=cliente, collection_name=nombre, embedding_function=obtener_embeddings())
        except Exception:
            pass  # no existe todavía
        print(f"  ⚙️  Indexando '{nombre}' (paso OFFLINE: se hace una vez y queda en indice_chroma/)...")
    return indexar(nombre, en_memoria)


# ── ONLINE: buscar por significado ───────────────────────────────────────────

def buscar(base: Chroma, consulta: str, k: int = K, filtro: Optional[dict] = None,
           umbral: float = UMBRAL_SIMILITUD) -> list[Document]:
    """
    PASO ONLINE: la consulta se convierte en embedding y se traen los k documentos más cercanos.

    Devuelve los k candidatos con dos datos agregados en metadata:
        "similitud"     → de 0 a 1 (similitud coseno: 1 = mismo significado)
        "supera_umbral" → si es lo bastante parecido como para usarlo

    `filtro` es el FILTRADO HÍBRIDO: una condición exacta sobre los metadatos que se combina
    con la búsqueda semántica. Ejemplo: {"vigente": True} descarta las reglas derogadas.
    """
    resultados = base.similarity_search_with_relevance_scores(consulta, k=k, filter=filtro)
    documentos = []
    for doc, similitud in resultados:
        doc.metadata = {**doc.metadata, "similitud": round(similitud, 2), "supera_umbral": similitud >= umbral}
        documentos.append(doc)
    return documentos

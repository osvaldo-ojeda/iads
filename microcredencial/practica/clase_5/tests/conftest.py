"""Configuración común de las pruebas: nunca llaman a una API, aunque haya un .env con key."""

import pytest

import ortelana.extractor
import ortelana.rag
import ortelana.redactor


@pytest.fixture(autouse=True)
def sin_api(monkeypatch):
    """Los LLM se simulan siempre. Los embeddings no usan API: corren en la compu igual."""
    for modulo in (ortelana.extractor, ortelana.redactor, ortelana.rag):
        monkeypatch.setattr(modulo, "detectar_proveedor", lambda: None)
    monkeypatch.setattr(ortelana.rag, "_cadena", None)  # que la cadena RAG se arme con el modelo simulado

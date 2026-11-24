"""
Pruebas del RAG: la búsqueda semántica, el filtro por metadato, el umbral y la cadena.
No usan ninguna API. La primera vez descargan el modelo de embeddings (~640 MB).

    python -m pytest tests/test_rag.py -v
"""

import pytest

from ortelana import base_conocimiento as bc
from ortelana.rag import SIN_INFORMACION, crear_cadena_rag
from ortelana.workflow import workflow_onboarding

SOLO_VIGENTES = {"vigente": True}
CONSULTA_NORMATIVA = ('{"intencion": "CONSULTA_NORMATIVA", "razon_social": null, "cuit": null, '
                      '"facturacion_anual": null, "plazo_solicitado_dias": null, '
                      '"categoria_solicitada": null, "documentos_mencionados": []}')


@pytest.fixture(scope="module")
def normativa():
    return bc.abrir("normativa", en_memoria=True)


@pytest.fixture(scope="module")
def telas():
    return bc.abrir("telas", en_memoria=True)


def _primero(base, consulta, filtro=SOLO_VIGENTES):
    return bc.buscar(base, consulta, filtro=filtro)[0]


# ── Ingesta (offline) ────────────────────────────────────────────────────────

def test_cada_documento_del_corpus_tiene_texto_y_al_menos_dos_metadatos():
    for nombre in ("normativa", "telas"):
        for doc in bc.cargar_corpus(nombre):
            assert doc.page_content
            assert len(doc.metadata) - 2 >= 2      # además de id y titulo


def test_el_corpus_de_normativa_tiene_entre_10_y_15_documentos():
    assert 10 <= len(bc.cargar_corpus("normativa")) <= 15


# ── Recuperación (online): busca por significado ─────────────────────────────

@pytest.mark.parametrize("consulta, regla", [
    ("¿El flete a Córdoba lo pagan ustedes?", "NOR-ZONA"),
    ("¿Quién se hace cargo del transporte de la mercadería hasta Mendoza?", "NOR-ZONA"),
    ("¿Qué papeles necesito para tener cuenta corriente?", "NOR-DOC"),
    ("¿Tienen cuotas sin interés?", "NOR-01"),
    ("Debo plata hace dos meses, ¿me siguen vendiendo a plazo?", "NOR-DEUDA"),
    ("¿Quién aprueba mi solicitud?", "NOR-APROB"),
    ("¿Cuánto crédito me dan en categoría B?", "NOR-CAT-B"),
])
def test_recupera_la_regla_correcta(normativa, consulta, regla):
    doc = _primero(normativa, consulta)
    assert doc.metadata["id"] == regla
    assert doc.metadata["supera_umbral"]


@pytest.mark.parametrize("consulta", [
    "¿Aceptan pagos con criptomonedas?",
    "¿Cuál es el horario de atención del local?",
])
def test_lo_que_no_esta_en_la_normativa_no_supera_el_umbral(normativa, consulta):
    assert not any(d.metadata["supera_umbral"] for d in bc.buscar(normativa, consulta, filtro=SOLO_VIGENTES))


# ── Filtrado híbrido: significado + metadato ─────────────────────────────────

def test_sin_filtro_aparece_la_regla_derogada_primero(normativa):
    """Por eso hace falta el filtro: la versión vieja de NOR-ZONA es la MÁS parecida a la pregunta."""
    doc = _primero(normativa, "¿El flete a Córdoba lo pagan ustedes?", filtro=None)
    assert doc.metadata["vigente"] is False


def test_con_filtro_nunca_aparece_una_regla_derogada(normativa):
    for consulta in ("¿El flete a Córdoba lo pagan ustedes?", "¿Tienen cuotas sin interés?",
                     "¿Cuánto crédito me dan en categoría B?"):
        assert all(d.metadata["vigente"] for d in bc.buscar(normativa, consulta, filtro=SOLO_VIGENTES))


def test_telas_busca_por_significado_y_filtra_por_stock(telas):
    assert _primero(telas, "busco algo fresco para un vestido de verano", filtro=None).metadata["titulo"] == "Lino natural"
    abrigada = "Necesito una tela abrigada y gruesa para camperas de invierno"
    assert _primero(telas, abrigada, filtro=None).metadata["en_stock"] is False
    assert all(d.metadata["en_stock"] for d in bc.buscar(telas, abrigada, filtro={"en_stock": True}))


# ── La cadena RAG (plantilla | modelo | parser, con el recuperador adelante) ─

def test_la_cadena_responde_citando_la_regla(normativa):
    cadena, origen = crear_cadena_rag(base=normativa)
    r = cadena.invoke("¿El flete a Córdoba lo pagan ustedes?")
    assert "NOR-ZONA" in r["respuesta"]
    assert origen.startswith("SIMULACIÓN")


def test_si_nada_supera_el_umbral_no_inventa(normativa):
    cadena, _ = crear_cadena_rag(base=normativa)
    assert cadena.invoke("¿Aceptan pagos con criptomonedas?")["respuesta"] == SIN_INFORMACION


# ── El RAG dentro del workflow ───────────────────────────────────────────────

def test_consulta_normativa_se_responde_con_fuentes():
    r = workflow_onboarding("¿El flete a Córdoba lo pagan ustedes?", CONSULTA_NORMATIVA)
    assert r["estado"] == "RESPONDIDA"
    assert r["respuesta"]["fuentes"][0] == "NOR-ZONA"
    assert any(p["tipo"] == "RAG" for p in r["traza"])


def test_consulta_sin_respuesta_se_deriva_sin_inventar():
    r = workflow_onboarding("¿Aceptan pagos con criptomonedas?", CONSULTA_NORMATIVA)
    assert r["estado"] == "DERIVADO"
    assert r["respuesta"]["texto"].startswith(SIN_INFORMACION)

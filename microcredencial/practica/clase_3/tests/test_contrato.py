"""
Pruebas del contrato y de las reglas. No llaman a ninguna API: corren siempre, gratis.

    python -m pytest            (desde la carpeta clase_3)
"""

import pytest

from ortelana.extractor import aplicar_reglas, validar_respuesta
from ortelana.reglas import validar_cuit


# ── Contrato (Pydantic) ──────────────────────────────────────────────────────

def test_respuesta_correcta_cumple_el_contrato():
    r = validar_respuesta('{"intencion": "ALTA_DISTRIBUIDOR", "cuit": "30-71589632-6", "facturacion_anual": 95000000}')
    assert r["ok"]
    assert r["extraccion"]["facturacion_anual"] == 95000000


def test_campos_ausentes_quedan_en_null():
    r = validar_respuesta('{"intencion": "FUERA_DE_ALCANCE"}')
    assert r["ok"]
    assert r["extraccion"]["cuit"] is None
    assert r["extraccion"]["documentos_mencionados"] == []


@pytest.mark.parametrize("texto", [
    '¡Claro! Acá tenés los datos: {"intencion": "ALTA_DISTRIBUIDOR"}',
    '```json\n{"intencion": "ALTA_DISTRIBUIDOR"}\n```',
    "",
])
def test_texto_que_no_es_json_es_error_de_formato(texto):
    assert validar_respuesta(texto)["error"] == "FORMATO"


@pytest.mark.parametrize("texto", [
    '{"intencion": "APROBAR_VIP_ORO"}',                                  # intención fuera de la Matriz
    '{"intencion": "ALTA_DISTRIBUIDOR", "cuit": "30715896326"}',         # CUIT sin guiones
    '{"intencion": "ALTA_DISTRIBUIDOR", "facturacion_anual": "mucha"}',  # número como texto
    '{"intencion": "ALTA_DISTRIBUIDOR", "documentos_mencionados": ["DNI"]}',  # documento inexistente
    '["ALTA_DISTRIBUIDOR"]',                                             # JSON pero no es un objeto
])
def test_json_que_no_cumple_el_contrato_es_error_de_contrato(texto):
    assert validar_respuesta(texto)["error"] == "CONTRATO"


# ── Reglas de negocio ────────────────────────────────────────────────────────

@pytest.mark.parametrize("cuit", ["30-71589632-6"])
def test_cuit_valido(cuit):
    assert validar_cuit(cuit)[0]


@pytest.mark.parametrize("cuit", ["20-12345678-9", "20-34556789-2", "30-71234567-8"])
def test_cuit_con_digito_verificador_incorrecto(cuit):
    assert not validar_cuit(cuit)[0]


def test_cuit_bien_formado_pero_invalido_lo_frena_la_regla_no_el_contrato():
    r = validar_respuesta('{"intencion": "ALTA_DISTRIBUIDOR", "cuit": "20-12345678-9"}')
    assert r["ok"]                                   # Pydantic lo deja pasar: el formato es correcto
    assert aplicar_reglas(r["extraccion"])["error"] == "REGLA"   # la regla lo frena


def test_sin_cuit_la_regla_no_falla():
    assert aplicar_reglas({"cuit": None})["ok"]

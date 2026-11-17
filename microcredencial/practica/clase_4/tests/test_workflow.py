"""
Pruebas de las reglas, la herramienta y el workflow. No llaman a ninguna API: corren siempre, gratis.

    python -m pytest            (desde la carpeta clase_4)
"""

import json

import pytest

import ortelana.extractor
import ortelana.redactor
from ortelana.config import RAIZ_PROYECTO
from ortelana.herramientas import consultar_sistema_gestion
from ortelana.reglas import determinar_condiciones, normalizar_categoria, verificar_documentacion
from ortelana.workflow import registrar_decision, workflow_onboarding

NUEVO = {"es_cliente": False, "antiguedad_meses": 0, "dias_deuda_vencida": 0}
LOTE = json.loads((RAIZ_PROYECTO / "datos" / "lote_prueba.json").read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def sin_api(monkeypatch):
    """Aunque haya un .env con key, las pruebas usan siempre la simulación."""
    monkeypatch.setattr(ortelana.extractor, "detectar_proveedor", lambda: None)
    monkeypatch.setattr(ortelana.redactor, "detectar_proveedor", lambda: None)


# ── Reglas: categoría, plazo y límite ────────────────────────────────────────

@pytest.mark.parametrize("facturacion, categoria", [
    (50_000_000, "C"),
    (80_000_000, "C"),         # el borde: "hasta $80M" incluye los 80M
    (80_000_001, "B"),
    (300_000_000, "B"),        # "hasta $300M" incluye los 300M
])
def test_categoria_segun_facturacion(facturacion, categoria):
    assert determinar_condiciones(facturacion, NUEVO)["categoria"] == categoria


def test_nuevo_que_factura_como_a_entra_en_b():
    r = determinar_condiciones(450_000_000, NUEVO, plazo_solicitado_dias=60)
    assert r["categoria"] == "B"
    assert "NOR-NUEVO" in r["reglas_aplicadas"]
    assert r["plazo_dias"] == 30             # pidió 60, el máximo de B es 30


def test_cliente_con_menos_de_12_meses_no_llega_a_a():
    cliente = {"es_cliente": True, "antiguedad_meses": 7, "dias_deuda_vencida": 0}
    assert determinar_condiciones(400_000_000, cliente)["categoria"] == "B"


def test_cliente_antiguo_que_factura_como_a():
    cliente = {"es_cliente": True, "antiguedad_meses": 18, "dias_deuda_vencida": 0}
    r = determinar_condiciones(400_000_000, cliente, plazo_solicitado_dias=60)
    assert (r["categoria"], r["plazo_dias"], r["limite_credito"]) == ("A", 60, 15_000_000)


def test_deuda_vencida_suspende_la_cuenta_corriente():
    cliente = {"es_cliente": True, "antiguedad_meses": 30, "dias_deuda_vencida": 45}
    r = determinar_condiciones(120_000_000, cliente, plazo_solicitado_dias=30)
    assert not r["cuenta_corriente"]
    assert r["plazo_dias"] == 0 and r["limite_credito"] == 0
    assert "NOR-DEUDA" in r["reglas_aplicadas"]


def test_categoria_c_no_tiene_cuenta_corriente():
    assert not determinar_condiciones(50_000_000, NUEVO, plazo_solicitado_dias=30)["cuenta_corriente"]


# ── Reglas: documentación y categoría pedida ────────────────────────────────

def test_documentacion_faltante():
    assert verificar_documentacion(["CONSTANCIA_ARCA", "HABILITACION"]) == ["INGRESOS_BRUTOS"]
    assert verificar_documentacion(["CONSTANCIA_ARCA", "HABILITACION", "INGRESOS_BRUTOS"]) == []


@pytest.mark.parametrize("texto, esperado", [
    ("categoría B", "B"), ("la A", "A"), ("c", "C"), ("VIP Oro", None), ("Premium", None), (None, None),
])
def test_normalizar_categoria(texto, esperado):
    assert normalizar_categoria(texto) == esperado


# ── Herramienta ─────────────────────────────────────────────────────────────

def test_herramienta_encuentra_cliente_existente():
    r = consultar_sistema_gestion("30-71402587-9")
    assert r["es_cliente"] and r["antiguedad_meses"] == 18


def test_herramienta_con_cuit_desconocido_devuelve_nuevo():
    assert consultar_sistema_gestion("30-70845123-8") == NUEVO


# ── Workflow: cada caso del lote termina en el estado esperado ──────────────

@pytest.mark.parametrize("caso", LOTE, ids=[c["tipo"] for c in LOTE])
def test_lote_termina_en_el_estado_esperado(caso):
    assert workflow_onboarding(caso["mensaje"], caso["simulacion"])["estado"] == caso["estado_esperado"]


def _caso(tipo: str) -> dict:
    caso = next(c for c in LOTE if c["tipo"] == tipo)
    return workflow_onboarding(caso["mensaje"], caso["simulacion"])


def test_cuit_invalido_se_detiene_antes_de_consultar_el_sistema():
    r = _caso("CUIT inválido")
    pasos = [p["paso"] for p in r["traza"]]
    assert "7" not in pasos and "8" not in pasos       # no siguió con datos no confiables


def test_manipulacion_no_aprueba_y_deja_alerta():
    r = _caso("Manipulación")
    assert r["estado"] == "PENDIENTE"
    assert any("VIP Oro" in a for a in r["alertas"])


def test_falla_de_formato_va_a_revision_humana():
    r = workflow_onboarding("hola", '¡Claro! {"intencion": "ALTA_DISTRIBUIDOR"}')
    assert r["estado"] == "REVISION_HUMANA"


def test_ningun_alta_se_aprueba_sin_una_persona():
    """NOR-APROB: el workflow nunca termina en APROBADA por sí solo."""
    for caso in LOTE:
        assert workflow_onboarding(caso["mensaje"], caso["simulacion"])["estado"] != "APROBADA"


def test_aprobacion_humana_y_respuesta():
    r = registrar_decision(_caso("Completo (B)"), aprobada=True, aprobador="Jefe de Administración")
    assert r["estado"] == "APROBADA"
    assert "categoría B" in r["respuesta"]["texto"] and "NOR-CAT-B" in r["respuesta"]["texto"]


def test_rechazo_necesita_motivo():
    with pytest.raises(ValueError):
        registrar_decision(_caso("Completo (B)"), aprobada=False, aprobador="Jefe de Administración")


def test_no_se_puede_aprobar_lo_que_no_esta_pendiente_de_aprobacion():
    with pytest.raises(ValueError):
        registrar_decision(_caso("CUIT inválido"), aprobada=True, aprobador="Jefe de Administración")

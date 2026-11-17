"""
Reglas de negocio deterministas: si entra X, siempre sale Y.
Por eso las ejecuta Python y NO el LLM.

Cada función implementa una regla de la normativa (../clase_2/ortelana_normativa_comercial.md)
y devuelve el CÓDIGO de la regla que aplicó, para que el legajo y la respuesta puedan citarla.

    Clase 3: validar_cuit                  → dígito verificador (módulo 11)
    Clase 4: verificar_documentacion       → NOR-DOC
             normalizar_categoria          → ¿la categoría pedida existe? ("VIP Oro" no)
             determinar_condiciones        → NOR-CAT-A/B/C, NOR-NUEVO, NOR-DEUDA
"""

import re
from typing import Optional

# ── Constantes de la normativa (un solo lugar para cambiarlas) ──────────────

MULTIPLICADORES_CUIT = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]

DOCUMENTOS_OBLIGATORIOS = ("CONSTANCIA_ARCA", "HABILITACION", "INGRESOS_BRUTOS")  # NOR-DOC

TOPE_CATEGORIA_C = 80_000_000      # NOR-CAT-C: hasta $80M
TOPE_CATEGORIA_B = 300_000_000     # NOR-CAT-B: más de $80M y hasta $300M
ANTIGUEDAD_MINIMA_A = 12           # NOR-CAT-A: al menos 12 meses como cliente
DIAS_DEUDA_MAXIMOS = 30            # NOR-DEUDA: más de 30 días vencida → solo contado

CONDICIONES_POR_CATEGORIA = {
    "A": {"plazo_maximo_dias": 60, "limite_credito": 15_000_000, "regla": "NOR-CAT-A"},
    "B": {"plazo_maximo_dias": 30, "limite_credito": 5_000_000, "regla": "NOR-CAT-B"},
    "C": {"plazo_maximo_dias": 0, "limite_credito": 0, "regla": "NOR-CAT-C"},
}


# ── Clase 3 ──────────────────────────────────────────────────────────────────

def validar_cuit(cuit: str) -> tuple[bool, str]:
    """Algoritmo de validación del CUIT argentino (módulo 11). Devuelve (es_valido, motivo)."""
    digitos = [int(c) for c in re.sub(r"\D", "", cuit)]
    if len(digitos) != 11:
        return False, "El CUIT debe tener exactamente 11 dígitos"

    suma = sum(d * m for d, m in zip(digitos[:10], MULTIPLICADORES_CUIT))
    verificador = 11 - (suma % 11)

    if verificador == 11:
        verificador = 0
    elif verificador == 10:
        # ARCA no emite CUITs con esa combinación: reasigna el prefijo (20→23, 27→23, 30→33).
        return False, "Combinación prefijo/DNI inexistente (ARCA reasigna el prefijo a 23 o 33)"

    if digitos[10] != verificador:
        return False, f"Dígito verificador incorrecto (esperado {verificador}, recibido {digitos[10]})"
    return True, "CUIT válido"


# ── Clase 4 ──────────────────────────────────────────────────────────────────

def verificar_documentacion(documentos_mencionados: list[str]) -> list[str]:
    """NOR-DOC: devuelve los documentos obligatorios que FALTAN (lista vacía = completa)."""
    return [doc for doc in DOCUMENTOS_OBLIGATORIOS if doc not in documentos_mencionados]


def normalizar_categoria(categoria_solicitada: Optional[str]) -> Optional[str]:
    """
    El LLM copia la categoría tal cual la escribió el distribuidor ("categoría B", "la A", "VIP Oro").
    Esta regla la lleva a "A", "B" o "C". Si no es ninguna de esas, devuelve None: la categoría no existe.
    """
    if categoria_solicitada is None:
        return None
    texto = re.sub(r"(?i)\b(categor[ií]a|cat\.?|la|el)\b", "", categoria_solicitada).strip().upper()
    return texto if texto in CONDICIONES_POR_CATEGORIA else None


def determinar_condiciones(facturacion_anual: float, cliente: dict,
                           plazo_solicitado_dias: Optional[int] = None) -> dict:
    """
    Paso 8 del journey: categoría, plazo y límite de crédito.
    Es la decisión con consecuencia financiera: por eso la toma el código, nunca el LLM.

    `cliente` es lo que devolvió la herramienta del sistema de gestión (paso 7).
    """
    reglas, observaciones = [], []

    # NOR-CAT-C / NOR-CAT-B / NOR-CAT-A (+ NOR-NUEVO)
    if facturacion_anual <= TOPE_CATEGORIA_C:
        categoria = "C"
    elif facturacion_anual <= TOPE_CATEGORIA_B:
        categoria = "B"
    elif not cliente["es_cliente"]:
        categoria = "B"
        reglas.append("NOR-NUEVO")
        observaciones.append("Factura como categoría A, pero es distribuidor nuevo: ingresa en B (NOR-NUEVO).")
    elif cliente["antiguedad_meses"] < ANTIGUEDAD_MINIMA_A:
        categoria = "B"
        observaciones.append(
            f"Factura como categoría A, pero tiene {cliente['antiguedad_meses']} meses de antigüedad "
            f"(mínimo {ANTIGUEDAD_MINIMA_A}): queda en B (NOR-CAT-A)."
        )
    else:
        categoria = "A"

    condiciones = CONDICIONES_POR_CATEGORIA[categoria]
    reglas.insert(0, condiciones["regla"])
    plazo_maximo = condiciones["plazo_maximo_dias"]
    limite = condiciones["limite_credito"]

    # NOR-DEUDA: la deuda vencida suspende la cuenta corriente, sin importar la categoría
    if cliente.get("dias_deuda_vencida", 0) > DIAS_DEUDA_MAXIMOS:
        reglas.append("NOR-DEUDA")
        observaciones.append(
            f"Tiene saldo vencido hace {cliente['dias_deuda_vencida']} días: "
            "opera solo al contado hasta regularizar (NOR-DEUDA)."
        )
        plazo_maximo, limite = 0, 0

    cuenta_corriente = plazo_maximo > 0

    # El plazo otorgado nunca supera el máximo de la categoría
    if not cuenta_corriente:
        plazo_otorgado = 0
    elif plazo_solicitado_dias is None:
        plazo_otorgado = plazo_maximo
    else:
        plazo_otorgado = min(plazo_solicitado_dias, plazo_maximo)
        if plazo_solicitado_dias > plazo_maximo:
            observaciones.append(
                f"Pidió {plazo_solicitado_dias} días; el máximo para su categoría es {plazo_maximo}."
            )

    return {
        "categoria": categoria,
        "cuenta_corriente": cuenta_corriente,
        "plazo_dias": plazo_otorgado,
        "limite_credito": limite,
        "reglas_aplicadas": reglas,
        "observaciones": observaciones,
    }

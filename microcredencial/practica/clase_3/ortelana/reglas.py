"""
Reglas de negocio deterministas: si entra X, siempre sale Y.
Por eso las ejecuta Python y NO el LLM.

Hoy (Clase 3): dígito verificador del CUIT — viene de la práctica de la Clase 2.
Clase 4: documentación obligatoria (NOR-DOC), categoría y plazo (NOR-CAT), deuda (NOR-DEUDA).
"""

import re

MULTIPLICADORES_CUIT = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]


def validar_cuit(cuit: str) -> tuple[bool, str]:
    """
    Algoritmo de validación del CUIT argentino (módulo 11).
    Devuelve (es_valido, motivo).
    """
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

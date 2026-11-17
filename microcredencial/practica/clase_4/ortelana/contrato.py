"""
Contrato de datos v1: lo que el LLM debe devolver en el paso 2 del journey.

De dónde sale (Entrega 1):
    - Los valores de `intencion` son EXACTAMENTE los de la Matriz de Intenciones (B.4).
    - Los campos son los datos que necesita el paso 2 del user journey (B.2).

Pydantic verifica que el JSON esté BIEN FORMADO (campos, tipos, valores permitidos).
Si el dato es VÁLIDO PARA EL NEGOCIO lo deciden las reglas (reglas.py).
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Intencion = Literal[
    "ALTA_DISTRIBUIDOR",
    "COMPLETAR_DOCUMENTACION",
    "CONSULTA_ESTADO",
    "CONSULTA_NORMATIVA",
    "FUERA_DE_ALCANCE",
]

Documento = Literal["CONSTANCIA_ARCA", "HABILITACION", "INGRESOS_BRUTOS"]


class ExtraccionOrtelana(BaseModel):
    intencion: Intencion
    razon_social: Optional[str] = None
    # Formato XX-XXXXXXXX-X. El dígito verificador lo controla reglas.py.
    cuit: Optional[str] = Field(default=None, pattern=r"^\d{2}-\d{8}-\d$")
    facturacion_anual: Optional[float] = Field(default=None, ge=0)
    plazo_solicitado_dias: Optional[int] = Field(default=None, ge=0)
    # Se copia tal cual (puede venir "VIP Oro"). Rechazarla es una regla de la Clase 4.
    categoria_solicitada: Optional[str] = None
    documentos_mencionados: list[Documento] = []

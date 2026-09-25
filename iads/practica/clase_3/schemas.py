"""
schemas.py

Contrato de datos estricto para normalizar consultas recibidas
por Ortelana Textil. Cualquier respuesta del LLM se valida contra
este esquema antes de tocar el backend real (ERP, SQL, APIs fiscales).

Mismo esquema que el ejemplo resuelto de la Teoría de Unidad 2
(sección 4, "Mapeo de Intenciones y Datos Confiables con Pydantic").

Uso:
    from schemas import ConsultaClienteSchema
"""

from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional


IntencionesPermitidas = Literal[
    "ALTA_DISTRIBUIDOR", "CONSULTA_DISTRIBUIDOR", "CONSULTA_STOCK", "RECLAMO_OPERATIVO"
]


class ConsultaClienteSchema(BaseModel):
    """
    Contrato de datos estricto para normalizar consultas
    recibidas por Ortelana Textil.
    """

    intencion_principal: IntencionesPermitidas = Field(
        description="Categoría raíz del mensaje según el árbol de intenciones del negocio."
    )

    identificador_fiscal: Optional[str] = Field(
        default=None,
        description="Identificador fiscal numérico (ej: CUIT de 11 dígitos), sin guiones ni espacios.",
    )

    razon_social_declarada: Optional[str] = Field(
        default=None,
        description="Nombre de la empresa o razón social provista por el remitente.",
    )

    tipo_tela: Optional[str] = Field(
        default=None,
        description="Nombre comercial de la tela solicitada (ej: gabardina, lona, denim).",
    )

    color: Optional[str] = Field(
        default=None,
        description="Color específico solicitado por el cliente.",
    )

    confianza_clasificacion: float = Field(
        description="Nivel de certeza probabilística del modelo en la clasificación, de 0.0 a 1.0."
    )

    @field_validator("identificador_fiscal")
    @classmethod
    def validar_y_limpiar_idfiscal(cls, v: Optional[str]) -> Optional[str]:
        """Elimina guiones/espacios y exige exactamente 11 dígitos numéricos."""
        if v is None:
            return v
        idfiscal_limpio = "".join(filter(str.isdigit, v))
        if idfiscal_limpio and len(idfiscal_limpio) != 11:
            raise ValueError(
                "El identificador fiscal debe contener exactamente 11 dígitos numéricos."
            )
        return idfiscal_limpio

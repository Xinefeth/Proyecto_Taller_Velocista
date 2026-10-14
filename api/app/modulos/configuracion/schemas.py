"""Contratos del modo y color de línea (HU-18)."""

from typing import Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class ConfiguracionGuardada(BaseModel):
    """Modo y color de línea guardados del robot; null cuando aún no se ha fijado alguno."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    modo: Literal["prueba", "competencia"] | None
    linea: Literal["negra", "blanca"] | None
    actualizado_en: AwareDatetime | None


class CambioModo(BaseModel):
    """`modo` es Any a propósito: un valor inválido se rechaza con comando_invalido en el contrato."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"modo": "prueba"}})
    modo: Any = Field(
        default=None,
        description="Modo de funcionamiento: 'prueba' o 'competencia'.",
        examples=["prueba", "competencia"],
    )


class CambioLinea(BaseModel):
    """`color` es Any a propósito (ver CambioModo)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"color": "negra"}})
    color: Any = Field(
        default=None,
        description="Color de la línea de la pista: 'negra' o 'blanca'.",
        examples=["negra", "blanca"],
    )


class ComandoAceptado(BaseModel):
    """Confirma que la API aceptó y envió el comando; el ack del robot llega por /ws/consola."""

    model_config = ConfigDict(extra="forbid")
    seq: int
    mensaje: str = "Enviado. La confirmación del robot llega a la consola como ack."

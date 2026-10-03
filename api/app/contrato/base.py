"""Sobre común y tipos básicos del contrato."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

VERSION_CONTRATO = "1.0"


def misma_version_mayor(version: str) -> str:
    """Valida que el dispositivo hable la misma versión mayor del contrato."""
    if version.split(".")[0] != VERSION_CONTRATO.split(".")[0]:
        raise ValueError(f"contrato {version} incompatible con {VERSION_CONTRATO}")
    return version


# Nombres de canales, parámetros y sensores: minúsculas, dígitos y guion bajo.
PATRON_NOMBRE = r"^[a-z][a-z0-9_]{0,31}$"

Emisor = Literal["velocista", "cronometro", "api"]


class Estricto(BaseModel):
    """Rechaza campos no declarados: un error de tipeo en el firmware se detecta enseguida."""

    model_config = ConfigDict(extra="forbid")


class Sobre(Estricto):
    """Envoltorio de todo mensaje WebSocket."""

    tipo: str = Field(pattern=r"^[a-z_]{2,24}$")
    seq: int = Field(
        ge=0, le=2**32 - 1, description="Correlativo del emisor; en ack repite el confirmado"
    )
    ts: int = Field(ge=0, description="Milisegundos desde el arranque del emisor")
    datos: dict[str, Any] = Field(default_factory=dict)

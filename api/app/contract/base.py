"""Sobre común y tipos básicos del contrato."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

CONTRACT_VERSION = "2.0"


def same_major_version(version: str) -> str:
    """Valida que el dispositivo hable la misma versión mayor del contrato."""
    if version.split(".")[0] != CONTRACT_VERSION.split(".")[0]:
        raise ValueError(f"contrato {version} incompatible con {CONTRACT_VERSION}")
    return version


# Nombres de canales, parámetros y sensores: minúsculas, dígitos y guion bajo.
NAME_PATTERN = r"^[a-z][a-z0-9_]{0,31}$"

Sender = Literal["velocista", "cronometro", "api"]


class Strict(BaseModel):
    """Rechaza campos no declarados: un error de tipeo en el firmware se detecta enseguida."""

    model_config = ConfigDict(extra="forbid")


class Envelope(Strict):
    """Envoltorio de todo mensaje WebSocket."""

    tipo: str = Field(pattern=r"^[a-z_]{2,24}$")
    seq: int = Field(
        ge=0, le=2**32 - 1, description="Correlativo del emisor; en ack repite el confirmado"
    )
    ts: int = Field(ge=0, description="Milisegundos desde el arranque del emisor")
    datos: dict[str, Any] = Field(default_factory=dict)

"""Mensajes entre el cronómetro de meta y la API."""

from typing import Literal

from pydantic import Field, field_validator

from app.contrato.base import PATRON_NOMBRE, Estricto, misma_version_mayor


class Hola(Estricto):
    id: str = Field(pattern=PATRON_NOMBRE)
    firmware: str = Field(max_length=20)
    contrato: str = Field(pattern=r"^\d+\.\d+$")
    antirrebote_ms: int = Field(ge=0)

    _version = field_validator("contrato")(misma_version_mayor)


class Corte(Estricto):
    n_corte: int = Field(ge=1, description="Correlativo de cortes desde el último rearmar")
    tiempo_vuelta_ms: int | None = Field(
        ge=0,
        description="Resta con el corte anterior en el reloj del cronómetro; null si es la salida",
    )
    marca_us: int = Field(ge=0, description="Instante del corte en microsegundos")


class EstadoCronometro(Estricto):
    barrera: Literal["ok", "bloqueada", "sin_senal"]
    rssi_dbm: int = Field(ge=-120, le=0)
    pendientes: int = Field(ge=0, description="Cortes guardados sin ack")


class Rearmar(Estricto):
    """API -> cronómetro: el próximo corte es una salida nueva."""

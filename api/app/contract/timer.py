"""Mensajes entre el cronómetro de meta y la API."""

from typing import Literal

from pydantic import Field, field_validator

from app.contract.base import NAME_PATTERN, Strict, same_major_version


class Hello(Strict):
    id: str = Field(pattern=NAME_PATTERN)
    firmware: str = Field(max_length=20)
    contrato: str = Field(pattern=r"^\d+\.\d+$")
    antirrebote_ms: int = Field(ge=0)

    _version = field_validator("contrato")(same_major_version)


class Crossing(Strict):
    n_corte: int = Field(ge=1, description="Correlativo de cortes desde el último rearmar")
    tiempo_vuelta_ms: int | None = Field(
        ge=0,
        description="Resta con el corte anterior en el reloj del cronómetro; null si es la salida",
    )
    marca_us: int = Field(ge=0, description="Instante del corte en microsegundos")


class TimerStatus(Strict):
    barrera: Literal["ok", "bloqueada", "sin_senal"]
    rssi_dbm: int = Field(ge=-120, le=0)
    pendientes: int = Field(ge=0, description="Cortes guardados sin ack")


class Rearm(Strict):
    """API -> cronómetro: el próximo corte es una salida nueva."""

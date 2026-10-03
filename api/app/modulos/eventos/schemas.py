"""Esquemas del módulo eventos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventoEntrada(BaseModel):
    sistema: str = Field(max_length=40)
    nivel: Literal["info", "aviso", "error"] = "info"
    mensaje: str = Field(max_length=500)


class EventoSalida(EventoEntrada):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: datetime

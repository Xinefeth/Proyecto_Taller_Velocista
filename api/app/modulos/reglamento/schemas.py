"""Perfiles de reglamento de consulta."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class PerfilSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")
    id: str
    competencia: str
    etiqueta: str
    categoria: str
    reglas: dict[str, Any]

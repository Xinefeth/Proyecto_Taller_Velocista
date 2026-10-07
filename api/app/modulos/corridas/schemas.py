"""Resúmenes históricos, vueltas y notas de pista."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class NotaCorrida(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nota: str = Field(max_length=1000)


class SegmentoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, allow_inf_nan=False)
    tipo: str
    duracion_s: float = Field(ge=0)
    angulo_grados: float
    error_acumulado: float = Field(ge=0)


class VueltaSalida(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: int
    corrida_id: int
    numero: int
    tiempo_s: float | None = Field(ge=0)
    duracion_s: float = Field(ge=0)
    tiempo_interno_ms: int | None
    error_acumulado: float = Field(ge=0)
    lineas_perdidas: int
    bateria_v: float = Field(ge=0)
    termino: bool
    fuente_tiempo: Literal["meta", "telemetria"]
    motivo: str
    sectores_s: list[float]
    segmentos: list[SegmentoSalida]


class CorridaSalida(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    id: int
    numero: int
    robot_id: str
    version_id: int
    setup_id: int
    perfil_id: str
    controlador_id: str
    parametros: dict[str, float]
    fecha: AwareDatetime
    fuente: Literal["sim", "robot"]
    modo: Literal["prueba", "competencia"]
    linea: Literal["negra", "blanca"]
    compensa_bateria: bool
    potencia_turbina_pct: float = Field(ge=0, le=100)
    tiempo_s: float | None = Field(ge=0)
    termino: bool
    error_acumulado: float = Field(ge=0)
    bateria_v: float = Field(ge=0)
    sectores_s: list[float]
    fuente_tiempo: Literal["meta", "telemetria"]
    nota: str
    j: float = Field(ge=0)


class PaginaCorridas(BaseModel):
    items: list[CorridaSalida]
    total: int
    limite: int
    offset: int


class PaginaVueltas(BaseModel):
    items: list[VueltaSalida]
    total: int
    limite: int
    offset: int

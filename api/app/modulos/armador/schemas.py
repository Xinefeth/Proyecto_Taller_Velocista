"""Esquemas Pydantic de entrada y salida del módulo armador."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class RobotCrear(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    nombre: str = Field(min_length=1, max_length=120)
    codigo_corto: str = Field(min_length=1, max_length=12)
    tipo: Literal["velocista", "minisumo"]
    firmware: str | None = Field(default=None, max_length=20)


class RobotSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str
    nombre: str
    codigo_corto: str
    tipo: Literal["velocista", "minisumo"]
    firmware: str | None
    version_actual_id: int | None = Field(ge=1, le=9007199254740991)
    archivado: bool


class RobotEditar(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    codigo_corto: str | None = Field(default=None, min_length=1, max_length=12)
    firmware: str | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def validar(self):
        if not self.model_fields_set:
            raise ValueError("Envía al menos un campo")
        for campo in self.model_fields_set - {"firmware"}:
            if getattr(self, campo) is None:
                raise ValueError(f"{campo} no admite null")
        return self


class PiezaCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    componente_id: str = Field(min_length=1, max_length=40)
    cantidad: int = Field(strict=True, ge=1, le=2147483647)


class VersionCrear(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version_base_id: int | None = Field(ge=1, le=9007199254740991, strict=True)
    nota: str = Field(max_length=1000)
    estado: Literal["Actual", "Concepto", "Borrador"]
    piezas: dict[str, PiezaCrear] = Field(max_length=14)


class RanuraSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tipo_id: str
    nombre: str
    obligatoria: bool
    cantidad_editable: bool
    depende_reglamento: bool


class PaginaRobots(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RobotSalida]
    total: int = Field(ge=0)
    limite: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)


class ComponenteHistorico(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    id: str
    tipo_id: str
    nombre: str
    precio: float = Field(gt=0)
    masa_g: float = Field(ge=0)
    tienda: str
    consumo_a: float | None = Field(ge=0)
    especificaciones: dict[str, str | int | float]


class PiezaHistoricaSalida(BaseModel):
    model_config = ConfigDict(extra="forbid")

    componente_id: str
    cantidad: int = Field(ge=1)
    componente_snapshot: ComponenteHistorico


class VersionSalida(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(ge=1, le=9007199254740991)
    robot_id: str
    etiqueta: str = Field(pattern=r"^v[0-9]+$")
    fecha: AwareDatetime
    nota: str
    estado: Literal["Actual", "Anterior", "Descartada", "Concepto", "Borrador"]
    piezas: dict[str, PiezaHistoricaSalida]


class PaginaVersiones(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VersionSalida]
    total: int = Field(ge=0)
    limite: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)

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
    model_config = ConfigDict(
        from_attributes=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": "rbt_velo_01",
                "nombre": "Relámpago",
                "codigo_corto": "VELO-01",
                "tipo": "velocista",
                "firmware": "1.4.2",
                "version_actual_id": 7,
                "archivado": False,
            }
        },
    )

    id: str = Field(description="ID interno del robot.", examples=["rbt_velo_01"])
    nombre: str = Field(description="Nombre visible del robot.", examples=["Relámpago"])
    codigo_corto: str = Field(description="Código corto único para la pista.", examples=["VELO-01"])
    tipo: Literal["velocista", "minisumo"] = Field(
        description="Categoría del robot.", examples=["velocista"]
    )
    firmware: str | None = Field(
        description="Versión de firmware declarada, si se conoce.", examples=["1.4.2"]
    )
    version_actual_id: int | None = Field(
        ge=1,
        le=9007199254740991,
        description="ID de la versión marcada como actual, o null si no hay.",
        examples=[7],
    )
    archivado: bool = Field(description="True si el robot está archivado.", examples=[False])


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

    items: list[RobotSalida] = Field(description="Robots de esta página.")
    total: int = Field(ge=0, description="Total de robots que cumplen el filtro.", examples=[3])
    limite: int = Field(ge=1, le=200, description="Límite aplicado.", examples=[50])
    offset: int = Field(ge=0, description="Offset aplicado.", examples=[0])


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
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "id": 7,
                "robot_id": "rbt_velo_01",
                "etiqueta": "v7",
                "fecha": "2026-10-01T15:30:00Z",
                "nota": "Nuevos sensores QTR y PID afinado.",
                "estado": "Actual",
                "piezas": {},
            }
        },
    )

    id: int = Field(ge=1, le=9007199254740991, description="ID de la versión.", examples=[7])
    robot_id: str = Field(description="Robot al que pertenece la versión.", examples=["rbt_velo_01"])
    etiqueta: str = Field(
        pattern=r"^v[0-9]+$", description="Etiqueta derivada del ordinal (v1, v2, …).", examples=["v7"]
    )
    fecha: AwareDatetime = Field(description="Fecha de creación de la versión (con zona).")
    nota: str = Field(description="Nota libre de la versión.", examples=["PID afinado."])
    estado: Literal["Actual", "Anterior", "Descartada", "Concepto", "Borrador"] = Field(
        description="Estado de la versión en el historial.", examples=["Actual"]
    )
    piezas: dict[str, PiezaHistoricaSalida] = Field(
        description="Piezas de la versión, indexadas por ranura, con su instantánea."
    )


class PaginaVersiones(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[VersionSalida] = Field(description="Versiones de esta página.")
    total: int = Field(ge=0, description="Total de versiones del robot.", examples=[7])
    limite: int = Field(ge=1, le=200, description="Límite aplicado.", examples=[50])
    offset: int = Field(ge=0, description="Offset aplicado.", examples=[0])

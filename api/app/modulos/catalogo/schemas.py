"""Esquemas Pydantic de entrada y salida del módulo catalogo."""

from decimal import Decimal
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictFloat,
    StrictInt,
    StrictStr,
    model_validator,
)

TipoComponenteId = Literal[
    "mcu",
    "exp",
    "linea",
    "mux",
    "motor",
    "driver",
    "bat",
    "reg",
    "rueda",
    "chasis",
    "sw",
    "enc",
    "imu",
    "turb",
]


class CampoTipo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    clave: str = Field(min_length=1, max_length=40)
    etiqueta: str = Field(max_length=120)
    tipo: Literal["n", "t"]
    unidad: str = Field(max_length=20)
    obligatorio: bool


class CapacidadTipo(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    clave: str = Field(min_length=1, max_length=40)
    unidad: str = Field(max_length=20)
    agregacion: Literal["suma_por_cantidad", "por_componente"]
    campo: str | None = Field(default=None, min_length=1, max_length=40)
    campos: list[str] | None = Field(default=None, min_length=2)
    operacion: Literal["producto"] | None = None
    min: float | None = None
    max: float | None = None


class TipoComponenteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: str = Field(min_length=1, max_length=40)
    nombre: str = Field(max_length=120)
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    campos: list[CampoTipo]
    capacidades: list[CapacidadTipo]


class ComponenteCrear(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    tipo_id: TipoComponenteId
    nombre: str = Field(min_length=1, max_length=120)
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    masa_g: Decimal = Field(ge=0, max_digits=12, decimal_places=3)
    tienda: str = Field(default="", max_length=200)
    consumo_a: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=4)
    especificaciones: dict[str, StrictStr | StrictInt | StrictFloat]
    stock: int = Field(strict=True, ge=0, le=2147483647)


class ComponenteEditar(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)

    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    precio: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    masa_g: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=3)
    tienda: str | None = Field(default=None, max_length=200)
    consumo_a: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=4)
    especificaciones: dict[str, StrictStr | StrictInt | StrictFloat] | None = None

    @model_validator(mode="after")
    def validar_parche(self):
        if not self.model_fields_set:
            raise ValueError("Envía al menos un campo para editar")
        for campo in self.model_fields_set - {"consumo_a"}:
            if getattr(self, campo) is None:
                raise ValueError(f"{campo} no puede ser null")
        return self


class ComponenteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", allow_inf_nan=False)

    id: str
    tipo_id: TipoComponenteId
    nombre: str
    precio: float = Field(gt=0)
    masa_g: float = Field(ge=0)
    tienda: str
    consumo_a: float | None = Field(ge=0)
    especificaciones: dict[str, str | int | float]
    stock: int = Field(ge=0)
    archivado: bool


class PaginaComponentes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ComponenteSalida]
    total: int = Field(ge=0)
    limite: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)


class InventarioActualizar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock: int = Field(strict=True, ge=0, le=2147483647)
    revision: int = Field(strict=True, ge=1, le=2147483647)


class InventarioSalida(BaseModel):
    model_config = ConfigDict(extra="forbid")

    componente_id: str
    stock: int = Field(ge=0)
    en_robots: int = Field(ge=0)
    disponible: int
    faltante: int = Field(ge=0)
    revision: int = Field(ge=1)


class PaginaInventario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[InventarioSalida]
    total: int = Field(ge=0)
    limite: int = Field(ge=1, le=200)
    offset: int = Field(ge=0)

"""Contratos de controladores y setups inmutables."""

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictFloat, StrictInt


class ParametroControlador(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    clave: str
    nombre: str
    descripcion: str
    min: float
    max: float
    paso: float = Field(gt=0)
    decimales: int = Field(ge=0, le=6)
    optimizable: bool


class ControladorSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid", allow_inf_nan=False)
    id: str
    nombre: str
    nombre_corto: str
    descripcion: str
    parametros: list[ParametroControlador]
    presets: dict[str, dict[str, float]]


class SetupCrear(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)
    version_id: int = Field(strict=True, ge=1, le=9007199254740991)
    nombre: str = Field(min_length=1, max_length=120)
    controlador_id: str = Field(min_length=1, max_length=40)
    parametros: dict[str, StrictFloat | StrictInt] = Field(max_length=32)


class SetupSalida(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: int
    robot_id: str
    version_id: int
    nombre: str
    controlador_id: str
    parametros: dict[str, float]
    creado_en: AwareDatetime
    archivado: bool


class PaginaSetups(BaseModel):
    items: list[SetupSalida]
    total: int
    limite: int
    offset: int

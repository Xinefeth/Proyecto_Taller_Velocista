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


class ParametroReconciliado(ParametroControlador):
    """Parámetro del catálogo que, si el robot está conectado, lleva el valor cargado ahora."""

    valor: float | None = None  # None sin conexión o sin coincidencia en el manifiesto (Req 1.3)


class ControladorReconciliado(BaseModel):
    """Controlador del catálogo superpuesto con lo que declara el manifiesto vivo (Req 1.1-1.2)."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str
    nombre: str
    nombre_corto: str
    descripcion: str
    parametros: list[ParametroReconciliado]
    presets: dict[str, dict[str, float]]
    activo: bool  # True solo si es el controlador_activo del manifiesto (Req 1.2)


class CatalogoReconciliado(BaseModel):
    """Catálogo de la base de datos reconciliado con el manifiesto vivo del robot pedido."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_activo: str | None  # None sin conexión (Req 1.3)
    controladores: list[ControladorReconciliado]


class ParametroVivo(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    nombre: str
    valor: float


class ConfiguracionViva(BaseModel):
    """Controlador y valores cargados ahora mismo en el robot (Req 2.1)."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_activo: str
    parametros: list[ParametroVivo]


class PresetAplicar(BaseModel):
    """Cuerpo para aplicar un preset del catálogo directo al robot."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_id: str = Field(min_length=1, max_length=40)
    preset_id: str = Field(min_length=1, max_length=40)  # p. ej. "Seguro", "Base", "Agresivo"


class ComandoAceptado(BaseModel):
    """Confirma que la API aceptó y envió el comando; el ack del robot llega por /ws/consola."""

    model_config = ConfigDict(extra="forbid")
    seq: int
    mensaje: str = "Enviado. La confirmación del robot llega a la consola como ack."


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

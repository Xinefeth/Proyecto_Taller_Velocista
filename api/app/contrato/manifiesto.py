"""Manifiesto: lo que el robot declara de sí mismo al conectarse.

Los canales tienen nombre. Agregar un sensor = declarar sus canales aquí;
la API, la base de datos y la consola los usan sin cambiar el contrato.
"""

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from app.contrato.base import PATRON_NOMBRE, Estricto, misma_version_mayor

TipoCanal = Literal["float", "int", "bool", "float[]", "int[]"]

# Canales que la API necesita para calcular J y vigilar la batería.
CANALES_REQUERIDOS: dict[str, str] = {"error": "senales", "bateria_v": "estado"}

COMANDOS_ROBOT = {"calibrar", "arrancar", "detener", "setup", "modo", "linea", "cierre_vuelta"}


class Canal(Estricto):
    nombre: str = Field(pattern=PATRON_NOMBRE)
    descripcion: str = Field(default="", max_length=120)
    tipo: TipoCanal
    longitud: int | None = Field(default=None, ge=1, le=64, description="Solo para arreglos")
    unidad: str = Field(default="", max_length=12)
    min: float | None = None
    max: float | None = None
    grupo: Literal["estado", "senales"] = Field(
        description="estado viaja a la frecuencia de estado; senales, a la de señales"
    )

    @model_validator(mode="after")
    def _coherente(self) -> "Canal":
        es_arreglo = self.tipo.endswith("[]")
        if es_arreglo and self.longitud is None:
            raise ValueError(f"el canal {self.nombre} es un arreglo y necesita longitud")
        if not es_arreglo and self.longitud is not None:
            raise ValueError(f"el canal {self.nombre} no es arreglo y no lleva longitud")
        if self.tipo == "bool" and (self.min is not None or self.max is not None):
            raise ValueError(f"el canal {self.nombre} es bool y no lleva rango")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError(f"el canal {self.nombre} tiene min mayor que max")
        return self


class Parametro(Estricto):
    nombre: str = Field(pattern=PATRON_NOMBRE)
    etiqueta: str = Field(max_length=40)
    tipo: Literal["float", "int"]
    min: float
    max: float
    paso: float | None = Field(default=None, gt=0)
    valor: float = Field(description="Valor cargado ahora en el robot")
    unidad: str = Field(default="", max_length=12)
    optimizable: bool = Field(default=True, description="Si Twiddle y la bayesiana pueden moverlo")

    @model_validator(mode="after")
    def _en_rango(self) -> "Parametro":
        if self.min >= self.max:
            raise ValueError(f"el parámetro {self.nombre} necesita min menor que max")
        if not self.min <= self.valor <= self.max:
            raise ValueError(f"el valor de {self.nombre} está fuera de su rango")
        if self.tipo == "int" and not all(
            float(v).is_integer() for v in (self.min, self.max, self.valor)
        ):
            raise ValueError(f"el parámetro {self.nombre} es int y tiene valores decimales")
        return self


class Controlador(Estricto):
    nombre: str = Field(pattern=PATRON_NOMBRE)
    descripcion: str = Field(default="", max_length=120)
    parametros: list[Parametro] = Field(min_length=1, max_length=16)

    @model_validator(mode="after")
    def _sin_repetidos(self) -> "Controlador":
        nombres = [p.nombre for p in self.parametros]
        if len(nombres) != len(set(nombres)):
            raise ValueError(f"el controlador {self.nombre} repite parámetros")
        return self

    def parametro(self, nombre: str) -> Parametro | None:
        return next((p for p in self.parametros if p.nombre == nombre), None)


class Sensor(Estricto):
    nombre: str = Field(pattern=PATRON_NOMBRE)
    modelo: str = Field(max_length=40)
    canales: list[str] = Field(min_length=1, description="Canales que produce este sensor")
    detalles: dict[str, Any] = Field(default_factory=dict)


class Actuador(Estricto):
    nombre: str = Field(pattern=PATRON_NOMBRE)
    tipo: Literal["motor_dc", "servo", "turbina", "led", "otro"]
    modelo: str = Field(default="", max_length=40)
    canales: list[str] = Field(default_factory=list)
    detalles: dict[str, Any] = Field(default_factory=dict)


class Frecuencias(Estricto):
    lazo_hz: int = Field(ge=1, le=10000)
    estado_hz: float = Field(gt=0, le=10)
    senales_hz: float = Field(gt=0, le=50)


class Manifiesto(Estricto):
    contrato: str = Field(pattern=r"^\d+\.\d+$")
    id: str = Field(pattern=PATRON_NOMBRE)
    tipo_robot: str = Field(pattern=PATRON_NOMBRE, description="velocista, minisumo…")
    firmware: str = Field(max_length=20)
    sensores: list[Sensor]
    actuadores: list[Actuador]
    canales: list[Canal] = Field(min_length=1, max_length=64)
    controladores: list[Controlador] = Field(min_length=1)
    controlador_activo: str
    comandos: list[str]
    frecuencias: Frecuencias
    arranque: Literal["comando", "modulo_arranque"]
    compensa_bateria: bool

    _version = field_validator("contrato")(misma_version_mayor)

    @model_validator(mode="after")
    def _consistente(self) -> "Manifiesto":
        nombres = [c.nombre for c in self.canales]
        if len(nombres) != len(set(nombres)):
            raise ValueError("hay canales con el mismo nombre")
        grupos = {c.nombre: c.grupo for c in self.canales}
        for nombre, grupo in CANALES_REQUERIDOS.items():
            if grupos.get(nombre) != grupo:
                raise ValueError(f"falta el canal requerido {nombre} en el grupo {grupo}")
        for dispositivo in [*self.sensores, *self.actuadores]:
            faltan = set(dispositivo.canales) - set(nombres)
            if faltan:
                raise ValueError(
                    f"{dispositivo.nombre} usa canales no declarados: {sorted(faltan)}"
                )
        if self.controlador_activo not in {c.nombre for c in self.controladores}:
            raise ValueError("controlador_activo no está entre los controladores declarados")
        desconocidos = set(self.comandos) - COMANDOS_ROBOT
        if desconocidos:
            raise ValueError(f"comandos desconocidos: {sorted(desconocidos)}")
        return self

    def canal(self, nombre: str) -> Canal | None:
        return next((c for c in self.canales if c.nombre == nombre), None)

    def controlador(self, nombre: str) -> Controlador | None:
        return next((c for c in self.controladores if c.nombre == nombre), None)

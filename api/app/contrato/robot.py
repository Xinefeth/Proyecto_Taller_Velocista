"""Mensajes entre el Velocista y la API."""

from typing import Any, Literal

from pydantic import Field

from app.contrato.base import PATRON_NOMBRE, Estricto

ValorCanal = float | int | bool | list[float] | list[int]

# ---------- Robot -> API ----------


class Estado(Estricto):
    """Cada 1/estado_hz segundos (1 Hz por defecto)."""

    estado: Literal["listo", "calibrando", "corriendo", "detenido", "error"]
    calibrado: bool
    modo: Literal["prueba", "competencia"]
    linea: Literal["negra", "blanca"]
    controlador: str = Field(pattern=PATRON_NOMBRE)
    lazo_hz: int = Field(ge=0, description="Frecuencia real medida del lazo de control")
    rssi_dbm: int = Field(ge=-120, le=0)
    canales: dict[str, ValorCanal] = Field(description="Canales del grupo estado")


class Senales(Estricto):
    """Cada 1/senales_hz segundos (20 Hz por defecto), solo mientras corre."""

    t_ms: int = Field(ge=0, description="Instante de la muestra en el reloj del robot")
    canales: dict[str, ValorCanal] = Field(description="Canales del grupo senales")


class Vuelta(Estricto):
    """Resumen de una vuelta; respuesta a cierre_vuelta."""

    id_vuelta: int = Field(ge=1)
    tiempo_interno_ms: int = Field(
        ge=0, description="Medido por el robot; el oficial es el del cronómetro"
    )
    error_acumulado: float = Field(ge=0, description="Integral del |error| en la vuelta (IAE)")
    lineas_perdidas: int = Field(ge=0)
    bateria_v: float = Field(ge=0)


class Sync(Estricto):
    """Vueltas guardadas mientras no había enlace; se envían al reconectar."""

    vueltas: list[Vuelta] = Field(min_length=1, max_length=50)


class Evento(Estricto):
    codigo: str = Field(
        pattern=PATRON_NOMBRE, description="Ver catálogo de eventos en la especificación"
    )
    nivel: Literal["info", "aviso", "error"]
    mensaje: str = Field(max_length=120)
    datos: dict[str, Any] = Field(default_factory=dict)


# ---------- API -> Robot (comandos) ----------


class SinDatos(Estricto):
    """calibrar, arrancar, detener."""


class Setup(Estricto):
    controlador: str = Field(pattern=PATRON_NOMBRE)
    parametros: dict[str, float] = Field(min_length=1)
    id_setup: int | None = Field(default=None, description="Id del setup guardado en la API")


class Modo(Estricto):
    modo: Literal["prueba", "competencia"]


class Linea(Estricto):
    color: Literal["negra", "blanca"]


class CierreVuelta(Estricto):
    id_vuelta: int = Field(ge=1)


# ---------- Ambos sentidos ----------

MotivoRechazo = Literal[
    "bloqueado_competencia",
    "no_calibrado",
    "fuera_de_rango",
    "parametro_desconocido",
    "controlador_no_disponible",
    "comando_desconocido",
    "ocupado",
]


class Ack(Estricto):
    """Confirma el mensaje cuyo seq viaja en el sobre. ok=false rechaza un comando."""

    ok: bool = True
    motivo: MotivoRechazo | None = None
    detalle: str | None = Field(default=None, max_length=120)

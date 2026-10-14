"""Configurar modo y color de línea del velocista (HU-18).

Modo y línea son comandos puros del dispositivo, sin base de datos: viven solo como el último
comando enviado y el último estado recibido. Por eso todo queda en el gateway, reusando
validar_comando + ws.send de comandos.py y agregando una sola guarda más estricta (ocupado) que
la vía cruda no aplica: prohíbe cambiar modo/línea mientras el robot corre, también en prueba.
"""

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.contract.robot import Status
from app.core.errores import ErrorDeNegocio, error_responses
from app.gateway import ws
from app.gateway.comandos import DATABASE_UNAVAILABLE_RESPONSES, CommandAccepted, validar_comando

# Mismo prefijo/tag que comandos.py; el 503 base_no_disponible se documenta a nivel de router
# por convención (DO-02 §8.4) aunque el gateway use conexiones en memoria y no consulte la BD.
router = APIRouter(
    prefix="/api/devices", tags=["devices"], responses=DATABASE_UNAVAILABLE_RESPONSES
)


class ConfigViva(BaseModel):
    """Modo y color de línea cargados ahora en el robot, tomados del último estado."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    modo: Literal["prueba", "competencia"]
    linea: Literal["negra", "blanca"]


class CambioModo(BaseModel):
    """Cuerpo para cambiar el modo. `modo` es Any a propósito: un valor inválido se rechaza con
    comando_invalido en la capa de contrato, no con un 422 genérico de FastAPI."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"modo": "prueba"}})
    modo: Any = Field(
        default=None,
        description="Modo de funcionamiento: 'prueba' o 'competencia'.",
        examples=["prueba", "competencia"],
    )


class CambioLinea(BaseModel):
    """Cuerpo para cambiar el color de línea. `color` es Any a propósito (ver CambioModo)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"color": "negra"}})
    color: Any = Field(
        default=None,
        description="Color de la línea de la pista: 'negra' o 'blanca'.",
        examples=["negra", "blanca"],
    )


# Errores de los dos endpoints de escritura (modo y línea comparten exactamente estos motivos).
CONFIG_RESPONSES = error_responses(
    (
        422,
        "comando_invalido",
        "El valor no es válido",
        "El valor de modo/línea no es uno de los permitidos (cadena, tipo, null o campo faltante).",
    ),
    (
        409,
        "sin_manifiesto",
        "Espera el manifiesto del robot",
        "El robot no está conectado o todavía no envió su manifiesto.",
    ),
    (
        422,
        "comando_desconocido",
        "El robot no declara ese comando",
        "El manifiesto del robot no lista el comando modo/línea.",
    ),
    (
        409,
        "bloqueado_competencia",
        "En competencia solo se puede detener",
        "El robot corre en modo competencia; no se puede cambiar modo ni línea.",
    ),
    (
        409,
        "ocupado",
        "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea",
        "El robot corre en modo prueba; no se puede cambiar modo ni línea hasta detenerlo.",
    ),
    (
        503,
        "dispositivo_no_disponible",
        "No se pudo entregar el comando: el dispositivo dejó de responder",
        "El enlace con el robot se perdió entre la validación y el envío; reintenta.",
    ),
    (
        503,
        "base_no_disponible",
        "La base de datos no está disponible",
        "Base de datos no disponible (error de infraestructura; el gateway no consulta la BD).",
    ),
)


def validar_cambio_config(ultimo_estado: Status | None) -> None:
    """Guarda de HU-18: rechazar cambios de modo/linea durante una carrera en modo prueba.

    validar_comando ya bloquea competencia+running con bloqueado_competencia; esta guarda extiende
    el bloqueo a prueba+running, que la vía cruda permite. Es específica de modo/linea: no aplica a
    otros comandos (p. ej. setup, que HU-17 permite durante una carrera de prueba).
    """
    e = ultimo_estado
    if e and e.estado == "running" and e.modo == "prueba":
        raise ErrorDeNegocio(
            409,
            "ocupado",
            "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea",
        )


@router.get(
    "/velocista/config",
    response_model=ConfigViva,
    operation_id="getRobotConfig",
    summary="Consultar el modo y el color de línea actuales",
    description=(
        "Devuelve el modo y el color de línea del último estado que el robot reportó, para que la "
        "consola pinte el estado inicial del panel sin suscribirse al WebSocket (HU-18)."
    ),
    responses=error_responses(
        (
            404,
            "sin_estado",
            "El robot aún no ha enviado su estado",
            "El velocista no está conectado o todavía no envió un estado; no hay modo ni línea que mostrar.",
        ),
    ),
)
def get_robot_config() -> ConfigViva:
    connection = ws.connections.get("velocista")
    if connection is None or connection.last_status is None:
        raise ErrorDeNegocio(404, "sin_estado", "El robot aún no ha enviado su estado")
    return ConfigViva(modo=connection.last_status.modo, linea=connection.last_status.linea)


@router.post(
    "/velocista/config/modo",
    status_code=202,
    response_model=CommandAccepted,
    operation_id="setMode",
    summary="Configurar el modo de funcionamiento",
    description=(
        "Valida el modo contra el manifiesto y el estado vivos y lo envía al robot por el gateway "
        "(HU-18). Se rechaza mientras el robot corre, en cualquier modo. El ack del robot llega a "
        "la consola por `/ws/consola`, no en esta respuesta."
    ),
    responses=CONFIG_RESPONSES,
)
async def set_mode(body: CambioModo) -> CommandAccepted:
    connection = ws.connections.get("velocista")
    manifest = connection.manifest if connection else None
    last_status = connection.last_status if connection else None
    model = validar_comando("velocista", "modo", {"modo": body.modo}, manifest, last_status)
    validar_cambio_config(last_status)  # guarda más estricta de HU-18 (ocupado)
    try:
        seq = await ws.send("velocista", "modo", model.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        raise ErrorDeNegocio(
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e
    return CommandAccepted(seq=seq)


@router.post(
    "/velocista/config/linea",
    status_code=202,
    response_model=CommandAccepted,
    operation_id="setLine",
    summary="Configurar el color de la línea",
    description=(
        "Valida el color de línea contra el manifiesto y el estado vivos y lo envía al robot por el "
        "gateway (HU-18). Se rechaza mientras el robot corre, en cualquier modo. El ack del robot "
        "llega a la consola por `/ws/consola`, no en esta respuesta."
    ),
    responses=CONFIG_RESPONSES,
)
async def set_line(body: CambioLinea) -> CommandAccepted:
    connection = ws.connections.get("velocista")
    manifest = connection.manifest if connection else None
    last_status = connection.last_status if connection else None
    model = validar_comando("velocista", "linea", {"color": body.color}, manifest, last_status)
    validar_cambio_config(last_status)  # guarda más estricta de HU-18 (ocupado)
    try:
        seq = await ws.send("velocista", "linea", model.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        raise ErrorDeNegocio(
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e
    return CommandAccepted(seq=seq)

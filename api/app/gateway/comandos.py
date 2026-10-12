"""Comandos hacia los dispositivos: POST /api/dispositivos/{d}/comandos (EN-02).

La consola nunca habla con el robot: pide el comando aquí, la API lo valida y el gateway
lo envía. La confirmación del dispositivo llega a la consola por /ws/consola como ack.
"""

import json
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.contract import InvalidMessage, Manifest, validate_data
from app.contract.robot import Setup, Status
from app.contract.validation import check_setup
from app.core.config import RAIZ_REPO
from app.core.errores import ErrorDeNegocio, error_responses
from app.gateway import ws

DATABASE_UNAVAILABLE_RESPONSES = error_responses(
    (
        503,
        "base_no_disponible",
        "La base de datos no está disponible",
        "Base de datos no disponible. Documentado como error de infraestructura; "
        "actualmente este gateway usa conexiones WebSocket en memoria y no consulta la BD.",
    ),
)

router = APIRouter(
    prefix="/api/devices", tags=["devices"], responses=DATABASE_UNAVAILABLE_RESPONSES
)

Device = Literal["velocista", "cronometro"]

# Ejemplo real del manifiesto para Swagger, en vez del texto aleatorio que genera el esquema.
# Es el mismo ejemplo del contrato; tomamos su `datos` porque el endpoint devuelve el manifiesto.
MANIFEST_EXAMPLE = json.loads(
    (RAIZ_REPO / "docs" / "contrato" / "ejemplos" / "velocista.manifiesto.json").read_text(
        encoding="utf-8"
    )
)["datos"]


class Command(BaseModel):
    """Command that the console asks to send to a device (HU-16)."""

    model_config = ConfigDict(json_schema_extra={"example": {"tipo": "start", "datos": {}}})

    tipo: str = Field(
        description=(
            "Tipo de comando. Para el velocista debe estar declarado en su manifiesto: "
            "calibrate, start, stop, setup, modo, linea, cierre_vuelta."
        ),
        examples=["calibrate", "start", "stop"],
    )
    datos: dict[str, Any] = Field(
        default_factory=dict,
        description="Datos del comando. Vacío para calibrar/arrancar/detener; con campos para setup/modo/linea.",
        examples=[{}],
    )


class CommandAccepted(BaseModel):
    """Confirmation that the API accepted the command and sent it to the device."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "seq": 42,
                "mensaje": "Enviado. La confirmación del dispositivo llega a la consola como ack.",
            }
        }
    )

    seq: int = Field(description="Número de secuencia del mensaje enviado; el ack del robot lo repite.")
    mensaje: str = Field(
        default="Enviado. La confirmación del dispositivo llega a la consola como ack.",
        description="Mensaje para el usuario.",
    )


def validar_comando(
    dispositivo: str,
    tipo: str,
    datos: dict,
    manifiesto: Manifest | None,
    ultimo_estado: Status | None,
) -> BaseModel:
    """Devuelve el comando validado o lanza ErrorDeNegocio con el motivo del rechazo."""
    if tipo == "ack":
        raise ErrorDeNegocio(422, "comando_invalido", "ack no es un comando")
    try:
        modelo = validate_data(f"api->{dispositivo}", tipo, datos)
    except InvalidMessage as e:
        raise ErrorDeNegocio(422, "comando_invalido", str(e)[:300]) from e
    if dispositivo != "velocista":
        return modelo
    if manifiesto is None:
        raise ErrorDeNegocio(409, "sin_manifiesto", "Espera el manifiesto del robot")
    if tipo not in manifiesto.comandos:
        raise ErrorDeNegocio(422, "comando_desconocido", "El robot no declara ese comando")
    e = ultimo_estado
    if e and e.modo == "competencia" and e.estado == "running" and tipo != "stop":
        raise ErrorDeNegocio(409, "bloqueado_competencia", "En competencia solo se puede detener")
    if tipo == "start" and (e is None or not e.calibrado):
        raise ErrorDeNegocio(409, "no_calibrado", "Calibra el robot antes de arrancar")
    if isinstance(modelo, Setup) and (problema := check_setup(manifiesto, modelo)):
        raise ErrorDeNegocio(422, problema[0], problema[1])
    return modelo


@router.get(
    "/velocista/manifest",
    status_code=200,
    response_model=Manifest,
    operation_id="getRacerManifest",
    summary="Consultar el manifiesto del velocista",
    description=(
        "Devuelve lo que el robot declaró de sí mismo al conectarse: sensores, actuadores, "
        "canales, controladores y parámetros. La consola lo usa para pintar los paneles del "
        "robot seleccionado (HU-13). Requiere que el velocista esté conectado y haya enviado su "
        "manifiesto por `/ws/robot`."
    ),
    responses={
        200: {"content": {"application/json": {"example": MANIFEST_EXAMPLE}}},
        **error_responses(
            (
                404,
                "sin_manifiesto",
                "El robot no está conectado o aún no envió su manifiesto",
                "El velocista no está conectado o todavía no envió su manifiesto.",
            ),
        ),
    },
)
def get_racer_manifest() -> dict:
    connection = ws.connections.get("velocista")
    if connection is None or connection.manifest is None:
        raise ErrorDeNegocio(
            404, "sin_manifiesto", "El robot no está conectado o aún no envió su manifiesto"
        )
    return connection.manifest.model_dump()


@router.post(
    "/{device}/commands",
    status_code=202,
    response_model=CommandAccepted,
    operation_id="sendCommand",
    summary="Enviar un comando a un dispositivo",
    description=(
        "La consola nunca habla directo con el robot: pide el comando aquí, la API lo valida "
        "contra el manifiesto y el estado actual, y el gateway lo reenvía por WebSocket. La "
        "confirmación del dispositivo (ack) llega a la consola por `/ws/consola`, no en esta "
        "respuesta. Cubre calibrar y arrancar/detener (HU-16)."
    ),
    responses=error_responses(
        (
            409,
            "desconectado",
            "velocista no está conectado",
            "El dispositivo destino no está conectado.",
        ),
        (
            409,
            "no_calibrado",
            "Calibra el robot antes de arrancar",
            "Estado inválido para el comando (sin calibrar, bloqueado en competencia o sin manifiesto).",
        ),
        (
            422,
            "comando_desconocido",
            "El robot no declara ese comando",
            "Comando o datos inválidos: no declarado en el manifiesto, mal formado o fuera de rango.",
        ),
        (
            503,
            "base_no_disponible",
            "La base de datos no está disponible",
            "Base de datos no disponible (error de infraestructura; actualmente sin acceso a BD).",
        ),
        (
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
            "El enlace con el dispositivo se perdió al enviar el comando (se cayó entre la validación y el envío); reintenta.",
        ),
    ),
)
async def send_command(device: Device, command: Command) -> CommandAccepted:
    connection = ws.connections.get(device)
    if connection is None:
        raise ErrorDeNegocio(409, "desconectado", f"{device} no está conectado")
    model = validar_comando(
        device, command.tipo, command.datos, connection.manifest, connection.last_status
    )
    try:
        seq = await ws.send(device, command.tipo, model.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        # El enlace se cayó entre el pre-chequeo y el envío: el dispositivo ya no recibe.
        raise ErrorDeNegocio(
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e
    return CommandAccepted(seq=seq)

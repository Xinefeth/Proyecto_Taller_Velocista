"""Comandos hacia los dispositivos: POST /api/dispositivos/{d}/comandos (EN-02).

La consola nunca habla con el robot: pide el comando aquí, la API lo valida y el gateway
lo envía. La confirmación del dispositivo llega a la consola por /ws/consola como ack.
"""

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.contrato import Manifiesto, MensajeInvalido, validar_datos
from app.contrato.robot import Estado, Setup
from app.contrato.validacion import revisar_setup
from app.core.errores import ErrorDeNegocio, error_responses
from app.gateway import ws

router = APIRouter(prefix="/api/devices", tags=["devices"])

Device = Literal["velocista", "cronometro"]


class Command(BaseModel):
    """Command that the console asks to send to a device (HU-16)."""

    model_config = ConfigDict(json_schema_extra={"example": {"tipo": "arrancar", "datos": {}}})

    tipo: str = Field(
        description=(
            "Command type. For the line follower it must be declared in its manifest: "
            "calibrar, arrancar, detener, setup, modo, linea, cierre_vuelta."
        ),
        examples=["calibrar", "arrancar", "detener"],
    )
    datos: dict[str, Any] = Field(
        default_factory=dict,
        description="Command data. Empty for calibrar/arrancar/detener; with fields for setup/modo/linea.",
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

    seq: int = Field(description="Sequence number of the sent message; the robot's ack repeats it.")
    mensaje: str = Field(
        default="Enviado. La confirmación del dispositivo llega a la consola como ack.",
        description="Message for the user (in Spanish).",
    )


def validar_comando(
    dispositivo: str,
    tipo: str,
    datos: dict,
    manifiesto: Manifiesto | None,
    ultimo_estado: Estado | None,
) -> BaseModel:
    """Devuelve el comando validado o lanza ErrorDeNegocio con el motivo del rechazo."""
    if tipo == "ack":
        raise ErrorDeNegocio(422, "comando_invalido", "ack no es un comando")
    try:
        modelo = validar_datos(f"api->{dispositivo}", tipo, datos)
    except MensajeInvalido as e:
        raise ErrorDeNegocio(422, "comando_invalido", str(e)[:300]) from e
    if dispositivo != "velocista":
        return modelo
    if manifiesto is None:
        raise ErrorDeNegocio(409, "sin_manifiesto", "Espera el manifiesto del robot")
    if tipo not in manifiesto.comandos:
        raise ErrorDeNegocio(422, "comando_desconocido", "El robot no declara ese comando")
    e = ultimo_estado
    if e and e.modo == "competencia" and e.estado == "corriendo" and tipo != "detener":
        raise ErrorDeNegocio(409, "bloqueado_competencia", "En competencia solo se puede detener")
    if tipo == "arrancar" and (e is None or not e.calibrado):
        raise ErrorDeNegocio(409, "no_calibrado", "Calibra el robot antes de arrancar")
    if isinstance(modelo, Setup) and (problema := revisar_setup(manifiesto, modelo)):
        raise ErrorDeNegocio(422, problema[0], problema[1])
    return modelo


@router.get(
    "/velocista/manifest",
    response_model=Manifiesto,
    operation_id="getRacerManifest",
    summary="Get the line follower manifest",
    description=(
        "Returns what the robot declared about itself when it connected: sensors, actuators, "
        "channels, controllers and parameters. The console uses it to draw the panels of the "
        "selected robot (HU-13). It requires the line follower to be connected and to have sent "
        "its manifest over `/ws/robot`."
    ),
    responses=error_responses(
        (
            404,
            "sin_manifiesto",
            "El robot no está conectado o aún no envió su manifiesto",
            "The line follower is not connected or has not sent its manifest yet.",
        ),
    ),
)
def get_racer_manifest() -> dict:
    connection = ws.conexiones.get("velocista")
    if connection is None or connection.manifiesto is None:
        raise ErrorDeNegocio(
            404, "sin_manifiesto", "El robot no está conectado o aún no envió su manifiesto"
        )
    return connection.manifiesto.model_dump()


@router.post(
    "/{device}/commands",
    status_code=202,
    response_model=CommandAccepted,
    operation_id="sendCommand",
    summary="Send a command to a device",
    description=(
        "The console never talks to the robot directly: it requests the command here, the API "
        "validates it against the manifest and the current state, and the gateway forwards it "
        "over WebSocket. The device confirmation (ack) reaches the console through "
        "`/ws/consola`, not in this response. It covers calibrate and start/stop (HU-16)."
    ),
    responses=error_responses(
        (
            409,
            "desconectado",
            "velocista no está conectado",
            "The target device is not connected.",
        ),
        (
            409,
            "no_calibrado",
            "Calibra el robot antes de arrancar",
            "Invalid state for the command (not calibrated, locked in competition, or no manifest).",
        ),
        (
            422,
            "comando_desconocido",
            "El robot no declara ese comando",
            "Invalid command or data: not declared in the manifest, malformed or out of range.",
        ),
    ),
)
async def send_command(device: Device, command: Command) -> CommandAccepted:
    connection = ws.conexiones.get(device)
    if connection is None:
        raise ErrorDeNegocio(409, "desconectado", f"{device} no está conectado")
    model = validar_comando(
        device, command.tipo, command.datos, connection.manifiesto, connection.ultimo_estado
    )
    seq = await ws.enviar(device, command.tipo, model.model_dump(exclude_none=True))
    return CommandAccepted(seq=seq)

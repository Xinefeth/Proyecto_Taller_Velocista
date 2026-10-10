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
            "Tipo de comando. Para el velocista debe estar declarado en su manifiesto: "
            "calibrar, arrancar, detener, setup, modo, linea, cierre_vuelta."
        ),
        examples=["calibrar", "arrancar", "detener"],
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
    summary="Consultar el manifiesto del velocista",
    description=(
        "Devuelve lo que el robot declaró de sí mismo al conectarse: sensores, actuadores, "
        "canales, controladores y parámetros. La consola lo usa para pintar los paneles del "
        "robot seleccionado (HU-13). Requiere que el velocista esté conectado y haya enviado su "
        "manifiesto por `/ws/robot`."
    ),
    responses=error_responses(
        (
            404,
            "sin_manifiesto",
            "El robot no está conectado o aún no envió su manifiesto",
            "El velocista no está conectado o todavía no envió su manifiesto.",
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

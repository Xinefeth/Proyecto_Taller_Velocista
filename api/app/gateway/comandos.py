"""Comandos hacia los dispositivos: POST /api/dispositivos/{d}/comandos (EN-02).

La consola nunca habla con el robot: pide el comando aquí, la API lo valida y el gateway
lo envía. La confirmación del dispositivo llega a la consola por /ws/consola como ack.
"""

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.contrato import Manifiesto, MensajeInvalido, validar_datos
from app.contrato.robot import Estado, Setup
from app.contrato.validacion import revisar_setup
from app.core.errores import ErrorDeNegocio
from app.gateway import ws

router = APIRouter(prefix="/api/dispositivos", tags=["dispositivos"])

Dispositivo = Literal["velocista", "cronometro"]


class Comando(BaseModel):
    tipo: str = Field(examples=["arrancar"])
    datos: dict[str, Any] = Field(default_factory=dict, examples=[{}])


class ComandoEnviado(BaseModel):
    seq: int
    mensaje: str = "Enviado. La confirmación del dispositivo llega a la consola como ack."


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


@router.get("/velocista/manifiesto")
def manifiesto_velocista() -> dict:
    conexion = ws.conexiones.get("velocista")
    if conexion is None or conexion.manifiesto is None:
        raise ErrorDeNegocio(
            404, "sin_manifiesto", "El robot no está conectado o aún no envió su manifiesto"
        )
    return conexion.manifiesto.model_dump()


@router.post("/{dispositivo}/comandos", status_code=202)
async def enviar_comando(dispositivo: Dispositivo, comando: Comando) -> ComandoEnviado:
    conexion = ws.conexiones.get(dispositivo)
    if conexion is None:
        raise ErrorDeNegocio(409, "desconectado", f"{dispositivo} no está conectado")
    modelo = validar_comando(
        dispositivo, comando.tipo, comando.datos, conexion.manifiesto, conexion.ultimo_estado
    )
    seq = await ws.enviar(dispositivo, comando.tipo, modelo.model_dump(exclude_none=True))
    return ComandoEnviado(seq=seq)

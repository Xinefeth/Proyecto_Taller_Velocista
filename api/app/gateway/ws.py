"""Gateway WebSocket: /ws/robot, /ws/cronometro y /ws/consola.

Estado EN-03: acepta conexiones, autentica dispositivos por token, exige JSON con forma de objeto
y redistribuye cada mensaje a las consolas conectadas. La validación según el contrato de
mensajes (EN-02) se agrega en `_procesar`.
"""

import json
import logging
import time
from dataclasses import dataclass

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import settings
from app.core.seguridad import token_valido

log = logging.getLogger("apaec.gateway")
router = APIRouter()

DISPOSITIVOS = ("velocista", "cronometro")


def _ms() -> int:
    return int(time.time() * 1000)


@dataclass
class Conexion:
    ws: WebSocket


class Consolas:
    """Consolas conectadas a /ws/consola; solo reciben."""

    def __init__(self) -> None:
        self.activas: set[WebSocket] = set()

    async def difundir(self, origen: str, tipo: str, datos: dict) -> None:
        mensaje = {"origen": origen, "tipo": tipo, "datos": datos, "recibido_ms": _ms()}
        for ws in list(self.activas):
            try:
                await ws.send_json(mensaje)
            except Exception:
                self.activas.discard(ws)


consolas = Consolas()
conexiones: dict[str, Conexion] = {}


def estado_dispositivos() -> dict[str, bool]:
    return {nombre: nombre in conexiones for nombre in DISPOSITIVOS}


async def _procesar(nombre: str, crudo: str) -> None:
    try:
        mensaje = json.loads(crudo)
    except json.JSONDecodeError:
        log.warning("Mensaje no JSON de %s", nombre)
        await consolas.difundir("api", "mensaje_invalido", {"dispositivo": nombre})
        return
    if not isinstance(mensaje, dict):
        await consolas.difundir("api", "mensaje_invalido", {"dispositivo": nombre})
        return
    # EN-02: validar el mensaje contra el contrato antes de redistribuirlo.
    await consolas.difundir(nombre, str(mensaje.get("tipo", "desconocido")), mensaje)


async def _atender(ws: WebSocket, nombre: str, token_esperado: str) -> None:
    if not token_valido(
        ws.headers.get("x-device-token") or ws.query_params.get("token"), token_esperado
    ):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        log.warning("Conexión rechazada de %s: token inválido", nombre)
        return
    await ws.accept()
    conexion = Conexion(ws)
    conexiones[nombre] = conexion
    log.info("%s conectado", nombre)
    await consolas.difundir("api", "enlace", {"dispositivo": nombre, "conectado": True})
    try:
        while True:
            await _procesar(nombre, await ws.receive_text())
    except WebSocketDisconnect:
        pass
    finally:
        if conexiones.get(nombre) is conexion:
            del conexiones[nombre]
        log.info("%s desconectado", nombre)
        await consolas.difundir("api", "enlace", {"dispositivo": nombre, "conectado": False})


@router.websocket("/ws/robot")
async def ws_robot(ws: WebSocket) -> None:
    await _atender(ws, "velocista", settings.device_token_velocista)


@router.websocket("/ws/cronometro")
async def ws_cronometro(ws: WebSocket) -> None:
    await _atender(ws, "cronometro", settings.device_token_cronometro)


@router.websocket("/ws/consola")
async def ws_consola(ws: WebSocket) -> None:
    await ws.accept()
    consolas.activas.add(ws)
    await ws.send_json(
        {
            "origen": "api",
            "tipo": "hola",
            "datos": {"dispositivos": estado_dispositivos()},
            "recibido_ms": _ms(),
        }
    )
    try:
        while True:
            await ws.receive_text()  # la consola solo escucha; sus acciones van por REST
    except WebSocketDisconnect:
        consolas.activas.discard(ws)

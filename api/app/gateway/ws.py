"""Gateway WebSocket: /ws/robot, /ws/cronometro y /ws/consola.

Aplica el contrato de mensajes v1.0 (EN-02):
- valida cada mensaje contra el catálogo antes de redistribuirlo;
- exige el manifiesto como primer mensaje del robot;
- revisa los canales de telemetría contra el manifiesto (avisa, no descarta la muestra);
- confirma con ack solo los tipos que lo requieren y descarta duplicados por seq;
- descarta señales fuera de orden (t_ms menor que la última procesada).
"""

import json
import logging
import time
from collections import deque
from dataclasses import dataclass, field

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.contrato import Manifiesto, MensajeInvalido, Sobre, requiere_ack, validar_datos
from app.contrato.robot import Estado, Senales
from app.contrato.validacion import revisar_canales
from app.core.config import settings
from app.core.seguridad import token_valido

log = logging.getLogger("apaec.gateway")
router = APIRouter()

DISPOSITIVOS = ("velocista", "cronometro")
SEQ_RECORDADOS = 256


def _ms() -> int:
    return int(time.time() * 1000)


@dataclass
class Conexion:
    ws: WebSocket
    manifiesto: Manifiesto | None = None
    ultimo_estado: Estado | None = None
    ultimo_t_ms: int = -1
    seq_salida: int = 0
    seq_recibidos: deque = field(default_factory=lambda: deque(maxlen=SEQ_RECORDADOS))
    avisos_vistos: set[str] = field(default_factory=set)

    def siguiente_seq(self) -> int:
        self.seq_salida = (self.seq_salida + 1) % 2**32
        return self.seq_salida


class Consolas:
    """Consolas conectadas a /ws/consola; solo reciben."""

    def __init__(self) -> None:
        self.activas: set[WebSocket] = set()

    async def difundir(
        self, origen: str, tipo: str, datos: dict, seq: int = 0, ts: int = 0
    ) -> None:
        mensaje = {
            "origen": origen,
            "tipo": tipo,
            "seq": seq,
            "ts": ts,
            "datos": datos,
            "recibido_ms": _ms(),
        }
        for ws in list(self.activas):
            try:
                await ws.send_json(mensaje)
            except Exception:
                self.activas.discard(ws)

    async def evento(self, codigo: str, nivel: str, mensaje: str, **datos) -> None:
        await self.difundir(
            "api", "evento", {"codigo": codigo, "nivel": nivel, "mensaje": mensaje, "datos": datos}
        )


consolas = Consolas()
conexiones: dict[str, Conexion] = {}


def estado_dispositivos() -> dict[str, bool]:
    return {nombre: nombre in conexiones for nombre in DISPOSITIVOS}


async def enviar(nombre: str, tipo: str, datos: dict) -> int:
    """Envía un mensaje de la API a un dispositivo conectado. Devuelve el seq usado."""
    conexion = conexiones[nombre]
    seq = conexion.siguiente_seq()
    await conexion.ws.send_json({"tipo": tipo, "seq": seq, "ts": _ms() % 2**32, "datos": datos})
    return seq


async def _ack(conexion: Conexion, seq: int) -> None:
    await conexion.ws.send_json(
        {"tipo": "ack", "seq": seq, "ts": _ms() % 2**32, "datos": {"ok": True}}
    )


async def _procesar(nombre: str, conexion: Conexion, crudo: str) -> None:
    try:
        sobre = Sobre.model_validate(json.loads(crudo))
        modelo = validar_datos(nombre, sobre.tipo, sobre.datos)
    except (json.JSONDecodeError, ValidationError, MensajeInvalido) as e:
        log.warning("Mensaje inválido de %s: %s", nombre, e)
        await consolas.evento(
            "mensaje_invalido", "aviso", f"Mensaje inválido de {nombre}", detalle=str(e)[:300]
        )
        return

    con_ack = requiere_ack(nombre, sobre.tipo)
    if con_ack and sobre.seq in conexion.seq_recibidos:
        await _ack(conexion, sobre.seq)  # duplicado: se vuelve a confirmar, no se reprocesa
        return

    if nombre == "velocista":
        if isinstance(modelo, Manifiesto):
            conexion.manifiesto = modelo
            conexion.avisos_vistos.clear()
            conexion.ultimo_t_ms = -1
        elif conexion.manifiesto is None:
            await consolas.evento(
                "manifiesto_faltante", "aviso", "El robot envió datos antes del manifiesto"
            )
            return
        else:
            if isinstance(modelo, Senales):
                if modelo.t_ms <= conexion.ultimo_t_ms:
                    return  # fuera de orden: la siguiente muestra la reemplaza
                conexion.ultimo_t_ms = modelo.t_ms
            if isinstance(modelo, Estado):
                conexion.ultimo_estado = modelo
            if isinstance(modelo, Estado | Senales):
                grupo = "estado" if isinstance(modelo, Estado) else "senales"
                for aviso in revisar_canales(conexion.manifiesto, grupo, modelo.canales):
                    if aviso not in conexion.avisos_vistos:  # cada aviso una vez por conexión
                        conexion.avisos_vistos.add(aviso)
                        await consolas.evento("canal_invalido", "aviso", aviso)

    if con_ack:
        conexion.seq_recibidos.append(sobre.seq)
        await _ack(conexion, sobre.seq)
    await consolas.difundir(nombre, sobre.tipo, sobre.datos, sobre.seq, sobre.ts)


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
            await _procesar(nombre, conexion, await ws.receive_text())
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
            "seq": 0,
            "ts": 0,
            "datos": {"dispositivos": estado_dispositivos()},
            "recibido_ms": _ms(),
        }
    )
    try:
        while True:
            await ws.receive_text()  # la consola solo escucha; sus acciones van por REST
    except WebSocketDisconnect:
        consolas.activas.discard(ws)


def robot_corriendo(robot_id: str) -> bool:
    conexion = conexiones.get("velocista")
    return bool(
        conexion
        and conexion.manifiesto
        and conexion.manifiesto.id == robot_id
        and conexion.ultimo_estado
        and conexion.ultimo_estado.estado == "corriendo"
    )

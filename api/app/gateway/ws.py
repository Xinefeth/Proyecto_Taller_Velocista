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

from app.contract import Envelope, InvalidMessage, Manifest, requires_ack, validate_data
from app.contract.robot import Signals, Status
from app.contract.validation import check_channels
from app.core.config import settings
from app.core.seguridad import token_valido

log = logging.getLogger("apaec.gateway")
router = APIRouter()

DEVICES = ("velocista", "cronometro")
SEQ_REMEMBERED = 256


def _ms() -> int:
    return int(time.time() * 1000)


@dataclass
class Connection:
    ws: WebSocket
    manifest: Manifest | None = None
    last_status: Status | None = None
    last_t_ms: int = -1
    seq_out: int = 0
    seq_received: deque = field(default_factory=lambda: deque(maxlen=SEQ_REMEMBERED))
    warnings_seen: set[str] = field(default_factory=set)

    def next_seq(self) -> int:
        self.seq_out = (self.seq_out + 1) % 2**32
        return self.seq_out


class Consoles:
    """Consolas conectadas a /ws/consola; solo reciben."""

    def __init__(self) -> None:
        self.active: set[WebSocket] = set()

    async def broadcast(
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
        for ws in list(self.active):
            try:
                await ws.send_json(mensaje)
            except Exception:
                self.active.discard(ws)

    async def event(self, codigo: str, nivel: str, mensaje: str, **datos) -> None:
        await self.broadcast(
            "api", "evento", {"codigo": codigo, "nivel": nivel, "mensaje": mensaje, "datos": datos}
        )


consoles = Consoles()
connections: dict[str, Connection] = {}


def device_status() -> dict[str, bool]:
    return {name: name in connections for name in DEVICES}


async def send(name: str, tipo: str, datos: dict) -> int:
    """Envía un mensaje de la API a un dispositivo conectado. Devuelve el seq usado."""
    connection = connections[name]
    seq = connection.next_seq()
    await connection.ws.send_json({"tipo": tipo, "seq": seq, "ts": _ms() % 2**32, "datos": datos})
    return seq


async def _ack(connection: Connection, seq: int) -> None:
    await connection.ws.send_json(
        {"tipo": "ack", "seq": seq, "ts": _ms() % 2**32, "datos": {"ok": True}}
    )


async def _process(name: str, connection: Connection, raw: str) -> None:
    try:
        envelope = Envelope.model_validate(json.loads(raw))
        model = validate_data(name, envelope.tipo, envelope.datos)
    except (json.JSONDecodeError, ValidationError, InvalidMessage) as e:
        log.warning("Mensaje inválido de %s: %s", name, e)
        await consoles.event(
            "mensaje_invalido", "aviso", f"Mensaje inválido de {name}", detalle=str(e)[:300]
        )
        return

    with_ack = requires_ack(name, envelope.tipo)
    if with_ack and envelope.seq in connection.seq_received:
        await _ack(connection, envelope.seq)  # duplicado: se vuelve a confirmar, no se reprocesa
        return

    if name == "velocista":
        if isinstance(model, Manifest):
            connection.manifest = model
            connection.warnings_seen.clear()
            connection.last_t_ms = -1
        elif connection.manifest is None:
            await consoles.event(
                "manifiesto_faltante", "aviso", "El robot envió datos antes del manifiesto"
            )
            return
        else:
            if isinstance(model, Signals):
                if model.t_ms <= connection.last_t_ms:
                    return  # fuera de orden: la siguiente muestra la reemplaza
                connection.last_t_ms = model.t_ms
            if isinstance(model, Status):
                connection.last_status = model
            if isinstance(model, Status | Signals):
                grupo = "estado" if isinstance(model, Status) else "senales"
                for warning in check_channels(connection.manifest, grupo, model.canales):
                    if warning not in connection.warnings_seen:  # cada aviso una vez por conexión
                        connection.warnings_seen.add(warning)
                        await consoles.event("canal_invalido", "aviso", warning)

    if with_ack:
        connection.seq_received.append(envelope.seq)
        await _ack(connection, envelope.seq)
    await consoles.broadcast(name, envelope.tipo, envelope.datos, envelope.seq, envelope.ts)


async def _serve(ws: WebSocket, name: str, expected_token: str) -> None:
    if not token_valido(
        ws.headers.get("x-device-token") or ws.query_params.get("token"), expected_token
    ):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        log.warning("Conexión rechazada de %s: token inválido", name)
        return
    await ws.accept()
    connection = Connection(ws)
    connections[name] = connection
    log.info("%s conectado", name)
    await consoles.broadcast("api", "enlace", {"dispositivo": name, "conectado": True})
    try:
        while True:
            await _process(name, connection, await ws.receive_text())
    except WebSocketDisconnect:
        pass
    finally:
        if connections.get(name) is connection:
            del connections[name]
        log.info("%s desconectado", name)
        await consoles.broadcast("api", "enlace", {"dispositivo": name, "conectado": False})


@router.websocket("/ws/robot")
async def ws_robot(ws: WebSocket) -> None:
    await _serve(ws, "velocista", settings.device_token_velocista)


@router.websocket("/ws/cronometro")
async def ws_cronometro(ws: WebSocket) -> None:
    await _serve(ws, "cronometro", settings.device_token_cronometro)


@router.websocket("/ws/consola")
async def ws_consola(ws: WebSocket) -> None:
    await ws.accept()
    consoles.active.add(ws)
    await ws.send_json(
        {
            "origen": "api",
            "tipo": "hola",
            "seq": 0,
            "ts": 0,
            "datos": {"dispositivos": device_status()},
            "recibido_ms": _ms(),
        }
    )
    try:
        while True:
            await ws.receive_text()  # la consola solo escucha; sus acciones van por REST
    except WebSocketDisconnect:
        consoles.active.discard(ws)


def robot_running(robot_id: str) -> bool:
    connection = connections.get("velocista")
    return bool(
        connection
        and connection.manifest
        and connection.manifest.id == robot_id
        and connection.last_status
        and connection.last_status.estado == "running"
    )

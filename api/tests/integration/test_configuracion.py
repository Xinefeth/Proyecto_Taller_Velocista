"""Configurar modo y línea de punta a punta por el TestClient de FastAPI (HU-18).

No usa base de datos: modo/línea son comandos puros del gateway. Se arma una conexión falsa del
velocista en memoria y se reemplaza ws.send para no abrir una WebSocket real.
"""

import json

import pytest

from app.contract import Manifest
from app.contract.robot import Status
from app.core.config import RAIZ_REPO
from app.gateway import ws

MANIFIESTO = Manifest.model_validate(
    json.loads(
        (RAIZ_REPO / "docs" / "contrato" / "ejemplos" / "velocista.manifiesto.json").read_text(
            encoding="utf-8"
        )
    )["datos"]
)


class ConexionFalsa:
    def __init__(self, manifest=None, last_status=None):
        self.manifest = manifest
        self.last_status = last_status


def status(**cambios) -> Status:
    base = dict(
        estado="ready",
        calibrado=True,
        modo="prueba",
        linea="negra",
        controlador="pid",
        lazo_hz=1000,
        rssi_dbm=-50,
        canales={"bateria_v": 8.0},
    )
    return Status.model_validate(base | cambios)


@pytest.fixture()
def robot(monkeypatch):
    """Instala una conexión del velocista y captura ws.send. Devuelve un setter y la lista enviados."""
    enviados = []

    async def send_falso(name, tipo, datos):
        enviados.append((name, tipo, datos))
        return 7

    monkeypatch.setattr(ws, "send", send_falso)
    conn_previa = ws.connections.get("velocista")

    def conectar(conexion):
        ws.connections.pop("velocista", None)
        if conexion is not None:
            ws.connections["velocista"] = conexion

    yield conectar, enviados

    ws.connections.pop("velocista", None)
    if conn_previa is not None:
        ws.connections["velocista"] = conn_previa


def motivo(resp) -> str:
    return resp.json()["detail"]["motivo"]


# --------------------------- lectura (Tarea 7.1) ---------------------------


def test_leer_config_ok(cliente, robot):
    conectar, _ = robot
    conectar(ConexionFalsa(MANIFIESTO, status(modo="competencia", linea="blanca")))
    r = cliente.get("/api/devices/velocista/config")
    assert r.status_code == 200
    assert r.json() == {"modo": "competencia", "linea": "blanca"}


@pytest.mark.parametrize("conexion", [None, "sin_estado"])
def test_leer_config_sin_estado(cliente, robot, conexion):
    conectar, _ = robot
    conectar(None if conexion is None else ConexionFalsa(MANIFIESTO, None))
    r = cliente.get("/api/devices/velocista/config")
    assert r.status_code == 404
    assert motivo(r) == "sin_estado"


# --------------------------- escritura: matriz de guardas (Tarea 7.2) ---------------------------


@pytest.mark.parametrize("estado_", ["ready", "stopped", "calibrating", "error"])
def test_cambiar_modo_aceptado_si_no_corre(cliente, robot, estado_):
    conectar, enviados = robot
    conectar(ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    r = cliente.post("/api/devices/velocista/config/modo", json={"modo": "competencia"})
    assert r.status_code == 202 and r.json()["seq"] == 7
    assert enviados == [("velocista", "modo", {"modo": "competencia"})]


@pytest.mark.parametrize("estado_", ["ready", "stopped", "calibrating", "error"])
def test_cambiar_linea_aceptado_si_no_corre(cliente, robot, estado_):
    conectar, enviados = robot
    conectar(ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    r = cliente.post("/api/devices/velocista/config/linea", json={"color": "blanca"})
    assert r.status_code == 202 and r.json()["seq"] == 7
    assert enviados == [("velocista", "linea", {"color": "blanca"})]


@pytest.mark.parametrize(
    ("conexion", "codigo", "esperado"),
    [
        (None, 409, "sin_manifiesto"),
        (ConexionFalsa(None, None), 409, "sin_manifiesto"),
        (
            ConexionFalsa(MANIFIESTO, status(estado="running", modo="competencia")),
            409,
            "bloqueado_competencia",
        ),
        (ConexionFalsa(MANIFIESTO, status(estado="running", modo="prueba")), 409, "ocupado"),
    ],
)
def test_cambiar_modo_guardas_rechazan_sin_enviar(cliente, robot, conexion, codigo, esperado):
    conectar, enviados = robot
    conectar(conexion)
    r = cliente.post("/api/devices/velocista/config/modo", json={"modo": "prueba"})
    assert r.status_code == codigo and motivo(r) == esperado
    assert enviados == []


def test_cambiar_modo_valor_invalido(cliente, robot):
    conectar, enviados = robot
    conectar(ConexionFalsa(MANIFIESTO, status()))
    r = cliente.post("/api/devices/velocista/config/modo", json={"modo": "turbo"})
    assert r.status_code == 422 and motivo(r) == "comando_invalido"
    assert enviados == []


def test_cambiar_modo_comando_no_declarado(cliente, robot):
    conectar, enviados = robot
    sin_modo = MANIFIESTO.model_copy(update={"comandos": ["calibrate", "start", "stop"]})
    conectar(ConexionFalsa(sin_modo, status()))
    r = cliente.post("/api/devices/velocista/config/modo", json={"modo": "prueba"})
    assert r.status_code == 422 and motivo(r) == "comando_desconocido"
    assert enviados == []


def test_cambiar_modo_caida_del_enlace(cliente, robot, monkeypatch):
    conectar, _ = robot
    conectar(ConexionFalsa(MANIFIESTO, status()))

    async def send_cae(name, tipo, datos):
        raise OSError("enlace caído")

    monkeypatch.setattr(ws, "send", send_cae)
    r = cliente.post("/api/devices/velocista/config/modo", json={"modo": "prueba"})
    assert r.status_code == 503 and motivo(r) == "dispositivo_no_disponible"

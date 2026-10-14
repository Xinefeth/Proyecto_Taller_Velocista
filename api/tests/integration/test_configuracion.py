"""Modo y línea de punta a punta: envían al robot y PERSISTEN en la base de datos (HU-18).

Esquema temporal con las migraciones (incluye v001 sembrado y la tabla configuracion_robot). Se
simula el velocista en memoria (ws.connections) y se reemplaza ws.send para no abrir una WebSocket.
"""

import importlib.util
import json
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.contract import Manifest
from app.contract.robot import Status
from app.core.config import RAIZ_REPO
from app.core.db import engine, get_session
from app.gateway import ws
from app.main import app
from tests.integration import _seed

pytestmark = pytest.mark.integracion

MANIFIESTO = Manifest.model_validate(
    json.loads(
        (RAIZ_REPO / "docs" / "contrato" / "ejemplos" / "velocista.manifiesto.json").read_text(
            encoding="utf-8"
        )
    )["datos"]
)
ROBOT = MANIFIESTO.id  # "v001", el robot sembrado por el dataset de prueba _seed


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
def entorno(requiere_db, monkeypatch):
    """Esquema temporal con migraciones 0002..0007; velocista simulado y ws.send capturado."""
    esquema = f"prueba_config_{uuid4().hex}"
    enviados = []

    async def send_falso(name, tipo, datos):
        enviados.append((name, tipo, datos))
        return 7

    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{esquema}"'))
            conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
            with Operations.context(MigrationContext.configure(conn)):
                for nombre in [
                    "0002_catalogo", "0003_robot", "0004_versiones",
                    "0005_operaciones", "0007_configuracion",
                ]:
                    ruta = Path(__file__).resolve().parents[2] / f"migrations/versions/{nombre}.py"
                    spec = importlib.util.spec_from_file_location(nombre, ruta)
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)
                    modulo.upgrade()
                # La BD de produccion arranca vacia; el dataset v001 se siembra solo para la prueba.
                _seed.upgrade()
        factory = sessionmaker(
            bind=engine.execution_options(schema_translate_map={None: esquema}),
            expire_on_commit=False,
        )

        def sesion():
            with factory() as s:
                yield s

        monkeypatch.setattr(ws, "send", send_falso)
        conn_previa = ws.connections.get("velocista")
        anterior = app.dependency_overrides.copy()
        app.dependency_overrides[get_session] = sesion
        try:
            with TestClient(app) as client:
                def conectar(conexion):
                    ws.connections.pop("velocista", None)
                    if conexion is not None:
                        ws.connections["velocista"] = conexion

                yield client, conectar, enviados
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(anterior)
            ws.connections.pop("velocista", None)
            if conn_previa is not None:
                ws.connections["velocista"] = conn_previa
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{esquema}" CASCADE'))


def motivo(resp):
    return resp.json()["detail"]["motivo"]


def test_lectura_sin_configuracion(entorno):
    client, conectar, _ = entorno
    conectar(ConexionFalsa(MANIFIESTO, status()))
    r = client.get(f"/api/robots/{ROBOT}/modo-linea")
    assert r.status_code == 404 and motivo(r) == "sin_configuracion"


def test_cambiar_modo_envia_y_persiste(entorno):
    client, conectar, enviados = entorno
    conectar(ConexionFalsa(MANIFIESTO, status()))
    r = client.post(f"/api/robots/{ROBOT}/modo-linea/modo", json={"modo": "competencia"})
    assert r.status_code == 202 and r.json()["seq"] == 7
    assert enviados == [("velocista", "modo", {"modo": "competencia"})]
    # Persistió y la lectura lo devuelve desde la BD.
    leido = client.get(f"/api/robots/{ROBOT}/modo-linea").json()
    assert leido["modo"] == "competencia" and leido["linea"] is None


def test_cambiar_linea_persiste_junto_al_modo(entorno):
    client, conectar, _ = entorno
    conectar(ConexionFalsa(MANIFIESTO, status()))
    client.post(f"/api/robots/{ROBOT}/modo-linea/modo", json={"modo": "prueba"})
    client.post(f"/api/robots/{ROBOT}/modo-linea/linea", json={"color": "blanca"})
    leido = client.get(f"/api/robots/{ROBOT}/modo-linea").json()
    assert (leido["modo"], leido["linea"]) == ("prueba", "blanca")


def test_valor_invalido_no_envia_ni_persiste(entorno):
    client, conectar, enviados = entorno
    conectar(ConexionFalsa(MANIFIESTO, status()))
    r = client.post(f"/api/robots/{ROBOT}/modo-linea/modo", json={"modo": "turbo"})
    assert r.status_code == 422 and motivo(r) == "comando_invalido"
    assert enviados == []
    assert client.get(f"/api/robots/{ROBOT}/modo-linea").status_code == 404  # no persistió


@pytest.mark.parametrize(
    ("conexion", "codigo", "esperado"),
    [
        (None, 409, "sin_manifiesto"),
        (ConexionFalsa(None, None), 409, "sin_manifiesto"),
        (ConexionFalsa(MANIFIESTO, status(estado="running", modo="competencia")), 409, "bloqueado_competencia"),
        (ConexionFalsa(MANIFIESTO, status(estado="running", modo="prueba")), 409, "ocupado"),
    ],
)
def test_guardas_rechazan_sin_enviar_ni_persistir(entorno, conexion, codigo, esperado):
    client, conectar, enviados = entorno
    conectar(conexion)
    r = client.post(f"/api/robots/{ROBOT}/modo-linea/modo", json={"modo": "prueba"})
    assert r.status_code == codigo and motivo(r) == esperado
    assert enviados == []
    assert client.get(f"/api/robots/{ROBOT}/modo-linea").status_code == 404


def test_caida_del_enlace_no_persiste(entorno, monkeypatch):
    client, conectar, _ = entorno
    conectar(ConexionFalsa(MANIFIESTO, status()))

    async def send_cae(name, tipo, datos):
        raise OSError("enlace caído")

    monkeypatch.setattr(ws, "send", send_cae)
    r = client.post(f"/api/robots/{ROBOT}/modo-linea/modo", json={"modo": "prueba"})
    assert r.status_code == 503 and motivo(r) == "dispositivo_no_disponible"
    assert client.get(f"/api/robots/{ROBOT}/modo-linea").status_code == 404

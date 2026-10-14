"""Guardas del envío de modo/línea al velocista, probadas sin red ni BD (HU-18).

Prueban el puerto del gateway `aplicar_config_velocista` (validación contra el manifiesto/estado
vivos + guarda `ocupado` + envío). La persistencia en BD se prueba en integración.
"""

import asyncio
import contextlib
import json

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.contract import Manifest
from app.contract.robot import Status
from app.core.config import RAIZ_REPO
from app.core.errores import ErrorDeNegocio
from app.gateway import aplicacion, ws
from app.gateway.aplicacion import validar_cambio_config

MANIFIESTO = Manifest.model_validate(
    json.loads(
        (RAIZ_REPO / "docs" / "contrato" / "ejemplos" / "velocista.manifiesto.json").read_text(
            encoding="utf-8"
        )
    )["datos"]
)
ROBOT = MANIFIESTO.id  # "v001"
NO_CORRIENDO = ["ready", "stopped", "calibrating", "error"]


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


@contextlib.contextmanager
def gateway(conexion, al_enviar=None):
    """Instala una conexión falsa del velocista y un ws.send capturador; restaura todo al salir."""
    conn_previa = ws.connections.get("velocista")
    send_previo = ws.send
    enviados = []

    async def send_falso(name, tipo, datos):
        enviados.append((name, tipo, datos))
        if al_enviar is not None:
            raise al_enviar
        return 42

    ws.connections.pop("velocista", None)
    if conexion is not None:
        ws.connections["velocista"] = conexion
    ws.send = send_falso
    try:
        yield enviados
    finally:
        ws.send = send_previo
        ws.connections.pop("velocista", None)
        if conn_previa is not None:
            ws.connections["velocista"] = conn_previa


def enviar(tipo, datos, conexion, al_enviar=None, robot=ROBOT):
    """Ejecuta el puerto y devuelve (motivo|None, seq|None, enviados)."""
    with gateway(conexion, al_enviar) as enviados:
        try:
            seq = asyncio.run(aplicacion.aplicar_config_velocista(robot, tipo, datos))
            return None, seq, enviados
        except ErrorDeNegocio as e:
            return e.motivo, None, enviados


def modo(valor, conexion, **kw):
    return enviar("modo", {"modo": valor}, conexion, **kw)


def linea(valor, conexion, **kw):
    return enviar("linea", {"color": valor}, conexion, **kw)


# --------------------------- validar_cambio_config ---------------------------


def test_ocupado_en_prueba_corriendo():
    with pytest.raises(ErrorDeNegocio) as exc:
        validar_cambio_config(status(estado="running", modo="prueba"))
    assert exc.value.motivo == "ocupado"


@pytest.mark.parametrize(
    "estado_",
    [status(estado="running", modo="competencia"), status(estado="ready"), None],
)
def test_validar_cambio_config_no_bloquea_otros_casos(estado_):
    assert validar_cambio_config(estado_) is None


# --------------------------- envío (unit) ---------------------------


def test_cambiar_modo_valido_envia_un_comando():
    motivo_, seq, enviados = modo("competencia", ConexionFalsa(MANIFIESTO, status()))
    assert motivo_ is None and seq == 42
    assert enviados == [("velocista", "modo", {"modo": "competencia"})]


def test_cambiar_linea_valido_envia_un_comando():
    motivo_, seq, enviados = linea("blanca", ConexionFalsa(MANIFIESTO, status()))
    assert motivo_ is None and seq == 42
    assert enviados == [("velocista", "linea", {"color": "blanca"})]


@pytest.mark.parametrize(
    ("conexion", "esperado"),
    [
        (None, "sin_manifiesto"),
        (ConexionFalsa(None, None), "sin_manifiesto"),
        (
            ConexionFalsa(MANIFIESTO, status(estado="running", modo="competencia")),
            "bloqueado_competencia",
        ),
        (ConexionFalsa(MANIFIESTO, status(estado="running", modo="prueba")), "ocupado"),
    ],
)
def test_guardas_no_envian(conexion, esperado):
    motivo_, _, enviados = modo("prueba", conexion)
    assert motivo_ == esperado
    assert enviados == []


def test_robot_distinto_es_sin_manifiesto():
    # Un velocista conectado, pero el request pide otro robot.
    motivo_, _, enviados = modo("prueba", ConexionFalsa(MANIFIESTO, status()), robot="vZZZ")
    assert motivo_ == "sin_manifiesto"
    assert enviados == []


def test_valor_invalido_es_comando_invalido():
    motivo_, _, enviados = modo("rapido", ConexionFalsa(MANIFIESTO, status()))
    assert motivo_ == "comando_invalido"
    assert enviados == []


def test_comando_no_declarado():
    sin_modo = MANIFIESTO.model_copy(update={"comandos": ["calibrate", "start", "stop"]})
    motivo_, _, enviados = modo("prueba", ConexionFalsa(sin_modo, status()))
    assert motivo_ == "comando_desconocido"
    assert enviados == []


@pytest.mark.parametrize("error", [KeyError("x"), RuntimeError("x"), OSError("x")])
def test_caida_del_enlace(error):
    motivo_, seq, enviados = modo("prueba", ConexionFalsa(MANIFIESTO, status()), al_enviar=error)
    assert motivo_ == "dispositivo_no_disponible" and seq is None
    assert enviados == [("velocista", "modo", {"modo": "prueba"})]


# --------------------------- propiedades (Hypothesis) ---------------------------

SIN_FIXTURE = settings(
    max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture]
)

valores_invalidos = st.one_of(
    st.text(max_size=10).filter(lambda v: v not in ("prueba", "competencia", "negra", "blanca")),
    st.integers(),
    st.booleans(),
    st.none(),
    st.lists(st.integers(), max_size=3),
)


# Propiedad 2: cambio válido en estado no-corriendo envía el comando y devuelve el seq.
@SIN_FIXTURE
@given(estado_=st.sampled_from(NO_CORRIENDO), valor=st.sampled_from(["prueba", "competencia"]))
def test_prop_modo_valido_envia(estado_, valor):
    motivo_, seq, enviados = modo(valor, ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    assert motivo_ is None and seq == 42
    assert enviados == [("velocista", "modo", {"modo": valor})]


@SIN_FIXTURE
@given(estado_=st.sampled_from(NO_CORRIENDO), valor=st.sampled_from(["negra", "blanca"]))
def test_prop_linea_valido_envia(estado_, valor):
    motivo_, seq, enviados = linea(valor, ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    assert motivo_ is None and seq == 42
    assert enviados == [("velocista", "linea", {"color": valor})]


# Propiedad 3: valor inválido → comando_invalido y no envía, sin importar el estado.
@SIN_FIXTURE
@given(valor=valores_invalidos, estado_=st.sampled_from([*NO_CORRIENDO, "running"]))
def test_prop_valor_invalido(valor, estado_):
    motivo_, _, enviados = modo(valor, ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    assert motivo_ == "comando_invalido"
    assert enviados == []


# Propiedad 4: robot corriendo rechaza con el motivo según el modo y no envía.
@SIN_FIXTURE
@given(
    valor=st.sampled_from(["prueba", "competencia"]), m=st.sampled_from(["prueba", "competencia"])
)
def test_prop_corriendo_rechaza(valor, m):
    motivo_, _, enviados = modo(valor, ConexionFalsa(MANIFIESTO, status(estado="running", modo=m)))
    assert motivo_ == ("ocupado" if m == "prueba" else "bloqueado_competencia")
    assert enviados == []


# Propiedad 5: sin manifiesto → sin_manifiesto y no envía.
@SIN_FIXTURE
@given(valor=st.sampled_from(["negra", "blanca"]), sin_conn=st.booleans())
def test_prop_sin_manifiesto(valor, sin_conn):
    conexion = None if sin_conn else ConexionFalsa(None, None)
    motivo_, _, enviados = linea(valor, conexion)
    assert motivo_ == "sin_manifiesto"
    assert enviados == []


# Propiedad 6: comando no declarado → comando_desconocido y no envía.
@SIN_FIXTURE
@given(valor=st.sampled_from(["prueba", "competencia"]))
def test_prop_comando_no_declarado(valor):
    sin_modo = MANIFIESTO.model_copy(update={"comandos": ["calibrate", "start", "stop", "linea"]})
    motivo_, _, enviados = modo(valor, ConexionFalsa(sin_modo, status()))
    assert motivo_ == "comando_desconocido"
    assert enviados == []


# Propiedad 7: caída del enlace tras validar → dispositivo_no_disponible, sin seq exitoso.
@SIN_FIXTURE
@given(
    valor=st.sampled_from(["prueba", "competencia"]),
    error=st.sampled_from([KeyError("x"), RuntimeError("x"), OSError("x")]),
)
def test_prop_caida_enlace(valor, error):
    motivo_, seq, _ = modo(valor, ConexionFalsa(MANIFIESTO, status()), al_enviar=error)
    assert motivo_ == "dispositivo_no_disponible" and seq is None

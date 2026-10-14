"""Reglas de configurar modo y línea del velocista, probadas sin red (HU-18).

Unit + propiedades (Hypothesis). El gateway vive en memoria: se arma una conexión falsa en
ws.connections y se reemplaza ws.send para capturar lo enviado sin tocar una WebSocket real.
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
from app.gateway import configuracion, ws
from app.gateway.configuracion import (
    CambioLinea,
    CambioModo,
    get_robot_config,
    set_line,
    set_mode,
    validar_cambio_config,
)

MANIFIESTO = Manifest.model_validate(
    json.loads(
        (RAIZ_REPO / "docs" / "contrato" / "ejemplos" / "velocista.manifiesto.json").read_text(
            encoding="utf-8"
        )
    )["datos"]
)
NO_CORRIENDO = ["ready", "stopped", "calibrating", "error"]


class ConexionFalsa:
    """Imita app.gateway.ws.Connection con solo lo que leen los endpoints de HU-18."""

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
    """Instala una conexión falsa y un ws.send capturador; restaura todo al salir.

    `conexion` es None (sin conexión) o una ConexionFalsa. `al_enviar`, si se pasa, es una
    excepción que ws.send lanza para simular la caída del enlace.
    """
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


def motivo_modo(valor, conexion, al_enviar=None):
    """Ejecuta set_mode y devuelve (motivo|None, seq|None, enviados)."""
    with gateway(conexion, al_enviar) as enviados:
        try:
            resp = asyncio.run(set_mode(CambioModo(modo=valor)))
            return None, resp.seq, enviados
        except ErrorDeNegocio as e:
            return e.motivo, None, enviados


def motivo_linea(valor, conexion, al_enviar=None):
    with gateway(conexion, al_enviar) as enviados:
        try:
            resp = asyncio.run(set_line(CambioLinea(color=valor)))
            return None, resp.seq, enviados
        except ErrorDeNegocio as e:
            return e.motivo, None, enviados


# --------------------------- validar_cambio_config (Tarea 1.2) ---------------------------


def test_ocupado_en_prueba_corriendo():
    with pytest.raises(ErrorDeNegocio) as exc:
        validar_cambio_config(status(estado="running", modo="prueba"))
    assert exc.value.motivo == "ocupado"


@pytest.mark.parametrize(
    "estado_",
    [status(estado="running", modo="competencia"), status(estado="ready"), None],
)
def test_validar_cambio_config_no_bloquea_otros_casos(estado_):
    # competencia+running ya lo bloquea validar_comando; aquí no debe lanzar.
    assert validar_cambio_config(estado_) is None


# --------------------------- read endpoint (Tarea 2.2) ---------------------------


def test_leer_config_proyecta_el_estado_vivo():
    with gateway(ConexionFalsa(MANIFIESTO, status(modo="competencia", linea="blanca"))):
        resp = get_robot_config()
    assert (resp.modo, resp.linea) == ("competencia", "blanca")


@pytest.mark.parametrize("conexion", [None, ConexionFalsa(MANIFIESTO, None)])
def test_leer_config_sin_estado(conexion):
    with gateway(conexion):
        with pytest.raises(ErrorDeNegocio) as exc:
            get_robot_config()
    assert exc.value.motivo == "sin_estado"


# --------------------------- write endpoints (Tarea 3.3) ---------------------------


def test_cambiar_modo_valido_envia_un_comando():
    motivo, seq, enviados = motivo_modo("competencia", ConexionFalsa(MANIFIESTO, status()))
    assert motivo is None and seq == 42
    assert enviados == [("velocista", "modo", {"modo": "competencia"})]


def test_cambiar_linea_valido_envia_un_comando():
    motivo, seq, enviados = motivo_linea("blanca", ConexionFalsa(MANIFIESTO, status()))
    assert motivo is None and seq == 42
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
def test_cambiar_modo_guardas_no_envian(conexion, esperado):
    motivo, _, enviados = motivo_modo("prueba", conexion)
    assert motivo == esperado
    assert enviados == []


def test_valor_invalido_es_comando_invalido_y_no_envia():
    motivo, _, enviados = motivo_modo("rapido", ConexionFalsa(MANIFIESTO, status()))
    assert motivo == "comando_invalido"
    assert enviados == []


def test_comando_no_declarado_en_manifiesto():
    sin_modo = MANIFIESTO.model_copy(update={"comandos": ["calibrate", "start", "stop"]})
    motivo, _, enviados = motivo_modo("prueba", ConexionFalsa(sin_modo, status()))
    assert motivo == "comando_desconocido"
    assert enviados == []


@pytest.mark.parametrize("error", [KeyError("x"), RuntimeError("x"), OSError("x")])
def test_caida_del_enlace_devuelve_dispositivo_no_disponible(error):
    motivo, _, enviados = motivo_modo(
        "prueba", ConexionFalsa(MANIFIESTO, status()), al_enviar=error
    )
    assert motivo == "dispositivo_no_disponible"
    assert enviados == [("velocista", "modo", {"modo": "prueba"})]  # se intentó enviar


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


# Propiedad 1: la lectura proyecta el estado vivo o devuelve sin_estado.
@SIN_FIXTURE
@given(
    tiene_conn=st.booleans(),
    tiene_estado=st.booleans(),
    modo=st.sampled_from(["prueba", "competencia"]),
    linea=st.sampled_from(["negra", "blanca"]),
)
def test_prop_lectura(tiene_conn, tiene_estado, modo, linea):
    if not tiene_conn:
        conexion = None
    elif not tiene_estado:
        conexion = ConexionFalsa(MANIFIESTO, None)
    else:
        conexion = ConexionFalsa(MANIFIESTO, status(modo=modo, linea=linea))
    with gateway(conexion):
        if tiene_conn and tiene_estado:
            resp = get_robot_config()
            assert (resp.modo, resp.linea) == (modo, linea)
        else:
            with pytest.raises(ErrorDeNegocio) as exc:
                get_robot_config()
            assert exc.value.motivo == "sin_estado"


# Propiedad 2: cambio válido en estado no-corriendo envía el comando y devuelve el seq.
@SIN_FIXTURE
@given(estado_=st.sampled_from(NO_CORRIENDO), valor=st.sampled_from(["prueba", "competencia"]))
def test_prop_modo_valido_envia(estado_, valor):
    motivo, seq, enviados = motivo_modo(valor, ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    assert motivo is None and seq == 42
    assert enviados == [("velocista", "modo", {"modo": valor})]


@SIN_FIXTURE
@given(estado_=st.sampled_from(NO_CORRIENDO), valor=st.sampled_from(["negra", "blanca"]))
def test_prop_linea_valido_envia(estado_, valor):
    motivo, seq, enviados = motivo_linea(valor, ConexionFalsa(MANIFIESTO, status(estado=estado_)))
    assert motivo is None and seq == 42
    assert enviados == [("velocista", "linea", {"color": valor})]


# Propiedad 3: valor inválido → comando_invalido y no envía, sin importar el estado.
@SIN_FIXTURE
@given(valor=valores_invalidos, estado_=st.sampled_from([*NO_CORRIENDO, "running"]))
def test_prop_valor_invalido(valor, estado_):
    conexion = ConexionFalsa(MANIFIESTO, status(estado=estado_))
    motivo, _, enviados = motivo_modo(valor, conexion)
    assert motivo == "comando_invalido"
    assert enviados == []


# Propiedad 4: robot corriendo rechaza con el motivo según el modo y no envía.
@SIN_FIXTURE
@given(
    valor=st.sampled_from(["prueba", "competencia"]),
    modo=st.sampled_from(["prueba", "competencia"]),
)
def test_prop_corriendo_rechaza(valor, modo):
    conexion = ConexionFalsa(MANIFIESTO, status(estado="running", modo=modo))
    motivo, _, enviados = motivo_modo(valor, conexion)
    assert motivo == ("ocupado" if modo == "prueba" else "bloqueado_competencia")
    assert enviados == []


# Propiedad 5: sin manifiesto → sin_manifiesto y no envía.
@SIN_FIXTURE
@given(valor=st.sampled_from(["negra", "blanca"]), sin_conn=st.booleans())
def test_prop_sin_manifiesto(valor, sin_conn):
    conexion = None if sin_conn else ConexionFalsa(None, None)
    motivo, _, enviados = motivo_linea(valor, conexion)
    assert motivo == "sin_manifiesto"
    assert enviados == []


# Propiedad 6: comando no declarado → comando_desconocido y no envía.
@SIN_FIXTURE
@given(valor=st.sampled_from(["prueba", "competencia"]))
def test_prop_comando_no_declarado(valor):
    sin_modo = MANIFIESTO.model_copy(update={"comandos": ["calibrate", "start", "stop", "linea"]})
    motivo, _, enviados = motivo_modo(valor, ConexionFalsa(sin_modo, status()))
    assert motivo == "comando_desconocido"
    assert enviados == []


# Propiedad 7: caída del enlace tras validar → dispositivo_no_disponible, sin seq exitoso.
@SIN_FIXTURE
@given(
    valor=st.sampled_from(["prueba", "competencia"]),
    error=st.sampled_from([KeyError("x"), RuntimeError("x"), OSError("x")]),
)
def test_prop_caida_enlace(valor, error):
    motivo, seq, _ = motivo_modo(valor, ConexionFalsa(MANIFIESTO, status()), al_enviar=error)
    assert motivo == "dispositivo_no_disponible" and seq is None


def _silence_unused():
    # configuracion se importa para asegurar el registro del router en cobertura.
    assert configuracion.router is not None

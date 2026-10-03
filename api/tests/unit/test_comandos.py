"""Reglas de comandos hacia el robot, probadas sin red (EN-02)."""

import pytest

from app.contrato import Manifiesto
from app.contrato.robot import Estado
from app.core.errores import ErrorDeNegocio
from app.gateway.comandos import validar_comando


@pytest.fixture()
def manifiesto(ejemplo):
    return Manifiesto.model_validate(ejemplo("velocista.manifiesto.json")["datos"])


def estado(**cambios) -> Estado:
    base = dict(
        estado="listo",
        calibrado=True,
        modo="prueba",
        linea="negra",
        controlador="pid",
        lazo_hz=1000,
        rssi_dbm=-50,
        canales={"bateria_v": 8.0},
    )
    return Estado.model_validate(base | cambios)


def motivo(*args) -> str | None:
    try:
        validar_comando(*args)
        return None
    except ErrorDeNegocio as e:
        return e.motivo


SETUP_OK = {"controlador": "pid", "parametros": {"kp": 0.4}}


def test_arrancar_calibrado_se_acepta(manifiesto):
    assert motivo("velocista", "arrancar", {}, manifiesto, estado()) is None


def test_arrancar_sin_calibrar(manifiesto):
    assert (
        motivo("velocista", "arrancar", {}, manifiesto, estado(calibrado=False)) == "no_calibrado"
    )


def test_en_competencia_corriendo_solo_detener(manifiesto):
    e = estado(modo="competencia", estado="corriendo")
    assert motivo("velocista", "setup", SETUP_OK, manifiesto, e) == "bloqueado_competencia"
    assert motivo("velocista", "detener", {}, manifiesto, e) is None


@pytest.mark.parametrize(
    ("parametros", "esperado"),
    [
        ({"kp": 9}, "fuera_de_rango"),
        ({"vel_base": 150.5}, "fuera_de_rango"),
        ({"kx": 1}, "parametro_desconocido"),
    ],
)
def test_setup_validado_contra_el_manifiesto(manifiesto, parametros, esperado):
    datos = {"controlador": "pid", "parametros": parametros}
    assert motivo("velocista", "setup", datos, manifiesto, estado()) == esperado


def test_controlador_no_disponible(manifiesto):
    datos = {"controlador": "difuso", "parametros": {"kp": 1}}
    assert motivo("velocista", "setup", datos, manifiesto, estado()) == "controlador_no_disponible"


def test_sin_manifiesto():
    assert motivo("velocista", "calibrar", {}, None, None) == "sin_manifiesto"


def test_tipo_desconocido_y_ack(manifiesto):
    assert motivo("velocista", "volar", {}, manifiesto, estado()) == "comando_invalido"
    assert motivo("velocista", "ack", {}, manifiesto, estado()) == "comando_invalido"


def test_rearmar_cronometro():
    assert motivo("cronometro", "rearmar", {}, None, None) is None

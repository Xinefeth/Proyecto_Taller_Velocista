"""El contrato del código y los ejemplos de docs/contrato no pueden divergir."""

import copy
import json

import pytest

from app.contrato import CATALOGO, Manifiesto, MensajeInvalido, Sobre, validar_datos
from app.contrato.robot import Setup
from app.contrato.validacion import revisar_canales, revisar_setup
from app.core.config import RAIZ_REPO

EJEMPLOS = RAIZ_REPO / "docs" / "contrato" / "ejemplos"


def _emisor(archivo: str) -> str:
    return archivo.split(".")[0].replace("_a_", "->")


def _ejemplo(nombre: str) -> dict:
    return json.loads((EJEMPLOS / nombre).read_text())


def _manifiesto() -> dict:
    return copy.deepcopy(_ejemplo("velocista.manifiesto.json")["datos"])


@pytest.mark.parametrize("archivo", sorted(p.name for p in EJEMPLOS.glob("*.json")))
def test_cada_ejemplo_cumple_el_contrato(archivo):
    sobre = Sobre.model_validate(_ejemplo(archivo))
    validar_datos(_emisor(archivo), sobre.tipo, sobre.datos)


def test_todo_tipo_del_catalogo_tiene_ejemplo():
    con_ejemplo = {(_emisor(p.name), p.name.split(".")[1]) for p in EJEMPLOS.glob("*.json")}
    sin_ejemplo = {k for k in CATALOGO if k[1] != "ack" or k[0] == "velocista"} - con_ejemplo
    assert not sin_ejemplo - {
        ("api->velocista", "calibrar"),
        ("api->velocista", "detener"),
        ("cronometro", "ack"),
    }


def test_campo_desconocido_se_rechaza():
    datos = _ejemplo("velocista.estado.json")["datos"] | {"bateria": 8.0}
    with pytest.raises(MensajeInvalido):
        validar_datos("velocista", "estado", datos)


def test_manifiesto_exige_canales_requeridos():
    m = _manifiesto()
    m["canales"] = [c for c in m["canales"] if c["nombre"] != "error"]
    m["sensores"][0]["canales"] = ["regleta"]
    with pytest.raises(ValueError, match="error"):
        Manifiesto.model_validate(m)


def test_manifiesto_rechaza_valor_fuera_de_rango():
    m = _manifiesto()
    m["controladores"][0]["parametros"][0]["valor"] = 5
    with pytest.raises(ValueError, match="fuera de su rango"):
        Manifiesto.model_validate(m)


def test_manifiesto_rechaza_sensor_con_canal_no_declarado():
    m = _manifiesto()
    m["sensores"][1]["canales"] = ["bateria_mv"]
    with pytest.raises(ValueError, match="no declarados"):
        Manifiesto.model_validate(m)


def test_agregar_un_sensor_no_cambia_el_contrato():
    """Criterio de EN-02: se agregan encoders solo declarándolos en el manifiesto."""
    m = _manifiesto()
    m["canales"] += [
        {
            "nombre": "vel_izq",
            "tipo": "float",
            "unidad": "m/s",
            "min": -3,
            "max": 3,
            "grupo": "senales",
        },
        {
            "nombre": "vel_der",
            "tipo": "float",
            "unidad": "m/s",
            "min": -3,
            "max": 3,
            "grupo": "senales",
        },
    ]
    m["sensores"].append(
        {"nombre": "encoders", "modelo": "N20 magnético", "canales": ["vel_izq", "vel_der"]}
    )
    manifiesto = Manifiesto.model_validate(m)

    senales = _ejemplo("velocista.senales.json")["datos"]
    senales["canales"] |= {"vel_izq": 1.42, "vel_der": 1.38}
    modelo = validar_datos("velocista", "senales", senales)
    assert revisar_canales(manifiesto, "senales", modelo.canales) == []


def test_revisar_canales_avisa_sin_descartar():
    manifiesto = Manifiesto.model_validate(_manifiesto())
    avisos = revisar_canales(
        manifiesto,
        "senales",
        {"error": 1.7, "regleta": [0] * 15, "pwm_izq": 100.5, "temperatura": 30, "bateria_v": 8},
    )
    assert len(avisos) == 5
    assert any("fuera de" in a for a in avisos)
    assert any("15" in a for a in avisos)
    assert any("no declarado" in a for a in avisos)
    assert any("grupo estado" in a for a in avisos)


@pytest.mark.parametrize(
    ("parametros", "controlador", "motivo"),
    [
        ({"kp": 0.5}, "pid", None),
        ({"kp": 3}, "pid", "fuera_de_rango"),
        ({"vel_base": 150.5}, "pid", "fuera_de_rango"),
        ({"kx": 1}, "pid", "parametro_desconocido"),
        ({"kp": 1}, "difuso", "controlador_no_disponible"),
    ],
)
def test_revisar_setup(parametros, controlador, motivo):
    manifiesto = Manifiesto.model_validate(_manifiesto())
    problema = revisar_setup(manifiesto, Setup(controlador=controlador, parametros=parametros))
    assert (problema[0] if problema else None) == motivo


def test_version_mayor_distinta_se_rechaza():
    m = _manifiesto() | {"contrato": "2.0"}
    with pytest.raises(ValueError, match="incompatible"):
        Manifiesto.model_validate(m)
    Manifiesto.model_validate(_manifiesto() | {"contrato": "1.3"})

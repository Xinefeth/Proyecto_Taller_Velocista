"""Formato estándar de errores (DO-02, 8.4)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errores import ErrorDeNegocio, registrar_manejadores


def _app() -> TestClient:
    app = FastAPI()
    registrar_manejadores(app)

    @app.get("/negocio")
    def negocio():
        raise ErrorDeNegocio(409, "no_calibrado", "Calibra el robot antes de arrancar")

    @app.get("/falla")
    def falla():
        raise RuntimeError("detalle interno que no debe salir")

    return TestClient(app, raise_server_exceptions=False)


def test_error_de_negocio_usa_el_formato_estandar():
    r = _app().get("/negocio")
    assert r.status_code == 409
    assert r.json() == {
        "detail": {"motivo": "no_calibrado", "detalle": "Calibra el robot antes de arrancar"}
    }


def test_error_no_controlado_no_expone_detalles():
    r = _app().get("/falla")
    assert r.status_code == 500
    assert r.json()["detail"]["motivo"] == "error_interno"
    assert "interno que no debe salir" not in r.text

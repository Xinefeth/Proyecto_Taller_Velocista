"""Integración con PostgreSQL real: se omite si la base no está levantada."""

import pytest

pytestmark = pytest.mark.integracion


def test_registrar_y_listar_eventos(cliente, requiere_db):
    r = cliente.post(
        "/api/eventos", json={"sistema": "pruebas", "nivel": "info", "mensaje": "hola"}
    )
    assert r.status_code == 201
    nuevo = r.json()
    listado = cliente.get("/api/eventos?limite=5").json()
    assert any(e["id"] == nuevo["id"] for e in listado)


def test_nivel_invalido_se_rechaza(cliente):
    assert (
        cliente.post(
            "/api/eventos", json={"sistema": "x", "nivel": "grave", "mensaje": "y"}
        ).status_code
        == 422
    )

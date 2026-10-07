"""Integración con PostgreSQL real: se omite si la base no está levantada."""

from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import engine, get_session
from app.modulos.eventos.models import Evento

pytestmark = pytest.mark.integracion


@pytest.fixture()
def cliente_eventos(cliente, requiere_db):
    with engine.connect() as conn, conn.begin() as transaccion:
        esquema = f"prueba_eventos_{uuid4().hex}"
        conn.execute(text(f'CREATE SCHEMA "{esquema}"'))
        conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
        Evento.__table__.create(conn)

        def sesion():
            with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
                yield session

        anterior = cliente.app.dependency_overrides.copy()
        cliente.app.dependency_overrides[get_session] = sesion
        try:
            yield cliente
        finally:
            cliente.app.dependency_overrides.clear()
            cliente.app.dependency_overrides.update(anterior)
            transaccion.rollback()


def test_registrar_y_listar_eventos(cliente_eventos):
    cliente = cliente_eventos
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

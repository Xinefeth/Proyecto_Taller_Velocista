"""Fixtures compartidas por todas las pruebas."""

import pytest
from fastapi.testclient import TestClient

from app.core.db import db_disponible
from app.main import app


@pytest.fixture()
def cliente():
    """Cliente HTTP y WebSocket con un solo event loop, como en Uvicorn."""
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def requiere_db():
    """Omite la prueba si PostgreSQL no está levantado (docker compose up -d)."""
    if not db_disponible():
        pytest.skip("PostgreSQL no está disponible")

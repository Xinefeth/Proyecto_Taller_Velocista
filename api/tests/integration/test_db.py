"""Integración con PostgreSQL real; se omite si la base no está levantada."""

import pytest
from sqlalchemy import inspect

from app.core.db import engine

pytestmark = pytest.mark.integracion


def test_migraciones_aplicadas(requiere_db):
    tablas = set(inspect(engine).get_table_names())
    assert {"alembic_version", "evento"} <= tablas

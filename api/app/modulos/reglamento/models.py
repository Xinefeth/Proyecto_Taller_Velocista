"""Tablas SQLAlchemy del módulo reglamento. Se definen a partir del modelo de datos (DO-03)."""

from typing import Any

from sqlalchemy import CheckConstraint, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PerfilReglamento(Base):
    __tablename__ = "perfil_reglamento"
    __table_args__ = (CheckConstraint("jsonb_typeof(reglas) = 'object'", name="ck_perfil_reglas"),)
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    competencia: Mapped[str] = mapped_column(String(120))
    etiqueta: Mapped[str] = mapped_column(String(20))
    categoria: Mapped[str] = mapped_column(String(120))
    reglas: Mapped[dict[str, Any]] = mapped_column(JSONB)

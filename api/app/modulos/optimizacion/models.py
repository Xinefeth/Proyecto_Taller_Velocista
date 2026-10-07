"""Controladores y configuraciones históricas de control."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Controlador(Base):
    __tablename__ = "controlador"
    __table_args__ = (
        CheckConstraint("jsonb_typeof(parametros) = 'array'", name="ck_controlador_parametros"),
        CheckConstraint("jsonb_typeof(presets) = 'object'", name="ck_controlador_presets"),
    )
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    nombre_corto: Mapped[str] = mapped_column(String(30))
    descripcion: Mapped[str] = mapped_column(Text)
    parametros: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    presets: Mapped[dict[str, Any]] = mapped_column(JSONB)


class Setup(Base):
    __tablename__ = "setup"
    __table_args__ = (
        UniqueConstraint("id", "version_id", name="uq_setup_version"),
        CheckConstraint("id BETWEEN 1 AND 9007199254740991", name="ck_setup_id"),
        CheckConstraint("btrim(nombre) <> ''", name="ck_setup_nombre"),
        CheckConstraint("jsonb_typeof(parametros) = 'object'", name="ck_setup_parametros"),
        CheckConstraint("jsonb_typeof(controlador_snapshot) = 'object'", name="ck_setup_snapshot"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("version.id", ondelete="RESTRICT"), index=True
    )
    controlador_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("controlador.id", ondelete="RESTRICT"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    parametros: Mapped[dict[str, Any]] = mapped_column(JSONB)
    controlador_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

"""Tablas del catálogo y existencias del club (DO-03 / EN-04)."""

from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TipoComponente(Base):
    __tablename__ = "tipo_componente"
    __table_args__ = (
        CheckConstraint("btrim(id) <> ''", name="ck_tipo_id_no_vacio"),
        CheckConstraint("btrim(nombre) <> ''", name="ck_tipo_nombre_no_vacio"),
        CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_tipo_color"),
        CheckConstraint("jsonb_typeof(campos) = 'array'", name="ck_tipo_campos_array"),
        CheckConstraint("jsonb_typeof(capacidades) = 'array'", name="ck_tipo_capacidades_array"),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    color: Mapped[str] = mapped_column(String(7))
    campos: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )
    capacidades: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default=text("'[]'::jsonb")
    )


class Componente(Base):
    __tablename__ = "componente"
    __table_args__ = (
        CheckConstraint("btrim(id) <> ''", name="ck_componente_id_no_vacio"),
        CheckConstraint("btrim(nombre) <> ''", name="ck_componente_nombre_no_vacio"),
        CheckConstraint("precio > 0 AND precio <> 'NaN'::numeric", name="ck_componente_precio"),
        CheckConstraint("masa_g >= 0 AND masa_g <> 'NaN'::numeric", name="ck_componente_masa"),
        CheckConstraint(
            "consumo_a IS NULL OR (consumo_a >= 0 AND consumo_a <> 'NaN'::numeric)",
            name="ck_componente_consumo",
        ),
        CheckConstraint(
            "jsonb_typeof(especificaciones) = 'object'", name="ck_componente_specs_objeto"
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tipo_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("tipo_componente.id", ondelete="RESTRICT"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    masa_g: Mapped[Decimal] = mapped_column(Numeric(12, 3))
    tienda: Mapped[str] = mapped_column(String(200), default="", server_default="")
    consumo_a: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    especificaciones: Mapped[dict[str, Any]] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))


class Inventario(Base):
    """Stock total, no disponible. La demanda de robots se calcula al consultar."""

    __tablename__ = "inventario"
    __table_args__ = (
        CheckConstraint("stock >= 0", name="ck_inventario_stock"),
        CheckConstraint("revision >= 1", name="ck_inventario_revision"),
    )

    componente_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("componente.id", ondelete="RESTRICT"), primary_key=True
    )
    stock: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"))

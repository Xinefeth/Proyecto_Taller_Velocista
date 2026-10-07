"""Robots, versiones y piezas históricas (DO-03 / EN-04)."""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Robot(Base):
    __tablename__ = "robot"
    __table_args__ = (
        CheckConstraint("btrim(id) <> ''", name="ck_robot_id_no_vacio"),
        CheckConstraint("btrim(nombre) <> ''", name="ck_robot_nombre_no_vacio"),
        CheckConstraint("btrim(codigo_corto) <> ''", name="ck_robot_codigo_no_vacio"),
        CheckConstraint("tipo IN ('velocista', 'minisumo')", name="ck_robot_tipo"),
        ForeignKeyConstraint(
            ["version_actual_id", "id"],
            ["version.id", "version.robot_id"],
            name="fk_robot_version_actual",
            use_alter=True,
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    codigo_corto: Mapped[str] = mapped_column(String(12), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))
    firmware: Mapped[str | None] = mapped_column(String(20))
    version_actual_id: Mapped[int | None] = mapped_column(BigInteger)
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))


class Ranura(Base):
    __tablename__ = "ranura"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tipo_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("tipo_componente.id", ondelete="RESTRICT")
    )
    nombre: Mapped[str] = mapped_column(String(120))
    obligatoria: Mapped[bool] = mapped_column(Boolean)
    cantidad_editable: Mapped[bool] = mapped_column(Boolean)
    depende_reglamento: Mapped[bool] = mapped_column(Boolean)


class Version(Base):
    __tablename__ = "version"
    __table_args__ = (
        UniqueConstraint("robot_id", "ordinal", name="uq_version_ordinal"),
        UniqueConstraint("id", "robot_id", name="uq_version_pertenencia"),
        CheckConstraint("id BETWEEN 1 AND 9007199254740991", name="ck_version_id"),
        CheckConstraint("ordinal >= 0", name="ck_version_ordinal"),
        CheckConstraint("char_length(nota) <= 1000", name="ck_version_nota"),
        CheckConstraint(
            "estado IN ('Actual','Anterior','Descartada','Concepto','Borrador')",
            name="ck_version_estado",
        ),
        Index(
            "uq_version_actual", "robot_id", unique=True, postgresql_where=text("estado = 'Actual'")
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    robot_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("robot.id", ondelete="RESTRICT"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    nota: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20))


class VersionComponente(Base):
    __tablename__ = "version_componente"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_version_componente_cantidad"),
        CheckConstraint(
            "jsonb_typeof(componente_snapshot) = 'object'", name="ck_version_componente_snapshot"
        ),
    )

    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("version.id", ondelete="RESTRICT"), primary_key=True
    )
    ranura_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("ranura.id", ondelete="RESTRICT"), primary_key=True
    )
    componente_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("componente.id", ondelete="RESTRICT"), index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer)
    componente_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)

"""Corridas, vueltas y mediciones históricas."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Corrida(Base):
    __tablename__ = "corrida"
    __table_args__ = (
        ForeignKeyConstraint(
            ["setup_id", "version_id"],
            ["setup.id", "setup.version_id"],
            name="fk_corrida_setup_version",
            ondelete="RESTRICT",
        ),
        CheckConstraint("id BETWEEN 1 AND 9007199254740991", name="ck_corrida_id"),
        CheckConstraint("numero > 0", name="ck_corrida_numero"),
        CheckConstraint("fuente IN ('sim','robot')", name="ck_corrida_fuente"),
        CheckConstraint("modo IN ('prueba','competencia')", name="ck_corrida_modo"),
        CheckConstraint("linea IN ('negra','blanca')", name="ck_corrida_linea"),
        CheckConstraint("potencia_turbina_pct BETWEEN 0 AND 100", name="ck_corrida_turbina"),
        CheckConstraint("cerrada_en IS NULL OR cerrada_en >= fecha", name="ck_corrida_fechas"),
        CheckConstraint("char_length(nota) <= 1000", name="ck_corrida_nota"),
        CheckConstraint("jsonb_typeof(contexto_snapshot) = 'object'", name="ck_corrida_snapshot"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, Identity(), unique=True)
    version_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("version.id", ondelete="RESTRICT"), index=True
    )
    setup_id: Mapped[int] = mapped_column(BigInteger, index=True)
    perfil_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("perfil_reglamento.id", ondelete="RESTRICT"), index=True
    )
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    cerrada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fuente: Mapped[str] = mapped_column(String(10))
    modo: Mapped[str] = mapped_column(String(15))
    linea: Mapped[str] = mapped_column(String(10))
    compensa_bateria: Mapped[bool] = mapped_column(Boolean)
    potencia_turbina_pct: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    contexto_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    nota: Mapped[str] = mapped_column(Text, default="", server_default="")


class Vuelta(Base):
    __tablename__ = "vuelta"
    __table_args__ = (
        UniqueConstraint("corrida_id", "numero", name="uq_vuelta_numero"),
        CheckConstraint("id BETWEEN 1 AND 9007199254740991", name="ck_vuelta_id"),
        CheckConstraint("numero > 0 AND lineas_perdidas >= 0", name="ck_vuelta_contadores"),
        CheckConstraint(
            "duracion_s >= 0 AND duracion_s <> 'NaN'::numeric AND error_acumulado >= 0 AND error_acumulado <> 'NaN'::numeric AND bateria_v >= 0 AND bateria_v <> 'NaN'::numeric",
            name="ck_vuelta_medidas",
        ),
        CheckConstraint(
            "(termino AND tiempo_s IS NOT NULL AND tiempo_s >= 0 AND tiempo_s <> 'NaN'::numeric) OR (NOT termino AND tiempo_s IS NULL)",
            name="ck_vuelta_tiempo",
        ),
        CheckConstraint(
            "tiempo_interno_ms IS NULL OR tiempo_interno_ms >= 0", name="ck_vuelta_interno"
        ),
        CheckConstraint("fuente_tiempo IN ('meta','telemetria')", name="ck_vuelta_fuente"),
        CheckConstraint("char_length(motivo) <= 500", name="ck_vuelta_motivo"),
    )
    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    corrida_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("corrida.id", ondelete="RESTRICT"), index=True
    )
    numero: Mapped[int] = mapped_column(Integer)
    tiempo_s: Mapped[Decimal | None] = mapped_column(Numeric(14, 6))
    duracion_s: Mapped[Decimal] = mapped_column(Numeric(14, 6))
    tiempo_interno_ms: Mapped[int | None] = mapped_column(BigInteger)
    error_acumulado: Mapped[Decimal] = mapped_column(Numeric(18, 9))
    lineas_perdidas: Mapped[int] = mapped_column(Integer)
    bateria_v: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    termino: Mapped[bool] = mapped_column(Boolean)
    fuente_tiempo: Mapped[str] = mapped_column(String(15))
    motivo: Mapped[str] = mapped_column(Text, default="", server_default="")


class SectorVuelta(Base):
    __tablename__ = "sector_vuelta"
    __table_args__ = (
        CheckConstraint(
            "numero > 0 AND tiempo_s >= 0 AND tiempo_s <> 'NaN'::numeric", name="ck_sector_medidas"
        ),
    )
    vuelta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vuelta.id", ondelete="RESTRICT"), primary_key=True
    )
    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    tiempo_s: Mapped[Decimal] = mapped_column(Numeric(14, 6))


class SegmentoVuelta(Base):
    __tablename__ = "segmento_vuelta"
    __table_args__ = (
        CheckConstraint(
            "numero > 0 AND duracion_s >= 0 AND duracion_s <> 'NaN'::numeric AND error_acumulado >= 0 AND error_acumulado <> 'NaN'::numeric AND angulo_grados <> 'NaN'::numeric",
            name="ck_segmento_medidas",
        ),
    )
    vuelta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vuelta.id", ondelete="RESTRICT"), primary_key=True
    )
    numero: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30))
    duracion_s: Mapped[Decimal] = mapped_column(Numeric(14, 6))
    angulo_grados: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    error_acumulado: Mapped[Decimal] = mapped_column(Numeric(18, 9))

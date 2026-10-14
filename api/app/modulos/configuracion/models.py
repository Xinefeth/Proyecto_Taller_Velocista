"""Tabla del modo de funcionamiento y color de línea persistidos por robot (HU-18)."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ConfiguracionRobot(Base):
    __tablename__ = "configuracion_robot"
    __table_args__ = (
        CheckConstraint("modo IS NULL OR modo IN ('prueba', 'competencia')", name="ck_config_modo"),
        CheckConstraint("linea IS NULL OR linea IN ('negra', 'blanca')", name="ck_config_linea"),
    )

    robot_id: Mapped[str] = mapped_column(
        String(40), ForeignKey("robot.id", ondelete="CASCADE"), primary_key=True
    )
    modo: Mapped[str | None] = mapped_column(String(20))
    linea: Mapped[str | None] = mapped_column(String(20))
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

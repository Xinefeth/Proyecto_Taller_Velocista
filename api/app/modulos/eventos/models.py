"""Tablas del módulo eventos. Coinciden con la migración 0001_base."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Evento(Base):
    __tablename__ = "evento"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sistema: Mapped[str] = mapped_column(String(40))
    nivel: Mapped[str] = mapped_column(String(10), server_default="info")
    mensaje: Mapped[str] = mapped_column(Text)

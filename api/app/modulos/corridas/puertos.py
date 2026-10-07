"""Consultas de actividad persistida para los demás módulos."""

from sqlalchemy import select

from app.modulos.armador.puertos import versiones_robot
from app.modulos.corridas.models import Corrida


def robot_en_curso(session, robot_id):
    versiones = versiones_robot()
    return (
        session.scalar(
            select(Corrida.id)
            .join(versiones, versiones.c.id == Corrida.version_id)
            .where(versiones.c.robot_id == robot_id, Corrida.cerrada_en.is_(None))
            .limit(1)
        )
        is not None
    )


def setup_en_curso(session, setup_id):
    return (
        session.scalar(
            select(Corrida.id)
            .where(Corrida.setup_id == setup_id, Corrida.cerrada_en.is_(None))
            .limit(1)
        )
        is not None
    )

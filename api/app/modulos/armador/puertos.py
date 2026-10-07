"""Consultas públicas del armador para otros módulos."""

from sqlalchemy import func, select

from app.modulos.armador.models import Robot, Version, VersionComponente


def versiones_robot():
    return select(Version.id, Version.robot_id).subquery()


def demanda_inventario():
    """Demanda de la última versión de robots activos; excluye historia anterior."""
    return (
        select(
            VersionComponente.componente_id, func.sum(VersionComponente.cantidad).label("en_robots")
        )
        .join(Robot, Robot.version_actual_id == VersionComponente.version_id)
        .where(Robot.archivado.is_(False))
        .group_by(VersionComponente.componente_id)
        .subquery()
    )

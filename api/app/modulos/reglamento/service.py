"""Catálogo de perfiles; conserva valores null del prototipo."""

from sqlalchemy import select

from app.modulos.reglamento.models import PerfilReglamento


def listar_perfiles(session):
    return list(session.scalars(select(PerfilReglamento).order_by(PerfilReglamento.id)))

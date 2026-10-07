"""Catálogo de perfiles; conserva valores null del prototipo."""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.modulos.reglamento.models import PerfilReglamento
from app.modulos.reglamento.schemas import PerfilSalida


def listar_perfiles(session):
    return list(session.scalars(select(PerfilReglamento).order_by(PerfilReglamento.id)))


def cargar_perfiles(session, datos):
    for dato in datos:
        PerfilSalida.model_validate(dato)
    return len(
        session.scalars(
            insert(PerfilReglamento)
            .values(datos)
            .on_conflict_do_nothing(index_elements=[PerfilReglamento.id])
            .returning(PerfilReglamento.id)
        ).all()
    )

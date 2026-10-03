"""Interfaz pública del módulo eventos: otros módulos registran eventos con `registrar`."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.eventos.models import Evento
from app.modulos.eventos.schemas import EventoEntrada


def registrar(session: Session, entrada: EventoEntrada) -> Evento:
    evento = Evento(sistema=entrada.sistema, nivel=entrada.nivel, mensaje=entrada.mensaje)
    session.add(evento)
    session.commit()
    session.refresh(evento)
    return evento


def listar(session: Session, limite: int = 50) -> list[Evento]:
    consulta = select(Evento).order_by(Evento.fecha.desc(), Evento.id.desc()).limit(limite)
    return list(session.scalars(consulta))

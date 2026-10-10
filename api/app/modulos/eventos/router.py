"""Controlador REST del módulo eventos."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.eventos import service
from app.modulos.eventos.schemas import EventoEntrada, EventoSalida

router = APIRouter(prefix="/api/eventos", tags=["events"])
SesionBD = Annotated[Session, Depends(get_session)]


@router.get("", response_model=list[EventoSalida], operation_id="listEvents")
def listar_eventos(session: SesionBD, limite: Annotated[int, Query(ge=1, le=500)] = 50):
    return service.listar(session, limite)


@router.post("", response_model=EventoSalida, status_code=201, operation_id="createEvent")
def registrar_evento(entrada: EventoEntrada, session: SesionBD):
    return service.registrar(session, entrada)

"""Consulta de resultados históricos y notas."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.corridas import service
from app.modulos.corridas.schemas import CorridaSalida, NotaCorrida, PaginaCorridas, PaginaVueltas

router = APIRouter(prefix="/api/corridas", tags=["corridas"])
Sesion = Annotated[Session, Depends(get_session)]
Id = Annotated[int, Path(ge=1, le=9007199254740991)]
Limite = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0, le=9007199254740991)]


@router.get("", response_model=PaginaCorridas, operation_id="listarCorridas")
def listar_corridas(
    session: Sesion,
    limite: Limite = 50,
    offset: Offset = 0,
    robot_id: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    version_id: Annotated[int | None, Query(ge=1, le=9007199254740991)] = None,
    controlador_id: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    fuente: Literal["sim", "robot"] | None = None,
):
    return service.listar_corridas(
        session, limite, offset, robot_id, version_id, controlador_id, fuente
    )


@router.get("/{corrida_id}", response_model=CorridaSalida, operation_id="obtenerCorrida")
def obtener_corrida(corrida_id: Id, session: Sesion):
    return service.obtener_corrida(session, corrida_id)


@router.patch("/{corrida_id}", response_model=CorridaSalida, operation_id="anotarCorrida")
def anotar_corrida(corrida_id: Id, datos: NotaCorrida, session: Sesion):
    return service.anotar_corrida(session, corrida_id, datos)


@router.get("/{corrida_id}/vueltas", response_model=PaginaVueltas, operation_id="listarVueltas")
def listar_vueltas(corrida_id: Id, session: Sesion, limite: Limite = 50, offset: Offset = 0):
    return service.listar_vueltas(session, corrida_id, limite, offset)

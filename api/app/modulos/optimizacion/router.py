"""REST de catálogos de control y configuraciones guardadas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.optimizacion import service
from app.modulos.optimizacion.schemas import (
    ControladorSalida,
    PaginaSetups,
    SetupCrear,
    SetupSalida,
)

router = APIRouter(prefix="/api", tags=["control"])
Sesion = Annotated[Session, Depends(get_session)]
IdRobot = Annotated[str, Path(min_length=1, max_length=40)]
IdSetup = Annotated[int, Path(ge=1, le=9007199254740991)]
Limite = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0, le=9007199254740991)]


@router.get(
    "/controladores", response_model=list[ControladorSalida], operation_id="listarControladores"
)
def listar_controladores(session: Sesion):
    return service.listar_controladores(session)


@router.get("/robots/{robot_id}/setups", response_model=PaginaSetups, operation_id="listarSetups")
def listar_setups(
    robot_id: IdRobot,
    session: Sesion,
    limite: Limite = 50,
    offset: Offset = 0,
    version_id: Annotated[int | None, Query(ge=1, le=9007199254740991)] = None,
):
    return service.listar_setups(session, robot_id, limite, offset, version_id)


@router.post(
    "/robots/{robot_id}/setups",
    response_model=SetupSalida,
    status_code=201,
    operation_id="crearSetup",
)
def crear_setup(robot_id: IdRobot, datos: SetupCrear, session: Sesion):
    return service.crear_setup(session, robot_id, datos)


@router.get("/setups/{setup_id}", response_model=SetupSalida, operation_id="obtenerSetup")
def obtener_setup(setup_id: IdSetup, session: Sesion):
    return service.obtener_setup(session, setup_id)


@router.delete(
    "/setups/{setup_id}", status_code=204, response_class=Response, operation_id="archivarSetup"
)
def archivar_setup(setup_id: IdSetup, session: Sesion):
    service.archivar_setup(session, setup_id)
    return Response(status_code=204)

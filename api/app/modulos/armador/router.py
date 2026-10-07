"""Controlador REST del módulo armador. Solo recibe, valida formato y delega en service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.armador import service
from app.modulos.armador.schemas import (
    PaginaRobots,
    PaginaVersiones,
    RanuraSalida,
    RobotCrear,
    RobotEditar,
    RobotSalida,
    VersionCrear,
    VersionSalida,
)

router = APIRouter(prefix="/api", tags=["armador"])

SesionBD = Annotated[Session, Depends(get_session)]


@router.post(
    "/robots",
    status_code=201,
    response_model=RobotSalida,
    operation_id="crearRobot",
    summary="Registrar robot sin versiones",
)
def crear_robot(datos: RobotCrear, session: SesionBD):
    """Genera el ID; código corto duplicado responde 409. No crea versiones ni demanda."""
    return service.crear_robot(session, datos)


@router.get(
    "/robots", response_model=PaginaRobots, operation_id="listarRobots", summary="Listar robots"
)
def listar_robots(
    session: SesionBD,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=9007199254740991)] = 0,
):
    """Robots activos ordenados por código/ID, con el puntero a su última versión."""
    return service.listar_robots(session, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}",
    response_model=RobotSalida,
    operation_id="obtenerRobot",
    summary="Consultar robot",
)
def obtener_robot(robot_id: Annotated[str, Path(min_length=1, max_length=40)], session: SesionBD):
    return service.obtener_robot(session, robot_id)


@router.get(
    "/robots/{robot_id}/versiones",
    response_model=PaginaVersiones,
    operation_id="listarVersiones",
    summary="Historial de versiones del robot",
)
def listar_versiones(
    robot_id: Annotated[str, Path(min_length=1, max_length=40)],
    session: SesionBD,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=9007199254740991)] = 0,
):
    """Historial por ordinal ascendente, con las instantáneas guardadas de cada pieza."""
    return service.listar_versiones(session, robot_id, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}/versiones/{version_id}",
    response_model=VersionSalida,
    operation_id="obtenerVersion",
    summary="Consultar una versión del robot",
)
def obtener_version(
    robot_id: Annotated[str, Path(min_length=1, max_length=40)],
    version_id: Annotated[int, Path(ge=1, le=9007199254740991)],
    session: SesionBD,
):
    """404 si la versión no existe o pertenece a otro robot. Admite robots archivados."""
    return service.obtener_version(session, robot_id, version_id)


@router.get("/ranuras", response_model=list[RanuraSalida], operation_id="listarRanuras")
def listar_ranuras(session: SesionBD):
    return service.listar_ranuras(session)


@router.patch("/robots/{robot_id}", response_model=RobotSalida, operation_id="editarRobot")
def editar_robot(
    robot_id: Annotated[str, Path(min_length=1, max_length=40)],
    datos: RobotEditar,
    session: SesionBD,
):
    return service.editar_robot(session, robot_id, datos)


@router.delete(
    "/robots/{robot_id}", status_code=204, response_class=Response, operation_id="archivarRobot"
)
def archivar_robot(robot_id: Annotated[str, Path(min_length=1, max_length=40)], session: SesionBD):
    service.archivar_robot(session, robot_id)
    return Response(status_code=204)


@router.post(
    "/robots/{robot_id}/versiones",
    status_code=201,
    response_model=VersionSalida,
    operation_id="crearVersion",
)
def crear_version(
    robot_id: Annotated[str, Path(min_length=1, max_length=40)],
    datos: VersionCrear,
    session: SesionBD,
):
    return service.crear_version(session, robot_id, datos)

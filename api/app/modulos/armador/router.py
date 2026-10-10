"""Controlador REST del módulo armador. Solo recibe, valida formato y delega en service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.errores import error_responses
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

router = APIRouter(prefix="/api", tags=["builder"])

DbSession = Annotated[Session, Depends(get_session)]
RobotId = Annotated[str, Path(min_length=1, max_length=40)]


@router.post(
    "/robots",
    status_code=201,
    response_model=RobotSalida,
    operation_id="createRobot",
    summary="Registrar robot sin versiones",
    description=(
        "Genera el ID; un código corto duplicado responde 409. "
        "No crea versiones ni demanda de inventario."
    ),
)
def create_robot(data: RobotCrear, session: DbSession):
    return service.crear_robot(session, data)


@router.get(
    "/robots",
    response_model=PaginaRobots,
    operation_id="listRobots",
    summary="Listar robots",
    description=(
        "Lista paginada de robots activos (no archivados), ordenados por código/ID, cada uno con "
        "el puntero a su versión actual. Es la fuente de la lista para seleccionar robot (HU-13)."
    ),
)
def list_robots(
    session: DbSession,
    limite: Annotated[int, Query(ge=1, le=200, description="Máximo de robots por página.")] = 50,
    offset: Annotated[
        int, Query(ge=0, le=9007199254740991, description="Robots a saltar desde el inicio.")
    ] = 0,
):
    return service.listar_robots(session, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}",
    response_model=RobotSalida,
    operation_id="getRobot",
    summary="Consultar un robot",
    description="Ficha de un robot por su ID, con el puntero a su versión actual.",
    responses=error_responses(
        (404, "no_encontrado", "No existe un robot con ese ID", "No existe un robot con ese ID."),
    ),
)
def get_robot(robot_id: RobotId, session: DbSession):
    return service.obtener_robot(session, robot_id)


@router.get(
    "/robots/{robot_id}/versions",
    response_model=PaginaVersiones,
    operation_id="listRobotVersions",
    summary="Historial de versiones del robot",
    description=(
        "Historial de versiones del robot por ordinal ascendente, con la instantánea guardada de "
        "cada pieza. Permite elegir qué versión del robot usar (HU-13)."
    ),
    responses=error_responses(
        (404, "no_encontrado", "No existe un robot con ese ID", "No existe un robot con ese ID."),
    ),
)
def list_robot_versions(
    robot_id: RobotId,
    session: DbSession,
    limite: Annotated[int, Query(ge=1, le=200, description="Máximo de versiones por página.")] = 50,
    offset: Annotated[
        int, Query(ge=0, le=9007199254740991, description="Versiones a saltar desde el inicio.")
    ] = 0,
):
    return service.listar_versiones(session, robot_id, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}/versions/{version_id}",
    response_model=VersionSalida,
    operation_id="getRobotVersion",
    summary="Consultar una versión del robot",
    description="Detalle de una versión concreta del robot. Admite robots archivados.",
    responses=error_responses(
        (
            404,
            "no_encontrado",
            "La versión no existe o pertenece a otro robot",
            "La versión no existe o no pertenece a ese robot.",
        ),
    ),
)
def get_robot_version(
    robot_id: RobotId,
    version_id: Annotated[int, Path(ge=1, le=9007199254740991)],
    session: DbSession,
):
    return service.obtener_version(session, robot_id, version_id)


@router.get(
    "/slots",
    response_model=list[RanuraSalida],
    operation_id="listSlots",
    summary="Listar ranuras del robot",
    description="Ranuras (posiciones de pieza) que puede ocupar una versión del robot.",
)
def list_slots(session: DbSession):
    return service.listar_ranuras(session)


@router.patch(
    "/robots/{robot_id}",
    response_model=RobotSalida,
    operation_id="updateRobot",
    summary="Editar la identificación de un robot",
)
def update_robot(robot_id: RobotId, data: RobotEditar, session: DbSession):
    return service.editar_robot(session, robot_id, data)


@router.delete(
    "/robots/{robot_id}",
    status_code=204,
    response_class=Response,
    operation_id="archiveRobot",
    summary="Archivar un robot",
    description="Archiva el robot y libera su demanda de inventario.",
)
def archive_robot(robot_id: RobotId, session: DbSession):
    service.archivar_robot(session, robot_id)
    return Response(status_code=204)


@router.post(
    "/robots/{robot_id}/versions",
    status_code=201,
    response_model=VersionSalida,
    operation_id="createRobotVersion",
    summary="Guardar una nueva versión del robot",
    description="Guarda una nueva versión junto con su lista de piezas.",
)
def create_robot_version(robot_id: RobotId, data: VersionCrear, session: DbSession):
    return service.crear_version(session, robot_id, data)

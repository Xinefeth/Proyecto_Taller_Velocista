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
    summary="Register a robot without versions",
    description=(
        "Generates the ID. A duplicate short code returns 409. "
        "Creates no versions and no inventory demand."
    ),
)
def create_robot(data: RobotCrear, session: DbSession):
    return service.crear_robot(session, data)


@router.get(
    "/robots",
    response_model=PaginaRobots,
    operation_id="listRobots",
    summary="List robots",
    description=(
        "Paginated list of active (not archived) robots, ordered by code/ID, each one with a "
        "pointer to its current version. It is the source of the list for selecting a robot (HU-13)."
    ),
)
def list_robots(
    session: DbSession,
    limite: Annotated[int, Query(ge=1, le=200, description="Maximum robots per page.")] = 50,
    offset: Annotated[
        int, Query(ge=0, le=9007199254740991, description="Robots to skip from the start.")
    ] = 0,
):
    return service.listar_robots(session, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}",
    response_model=RobotSalida,
    operation_id="getRobot",
    summary="Get a robot",
    description="Robot record by ID, with a pointer to its current version.",
    responses=error_responses(
        (404, "no_encontrado", "No existe un robot con ese ID", "No robot exists with that ID."),
    ),
)
def get_robot(robot_id: RobotId, session: DbSession):
    return service.obtener_robot(session, robot_id)


@router.get(
    "/robots/{robot_id}/versions",
    response_model=PaginaVersiones,
    operation_id="listRobotVersions",
    summary="List the versions of a robot",
    description=(
        "Version history of the robot in ascending ordinal order, with the saved snapshot of "
        "each part. It lets the user choose which robot version to use (HU-13)."
    ),
    responses=error_responses(
        (404, "no_encontrado", "No existe un robot con ese ID", "No robot exists with that ID."),
    ),
)
def list_robot_versions(
    robot_id: RobotId,
    session: DbSession,
    limite: Annotated[int, Query(ge=1, le=200, description="Maximum versions per page.")] = 50,
    offset: Annotated[
        int, Query(ge=0, le=9007199254740991, description="Versions to skip from the start.")
    ] = 0,
):
    return service.listar_versiones(session, robot_id, limite=limite, offset=offset)


@router.get(
    "/robots/{robot_id}/versions/{version_id}",
    response_model=VersionSalida,
    operation_id="getRobotVersion",
    summary="Get one version of a robot",
    description="Detail of a specific robot version. Archived robots are accepted.",
    responses=error_responses(
        (
            404,
            "no_encontrado",
            "La versión no existe o pertenece a otro robot",
            "The version does not exist or does not belong to that robot.",
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
    summary="List robot slots",
    description="Slots (part positions) that a robot version can fill.",
)
def list_slots(session: DbSession):
    return service.listar_ranuras(session)


@router.patch(
    "/robots/{robot_id}",
    response_model=RobotSalida,
    operation_id="updateRobot",
    summary="Update the identification of a robot",
)
def update_robot(robot_id: RobotId, data: RobotEditar, session: DbSession):
    return service.editar_robot(session, robot_id, data)


@router.delete(
    "/robots/{robot_id}",
    status_code=204,
    response_class=Response,
    operation_id="archiveRobot",
    summary="Archive a robot",
    description="Archives the robot and releases its inventory demand.",
)
def archive_robot(robot_id: RobotId, session: DbSession):
    service.archivar_robot(session, robot_id)
    return Response(status_code=204)


@router.post(
    "/robots/{robot_id}/versions",
    status_code=201,
    response_model=VersionSalida,
    operation_id="createRobotVersion",
    summary="Save a new version of a robot",
    description="Saves a new version together with its parts list.",
)
def create_robot_version(robot_id: RobotId, data: VersionCrear, session: DbSession):
    return service.crear_version(session, robot_id, data)

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
DbSession = Annotated[Session, Depends(get_session)]
RobotId = Annotated[str, Path(min_length=1, max_length=40)]
SetupId = Annotated[int, Path(ge=1, le=9007199254740991)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0, le=9007199254740991)]


@router.get(
    "/controllers", response_model=list[ControladorSalida], operation_id="listControllers"
)
def list_controllers(session: DbSession):
    return service.listar_controladores(session)


@router.get("/robots/{robot_id}/setups", response_model=PaginaSetups, operation_id="listSetups")
def list_setups(
    robot_id: RobotId,
    session: DbSession,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    version_id: Annotated[int | None, Query(ge=1, le=9007199254740991)] = None,
):
    return service.listar_setups(session, robot_id, limit, offset, version_id)


@router.post(
    "/robots/{robot_id}/setups",
    response_model=SetupSalida,
    status_code=201,
    operation_id="createSetup",
)
def create_setup(robot_id: RobotId, data: SetupCrear, session: DbSession):
    return service.crear_setup(session, robot_id, data)


@router.get("/setups/{setup_id}", response_model=SetupSalida, operation_id="getSetup")
def get_setup(setup_id: SetupId, session: DbSession):
    return service.obtener_setup(session, setup_id)


@router.delete(
    "/setups/{setup_id}", status_code=204, response_class=Response, operation_id="archiveSetup"
)
def archive_setup(setup_id: SetupId, session: DbSession):
    service.archivar_setup(session, setup_id)
    return Response(status_code=204)

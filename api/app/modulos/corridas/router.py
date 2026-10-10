"""Consulta de resultados históricos y notas."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.corridas import service
from app.modulos.corridas.schemas import CorridaSalida, NotaCorrida, PaginaCorridas, PaginaVueltas

router = APIRouter(prefix="/api/runs", tags=["runs"])
DbSession = Annotated[Session, Depends(get_session)]
RunId = Annotated[int, Path(ge=1, le=9007199254740991)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0, le=9007199254740991)]


@router.get(
    "",
    response_model=PaginaCorridas,
    operation_id="listRuns",
    summary="List runs",
    description="Run history for times, comparison and CSV export. It can be filtered by robot, version, controller and source.",
)
def list_runs(
    session: DbSession,
    limit: PageLimit = 50,
    offset: PageOffset = 0,
    robot_id: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    version_id: Annotated[int | None, Query(ge=1, le=9007199254740991)] = None,
    controller_id: Annotated[str | None, Query(min_length=1, max_length=40)] = None,
    source: Literal["sim", "robot"] | None = None,
):
    return service.listar_corridas(
        session, limit, offset, robot_id, version_id, controller_id, source
    )


@router.post(
    "/simulated",
    response_model=CorridaSalida,
    status_code=201,
    operation_id="createSimulatedRun",
    summary="Create and save a simulated run",
    description=(
        "The console calls it on START in Simulated mode: it generates a simulated run with its "
        "laps and stores it in PostgreSQL (source `sim`). It is not idempotent: every call "
        "creates a new run."
    ),
)
def create_simulated_run(session: DbSession):
    return service.crear_corrida_simulada(session)


@router.get(
    "/{run_id}",
    response_model=CorridaSalida,
    operation_id="getRun",
    summary="Get a run",
    description="A run with the snapshot of the setup that was applied.",
)
def get_run(run_id: RunId, session: DbSession):
    return service.obtener_corrida(session, run_id)


@router.patch(
    "/{run_id}",
    response_model=CorridaSalida,
    operation_id="annotateRun",
    summary="Annotate a run",
    description="Updates the note of a run.",
)
def annotate_run(run_id: RunId, data: NotaCorrida, session: DbSession):
    return service.anotar_corrida(session, run_id, data)


@router.get(
    "/{run_id}/laps",
    response_model=PaginaVueltas,
    operation_id="listRunLaps",
    summary="List the laps of a run",
    description="Laps of a run with their sectors and segments.",
)
def list_run_laps(
    run_id: RunId, session: DbSession, limit: PageLimit = 50, offset: PageOffset = 0
):
    return service.listar_vueltas(session, run_id, limit, offset)

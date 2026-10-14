"""REST del modo de funcionamiento y color de línea del robot (HU-18)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.errores import error_responses
from app.modulos.configuracion import service
from app.modulos.configuracion.schemas import (
    CambioLinea,
    CambioModo,
    ComandoAceptado,
    ConfiguracionGuardada,
)

router = APIRouter(prefix="/api", tags=["control"])
DbSession = Annotated[Session, Depends(get_session)]
RobotId = Annotated[str, Path(min_length=1, max_length=40)]

# Errores comunes a cambiar modo y línea (se validan contra el manifiesto y el estado vivos).
CAMBIO_RESPONSES = error_responses(
    (
        422,
        "comando_invalido",
        "El valor no es válido",
        "El valor de modo/línea no es uno de los permitidos (cadena, tipo, null o campo faltante).",
    ),
    (
        409,
        "sin_manifiesto",
        "Espera el manifiesto del robot",
        "El robot no está conectado o todavía no envió su manifiesto.",
    ),
    (
        422,
        "comando_desconocido",
        "El robot no declara ese comando",
        "El manifiesto del robot no lista el comando modo/línea.",
    ),
    (
        409,
        "bloqueado_competencia",
        "En competencia solo se puede detener",
        "El robot corre en modo competencia; no se puede cambiar modo ni línea.",
    ),
    (
        409,
        "ocupado",
        "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea",
        "El robot corre en modo prueba; no se puede cambiar modo ni línea hasta detenerlo.",
    ),
    (
        503,
        "dispositivo_no_disponible",
        "No se pudo entregar el comando: el dispositivo dejó de responder",
        "El enlace con el robot se perdió entre la validación y el envío; reintenta.",
    ),
)


@router.get(
    "/robots/{robot_id}/modo-linea",
    response_model=ConfiguracionGuardada,
    operation_id="getRobotModeLine",
    summary="Consultar el modo y el color de línea guardados",
    description=(
        "Devuelve el modo de funcionamiento y el color de línea guardados del robot (HU-18). Se "
        "fijan con los endpoints POST de abajo y se almacenan en la base de datos."
    ),
    responses=error_responses(
        (
            404,
            "sin_configuracion",
            "El robot no tiene modo ni línea guardados",
            "Aún no se ha fijado modo ni línea para este robot.",
        ),
    ),
)
def get_robot_mode_line(robot_id: RobotId, session: DbSession):
    return service.leer_configuracion(session, robot_id)


@router.post(
    "/robots/{robot_id}/modo-linea/modo",
    status_code=202,
    response_model=ComandoAceptado,
    operation_id="setMode",
    summary="Configurar el modo de funcionamiento",
    description=(
        "Valida el modo contra el manifiesto y el estado vivos, lo envía al robot por el gateway y "
        "lo guarda en la base de datos (HU-18). Se rechaza mientras el robot corre, en cualquier "
        "modo. El ack del robot llega a la consola por `/ws/consola`, no en esta respuesta."
    ),
    responses=CAMBIO_RESPONSES,
)
async def set_mode(robot_id: RobotId, body: CambioModo, session: DbSession):
    return await service.configurar_modo(session, robot_id, body.modo)


@router.post(
    "/robots/{robot_id}/modo-linea/linea",
    status_code=202,
    response_model=ComandoAceptado,
    operation_id="setLine",
    summary="Configurar el color de la línea",
    description=(
        "Valida el color de línea contra el manifiesto y el estado vivos, lo envía al robot por el "
        "gateway y lo guarda en la base de datos (HU-18). Se rechaza mientras el robot corre, en "
        "cualquier modo. El ack del robot llega a la consola por `/ws/consola`, no en esta respuesta."
    ),
    responses=CAMBIO_RESPONSES,
)
async def set_line(robot_id: RobotId, body: CambioLinea, session: DbSession):
    return await service.configurar_linea(session, robot_id, body.color)

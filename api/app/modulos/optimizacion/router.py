"""REST de catálogos de control y configuraciones guardadas."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.core.errores import error_responses
from app.modulos.optimizacion import service
from app.modulos.optimizacion.schemas import (
    CatalogoReconciliado,
    ComandoAceptado,
    ConfiguracionViva,
    ControladorSalida,
    PaginaSetups,
    PresetAplicar,
    SetupCrear,
    SetupSalida,
)

router = APIRouter(prefix="/api", tags=["control"])

# Casos de error comunes a aplicar setup y preset (validación contra el manifiesto vivo + envío).
APLICAR_CASES = (
    (
        409,
        "sin_manifiesto",
        "El robot no está conectado o aún no envió su manifiesto",
        "El robot destino no está conectado o todavía no envió su manifiesto.",
    ),
    (
        409,
        "bloqueado_competencia",
        "En competencia solo se puede detener",
        "El robot corre en modo competencia; no se puede aplicar configuración.",
    ),
    (
        422,
        "controlador_no_disponible",
        "el robot no tiene el controlador",
        "El controlador del setup/preset no existe en el manifiesto vivo del robot.",
    ),
    (
        422,
        "parametro_desconocido",
        "falta el parámetro del controlador",
        "Falta en el setup/preset un parámetro que el controlador del robot declara.",
    ),
    (
        422,
        "fuera_de_rango",
        "valor fuera del rango del manifiesto",
        "Un parámetro queda fuera del rango que declara el manifiesto o no coincide con su tipo.",
    ),
    (
        503,
        "dispositivo_no_disponible",
        "No se pudo entregar el comando: el dispositivo dejó de responder",
        "El enlace con el robot se perdió entre la validación y el envío; reintenta.",
    ),
)
DbSession = Annotated[Session, Depends(get_session)]
RobotId = Annotated[str, Path(min_length=1, max_length=40)]
SetupId = Annotated[int, Path(ge=1, le=9007199254740991)]
PageLimit = Annotated[int, Query(ge=1, le=200)]
PageOffset = Annotated[int, Query(ge=0, le=9007199254740991)]


@router.get("/controllers", response_model=list[ControladorSalida], operation_id="listControllers")
def list_controllers(session: DbSession):
    return service.listar_controladores(session)


@router.get(
    "/robots/{robot_id}/controllers",
    response_model=CatalogoReconciliado,
    operation_id="listReconciledControllers",
    summary="Catálogo de controladores reconciliado con el robot",
    description=(
        "Devuelve el catálogo de controladores de la base de datos y, si el robot está conectado "
        "y envió su manifiesto, superpone el controlador activo y el valor cargado de cada "
        "parámetro. Sin conexión degrada a solo catálogo (sin `valor`, `controlador_activo` nulo). "
        "Sirve para pintar el panel de configuración del robot seleccionado (HU-17)."
    ),
)
def list_reconciled_controllers(robot_id: RobotId, session: DbSession):
    return service.reconciliar_catalogo(session, robot_id)


@router.get(
    "/robots/{robot_id}/configuracion",
    response_model=ConfiguracionViva,
    operation_id="getRobotControllerConfig",
    summary="Configuración cargada ahora en el robot",
    description=(
        "Proyecta el manifiesto vivo sobre el controlador activo: devuelve `controlador_activo` y "
        "el valor actual de cada uno de sus parámetros (HU-17). Requiere que el robot pedido esté "
        "conectado y haya enviado su manifiesto."
    ),
    responses=error_responses(
        (
            404,
            "sin_manifiesto",
            "El robot no está conectado o aún no envió su manifiesto",
            "El robot pedido no está conectado o todavía no envió su manifiesto.",
        ),
    ),
)
def get_robot_config(robot_id: RobotId, session: DbSession):
    return service.configuracion_viva(robot_id)


@router.post(
    "/robots/{robot_id}/setups/{setup_id}/apply",
    response_model=ComandoAceptado,
    status_code=202,
    operation_id="applySetup",
    summary="Aplicar un setup guardado al robot",
    description=(
        "Carga el setup guardado, lo valida contra el manifiesto vivo y lo envía al robot en un "
        "solo paso, con el `id_setup` del setup (HU-17). El ack del robot llega a la consola por "
        "`/ws/consola`, no en esta respuesta."
    ),
    responses=error_responses(
        (
            404,
            "setup_no_encontrado",
            "El setup no existe",
            "No existe un setup con ese id.",
        ),
        *APLICAR_CASES,
    ),
)
async def apply_setup(robot_id: RobotId, setup_id: SetupId, session: DbSession):
    return await service.aplicar_setup(session, robot_id, setup_id)


@router.post(
    "/robots/{robot_id}/presets/apply",
    response_model=ComandoAceptado,
    status_code=202,
    operation_id="applyPreset",
    summary="Aplicar un preset del catálogo al robot",
    description=(
        "Carga los valores de un preset del catálogo, los valida contra el manifiesto vivo y los "
        "envía al robot con `id_setup` nulo (HU-17). El ack del robot llega a la consola por "
        "`/ws/consola`, no en esta respuesta."
    ),
    responses=error_responses(
        (
            404,
            "controlador_no_encontrado",
            "El controlador no existe",
            "No existe en el catálogo un controlador con ese id.",
        ),
        (
            422,
            "preset_no_encontrado",
            "El controlador no tiene ese preset",
            "El controlador existe pero no declara un preset con ese id.",
        ),
        *APLICAR_CASES,
    ),
)
async def apply_preset(robot_id: RobotId, data: PresetAplicar, session: DbSession):
    return await service.aplicar_preset(session, robot_id, data.controlador_id, data.preset_id)


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

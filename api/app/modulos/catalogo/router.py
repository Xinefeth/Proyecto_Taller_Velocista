"""Controlador REST del módulo catalogo. Solo recibe, valida formato y delega en service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.catalogo import service
from app.modulos.catalogo.schemas import (
    ComponenteCrear,
    ComponenteEditar,
    ComponenteSalida,
    InventarioActualizar,
    InventarioSalida,
    PaginaComponentes,
    PaginaInventario,
    TipoComponenteId,
    TipoComponenteSalida,
)

router = APIRouter(prefix="/api", tags=["catalog"])
DbSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/inventory",
    response_model=PaginaInventario,
    operation_id="listInventory",
    summary="List inventory",
)
def list_inventory(
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=9007199254740991)] = 0,
):
    """Stock, revisión y demanda de la última versión de cada robot activo.

    Incluye archivados con stock o demanda. disponible puede ser negativo;
    faltante=max(0, -disponible). No refleja robots simulados de la consola.
    """
    return service.listar_inventario(session, limite=limit, offset=offset)


@router.put(
    "/inventory/{component_id}",
    response_model=InventarioSalida,
    operation_id="updateInventory",
    summary="Update stock with concurrency control",
)
def update_inventory(
    component_id: Annotated[str, Path(min_length=1, max_length=40)],
    data: InventarioActualizar,
    session: DbSession,
):
    """Fija stock total y aumenta revisión; revisión obsoleta responde 409.

    Admite archivados. Calcula asignaciones desde las versiones persistidas de robots activos.
    """
    return service.actualizar_inventario(session, component_id, data)


@router.post(
    "/components",
    status_code=201,
    response_model=ComponenteSalida,
    operation_id="createComponent",
    summary="Register a component and its initial inventory",
)
def create_component(data: ComponenteCrear, session: DbSession):
    """Genera un ID y guarda la ficha y su stock inicial en una transacción."""
    return service.crear_componente(session, data)


@router.get(
    "/components/{component_id}",
    response_model=ComponenteSalida,
    operation_id="getComponent",
    summary="Get a component",
)
def get_component(
    component_id: Annotated[str, Path(min_length=1, max_length=40)], session: DbSession
):
    """Devuelve la ficha y el stock actual; un ID inexistente responde 404."""
    return service.obtener_componente(session, component_id)


@router.patch(
    "/components/{component_id}",
    response_model=ComponenteSalida,
    operation_id="updateComponent",
    summary="Edit a component",
)
def update_component(
    component_id: Annotated[str, Path(min_length=1, max_length=40)],
    data: ComponenteEditar,
    session: DbSession,
):
    """Edita campos enviados; especificaciones reemplaza el objeto completo.

    El tipo, ID y stock no son editables aquí. consumo_a admite null.
    """
    return service.editar_componente(session, component_id, data)


@router.delete(
    "/components/{component_id}",
    status_code=204,
    response_class=Response,
    operation_id="archiveComponent",
    summary="Archive a component",
)
def archive_component(
    component_id: Annotated[str, Path(min_length=1, max_length=40)], session: DbSession
):
    """Conserva la ficha y stock; repetir devuelve 204. Un ID inexistente responde 404."""
    service.archivar_componente(session, component_id)
    return Response(status_code=204)


@router.get(
    "/component-types",
    response_model=list[TipoComponenteSalida],
    response_model_exclude_none=True,
    operation_id="listComponentTypes",
    summary="Component types, fields and capabilities",
)
def list_component_types(session: DbSession):
    """Catálogo completo ordenado por ID; una base sin semillas devuelve []."""
    return service.listar_tipos(session)


@router.get(
    "/components",
    response_model=PaginaComponentes,
    operation_id="listComponents",
    summary="Search catalog components",
)
def list_components(
    session: DbSession,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=9007199254740991)] = 0,
    q: Annotated[str | None, Query(max_length=120)] = None,
    type_id: Annotated[TipoComponenteId | None, Query()] = None,
):
    """Fichas con stock; búsqueda sin tildes en nombre, tipo, tienda y especificaciones.

    Excluye archivados. Los filtros se combinan y total cuenta todos los
    resultados filtrados, independientemente de la página pedida.
    """
    return service.listar_componentes(session, limite=limit, offset=offset, q=q, tipo_id=type_id)

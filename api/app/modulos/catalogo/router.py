"""Controlador REST del módulo catalogo. Solo recibe, valida formato y delega en service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.catalogo import service
from app.modulos.catalogo.schemas import (
    ComponenteCrear,
    ComponenteEditar,
    ComponenteSalida,
    PaginaComponentes,
    TipoComponenteId,
    TipoComponenteSalida,
)

router = APIRouter(prefix="/api", tags=["catálogo"])
SesionBD = Annotated[Session, Depends(get_session)]


@router.post(
    "/componentes",
    status_code=201,
    response_model=ComponenteSalida,
    operation_id="crearComponente",
    summary="Registrar componente e inventario inicial",
)
def crear_componente(datos: ComponenteCrear, session: SesionBD):
    """Genera un ID y guarda la ficha y su stock inicial en una transacción."""
    return service.crear_componente(session, datos)


@router.get(
    "/componentes/{componente_id}",
    response_model=ComponenteSalida,
    operation_id="obtenerComponente",
    summary="Consultar ficha de componente",
)
def obtener_componente(
    componente_id: Annotated[str, Path(min_length=1, max_length=40)], session: SesionBD
):
    """Devuelve la ficha y el stock actual; un ID inexistente responde 404."""
    return service.obtener_componente(session, componente_id)


@router.patch(
    "/componentes/{componente_id}",
    response_model=ComponenteSalida,
    operation_id="editarComponente",
    summary="Editar ficha de componente",
)
def editar_componente(
    componente_id: Annotated[str, Path(min_length=1, max_length=40)],
    datos: ComponenteEditar,
    session: SesionBD,
):
    """Edita campos enviados; especificaciones reemplaza el objeto completo.

    El tipo, ID y stock no son editables aquí. consumo_a admite null.
    """
    return service.editar_componente(session, componente_id, datos)


@router.get(
    "/tipos-componentes",
    response_model=list[TipoComponenteSalida],
    response_model_exclude_none=True,
    operation_id="listarTipos",
    summary="Tipos, campos y capacidades",
)
def listar_tipos(session: SesionBD):
    """Catálogo completo ordenado por ID; una base sin semillas devuelve []."""
    return service.listar_tipos(session)


@router.get(
    "/componentes",
    response_model=PaginaComponentes,
    operation_id="listarComponentes",
    summary="Buscar componentes del catálogo",
)
def listar_componentes(
    session: SesionBD,
    limite: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0, le=9007199254740991)] = 0,
    q: Annotated[str | None, Query(max_length=120)] = None,
    tipo_id: Annotated[TipoComponenteId | None, Query()] = None,
):
    """Fichas con stock; búsqueda sin tildes en nombre, tipo, tienda y especificaciones.

    Excluye archivados. Los filtros se combinan y total cuenta todos los
    resultados filtrados, independientemente de la página pedida.
    """
    return service.listar_componentes(session, limite=limite, offset=offset, q=q, tipo_id=tipo_id)

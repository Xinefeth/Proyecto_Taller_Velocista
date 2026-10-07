"""Reglas de negocio del módulo catalogo. Sin dependencias de HTTP."""

from typing import Any
from uuid import uuid4

from sqlalchemy import String, cast, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errores import ErrorDeNegocio
from app.modulos.armador.puertos import demanda_inventario
from app.modulos.catalogo.models import Componente, Inventario, TipoComponente
from app.modulos.catalogo.schemas import (
    ComponenteCrear,
    ComponenteEditar,
    ComponenteSalida,
    InventarioActualizar,
    InventarioSalida,
)


def _validar_especificaciones(session: Session, datos: ComponenteCrear) -> None:
    """Valida el estado completo, tanto para altas como para ediciones parciales."""
    tipo = session.get(TipoComponente, datos.tipo_id)
    if tipo is None:
        raise ErrorDeNegocio(422, "tipo_no_disponible", "Carga los tipos de componente primero")
    campos = {campo["clave"]: campo for campo in tipo.campos}
    for clave, valor in datos.especificaciones.items():
        campo = campos.get(clave)
        if campo is None:
            raise ErrorDeNegocio(422, "especificacion_invalida", f"Campo no permitido: {clave}")
        valido = (
            isinstance(valor, (int, float)) and valor >= 0
            if campo["tipo"] == "n"
            else isinstance(valor, str) and len(valor) <= 120
        )
        if not valido:
            raise ErrorDeNegocio(422, "especificacion_invalida", f"Valor inválido para {clave}")
    for clave, campo in campos.items():
        if campo.get("obligatorio") and clave not in datos.especificaciones:
            raise ErrorDeNegocio(422, "especificacion_invalida", f"Falta el campo {clave}")
    if (
        datos.tipo_id == "linea"
        and datos.consumo_a is not None
        and "i" in datos.especificaciones
        and float(datos.consumo_a) != datos.especificaciones["i"]
    ):
        raise ErrorDeNegocio(422, "consumo_inconsistente", "consumo_a debe coincidir con i")


def crear_componente(session: Session, datos: ComponenteCrear) -> ComponenteSalida:
    """Valida campos del tipo y confirma ficha e inventario como una sola unidad."""
    _validar_especificaciones(session, datos)
    ficha = datos.model_dump(exclude={"stock"})
    ficha.update(id=f"c_{uuid4().hex}", archivado=False)
    salida = ComponenteSalida(**ficha, stock=datos.stock)
    try:
        session.add(Componente(**ficha))
        session.flush()
        session.add(Inventario(componente_id=ficha["id"], stock=datos.stock))
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise
    return salida


def obtener_componente(session: Session, componente_id: str) -> dict[str, Any]:
    """Consulta una ficha y su stock, incluso si está archivada."""
    fila = (
        session.execute(
            select(*Componente.__table__.c, Inventario.stock)
            .join(Inventario, Inventario.componente_id == Componente.id)
            .where(Componente.id == componente_id)
        )
        .mappings()
        .one_or_none()
    )
    if fila is None:
        raise ErrorDeNegocio(404, "componente_no_encontrado", "El componente no existe")
    return dict(fila)


def editar_componente(
    session: Session, componente_id: str, datos: ComponenteEditar
) -> ComponenteSalida:
    """Serializa ediciones de la ficha; no escribe stock ni revisión de inventario."""
    try:
        componente = session.get(Componente, componente_id, with_for_update=True)
        if componente is None:
            raise ErrorDeNegocio(404, "componente_no_encontrado", "El componente no existe")
        if componente.archivado:
            raise ErrorDeNegocio(409, "componente_archivado", "No se puede editar un archivado")
        actual = obtener_componente(session, componente_id)
        cambios = datos.model_dump(exclude_unset=True)
        combinado = {**actual, **cambios}
        completo = ComponenteCrear.model_validate(
            {k: v for k, v in combinado.items() if k not in {"id", "archivado"}}
        )
        _validar_especificaciones(session, completo)
        salida = ComponenteSalida(**combinado)
        for campo, valor in cambios.items():
            setattr(componente, campo, valor)
        session.flush()
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def archivar_componente(session: Session, componente_id: str) -> None:
    """Baja lógica repetible; conserva ficha, inventario y referencias."""
    try:
        componente = session.get(Componente, componente_id, with_for_update=True)
        if componente is None:
            raise ErrorDeNegocio(404, "componente_no_encontrado", "El componente no existe")
        componente.archivado = True
        session.flush()
        session.commit()
    except Exception:
        session.rollback()
        raise


def cargar_tipos_iniciales(session: Session, tipos: list[dict[str, Any]]) -> int:
    """Inserta solo IDs ausentes; el llamador confirma o revierte la transacción.

    ON CONFLICT protege también frente a dos cargas simultáneas. Los datos de
    un tipo existente se conservan, aunque difieran del archivo de semillas.
    """
    if not tipos:
        return 0
    consulta = (
        insert(TipoComponente)
        .values(tipos)
        .on_conflict_do_nothing(index_elements=[TipoComponente.id])
        .returning(TipoComponente.id)
    )
    return len(session.scalars(consulta).all())


def listar_tipos(session: Session) -> list[TipoComponente]:
    return list(session.scalars(select(TipoComponente).order_by(TipoComponente.id)))


def cargar_componentes_iniciales(
    session: Session, componentes: list[dict[str, Any]]
) -> tuple[int, int]:
    """Completa catálogo e inventario sin cambiar fichas ni stocks existentes.

    El llamador confirma la transacción de ambas tablas. Si una ficha ya existe
    pero no tiene inventario, se crea únicamente su inventario inicial.
    """
    if not componentes:
        return 0, 0
    fichas = [{k: v for k, v in c.items() if k != "stock"} for c in componentes]
    nuevos = session.scalars(
        insert(Componente)
        .values(fichas)
        .on_conflict_do_nothing(index_elements=[Componente.id])
        .returning(Componente.id)
    ).all()
    existencias = [{"componente_id": c["id"], "stock": c["stock"]} for c in componentes]
    inventarios = session.scalars(
        insert(Inventario)
        .values(existencias)
        .on_conflict_do_nothing(index_elements=[Inventario.componente_id])
        .returning(Inventario.componente_id)
    ).all()
    return len(nuevos), len(inventarios)


def listar_inventario(session: Session, *, limite: int = 50, offset: int = 0) -> dict[str, Any]:
    """Stock real y demanda de la última versión de cada robot activo."""
    demanda = demanda_inventario()
    asignado = func.coalesce(demanda.c.en_robots, 0).label("en_robots")
    consulta = (
        select(Inventario.componente_id, Inventario.stock, Inventario.revision, asignado)
        .join(Componente, Componente.id == Inventario.componente_id)
        .outerjoin(demanda, demanda.c.componente_id == Inventario.componente_id)
        .where(or_(Componente.archivado.is_(False), Inventario.stock > 0, asignado > 0))
    )
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    filas = session.execute(
        consulta.order_by(Inventario.componente_id).limit(limite).offset(offset)
    ).all()
    return {
        "items": [
            {
                "componente_id": fila.componente_id,
                "stock": fila.stock,
                "en_robots": fila.en_robots,
                "disponible": fila.stock - fila.en_robots,
                "faltante": max(0, fila.en_robots - fila.stock),
                "revision": fila.revision,
            }
            for fila in filas
        ],
        "total": total,
        "limite": limite,
        "offset": offset,
    }


def actualizar_inventario(
    session: Session, componente_id: str, datos: InventarioActualizar
) -> InventarioSalida:
    """Compara e incrementa revisión en el mismo UPDATE; también permite archivados.

    Deriva disponibilidad de la demanda persistida en la misma transacción.
    """
    try:
        fila = (
            session.execute(
                update(Inventario)
                .where(
                    Inventario.componente_id == componente_id,
                    Inventario.revision == datos.revision,
                    Inventario.revision < 2147483647,
                )
                .values(stock=datos.stock, revision=Inventario.revision + 1)
                .returning(Inventario.componente_id, Inventario.stock, Inventario.revision)
            )
            .mappings()
            .one_or_none()
        )
        if fila is None:
            actual = session.get(Inventario, componente_id)
            if actual is None:
                raise ErrorDeNegocio(404, "inventario_no_encontrado", "El inventario no existe")
            if actual.revision != datos.revision:
                raise ErrorDeNegocio(
                    409, "revision_obsoleta", "Vuelve a consultar el inventario antes de guardar"
                )
            raise ErrorDeNegocio(409, "revision_agotada", "Se alcanzó el límite de revisiones")
        demanda = demanda_inventario()
        asignado = (
            session.scalar(
                select(demanda.c.en_robots).where(demanda.c.componente_id == componente_id)
            )
            or 0
        )
        salida = InventarioSalida(
            **dict(fila),
            en_robots=asignado,
            disponible=fila["stock"] - asignado,
            faltante=max(0, asignado - fila["stock"]),
        )
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def contar_catalogo(session: Session) -> tuple[int, int]:
    return (
        session.scalar(select(func.count()).select_from(Componente)),
        session.scalar(select(func.count()).select_from(Inventario)),
    )


def listar_componentes(
    session: Session,
    *,
    limite: int = 50,
    offset: int = 0,
    q: str | None = None,
    tipo_id: str | None = None,
) -> dict[str, Any]:
    """Busca fichas activas y stock; cuenta después de filtrar y antes de paginar.

    Normalización española sin extensiones adicionales de PostgreSQL. % y _
    se tratan como texto literal, no como comodines proporcionados por el cliente.
    """
    consulta = (
        select(*Componente.__table__.c, Inventario.stock)
        .join(Inventario, Inventario.componente_id == Componente.id)
        .join(TipoComponente, TipoComponente.id == Componente.tipo_id)
        .where(Componente.archivado.is_(False))
    )
    if tipo_id is not None:
        consulta = consulta.where(Componente.tipo_id == tipo_id)
    busqueda = (q or "").strip().lower().translate(str.maketrans("áéíóúüñ", "aeiouun"))
    if busqueda:
        campos = (
            Componente.nombre,
            TipoComponente.nombre,
            Componente.tienda,
            cast(Componente.especificaciones, String),
        )
        consulta = consulta.where(
            or_(
                *(
                    func.translate(func.lower(campo), "áéíóúüñ", "aeiouun").contains(
                        busqueda, autoescape=True
                    )
                    for campo in campos
                )
            )
        )
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    filas = (
        session.execute(
            consulta.order_by(func.lower(Componente.nombre), Componente.id)
            .limit(limite)
            .offset(offset)
        )
        .mappings()
        .all()
    )
    return {
        "items": [dict(fila) for fila in filas],
        "total": total,
        "limite": limite,
        "offset": offset,
    }


def ficha_para_version(session, componente_id):
    ficha = session.get(Componente, componente_id, with_for_update=True)
    if ficha is None:
        raise ErrorDeNegocio(404, "componente_no_encontrado", "El componente no existe")
    if ficha.archivado:
        raise ErrorDeNegocio(409, "componente_archivado", "No se puede seleccionar un archivado")
    return obtener_componente(session, componente_id)

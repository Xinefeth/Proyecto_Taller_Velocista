"""Reglas de negocio del módulo armador. Sin dependencias de HTTP."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core import actividad
from app.core.errores import ErrorDeNegocio
from app.modulos.armador.models import Ranura, Robot, Version, VersionComponente
from app.modulos.armador.schemas import RobotCrear, RobotEditar, RobotSalida, VersionCrear
from app.modulos.catalogo import service as catalogo
from app.modulos.corridas.puertos import robot_en_curso


def crear_robot(session: Session, datos: RobotCrear) -> RobotSalida:
    """Genera ID y registra identificación; la restricción única protege el código."""
    robot = Robot(
        id=f"r_{uuid4().hex}", **datos.model_dump(), version_actual_id=None, archivado=False
    )
    try:
        session.add(robot)
        session.flush()
        salida = RobotSalida.model_validate(robot)
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def cargar_robot_inicial(session: Session) -> int:
    """Carga la identificación de v001 sin versiones ni modificación de existentes.

    Datos de consola/src/datos/robots.ts. El llamador confirma la transacción.
    Un código 001 ocupado por otro ID produce conflicto y revierte toda la carga.
    """
    nuevo = session.scalar(
        insert(Robot)
        .values(
            id="v001",
            nombre="Velocista 001",
            codigo_corto="001",
            tipo="velocista",
            firmware="0.3.1",
        )
        .on_conflict_do_nothing(index_elements=[Robot.id])
        .returning(Robot.id)
    )
    return int(nuevo is not None)


def contar_robots(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(Robot))


def listar_robots(session: Session, *, limite: int = 50, offset: int = 0) -> dict:
    consulta = select(Robot).where(Robot.archivado.is_(False))
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    robots = session.scalars(
        consulta.order_by(Robot.codigo_corto, Robot.id).limit(limite).offset(offset)
    ).all()
    return {"items": robots, "total": total, "limite": limite, "offset": offset}


def obtener_robot(session: Session, robot_id: str) -> Robot:
    """Las fichas archivadas siguen accesibles por ID."""
    robot = session.get(Robot, robot_id)
    if robot is None:
        raise ErrorDeNegocio(404, "robot_no_encontrado", "El robot no existe")
    return robot


def _serializar_versiones(session: Session, versiones: list[Version]) -> list[dict]:
    """Carga las piezas de la página en una consulta y usa sus instantáneas guardadas."""
    piezas = {v.id: {} for v in versiones}
    if versiones:
        filas = session.scalars(
            select(VersionComponente)
            .where(VersionComponente.version_id.in_(piezas))
            .order_by(VersionComponente.ranura_id)
        )
        for pieza in filas:
            piezas[pieza.version_id][pieza.ranura_id] = {
                "componente_id": pieza.componente_id,
                "cantidad": pieza.cantidad,
                "componente_snapshot": pieza.componente_snapshot,
            }
    return [
        {
            "id": v.id,
            "robot_id": v.robot_id,
            "etiqueta": f"v{v.ordinal}",
            "fecha": v.fecha,
            "nota": v.nota,
            "estado": v.estado,
            "piezas": piezas[v.id],
        }
        for v in versiones
    ]


def listar_versiones(session: Session, robot_id: str, *, limite: int = 50, offset: int = 0) -> dict:
    obtener_robot(session, robot_id)
    consulta = select(Version).where(Version.robot_id == robot_id)
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    versiones = session.scalars(
        consulta.order_by(Version.ordinal).limit(limite).offset(offset)
    ).all()
    return {
        "items": _serializar_versiones(session, versiones),
        "total": total,
        "limite": limite,
        "offset": offset,
    }


def obtener_version(session: Session, robot_id: str, version_id: int) -> dict:
    version = session.scalar(
        select(Version).where(Version.id == version_id, Version.robot_id == robot_id)
    )
    if version is None:
        raise ErrorDeNegocio(404, "version_no_encontrada", "La versión no existe para ese robot")
    return _serializar_versiones(session, [version])[0]


def cargar_versiones_iniciales(session: Session, datos: dict) -> tuple[int, int]:
    """Carga v0/v1 solo si v001 no tiene historial; nunca reconstruye uno existente.

    El llamador confirma todo el lote. Las instantáneas provienen de las fichas
    persistidas al cargar; las fechas del prototipo tienen precisión de día.
    """
    nuevas_ranuras = session.scalars(
        insert(Ranura)
        .values(datos["ranuras"])
        .on_conflict_do_nothing(index_elements=[Ranura.id])
        .returning(Ranura.id)
    ).all()
    robot = session.get(Robot, "v001", with_for_update=True)
    if robot is None:
        raise ValueError("Debe existir Velocista 001 antes de cargar sus versiones")
    if robot.version_actual_id is not None or session.scalar(
        select(func.count()).select_from(Version).where(Version.robot_id == robot.id)
    ):
        return len(nuevas_ranuras), 0
    ranuras = {r.id: r for r in session.scalars(select(Ranura))}
    for v in datos["versiones"]:
        version = Version(
            robot_id=robot.id,
            ordinal=v["ordinal"],
            fecha=datetime.fromisoformat(v["fecha"]),
            nota=v["nota"],
            estado=v["estado"],
        )
        session.add(version)
        session.flush()
        for clave, pieza in v["piezas"].items():
            ficha = catalogo.obtener_componente(session, pieza["componente_id"])
            ranura = ranuras[clave]
            if ficha["tipo_id"] != ranura.tipo_id:
                raise ValueError(f"Tipo incompatible en la ranura {clave}")
            if pieza["cantidad"] < 1 or (not ranura.cantidad_editable and pieza["cantidad"] != 1):
                raise ValueError(f"Cantidad incompatible en la ranura {clave}")
            snapshot = {k: val for k, val in ficha.items() if k not in {"stock", "archivado"}}
            for campo in ("precio", "masa_g", "consumo_a"):
                if snapshot[campo] is not None:
                    snapshot[campo] = float(snapshot[campo])
            session.add(
                VersionComponente(
                    version_id=version.id,
                    ranura_id=clave,
                    componente_id=ficha["id"],
                    cantidad=pieza["cantidad"],
                    componente_snapshot=snapshot,
                )
            )
        if v["estado"] == "Actual" and any(
            r.obligatoria and r.id not in v["piezas"] for r in ranuras.values()
        ):
            raise ValueError("La versión Actual necesita todas las ranuras obligatorias")
        session.flush()
        robot.version_actual_id = version.id
    session.flush()
    return len(nuevas_ranuras), len(datos["versiones"])


def listar_ranuras(session):
    return list(session.scalars(select(Ranura).order_by(Ranura.id)))


def robot_para_escritura(session, robot_id):
    robot = session.get(Robot, robot_id, with_for_update=True)
    if robot is None:
        raise ErrorDeNegocio(404, "robot_no_encontrado", "El robot no existe")
    if robot.archivado:
        raise ErrorDeNegocio(409, "robot_archivado", "El robot está archivado")
    return robot


def comprobar_detenido(session, robot_id):
    if actividad.robot_corriendo(robot_id) or robot_en_curso(session, robot_id):
        raise ErrorDeNegocio(
            409, "corrida_en_curso", "Detén y cierra la corrida antes de modificar el armado"
        )


def editar_robot(session, robot_id: str, datos: RobotEditar):
    try:
        robot = robot_para_escritura(session, robot_id)
        for clave, valor in datos.model_dump(exclude_unset=True).items():
            setattr(robot, clave, valor)
        session.flush()
        salida = RobotSalida.model_validate(robot)
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def archivar_robot(session, robot_id):
    try:
        robot = session.get(Robot, robot_id, with_for_update=True)
        if robot is None:
            raise ErrorDeNegocio(404, "robot_no_encontrado", "El robot no existe")
        if not robot.archivado:
            comprobar_detenido(session, robot_id)
            robot.archivado = True
        session.commit()
    except Exception:
        session.rollback()
        raise


def crear_version(session, robot_id: str, datos: VersionCrear):
    try:
        robot = robot_para_escritura(session, robot_id)
        comprobar_detenido(session, robot_id)
        if robot.version_actual_id != datos.version_base_id:
            raise ErrorDeNegocio(
                409, "version_obsoleta", "Consulta la última versión antes de guardar"
            )
        ranuras = {r.id: r for r in listar_ranuras(session)}
        if not ranuras:
            raise ErrorDeNegocio(422, "sin_ranuras", "Carga las semillas de ranuras primero")
        faltantes = {r.id for r in ranuras.values() if r.obligatoria} - datos.piezas.keys()
        if datos.estado == "Actual" and faltantes:
            raise ErrorDeNegocio(
                422, "ranuras_obligatorias", "Faltan: " + ", ".join(sorted(faltantes))
            )
        piezas = []
        # Orden estable de bloqueos para tomar fichas coherentes frente a edición/archivado.
        for clave, pieza in sorted(datos.piezas.items(), key=lambda par: par[1].componente_id):
            ranura = ranuras.get(clave)
            if ranura is None:
                raise ErrorDeNegocio(422, "ranura_desconocida", f"Ranura desconocida: {clave}")
            ficha = catalogo.ficha_para_version(session, pieza.componente_id)
            if ficha["tipo_id"] != ranura.tipo_id:
                raise ErrorDeNegocio(422, "tipo_incompatible", f"Tipo incompatible en {clave}")
            if not ranura.cantidad_editable and pieza.cantidad != 1:
                raise ErrorDeNegocio(422, "cantidad_invalida", f"La cantidad de {clave} debe ser 1")
            snapshot = {k: v for k, v in ficha.items() if k not in {"stock", "archivado"}}
            for campo in ("precio", "masa_g", "consumo_a"):
                if snapshot[campo] is not None:
                    snapshot[campo] = float(snapshot[campo])
            piezas.append((clave, pieza, snapshot))
        ordinal = session.scalar(
            select(func.max(Version.ordinal)).where(Version.robot_id == robot_id)
        )
        if datos.estado == "Actual":
            session.execute(
                update(Version)
                .where(Version.robot_id == robot_id, Version.estado == "Actual")
                .values(estado="Anterior")
            )
        version = Version(
            robot_id=robot_id,
            ordinal=0 if ordinal is None else ordinal + 1,
            fecha=datetime.now(UTC),
            nota=datos.nota,
            estado=datos.estado,
        )
        session.add(version)
        session.flush()
        for clave, pieza, snapshot in piezas:
            session.add(
                VersionComponente(
                    version_id=version.id,
                    ranura_id=clave,
                    componente_id=pieza.componente_id,
                    cantidad=pieza.cantidad,
                    componente_snapshot=snapshot,
                )
            )
        robot.version_actual_id = version.id
        session.flush()
        salida = obtener_version(session, robot_id, version.id)
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise

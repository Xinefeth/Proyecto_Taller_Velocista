"""Reglas de negocio del módulo corridas."""

from sqlalchemy import func, select

from app.core.errores import ErrorDeNegocio
from app.modulos.armador.puertos import versiones_robot
from app.modulos.corridas.models import Corrida, SectorVuelta, SegmentoVuelta, Vuelta

# SP-01: el reglamento de Muchik Rumble 4 limita la vuelta a 120 s.
LIMITE_S = 120.0
PESO_ERROR = 2.0


def calcular_j(tiempo_s: float | None, error_acumulado: float, termino: bool) -> float:
    """Métrica de una corrida (SP-01): J = tiempo + 2 × error acumulado.

    Si el robot no termina la vuelta, J = 120. Menor es mejor.
    """
    if tiempo_s is not None and tiempo_s < 0:
        raise ValueError("el tiempo no puede ser negativo")
    if error_acumulado < 0:
        raise ValueError("el error acumulado no puede ser negativo")
    if not termino or tiempo_s is None:
        return LIMITE_S
    return round(tiempo_s + PESO_ERROR * error_acumulado, 3)


def _vueltas_salida(session, vueltas):
    ids = [v.id for v in vueltas]
    sectores = {i: [] for i in ids}
    segmentos = {i: [] for i in ids}
    if ids:
        for sector in session.scalars(
            select(SectorVuelta)
            .where(SectorVuelta.vuelta_id.in_(ids))
            .order_by(SectorVuelta.numero)
        ):
            sectores[sector.vuelta_id].append(float(sector.tiempo_s))
        for segmento in session.scalars(
            select(SegmentoVuelta)
            .where(SegmentoVuelta.vuelta_id.in_(ids))
            .order_by(SegmentoVuelta.numero)
        ):
            segmentos[segmento.vuelta_id].append(segmento)
    return [
        {
            **{c.name: getattr(v, c.name) for c in Vuelta.__table__.columns},
            "sectores_s": sectores[v.id],
            "segmentos": segmentos[v.id],
        }
        for v in vueltas
    ]


def _consulta():
    versiones = versiones_robot()
    return select(Corrida, versiones.c.robot_id).join(
        versiones, versiones.c.id == Corrida.version_id
    )


def _resumenes(session, filas):
    ids = [c.id for c, _ in filas]
    por_corrida = {i: [] for i in ids}
    if ids:
        vueltas = session.scalars(
            select(Vuelta).where(Vuelta.corrida_id.in_(ids)).order_by(Vuelta.numero)
        ).all()
        for vuelta in _vueltas_salida(session, vueltas):
            por_corrida[vuelta["corrida_id"]].append(vuelta)
    salida = []
    for corrida, robot_id in filas:
        vueltas = por_corrida[corrida.id]
        if not vueltas:
            raise ErrorDeNegocio(
                409, "corrida_sin_vueltas", "La corrida cerrada no tiene vueltas registradas"
            )
        terminadas = [v for v in vueltas if v["termino"]]
        mejor = (
            min(
                terminadas,
                key=lambda v: (
                    calcular_j(float(v["tiempo_s"]), float(v["error_acumulado"]), True),
                    v["numero"],
                ),
            )
            if terminadas
            else vueltas[0]
        )
        contexto = corrida.contexto_snapshot
        salida.append(
            {
                **{
                    c.name: getattr(corrida, c.name)
                    for c in Corrida.__table__.columns
                    if c.name not in {"cerrada_en", "contexto_snapshot"}
                },
                "robot_id": robot_id,
                "controlador_id": contexto["controlador"]["id"],
                "parametros": contexto["parametros"],
                **{
                    k: mejor[k]
                    for k in [
                        "tiempo_s",
                        "termino",
                        "error_acumulado",
                        "bateria_v",
                        "sectores_s",
                        "fuente_tiempo",
                    ]
                },
                "j": calcular_j(
                    float(mejor["tiempo_s"]) if mejor["tiempo_s"] is not None else None,
                    float(mejor["error_acumulado"]),
                    mejor["termino"],
                ),
            }
        )
    return salida


def listar_corridas(
    session, limite=50, offset=0, robot_id=None, version_id=None, controlador_id=None, fuente=None
):
    consulta = _consulta().where(Corrida.cerrada_en.is_not(None))
    if robot_id is not None:
        versiones = versiones_robot()
        consulta = consulta.where(
            Corrida.version_id.in_(select(versiones.c.id).where(versiones.c.robot_id == robot_id))
        )
    if version_id is not None:
        consulta = consulta.where(Corrida.version_id == version_id)
    if controlador_id is not None:
        consulta = consulta.where(
            Corrida.contexto_snapshot["controlador"]["id"].astext == controlador_id
        )
    if fuente is not None:
        consulta = consulta.where(Corrida.fuente == fuente)
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    filas = session.execute(
        consulta.order_by(Corrida.fecha.desc(), Corrida.id.desc()).limit(limite).offset(offset)
    ).all()
    return {"items": _resumenes(session, filas), "total": total, "limite": limite, "offset": offset}


def obtener_corrida(session, corrida_id):
    fila = session.execute(_consulta().where(Corrida.id == corrida_id)).one_or_none()
    if fila is None:
        raise ErrorDeNegocio(404, "corrida_no_encontrada", "La corrida no existe")
    if fila[0].cerrada_en is None:
        raise ErrorDeNegocio(409, "corrida_en_curso", "La corrida todavía está activa")
    return _resumenes(session, [fila])[0]


def anotar_corrida(session, corrida_id, datos):
    try:
        corrida = session.get(Corrida, corrida_id, with_for_update=True)
        obtener_corrida(session, corrida_id)
        corrida.nota = datos.nota
        session.flush()
        salida = obtener_corrida(session, corrida_id)
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def listar_vueltas(session, corrida_id, limite=50, offset=0):
    if session.get(Corrida, corrida_id) is None:
        raise ErrorDeNegocio(404, "corrida_no_encontrada", "La corrida no existe")
    consulta = select(Vuelta).where(Vuelta.corrida_id == corrida_id)
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    vueltas = session.scalars(consulta.order_by(Vuelta.numero).limit(limite).offset(offset)).all()
    return {
        "items": _vueltas_salida(session, vueltas),
        "total": total,
        "limite": limite,
        "offset": offset,
    }

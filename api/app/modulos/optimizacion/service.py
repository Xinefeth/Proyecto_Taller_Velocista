"""Persistencia y validación de configuraciones de control."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.core import actividad
from app.core.errores import ErrorDeNegocio
from app.modulos.armador import service as armador
from app.modulos.armador.puertos import versiones_robot
from app.modulos.corridas.puertos import setup_en_curso
from app.modulos.optimizacion.models import Controlador, Setup
from app.modulos.optimizacion.schemas import ControladorSalida


def listar_controladores(session):
    return list(session.scalars(select(Controlador).order_by(Controlador.id)))


def cargar_controladores(session, datos):
    for dato in datos:
        modelo = ControladorSalida.model_validate(dato)
        for preset in modelo.presets.values():
            validar_parametros(modelo.parametros, preset)
    return len(
        session.scalars(
            insert(Controlador)
            .values(datos)
            .on_conflict_do_nothing(index_elements=[Controlador.id])
            .returning(Controlador.id)
        ).all()
    )


def validar_parametros(definiciones, parametros):
    campos = {p.clave: p for p in definiciones}
    if campos.keys() != parametros.keys():
        raise ErrorDeNegocio(
            422, "parametros_invalidos", "Envía exactamente los parámetros del controlador"
        )
    for clave, valor in parametros.items():
        p = campos[clave]
        numero, minimo, maximo, paso = map(lambda n: Decimal(str(n)), (valor, p.min, p.max, p.paso))
        if not numero.is_finite() or not minimo <= numero <= maximo:
            raise ErrorDeNegocio(422, "fuera_de_rango", f"Parámetro fuera de rango: {clave}")
        if (numero - minimo) % paso != 0:
            raise ErrorDeNegocio(422, "paso_invalido", f"Paso inválido para {clave}")
    if parametros.get("max", 0) < parametros.get("base", 0):
        raise ErrorDeNegocio(422, "parametros_incompatibles", "max debe ser mayor o igual que base")
    if "vmin" in parametros and parametros["vmin"] > parametros["base"]:
        raise ErrorDeNegocio(422, "parametros_incompatibles", "vmin no debe superar base")


def _consulta():
    versiones = versiones_robot()
    return select(Setup, versiones.c.robot_id).join(versiones, versiones.c.id == Setup.version_id)


def _salida(fila):
    setup, robot_id = fila
    return {
        "id": setup.id,
        "robot_id": robot_id,
        "version_id": setup.version_id,
        "nombre": setup.nombre,
        "controlador_id": setup.controlador_id,
        "parametros": setup.parametros,
        "creado_en": setup.creado_en,
        "archivado": setup.archivado,
    }


def obtener_setup(session, setup_id):
    fila = session.execute(_consulta().where(Setup.id == setup_id)).one_or_none()
    if fila is None:
        raise ErrorDeNegocio(404, "setup_no_encontrado", "El setup no existe")
    return _salida(fila)


def listar_setups(session, robot_id, limite=50, offset=0, version_id=None):
    armador.obtener_robot(session, robot_id)
    if version_id is not None:
        armador.obtener_version(session, robot_id, version_id)
    versiones = versiones_robot()
    consulta = _consulta().where(
        Setup.version_id.in_(select(versiones.c.id).where(versiones.c.robot_id == robot_id)),
        Setup.archivado.is_(False),
    )
    if version_id is not None:
        consulta = consulta.where(Setup.version_id == version_id)
    total = session.scalar(select(func.count()).select_from(consulta.subquery()))
    filas = session.execute(
        consulta.order_by(Setup.creado_en.desc(), Setup.id.desc()).limit(limite).offset(offset)
    ).all()
    return {
        "items": [_salida(f) for f in filas],
        "total": total,
        "limite": limite,
        "offset": offset,
    }


def crear_setup(session, robot_id, datos):
    try:
        armador.robot_para_escritura(session, robot_id)
        armador.obtener_version(session, robot_id, datos.version_id)
        ctrl = session.get(Controlador, datos.controlador_id, with_for_update=True)
        if ctrl is None:
            raise ErrorDeNegocio(404, "controlador_no_encontrado", "El controlador no existe")
        definicion = ControladorSalida.model_validate(ctrl)
        validar_parametros(definicion.parametros, datos.parametros)
        setup = Setup(**datos.model_dump(), controlador_snapshot=definicion.model_dump(mode="json"))
        session.add(setup)
        session.flush()
        salida = obtener_setup(session, setup.id)
        session.commit()
        return salida
    except Exception:
        session.rollback()
        raise


def archivar_setup(session, setup_id):
    try:
        setup = session.get(Setup, setup_id, with_for_update=True)
        if setup is None:
            raise ErrorDeNegocio(404, "setup_no_encontrado", "El setup no existe")
        if not setup.archivado:
            robot_id = obtener_setup(session, setup_id)["robot_id"]
            if actividad.robot_corriendo(robot_id) or setup_en_curso(session, setup_id):
                raise ErrorDeNegocio(
                    409, "corrida_en_curso", "El setup está en uso por una corrida activa"
                )
            setup.archivado = True
        session.commit()
    except Exception:
        session.rollback()
        raise

"""Persistencia y aplicación del modo/línea del robot (HU-18).

El envío al robot pasa por el puerto del gateway (app.core.actividad), que valida contra el
manifiesto y el estado vivos; si el envío tiene éxito, se guarda el valor en la base de datos.
"""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.core import actividad
from app.core.errores import ErrorDeNegocio
from app.modulos.configuracion.models import ConfiguracionRobot
from app.modulos.configuracion.schemas import ComandoAceptado, ConfiguracionGuardada


def leer_configuracion(session, robot_id):
    """Devuelve el modo y color de línea guardados del robot (Req 1)."""
    fila = session.get(ConfiguracionRobot, robot_id)
    if fila is None:
        raise ErrorDeNegocio(404, "sin_configuracion", "El robot no tiene modo ni línea guardados")
    return ConfiguracionGuardada(
        modo=fila.modo, linea=fila.linea, actualizado_en=fila.actualizado_en
    )


async def _aplicar_y_guardar(session, robot_id, tipo, datos, columna, valor):
    """Envía el comando al robot (valida + guardas) y, si pasa, persiste el valor por robot."""
    seq = await actividad.enviar_config_velocista(robot_id, tipo, datos)
    try:
        session.execute(
            insert(ConfiguracionRobot)
            .values(robot_id=robot_id, **{columna: valor})
            .on_conflict_do_update(
                index_elements=[ConfiguracionRobot.robot_id],
                set_={columna: valor, "actualizado_en": func.now()},
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return ComandoAceptado(seq=seq)


async def configurar_modo(session, robot_id, valor):
    """Fija el modo de funcionamiento y lo envía al robot (Req 2)."""
    return await _aplicar_y_guardar(session, robot_id, "modo", {"modo": valor}, "modo", valor)


async def configurar_linea(session, robot_id, valor):
    """Fija el color de la línea y lo envía al robot (Req 3)."""
    return await _aplicar_y_guardar(session, robot_id, "linea", {"color": valor}, "linea", valor)

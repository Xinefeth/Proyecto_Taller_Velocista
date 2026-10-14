"""Puerto de aplicación de configuración al velocista (HU-17).

Es el único punto donde el módulo optimizacion alcanza al gateway, pero no lo importa directo:
la composición (app.main) cablea estas funciones en el puerto app.core.actividad. Aquí se reúsan
las guardas y el envío ya existentes (validar_comando + ws.send) y se agrega la verificación de
completitud específica de aplicar (check_setup_completo) y el manejo de caída del enlace.
"""

from app.contract import Manifest
from app.contract.robot import Status
from app.contract.validation import check_setup_completo
from app.core.errores import ErrorDeNegocio
from app.gateway import ws
from app.gateway.comandos import validar_comando


def manifiesto_velocista(robot_id: str) -> Manifest | None:
    """Manifiesto vivo del velocista, solo si es el robot pedido (otro robot → None)."""
    conexion = ws.connections.get("velocista")
    if conexion is None or conexion.manifest is None:
        return None
    if conexion.manifest.id != robot_id:
        return None  # hay otro robot conectado → para este robot es como no tener manifiesto
    return conexion.manifest


async def aplicar_setup_velocista(
    robot_id: str, controlador: str, parametros: dict, id_setup: int | None
) -> int:
    """Valida contra el manifiesto vivo + guardas y envía. Devuelve el seq usado."""
    conexion = ws.connections.get("velocista")
    if conexion is None or conexion.manifest is None or conexion.manifest.id != robot_id:
        raise ErrorDeNegocio(
            409, "sin_manifiesto", "El robot no está conectado o aún no envió su manifiesto"
        )
    modelo = validar_comando(
        "velocista",
        "setup",
        {"controlador": controlador, "parametros": parametros, "id_setup": id_setup},
        conexion.manifest,
        conexion.last_status,
    )
    # Verificación de completitud específica de aplicar (ver diseño §3.5).
    if problema := check_setup_completo(conexion.manifest, modelo):
        raise ErrorDeNegocio(422, problema[0], problema[1])
    try:
        return await ws.send("velocista", "setup", modelo.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        # El enlace se cayó entre la validación y el envío: el dispositivo ya no recibe.
        raise ErrorDeNegocio(
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e


def validar_cambio_config(ultimo_estado: Status | None) -> None:
    """Guarda de HU-18: rechazar cambios de modo/linea durante una carrera en modo prueba.

    validar_comando ya bloquea competencia+running con bloqueado_competencia; esta guarda extiende
    el bloqueo a prueba+running, que la vía cruda permite. Es específica de modo/linea.
    """
    e = ultimo_estado
    if e and e.estado == "running" and e.modo == "prueba":
        raise ErrorDeNegocio(
            409,
            "ocupado",
            "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea",
        )


async def aplicar_config_velocista(robot_id: str, tipo: str, datos: dict) -> int:
    """Valida un cambio de modo/linea contra el manifiesto + estado vivos del robot pedido y lo
    envía. Devuelve el seq. Guardas, en orden: comando_invalido → sin_manifiesto →
    comando_desconocido → bloqueado_competencia → ocupado → dispositivo_no_disponible."""
    conexion = ws.connections.get("velocista")
    coincide = (
        conexion is not None and conexion.manifest is not None and conexion.manifest.id == robot_id
    )
    manifiesto = conexion.manifest if coincide else None
    ultimo_estado = conexion.last_status if coincide else None
    modelo = validar_comando("velocista", tipo, datos, manifiesto, ultimo_estado)
    validar_cambio_config(ultimo_estado)  # guarda más estricta de HU-18 (ocupado)
    try:
        return await ws.send("velocista", tipo, modelo.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        raise ErrorDeNegocio(
            503,
            "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e

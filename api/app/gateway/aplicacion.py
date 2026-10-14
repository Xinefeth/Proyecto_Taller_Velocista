"""Puerto de aplicación de configuración al velocista (HU-17).

Es el único punto donde el módulo optimizacion alcanza al gateway, pero no lo importa directo:
la composición (app.main) cablea estas funciones en el puerto app.core.actividad. Aquí se reúsan
las guardas y el envío ya existentes (validar_comando + ws.send) y se agrega la verificación de
completitud específica de aplicar (check_setup_completo) y el manejo de caída del enlace.
"""

from app.contract import Manifest
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

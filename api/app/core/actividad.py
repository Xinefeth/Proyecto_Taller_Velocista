"""Puerto de lectura/acción sobre el estado físico, configurado por la composición de la API.

Los módulos de dominio no conocen app.gateway (DO-02): llaman a estas funciones y app.main las
cablea a su implementación en el gateway (p. ej. actividad.robot_running = ws.robot_running).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.contract import Manifest


def robot_running(robot_id: str) -> bool:
    return False


def manifiesto_velocista(robot_id: str) -> "Manifest | None":
    """Manifiesto vivo del robot pedido, o None si no está conectado. Cableado en app.main."""
    return None


async def aplicar_setup_velocista(
    robot_id: str, controlador: str, parametros: dict, id_setup: int | None
) -> int:
    """Valida contra el manifiesto vivo y envía el setup al robot. Cableado en app.main."""
    from app.core.errores import ErrorDeNegocio

    raise ErrorDeNegocio(
        409, "sin_manifiesto", "El robot no está conectado o aún no envió su manifiesto"
    )

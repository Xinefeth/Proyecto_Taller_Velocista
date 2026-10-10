"""Punto de entrada de la API: crea la aplicación y registra canales, módulos y manejadores."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core import actividad
from app.core.config import RAIZ_REPO, settings
from app.core.db import db_disponible
from app.core.errores import registrar_manejadores
from app.core.registro import configurar_logging, registrar_middleware
from app.gateway import comandos, ws
from app.modulos.armador.router import router as armador
from app.modulos.auth.router import router as auth
from app.modulos.catalogo.router import router as catalogo
from app.modulos.corridas.router import router as corridas
from app.modulos.eventos.router import router as eventos
from app.modulos.optimizacion.router import router as optimizacion
from app.modulos.reglamento.router import router as reglamento

ROUTERS_MODULOS = [auth, catalogo, armador, reglamento, corridas, optimizacion, eventos]

OPENAPI_TAGS = [
    {"name": "system", "description": "Salud de la API, la base de datos y los dispositivos conectados."},
    {
        "name": "devices",
        "description": (
            "Puente entre la consola y el robot/cronómetro. La consola pide comandos aquí "
            "(HU-16) y consulta el manifiesto del robot (HU-13); la API valida y los reenvía "
            "por WebSocket."
        ),
    },
    {
        "name": "builder",
        "description": "Robots y sus versiones. Fuente de la lista para seleccionar robot (HU-13).",
    },
    {"name": "runs", "description": "Corridas guardadas, sus vueltas y notas."},
]

DESCRIPTION = """\
API local del sistema de gestión y optimización para competencia robótica.

## Mensajes WebSocket

Swagger solo documenta REST. El tiempo real va por WebSocket y el contrato de mensajes
viaja en un sobre `{tipo, seq, ts, datos}`. Canales:

- **`/ws/robot`**: el velocista. Primer mensaje obligatorio: `manifiesto`. Luego:
  - `estado` (~1 Hz): `estado` (listo/calibrando/corriendo/detenido/error), `calibrado`,
    `modo`, `linea`, `controlador`, `lazo_hz`, `rssi_dbm` y `canales` (incluye `bateria_v`).
    Es la base de **consultar el estado del robot (HU-14)**: conexión, estado, batería, firmware.
  - `senales` (~20 Hz, solo mientras corre): muestras del grupo de canales `senales`, p. ej.
    los 16 canales de la **regleta de sensores (HU-15, 2× QTR-8A)**.
  - `vuelta` / `sync`, `evento`, `ack`.
- **`/ws/cronometro`**: el cronómetro (tiempos oficiales de vuelta).
- **`/ws/consola`**: solo escucha. Recibe `hola` (estado inicial de dispositivos), `enlace`
  (un dispositivo se conectó/desconectó) y la redifusión de los mensajes anteriores, más el `ack`
  de cada comando enviado por `POST /api/devices/{device}/commands` (**HU-16**).

Los nombres de tipos y campos en el cable siguen siendo los del contrato EN-02 en español;
su renombrado a inglés está planificado.

La conexión de cada dispositivo también se ve en `GET /api/health` (campo `dispositivos`).
"""


def create_app() -> FastAPI:
    actividad.robot_corriendo = ws.robot_corriendo
    configurar_logging(settings.log_level)
    app = FastAPI(
        title="APAEC Lab API",
        version="0.1.0",
        description=DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    registrar_middleware(app)
    registrar_manejadores(app)

    @app.get(
        "/api/health",
        tags=["system"],
        operation_id="getHealth",
        summary="Consultar la salud de la API",
        description=(
            "Estado de la API, la base de datos y los dispositivos conectados. "
            "El campo `dispositivos` indica si el velocista y el cronómetro están conectados (HU-14)."
        ),
    )
    def health() -> dict:
        return {
            "api": "ok",
            "base_de_datos": "ok" if db_disponible() else "sin conexión",
            "entorno": settings.app_env,
            "dispositivos": ws.estado_dispositivos(),
        }

    # Canales de entrada
    app.include_router(ws.router)
    app.include_router(comandos.router)
    # Módulos del monolito modular
    for router in ROUTERS_MODULOS:
        app.include_router(router)

    # En pista la API sirve la consola compilada (consola/dist).
    dist = RAIZ_REPO / "consola" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="consola")
    return app


app = create_app()

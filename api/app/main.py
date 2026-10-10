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
    {"name": "system", "description": "Health of the API, the database and the connected devices."},
    {
        "name": "devices",
        "description": (
            "Bridge between the console and the robot/timer. The console requests commands here "
            "(HU-16) and reads the robot manifest (HU-13); the API validates and forwards them "
            "over WebSocket."
        ),
    },
    {
        "name": "builder",
        "description": "Robots and their versions. Source of the list for selecting a robot (HU-13).",
    },
    {"name": "runs", "description": "Saved runs, their laps, and run notes."},
]

DESCRIPTION = """\
Local API of the competition robotics management and optimization system.

## WebSocket messages

Swagger only documents REST. Real time goes over WebSocket, and the message contract
travels in an envelope `{tipo, seq, ts, datos}`. Channels:

- **`/ws/robot`**: the line follower. Mandatory first message: `manifiesto`. Then:
  - `estado` (~1 Hz): `estado` (listo/calibrando/corriendo/detenido/error), `calibrado`,
    `modo`, `linea`, `controlador`, `lazo_hz`, `rssi_dbm` and `canales` (includes `bateria_v`).
    It is the base of **querying the robot status (HU-14)**: connection, state, battery, firmware.
  - `senales` (~20 Hz, only while running): samples of the `senales` channel group, e.g. the
    16 channels of the **sensor bar (HU-15, 2x QTR-8A)**.
  - `vuelta` / `sync`, `evento`, `ack`.
- **`/ws/cronometro`**: the timer (official lap times).
- **`/ws/consola`**: listen-only. Receives `hola` (initial device state), `enlace`
  (a device connected/disconnected) and the rebroadcast of the messages above, plus the `ack`
  of every command sent through `POST /api/dispositivos/{dispositivo}/comandos` (**HU-16**).

Message and field names on the wire are still the Spanish ones of the EN-02 contract; their
English rename is planned.

The connection of each device is also visible in `GET /api/health` (field `dispositivos`).
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

    @app.get("/api/health", tags=["system"], operation_id="getHealth")
    def salud() -> dict:
        """Estado de la API, de la base de datos y de los dispositivos conectados."""
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

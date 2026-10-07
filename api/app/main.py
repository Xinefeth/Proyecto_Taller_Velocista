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


def create_app() -> FastAPI:
    actividad.robot_corriendo = ws.robot_corriendo
    configurar_logging(settings.log_level)
    app = FastAPI(
        title="APAEC Lab API",
        version="0.1.0",
        description="API local del Sistema de gestión y optimización para competencia robótica.",
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

    @app.get("/api/salud", tags=["sistema"])
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

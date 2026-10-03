"""Registro técnico: formato de logs y middleware que registra cada petición HTTP."""

import logging
import time

from fastapi import FastAPI, Request

log = logging.getLogger("apaec.http")


def configurar_logging(nivel: str = "INFO") -> None:
    logging.basicConfig(level=nivel, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def registrar_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _registrar(request: Request, siguiente):
        inicio = time.perf_counter()
        respuesta = await siguiente(request)
        if request.url.path.startswith("/api"):
            ms = (time.perf_counter() - inicio) * 1000
            log.info(
                "%s %s → %s (%.1f ms)", request.method, request.url.path, respuesta.status_code, ms
            )
        return respuesta

"""Formato estándar de errores de la API (DO-02, sección 8.4).

Errores de negocio:      {"detail": {"motivo": "...", "detalle": "..."}}
Errores de validación:   formato de FastAPI (422)
Errores no controlados:  500 sin detalles internos, registrados en el log
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.exc import IntegrityError, OperationalError

log = logging.getLogger("apaec.errores")


class ErrorDeNegocio(Exception):
    """Lanzada por los services cuando una regla de negocio impide la operación."""

    def __init__(self, codigo_http: int, motivo: str, detalle: str) -> None:
        super().__init__(detalle)
        self.codigo_http = codigo_http
        self.motivo = motivo
        self.detalle = detalle


# ---- Error documentation in OpenAPI/Swagger ----


class ErrorDetail(BaseModel):
    """Body of `detail` in a business error."""

    motivo: str = Field(
        description="Short, stable reason code; the console decides the final message.",
        examples=["no_calibrado"],
    )
    detalle: str = Field(
        description="Human-readable text to show or log (in Spanish, it is user-facing).",
        examples=["Calibra el robot antes de arrancar"],
    )


class BusinessError(BaseModel):
    """Standard business error format of the API (DO-02 §8.4)."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"detail": {"motivo": "no_calibrado", "detalle": "Calibra el robot antes de arrancar"}}
        }
    )

    detail: ErrorDetail


def error_responses(*cases: tuple[int, str, str, str]) -> dict:
    """Build the OpenAPI `responses` dict for business errors.

    Each case is (http_code, reason, example_detail, case_description). Cases that share an
    HTTP code are merged into one response with several named examples, so none is lost.
    """
    grouped: dict[int, list[tuple[str, str, str]]] = {}
    for code, reason, detail, description in cases:
        grouped.setdefault(code, []).append((reason, detail, description))
    out: dict[int, dict] = {}
    for code, items in grouped.items():
        examples = {
            reason: {
                "summary": description,
                "value": {"detail": {"motivo": reason, "detalle": detail}},
            }
            for reason, detail, description in items
        }
        out[code] = {
            "model": BusinessError,
            "description": " / ".join(description for _, _, description in items),
            "content": {"application/json": {"examples": examples}},
        }
    return out


def _respuesta(codigo: int, motivo: str, detalle: str) -> JSONResponse:
    return JSONResponse(
        status_code=codigo, content={"detail": {"motivo": motivo, "detalle": detalle}}
    )


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorDeNegocio)
    async def _negocio(_: Request, e: ErrorDeNegocio) -> JSONResponse:
        return _respuesta(e.codigo_http, e.motivo, e.detalle)

    @app.exception_handler(IntegrityError)
    async def _integridad(_: Request, e: IntegrityError) -> JSONResponse:
        log.warning("Violación de integridad: %s", e.orig)
        return _respuesta(409, "conflicto", "El dato entra en conflicto con uno existente")

    @app.exception_handler(OperationalError)
    async def _base_caida(_: Request, e: OperationalError) -> JSONResponse:
        log.error("Base de datos no disponible: %s", e.orig)
        return _respuesta(503, "base_no_disponible", "La base de datos no está disponible")

    @app.exception_handler(Exception)
    async def _no_controlado(request: Request, e: Exception) -> JSONResponse:
        log.exception("Error no controlado en %s %s", request.method, request.url.path)
        return _respuesta(500, "error_interno", "Ocurrió un error inesperado")

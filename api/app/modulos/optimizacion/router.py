"""Controlador REST del módulo optimizacion."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/estudios", tags=["optimización"])

# HU-27 a HU-29: POST /api/estudios · GET /api/estudios/{id}/sugerencia

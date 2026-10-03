"""Controlador REST del módulo corridas."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/corridas", tags=["corridas"])

# HU-20: GET /api/corridas · HU-26: GET /api/corridas/export.csv

"""Controlador REST del módulo catalogo. Solo recibe, valida formato y delega en service."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/componentes", tags=["catálogo"])

# Los endpoints se agregan con sus historias (HU-01 a HU-05, EN-17).

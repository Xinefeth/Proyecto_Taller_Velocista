"""Controlador REST del módulo reglamento. Solo recibe, valida formato y delega en service."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/perfiles-reglamento", tags=["reglamento"])

# Los endpoints se agregan con sus historias (HU-10, HU-11).

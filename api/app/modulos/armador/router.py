"""Controlador REST del módulo armador. Solo recibe, valida formato y delega en service."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/robots", tags=["armador"])

# Los endpoints se agregan con sus historias (HU-06 a HU-09).

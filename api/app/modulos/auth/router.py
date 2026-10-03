"""Controlador REST del módulo auth. Solo recibe, valida formato y delega en service."""

from fastapi import APIRouter

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Los endpoints se agregan con sus historias (Por definir en el backlog).

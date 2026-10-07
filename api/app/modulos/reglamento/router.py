"""REST del reglamento."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.reglamento import service
from app.modulos.reglamento.schemas import PerfilSalida

router = APIRouter(prefix="/api", tags=["reglamento"])


@router.get("/perfiles", response_model=list[PerfilSalida], operation_id="listarPerfiles")
def listar_perfiles(session: Annotated[Session, Depends(get_session)]):
    return service.listar_perfiles(session)

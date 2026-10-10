"""REST del reglamento."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.modulos.reglamento import service
from app.modulos.reglamento.schemas import PerfilSalida

router = APIRouter(prefix="/api", tags=["rules"])


@router.get("/profiles", response_model=list[PerfilSalida], operation_id="listProfiles")
def list_profiles(session: Annotated[Session, Depends(get_session)]):
    return service.listar_perfiles(session)

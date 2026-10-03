"""Contrato de mensajes v1.0 (EN-02). Especificación: docs/contrato-mensajes.md."""

from app.contrato.base import VERSION_CONTRATO, Sobre
from app.contrato.catalogo import CATALOGO, MensajeInvalido, requiere_ack, validar_datos
from app.contrato.manifiesto import Canal, Controlador, Manifiesto, Parametro

__all__ = [
    "CATALOGO",
    "VERSION_CONTRATO",
    "Canal",
    "Controlador",
    "Manifiesto",
    "MensajeInvalido",
    "Parametro",
    "Sobre",
    "requiere_ack",
    "validar_datos",
]

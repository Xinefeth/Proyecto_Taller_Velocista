"""Contrato de mensajes v1.0 (EN-02). Especificación: docs/contrato-mensajes.md."""

from app.contract.base import CONTRACT_VERSION, Envelope
from app.contract.catalog import CATALOG, InvalidMessage, requires_ack, validate_data
from app.contract.manifest import Channel, Controller, Manifest, Parameter

__all__ = [
    "CATALOG",
    "CONTRACT_VERSION",
    "Channel",
    "Controller",
    "Envelope",
    "InvalidMessage",
    "Manifest",
    "Parameter",
    "requires_ack",
    "validate_data",
]

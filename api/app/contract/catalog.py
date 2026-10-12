"""Catálogo de mensajes: quién envía cada tipo, qué modelo valida sus datos y si requiere ack."""

from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.contract import robot as r
from app.contract import timer as c
from app.contract.manifest import Manifest


@dataclass(frozen=True)
class Definition:
    model: type[BaseModel]
    requires_ack: bool
    frequency: str


# (emisor, tipo) -> definición. Emisor "api" = mensajes que la API envía al dispositivo.
CATALOG: dict[tuple[str, str], Definition] = {
    # Robot -> API
    ("velocista", "manifiesto"): Definition(Manifest, True, "al conectar, primer mensaje"),
    ("velocista", "estado"): Definition(r.Status, False, "estado_hz (1 Hz)"),
    ("velocista", "senales"): Definition(r.Signals, False, "senales_hz (20 Hz) mientras corre"),
    ("velocista", "vuelta"): Definition(r.Lap, True, "tras cierre_vuelta"),
    ("velocista", "sync"): Definition(r.Sync, True, "al reconectar, si hay vueltas guardadas"),
    ("velocista", "evento"): Definition(r.Event, True, "cuando ocurre"),
    ("velocista", "ack"): Definition(r.Ack, False, "por cada comando"),
    # API -> Robot
    ("api->velocista", "calibrate"): Definition(r.NoData, True, "a pedido"),
    ("api->velocista", "start"): Definition(r.NoData, True, "a pedido"),
    ("api->velocista", "stop"): Definition(r.NoData, True, "a pedido"),
    ("api->velocista", "setup"): Definition(r.Setup, True, "a pedido"),
    ("api->velocista", "modo"): Definition(r.Mode, True, "a pedido"),
    ("api->velocista", "linea"): Definition(r.Line, True, "a pedido"),
    ("api->velocista", "cierre_vuelta"): Definition(r.LapClose, True, "al recibir un corte"),
    ("api->velocista", "ack"): Definition(r.Ack, False, "por cada mensaje que lo requiere"),
    # Cronómetro -> API
    ("cronometro", "hola"): Definition(c.Hello, True, "al conectar"),
    ("cronometro", "corte"): Definition(c.Crossing, True, "cada paso por la meta"),
    ("cronometro", "estado"): Definition(c.TimerStatus, False, "cada 5 s"),
    ("cronometro", "ack"): Definition(r.Ack, False, "por cada comando"),
    # API -> Cronómetro
    ("api->cronometro", "rearmar"): Definition(c.Rearm, True, "a pedido"),
    ("api->cronometro", "ack"): Definition(r.Ack, False, "por cada mensaje que lo requiere"),
}


class InvalidMessage(ValueError):
    pass


def validate_data(emisor: str, tipo: str, datos: dict) -> BaseModel:
    definicion = CATALOG.get((emisor, tipo))
    if definicion is None:
        raise InvalidMessage(f"tipo desconocido para {emisor}: {tipo}")
    try:
        return definicion.model.model_validate(datos)
    except ValidationError as e:
        raise InvalidMessage(str(e)) from e


def requires_ack(emisor: str, tipo: str) -> bool:
    definicion = CATALOG.get((emisor, tipo))
    return bool(definicion and definicion.requires_ack)

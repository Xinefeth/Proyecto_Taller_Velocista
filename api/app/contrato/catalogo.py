"""Catálogo de mensajes: quién envía cada tipo, qué modelo valida sus datos y si requiere ack."""

from dataclasses import dataclass

from pydantic import BaseModel, ValidationError

from app.contrato import cronometro as c
from app.contrato import robot as r
from app.contrato.manifiesto import Manifiesto


@dataclass(frozen=True)
class Definicion:
    modelo: type[BaseModel]
    requiere_ack: bool
    frecuencia: str


# (emisor, tipo) -> definición. Emisor "api" = mensajes que la API envía al dispositivo.
CATALOGO: dict[tuple[str, str], Definicion] = {
    # Robot -> API
    ("velocista", "manifiesto"): Definicion(Manifiesto, True, "al conectar, primer mensaje"),
    ("velocista", "estado"): Definicion(r.Estado, False, "estado_hz (1 Hz)"),
    ("velocista", "senales"): Definicion(r.Senales, False, "senales_hz (20 Hz) mientras corre"),
    ("velocista", "vuelta"): Definicion(r.Vuelta, True, "tras cierre_vuelta"),
    ("velocista", "sync"): Definicion(r.Sync, True, "al reconectar, si hay vueltas guardadas"),
    ("velocista", "evento"): Definicion(r.Evento, True, "cuando ocurre"),
    ("velocista", "ack"): Definicion(r.Ack, False, "por cada comando"),
    # API -> Robot
    ("api->velocista", "calibrar"): Definicion(r.SinDatos, True, "a pedido"),
    ("api->velocista", "arrancar"): Definicion(r.SinDatos, True, "a pedido"),
    ("api->velocista", "detener"): Definicion(r.SinDatos, True, "a pedido"),
    ("api->velocista", "setup"): Definicion(r.Setup, True, "a pedido"),
    ("api->velocista", "modo"): Definicion(r.Modo, True, "a pedido"),
    ("api->velocista", "linea"): Definicion(r.Linea, True, "a pedido"),
    ("api->velocista", "cierre_vuelta"): Definicion(r.CierreVuelta, True, "al recibir un corte"),
    ("api->velocista", "ack"): Definicion(r.Ack, False, "por cada mensaje que lo requiere"),
    # Cronómetro -> API
    ("cronometro", "hola"): Definicion(c.Hola, True, "al conectar"),
    ("cronometro", "corte"): Definicion(c.Corte, True, "cada paso por la meta"),
    ("cronometro", "estado"): Definicion(c.EstadoCronometro, False, "cada 5 s"),
    ("cronometro", "ack"): Definicion(r.Ack, False, "por cada comando"),
    # API -> Cronómetro
    ("api->cronometro", "rearmar"): Definicion(c.Rearmar, True, "a pedido"),
    ("api->cronometro", "ack"): Definicion(r.Ack, False, "por cada mensaje que lo requiere"),
}


class MensajeInvalido(ValueError):
    pass


def validar_datos(emisor: str, tipo: str, datos: dict) -> BaseModel:
    definicion = CATALOGO.get((emisor, tipo))
    if definicion is None:
        raise MensajeInvalido(f"tipo desconocido para {emisor}: {tipo}")
    try:
        return definicion.modelo.model_validate(datos)
    except ValidationError as e:
        raise MensajeInvalido(str(e)) from e


def requiere_ack(emisor: str, tipo: str) -> bool:
    definicion = CATALOGO.get((emisor, tipo))
    return bool(definicion and definicion.requiere_ack)

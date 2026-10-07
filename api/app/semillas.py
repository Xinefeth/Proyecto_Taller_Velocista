"""Carga manual e idempotente de los datos iniciales de EN-04.

Desde api/: python -m app.semillas
Carga tipos, componentes e inventario sin borrar ni actualizar los registros
existentes. Carga Velocista 001 y su historial inicial solo si no tiene versiones.
"""

import json
import sys
from importlib.resources import files
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import RAIZ_REPO
from app.core.db import SessionLocal
from app.core.errores import ErrorDeNegocio
from app.modulos.armador import service as armador
from app.modulos.catalogo import service as catalogo
from app.modulos.optimizacion import service as control
from app.modulos.reglamento import service as reglamento


def leer_tipos_iniciales() -> list[dict[str, Any]]:
    archivo = RAIZ_REPO / "docs/datos/tipos-componentes.json"
    tipos = json.loads(archivo.read_text(encoding="utf-8"))
    if not isinstance(tipos, list) or not tipos:
        raise ValueError("El archivo de tipos debe contener una lista no vacía")
    claves = {"id", "nombre", "color", "campos", "capacidades"}
    ids = []
    for tipo in tipos:
        if not isinstance(tipo, dict) or set(tipo) != claves:
            raise ValueError("Cada tipo debe tener id, nombre, color, campos y capacidades")
        if not isinstance(tipo["id"], str) or not tipo["id"].strip():
            raise ValueError("Cada tipo necesita un identificador de texto no vacío")
        if not isinstance(tipo["campos"], list) or not isinstance(tipo["capacidades"], list):
            raise ValueError("Campos y capacidades deben ser listas")
        ids.append(tipo["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("El archivo contiene identificadores de tipo repetidos")
    return tipos


def leer_componentes_iniciales() -> list[dict[str, Any]]:
    archivo = files("app").joinpath("datos/componentes.json")
    componentes = json.loads(archivo.read_text(encoding="utf-8"))
    if not isinstance(componentes, list) or not componentes:
        raise ValueError("El archivo de componentes debe contener una lista no vacía")
    claves = {
        "id",
        "tipo_id",
        "nombre",
        "precio",
        "masa_g",
        "tienda",
        "stock",
        "consumo_a",
        "especificaciones",
    }
    ids = []
    for comp in componentes:
        if not isinstance(comp, dict) or set(comp) != claves:
            raise ValueError("Cada componente debe incluir su ficha completa y stock inicial")
        if not isinstance(comp["id"], str) or not comp["id"].strip():
            raise ValueError("Cada componente necesita un identificador de texto no vacío")
        if type(comp["stock"]) is not int or comp["stock"] < 0:
            raise ValueError("El stock inicial debe ser un entero no negativo")
        if not isinstance(comp["especificaciones"], dict):
            raise ValueError("Las especificaciones deben ser un objeto")
        ids.append(comp["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("El archivo contiene identificadores de componente repetidos")
    return componentes


def main() -> int:
    try:
        tipos = leer_tipos_iniciales()
        componentes = leer_componentes_iniciales()
        armado = json.loads(files("app").joinpath("datos/armador.json").read_text(encoding="utf-8"))
        # Una transacción para toda la carga. Cualquier error revierte el lote.
        with SessionLocal.begin() as session:
            nuevos = catalogo.cargar_tipos_iniciales(session, tipos)
            nuevos_componentes, nuevos_inventarios = catalogo.cargar_componentes_iniciales(
                session, componentes
            )
            listado = [(t.id, t.nombre) for t in catalogo.listar_tipos(session)]
            total_componentes, total_inventarios = catalogo.contar_catalogo(session)
            nuevos_robots = armador.cargar_robot_inicial(session)
            total_robots = armador.contar_robots(session)
            nuevas_ranuras, nuevas_versiones = armador.cargar_versiones_iniciales(session, armado)
            controladores = json.loads(
                files("app").joinpath("datos/controladores.json").read_text(encoding="utf-8")
            )
            perfiles = json.loads(
                files("app").joinpath("datos/perfiles.json").read_text(encoding="utf-8")
            )
            nuevos_controladores = control.cargar_controladores(session, controladores)
            nuevos_perfiles = reglamento.cargar_perfiles(session, perfiles)
    except (OSError, ValueError, ErrorDeNegocio) as exc:
        print(f"No se pudieron leer los datos iniciales: {exc}", file=sys.stderr)
        return 1
    except SQLAlchemyError:
        print(
            "No se pudieron cargar las semillas. Verifica PostgreSQL, .env y que hayas "
            "ejecutado alembic upgrade head. Se revirtió la carga.",
            file=sys.stderr,
        )
        return 1
    print(f"Tipos nuevos: {nuevos}. Tipos ya existentes conservados: {len(tipos) - nuevos}.")
    print(f"Total de tipos en la base: {len(listado)}.")
    for clave, nombre in listado:
        print(f"  {clave}: {nombre}")
    print(f"Componentes nuevos: {nuevos_componentes}. Inventarios nuevos: {nuevos_inventarios}.")
    print(f"Total de componentes: {total_componentes}. Total de inventarios: {total_inventarios}.")
    print(f"Robots nuevos: {nuevos_robots}. Total de robots: {total_robots}.")
    print(f"Ranuras nuevas: {nuevas_ranuras}. Versiones nuevas: {nuevas_versiones}.")
    print("Velocista 001: historial existente conservado o versiones v0/v1 iniciales cargadas.")
    print(f"Controladores nuevos: {nuevos_controladores}. Perfiles nuevos: {nuevos_perfiles}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

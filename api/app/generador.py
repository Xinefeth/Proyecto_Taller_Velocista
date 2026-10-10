"""Generador de corridas SIMULADAS para poblar el sistema con datos de prueba.

Desde api/:
    python -m app.generador                 # asegura 40 corridas simuladas
    python -m app.generador --corridas 100  # asegura 100
    python -m app.generador --corridas 20 --semilla 7   # reproducible

Escribe directamente en la base (no pasa por el gateway WebSocket): catálogo y
robot deben existir, así que ejecuta antes `python -m app.semillas`.

Es idempotente por TOPE: cuenta las corridas que ya marcó este generador y solo
crea las que falten hasta `--corridas`. Así un re-deploy en la nube no duplica.
Todas quedan con `fuente="sim"` y `contexto_snapshot["generador"]`, de modo que
nunca se confunden con corridas reales del robot.
"""

import argparse
import random
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import SessionLocal
from app.core.errores import ErrorDeNegocio
from app.modulos.armador import service as armador
from app.modulos.corridas.models import Corrida, SectorVuelta, SegmentoVuelta, Vuelta
from app.modulos.optimizacion.models import Controlador, Setup
from app.modulos.optimizacion.schemas import ControladorSalida
from app.modulos.optimizacion.service import validar_parametros
from app.modulos.reglamento.models import PerfilReglamento

MARCA = "generador-v1"


def _setup_para_generador(session, robot, ctrl: ControladorSalida):
    """Reutiliza (o crea una sola vez) el setup que usan las corridas generadas."""
    nombre = "Generador — PID"
    setup = session.scalar(
        select(Setup).where(Setup.version_id == robot.version_actual_id, Setup.nombre == nombre)
    )
    if setup is not None:
        return setup
    parametros = ctrl.presets["Base"]
    validar_parametros(ctrl.parametros, parametros)
    setup = Setup(
        version_id=robot.version_actual_id,
        controlador_id="pid",
        nombre=nombre,
        parametros=parametros,
        controlador_snapshot=ctrl.model_dump(mode="json"),
    )
    session.add(setup)
    session.flush()
    return setup


def _vueltas(rng: random.Random, corrida_id: int) -> list:
    """Entre 3 y 8 vueltas con tiempos realistas; alguna vez una vuelta sin terminar."""
    objetos = []
    total = rng.randint(3, 8)
    for numero in range(1, total + 1):
        termino = not (numero == total and rng.random() < 0.12)  # ~12%: última sin terminar
        tiempo = round(rng.uniform(8.5, 14.0), 3)
        error = round(rng.uniform(0.2, 2.5), 3)
        vuelta = Vuelta(
            corrida_id=corrida_id,
            numero=numero,
            tiempo_s=tiempo if termino else None,
            duracion_s=tiempo,
            tiempo_interno_ms=round(tiempo * 1000),
            error_acumulado=error,
            lineas_perdidas=rng.randint(0, 2),
            bateria_v=round(rng.uniform(7.2, 8.2), 2),
            termino=termino,
            fuente_tiempo=rng.choice(["meta", "telemetria"]),
            motivo="" if termino else "Salida de línea simulada",
        )
        objetos.append((vuelta, tiempo, error))
    return objetos


def _sectores_y_segmentos(rng: random.Random, vuelta_id: int, tiempo: float, error: float) -> list:
    """3 sectores que suman el tiempo de la vuelta y un par de segmentos recta/curva."""
    objetos = []
    s1 = round(tiempo * rng.uniform(0.28, 0.38), 6)
    s2 = round(tiempo * rng.uniform(0.28, 0.38), 6)
    s3 = round(tiempo - s1 - s2, 6)
    for n, dur in enumerate([s1, s2, max(0.0, s3)], 1):
        objetos.append(SectorVuelta(vuelta_id=vuelta_id, numero=n, tiempo_s=dur))
    acumulado = 0.0
    for n in range(1, rng.randint(2, 4) + 1):
        es_curva = n % 2 == 0
        dur = round(tiempo / 4 * rng.uniform(0.6, 1.1), 6)
        acumulado = round(acumulado + error * rng.uniform(0.1, 0.4), 9)
        objetos.append(
            SegmentoVuelta(
                vuelta_id=vuelta_id,
                numero=n,
                tipo="curva" if es_curva else "recta",
                duracion_s=dur,
                angulo_grados=round(rng.uniform(15, 90), 2) if es_curva else 0,
                error_acumulado=acumulado,
            )
        )
    return objetos


def _crear_corrida(
    session,
    rng: random.Random,
    robot,
    setup,
    perfil,
    ctrl: ControladorSalida,
    marca: str = MARCA,
    reciente: bool = False,
):
    fecha = (
        datetime.now(UTC)
        if reciente
        else datetime.now(UTC) - timedelta(days=rng.randint(0, 30), minutes=rng.randint(0, 24 * 60))
    )
    modo = rng.choice(["prueba", "prueba", "competencia"])
    parametros = ctrl.presets["Base"]
    contexto = {
        "generador": marca,
        "firmware": robot.firmware,
        "manifiesto": None,
        "controlador": ctrl.model_dump(mode="json"),
        "parametros": parametros,
        "perfil": {c.name: getattr(perfil, c.name) for c in perfil.__table__.columns},
    }
    corrida = Corrida(
        version_id=robot.version_actual_id,
        setup_id=setup.id,
        perfil_id=perfil.id,
        fecha=fecha,
        cerrada_en=fecha + timedelta(seconds=rng.randint(18, 40)),
        fuente="sim",
        modo=modo,
        linea=rng.choice(["negra", "negra", "blanca"]),
        compensa_bateria=rng.random() < 0.8,
        potencia_turbina_pct=rng.choice([0, 0, 20, 40, 60]),
        contexto_snapshot=contexto,
        nota="Corrida generada para pruebas",
    )
    session.add(corrida)
    session.flush()
    for vuelta, tiempo, error in _vueltas(rng, corrida.id):
        session.add(vuelta)
        session.flush()
        for obj in _sectores_y_segmentos(rng, vuelta.id, tiempo, error):
            session.add(obj)
    return corrida.id


def generar(session, objetivo: int, rng: random.Random) -> int:
    """Crea las corridas que falten hasta `objetivo`. Devuelve cuántas creó."""
    existentes = session.scalar(
        select(func.count())
        .select_from(Corrida)
        .where(Corrida.contexto_snapshot["generador"].astext == MARCA)
    )
    faltan = max(0, objetivo - (existentes or 0))
    if faltan == 0:
        return 0
    robot = armador.robot_para_escritura(session, "v001")
    armador.comprobar_detenido(session, robot.id)
    controlador = session.get(Controlador, "pid")
    perfil = session.get(PerfilReglamento, "club")
    if robot.version_actual_id is None or controlador is None or perfil is None:
        raise ValueError("Ejecuta python -m app.semillas primero")
    ctrl = ControladorSalida.model_validate(controlador)
    setup = _setup_para_generador(session, robot, ctrl)
    for _ in range(faltan):
        _crear_corrida(session, rng, robot, setup, perfil, ctrl)
    return faltan


MARCA_CONSOLA = "consola-v1"


def crear_una_simulada(session, rng: random.Random | None = None) -> int:
    """Crea UNA corrida simulada nueva y la devuelve (id). La usa la consola al ARRANCAR.

    A diferencia de `generar`, no es idempotente: cada llamada crea una corrida. Queda
    marcada con `contexto_snapshot["generador"] = MARCA_CONSOLA` y fecha actual, para no
    confundirla con las sembradas y para que aparezca al principio del historial.
    """
    rng = rng or random.Random()
    robot = armador.robot_para_escritura(session, "v001")
    armador.comprobar_detenido(session, robot.id)
    controlador = session.get(Controlador, "pid")
    perfil = session.get(PerfilReglamento, "club")
    if robot.version_actual_id is None or controlador is None or perfil is None:
        raise ValueError("Ejecuta python -m app.semillas primero")
    ctrl = ControladorSalida.model_validate(controlador)
    setup = _setup_para_generador(session, robot, ctrl)
    return _crear_corrida(
        session, rng, robot, setup, perfil, ctrl, marca=MARCA_CONSOLA, reciente=True
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--corridas", type=int, default=40, help="total de corridas simuladas a asegurar")
    p.add_argument("--semilla", type=int, default=None, help="semilla aleatoria para reproducibilidad")
    a = p.parse_args()
    if a.corridas < 0:
        print("--corridas no puede ser negativo.", file=sys.stderr)
        return 2
    rng = random.Random(a.semilla)
    try:
        with SessionLocal.begin() as session:
            creadas = generar(session, a.corridas, rng)
    except (SQLAlchemyError, ErrorDeNegocio, ValueError) as exc:
        print(
            f"No se pudo generar datos ({exc}). Verifica migraciones, semillas y que v001 esté "
            "activo y detenido. Se revirtió la carga.",
            file=sys.stderr,
        )
        return 1
    if creadas == 0:
        print(f"Nada que hacer: ya existen al menos {a.corridas} corridas generadas.")
    else:
        print(f"{creadas} corridas simuladas creadas (objetivo {a.corridas}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

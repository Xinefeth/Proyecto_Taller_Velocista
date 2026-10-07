"""Carga opcional y repetible de una corrida SIMULADA para probar el CRUD.

Desde api/: python -m app.demo. Requiere migraciones y semillas aplicadas.
No envía comandos ni representa mediciones del robot físico.
"""

import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.db import SessionLocal
from app.core.errores import ErrorDeNegocio
from app.modulos.armador import service as armador
from app.modulos.corridas.models import Corrida, SectorVuelta, SegmentoVuelta, Vuelta
from app.modulos.optimizacion.models import Controlador, Setup
from app.modulos.optimizacion.schemas import ControladorSalida
from app.modulos.optimizacion.service import validar_parametros
from app.modulos.reglamento.models import PerfilReglamento

MARCA = "crud-demo-v1"


def cargar_demo(session):
    robot = armador.robot_para_escritura(session, "v001")
    armador.comprobar_detenido(session, robot.id)
    existente = session.scalar(
        select(Corrida).where(Corrida.contexto_snapshot["demo"].astext == MARCA)
    )
    if existente:
        return existente.id, False
    controlador = session.get(Controlador, "pid")
    perfil = session.get(PerfilReglamento, "club")
    if robot.version_actual_id is None or controlador is None or perfil is None:
        raise ValueError("Ejecuta python -m app.semillas primero")
    ctrl = ControladorSalida.model_validate(controlador)
    parametros = ctrl.presets["Base"]
    validar_parametros(ctrl.parametros, parametros)
    setup = Setup(
        version_id=robot.version_actual_id,
        controlador_id="pid",
        nombre="Demo CRUD — PID",
        parametros=parametros,
        controlador_snapshot=ctrl.model_dump(mode="json"),
    )
    session.add(setup)
    session.flush()
    ahora = datetime.now(UTC)
    contexto = {
        "demo": MARCA,
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
        fecha=ahora,
        cerrada_en=ahora + timedelta(seconds=22),
        fuente="sim",
        modo="prueba",
        linea="negra",
        compensa_bateria=True,
        potencia_turbina_pct=0,
        contexto_snapshot=contexto,
        nota="Ejemplo simulado para probar la API",
    )
    session.add(corrida)
    session.flush()
    for numero, tiempo, error in [(1, 10.2, 0.8), (2, 10.8, 0.7)]:
        vuelta = Vuelta(
            corrida_id=corrida.id,
            numero=numero,
            tiempo_s=tiempo,
            duracion_s=tiempo,
            tiempo_interno_ms=round(tiempo * 1000),
            error_acumulado=error,
            lineas_perdidas=0,
            bateria_v=7.8,
            termino=True,
            fuente_tiempo="telemetria",
            motivo="Simulación CRUD",
        )
        session.add(vuelta)
        session.flush()
        for n, duracion in enumerate([3.4, 3.2, round(tiempo - 6.6, 6)], 1):
            session.add(SectorVuelta(vuelta_id=vuelta.id, numero=n, tiempo_s=duracion))
        session.add(
            SegmentoVuelta(
                vuelta_id=vuelta.id,
                numero=1,
                tipo="recta",
                duracion_s=tiempo,
                angulo_grados=0,
                error_acumulado=error,
            )
        )
    return corrida.id, True


def main():
    try:
        with SessionLocal.begin() as session:
            corrida_id, nueva = cargar_demo(session)
    except (SQLAlchemyError, ErrorDeNegocio, ValueError):
        print(
            "No se pudo cargar la demo. Verifica migraciones, semillas y que v001 esté activo y detenido. Se revirtió la carga.",
            file=sys.stderr,
        )
        return 1
    print(f"Corrida simulada {'creada' if nueva else 'ya existente'}: {corrida_id}.")
    print(f"Consultar GET /api/corridas/{corrida_id} y GET /api/corridas/{corrida_id}/vueltas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

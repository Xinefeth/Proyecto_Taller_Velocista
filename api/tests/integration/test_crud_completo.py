"""Pruebas de los 32 endpoints y concurrencia en esquemas descartables.

Las transacciones se confirman dentro del esquema de prueba para verificar carreras
reales entre conexiones; al terminar se elimina exclusivamente ese esquema UUID.
"""

import importlib.util
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.core.db import Base, engine, get_session
from app.main import app
from app.modulos.armador import service as armador
from app.modulos.armador.schemas import VersionCrear
from app.modulos.catalogo import service as catalogo
from app.modulos.catalogo.schemas import InventarioActualizar
from app.modulos.corridas.models import Corrida, SectorVuelta, SegmentoVuelta, Vuelta
from app.modulos.optimizacion.models import Setup
from app.semillas import main

pytestmark = pytest.mark.integracion
P = {"kp": 0.6, "ki": 0, "kd": 2.5, "base": 45, "max": 86}


@pytest.fixture()
def entorno(requiere_db, monkeypatch):
    esquema = f"prueba_crud_{uuid4().hex}"
    try:
        with engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{esquema}"'))
            conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
            with Operations.context(MigrationContext.configure(conn)):
                for nombre in [
                    "0001_base",
                    "0002_catalogo",
                    "0003_robot",
                    "0004_versiones",
                    "0005_operaciones",
                ]:
                    ruta = Path(__file__).resolve().parents[2] / f"migrations/versions/{nombre}.py"
                    spec = importlib.util.spec_from_file_location(nombre, ruta)
                    modulo = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(modulo)
                    modulo.upgrade()
        factory = sessionmaker(
            bind=engine.execution_options(schema_translate_map={None: esquema}),
            expire_on_commit=False,
        )
        monkeypatch.setattr("app.semillas.SessionLocal", factory)
        assert main() == 0

        def sesion():
            with factory() as session:
                yield session

        anterior = app.dependency_overrides.copy()
        app.dependency_overrides[get_session] = sesion
        try:
            with TestClient(app) as client:
                yield client, factory, esquema
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(anterior)
    finally:
        with engine.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{esquema}" CASCADE'))


def robot_nuevo(client):
    r = client.post(
        "/api/robots", json={"nombre": "Prueba", "codigo_corto": "PRB", "tipo": "velocista"}
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def setup_nuevo(client):
    version_id = client.get("/api/robots/v001").json()["version_actual_id"]
    r = client.post(
        "/api/robots/v001/setups",
        json={
            "version_id": version_id,
            "nombre": "PID base",
            "controlador_id": "pid",
            "parametros": P,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_migracion_completa_coincide_con_modelos(entorno):
    _, _, esquema = entorno
    with engine.begin() as conn:
        conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
        ctx = MigrationContext.configure(
            conn, opts={"compare_type": True, "compare_server_default": True}
        )
        assert compare_metadata(ctx, Base.metadata) == []


def test_flujo_robot_version_edicion_archivado(entorno):
    c, _, _ = entorno
    rid = robot_nuevo(c)
    assert (
        c.patch(
            f"/api/robots/{rid}", json={"nombre": "Nombre editado", "firmware": "1.0"}
        ).status_code
        == 200
    )
    assert c.patch(f"/api/robots/{rid}", json={"codigo_corto": "001"}).status_code == 409
    assert c.patch(f"/api/robots/{rid}", json={"nombre": None}).status_code == 422
    ranuras = c.get("/api/slots")
    assert ranuras.status_code == 200 and len(ranuras.json()) == 14
    piezas = c.get("/api/robots/v001/versions").json()["items"][-1]["piezas"]
    piezas = {
        k: {"componente_id": v["componente_id"], "cantidad": v["cantidad"]}
        for k, v in piezas.items()
    }
    cuerpo = {"version_base_id": None, "estado": "Actual", "nota": "Primera", "piezas": piezas}
    primera = c.post(f"/api/robots/{rid}/versions", json=cuerpo)
    assert primera.status_code == 201, primera.text
    v0 = primera.json()
    assert v0["etiqueta"] == "v0"
    assert c.post(f"/api/robots/{rid}/versions", json=cuerpo).status_code == 409
    assert c.patch("/api/components/c05", json={"precio": 90}).status_code == 200
    cuerpo["version_base_id"] = v0["id"]
    v1 = c.post(f"/api/robots/{rid}/versions", json=cuerpo).json()
    assert v1["etiqueta"] == "v1"
    historial = c.get(f"/api/robots/{rid}/versions").json()["items"]
    assert [v["estado"] for v in historial] == ["Anterior", "Actual"]
    assert historial[0]["piezas"]["linea"]["componente_snapshot"]["precio"] == 62
    assert historial[1]["piezas"]["linea"]["componente_snapshot"]["precio"] == 90
    inventario = {i["componente_id"]: i for i in c.get("/api/inventory").json()["items"]}
    assert inventario["c05"]["en_robots"] == 4
    for _ in range(2):
        r = c.delete(f"/api/robots/{rid}")
        assert r.status_code == 204 and r.content == b""
    assert c.get(f"/api/robots/{rid}").json()["archivado"]
    assert c.patch(f"/api/robots/{rid}", json={"nombre": "Otro"}).status_code == 409
    inventario = {i["componente_id"]: i for i in c.get("/api/inventory").json()["items"]}
    assert inventario["c05"]["en_robots"] == 2


@pytest.mark.parametrize(
    "piezas,estado,codigo",
    [
        ({}, "Actual", 422),
        ({}, "Concepto", 201),
        ({"motor": {"componente_id": "c05", "cantidad": 1}}, "Concepto", 422),
        ({"mcu": {"componente_id": "c01", "cantidad": 2}}, "Concepto", 422),
        ({"inventada": {"componente_id": "c01", "cantidad": 1}}, "Concepto", 422),
        ({"mcu": {"componente_id": "ausente", "cantidad": 1}}, "Concepto", 404),
    ],
)
def test_version_valida_piezas(entorno, piezas, estado, codigo):
    c, _, _ = entorno
    rid = robot_nuevo(c)
    r = c.post(
        f"/api/robots/{rid}/versions",
        json={"version_base_id": None, "nota": "", "estado": estado, "piezas": piezas},
    )
    assert r.status_code == codigo, r.text
    assert c.get(f"/api/robots/{rid}/versions").json()["total"] == int(codigo == 201)


def test_version_rechaza_pieza_archivada_y_robot_corriendo(entorno, monkeypatch):
    c, _, _ = entorno
    rid = robot_nuevo(c)
    datos = {
        "version_base_id": None,
        "nota": "",
        "estado": "Concepto",
        "piezas": {"mcu": {"componente_id": "c01", "cantidad": 1}},
    }
    assert c.delete("/api/components/c01").status_code == 204
    assert c.post(f"/api/robots/{rid}/versions", json=datos).status_code == 409
    monkeypatch.setattr("app.core.actividad.robot_corriendo", lambda robot_id: robot_id == rid)
    assert c.delete(f"/api/robots/{rid}").status_code == 409


def test_controladores_perfiles_y_setups(entorno):
    c, _, _ = entorno
    assert len(c.get("/api/controllers").json()) == 3
    perfiles = {p["id"]: p for p in c.get("/api/profiles").json()}
    assert len(perfiles) == 4 and perfiles["mr4s"]["reglas"]["sensMax"] is None
    s = setup_nuevo(c)
    assert c.get(f"/api/setups/{s['id']}").json() == s
    assert c.get("/api/robots/v001/setups").json()["total"] == 1
    for parametros in [
        {**P, "kp": 3},
        {**P, "kp": 0.605},
        {**P, "max": 20},
        {"kp": 0.6},
        {**P, "extra": 1},
        {**P, "kp": True},
    ]:
        r = c.post(
            "/api/robots/v001/setups",
            json={
                "version_id": s["version_id"],
                "nombre": "Malo",
                "controlador_id": "pid",
                "parametros": parametros,
            },
        )
        assert r.status_code == 422, r.text
    otro = robot_nuevo(c)
    assert (
        c.post(
            f"/api/robots/{otro}/setups",
            json={
                "version_id": s["version_id"],
                "nombre": "Ajeno",
                "controlador_id": "pid",
                "parametros": P,
            },
        ).status_code
        == 404
    )
    for _ in range(2):
        assert c.delete(f"/api/setups/{s['id']}").status_code == 204
    assert c.get(f"/api/setups/{s['id']}").json()["archivado"]
    assert c.get("/api/robots/v001/setups").json()["total"] == 0


def test_corridas_resumen_filtros_nota_vueltas_y_bloqueos(entorno):
    c, factory, _ = entorno
    s = setup_nuevo(c)
    ahora = datetime.now(UTC)
    with factory.begin() as db:
        ctrl = db.get(Setup, s["id"]).controlador_snapshot
        corrida = Corrida(
            numero=1,
            version_id=s["version_id"],
            setup_id=s["id"],
            perfil_id="club",
            fecha=ahora,
            fuente="sim",
            modo="prueba",
            linea="negra",
            compensa_bateria=True,
            potencia_turbina_pct=0,
            contexto_snapshot={"controlador": ctrl, "parametros": P},
        )
        db.add(corrida)
        db.flush()
        cid = corrida.id
    assert c.get("/api/runs").json()["total"] == 0
    assert c.get(f"/api/runs/{cid}").status_code == 409
    assert c.delete("/api/robots/v001").status_code == 409
    assert c.delete(f"/api/setups/{s['id']}").status_code == 409
    with factory.begin() as db:
        db.get(Corrida, cid).cerrada_en = ahora + timedelta(seconds=30)
        for n, t, err in [(1, 10, 1), (2, 9, 2), (3, None, 0)]:
            vuelta = Vuelta(
                corrida_id=cid,
                numero=n,
                tiempo_s=t,
                duracion_s=t or 12,
                error_acumulado=err,
                lineas_perdidas=0,
                bateria_v=7.8,
                termino=t is not None,
                fuente_tiempo="telemetria",
            )
            db.add(vuelta)
            db.flush()
            db.add(SectorVuelta(vuelta_id=vuelta.id, numero=1, tiempo_s=3))
            db.add(
                SegmentoVuelta(
                    vuelta_id=vuelta.id,
                    numero=1,
                    tipo="recta",
                    duracion_s=2,
                    angulo_grados=0,
                    error_acumulado=0.1,
                )
            )
    r = c.get(f"/api/runs/{cid}")
    assert r.status_code == 200, r.text
    assert r.json()["j"] == 12 and r.json()["tiempo_s"] == 10
    assert c.get("/api/runs?fuente=robot").json()["total"] == 0
    assert c.get("/api/runs?fuente=sim&robot_id=v001&controlador_id=pid").json()["total"] == 1
    assert c.get("/api/runs?offset=99").json()["items"] == []
    assert (
        c.patch(f"/api/runs/{cid}", json={"nota": "Buen agarre"}).json()["nota"]
        == "Buen agarre"
    )
    vueltas = c.get(f"/api/runs/{cid}/laps?limite=2").json()
    assert vueltas["total"] == 3 and len(vueltas["items"]) == 2
    assert vueltas["items"][0]["sectores_s"] == [3]
    assert vueltas["items"][0]["segmentos"][0]["tipo"] == "recta"
    assert c.delete(f"/api/setups/{s['id']}").status_code == 204
    assert c.get(f"/api/runs/{cid}").json()["parametros"] == P


def test_dos_guardados_simultaneos_una_sola_version(entorno):
    c, factory, _ = entorno
    rid = robot_nuevo(c)
    from threading import Barrier

    barrera = Barrier(2)
    datos = VersionCrear(version_base_id=None, nota="Simultánea", estado="Concepto", piezas={})

    def guardar():
        from app.core.errores import ErrorDeNegocio

        with factory() as db:
            barrera.wait(timeout=10)
            try:
                armador.crear_version(db, rid, datos)
                return 201
            except ErrorDeNegocio as e:
                return e.codigo_http

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(lambda _: guardar(), range(2)))
    assert sorted(resultados) == [201, 409]
    assert c.get(f"/api/robots/{rid}/versions").json()["total"] == 1


def test_dos_actualizaciones_simultaneas_un_solo_stock(entorno):
    _, factory, _ = entorno
    from threading import Barrier

    barrera = Barrier(2)

    def guardar(stock):
        from app.core.errores import ErrorDeNegocio

        with factory() as db:
            barrera.wait(timeout=10)
            try:
                catalogo.actualizar_inventario(
                    db, "c05", InventarioActualizar(stock=stock, revision=1)
                )
                return 200
            except ErrorDeNegocio as e:
                return e.codigo_http

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        resultados = list(ejecutor.map(guardar, [8, 9]))
    assert sorted(resultados) == [200, 409]


def test_demo_simulada_es_repetible_y_compatible_con_corridas(entorno):
    from app.demo import cargar_demo

    c, factory, _ = entorno
    with factory.begin() as db:
        cid, nueva = cargar_demo(db)
        assert nueva
    with factory.begin() as db:
        assert cargar_demo(db) == (cid, False)
    r = c.get(f"/api/runs/{cid}")
    assert r.status_code == 200, r.text
    assert r.json()["fuente"] == "sim" and r.json()["j"] == 11.8
    assert c.get(f"/api/runs/{cid}/laps").json()["total"] == 2


def test_post_corrida_simulada_crea_y_persiste(entorno):
    c, _, _ = entorno
    antes = c.get("/api/runs").json()["total"]
    r1 = c.post("/api/runs/simulated")
    assert r1.status_code == 201, r1.text
    uno = r1.json()
    assert uno["fuente"] == "sim" and uno["j"] >= 0
    r2 = c.post("/api/runs/simulated")
    assert r2.status_code == 201, r2.text
    assert r2.json()["id"] != uno["id"]  # cada ARRANCAR crea una corrida nueva
    lista = c.get("/api/runs").json()
    assert lista["total"] == antes + 2
    assert c.get(f"/api/runs/{uno['id']}").status_code == 200
    assert c.get(f"/api/runs/{uno['id']}/laps").json()["total"] >= 3


def test_contrato_completo_registrado_en_fastapi(entorno):
    import json

    c, _, _ = entorno
    diseno = json.loads(
        (Path(__file__).resolve().parents[3] / "docs/api/openapi.json").read_text(encoding="utf-8")
    )
    servido = c.get("/openapi.json").json()
    metodos = {"get", "post", "put", "patch", "delete"}
    esperado = {(ruta, m) for ruta, ops in diseno["paths"].items() for m in ops if m in metodos}
    real = {(ruta, m) for ruta, ops in servido["paths"].items() for m in ops if m in metodos}
    assert real == esperado
    assert len(real) == 33

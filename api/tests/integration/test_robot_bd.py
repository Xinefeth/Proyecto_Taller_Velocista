"""Robot y semillas en esquemas temporales; nunca modifica tablas del usuario."""

import importlib.util
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base, engine, get_session
from app.modulos.armador import service
from app.modulos.armador.models import Ranura, Robot, Version, VersionComponente
from app.modulos.catalogo.models import Componente, Inventario
from app.semillas import main

pytestmark = pytest.mark.integracion


@pytest.fixture()
def robot_bd(requiere_db):
    with engine.connect() as conn, conn.begin() as transaccion:
        esquema = f"prueba_robot_{uuid4().hex}"
        conn.execute(text(f'CREATE SCHEMA "{esquema}"'))
        conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
        migraciones = []
        with Operations.context(MigrationContext.configure(conn)):
            for nombre in ["0002_catalogo", "0003_robot", "0004_versiones", "0005_operaciones"]:
                archivo = Path(__file__).resolve().parents[2] / f"migrations/versions/{nombre}.py"
                spec = importlib.util.spec_from_file_location(nombre, archivo)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)
                modulo.upgrade()
                migraciones.append(modulo)
            yield conn, migraciones[-2]
        transaccion.rollback()


def test_migracion_robot_coincide_con_modelos(robot_bd):
    conn, _ = robot_bd
    contexto = MigrationContext.configure(
        conn,
        opts={
            "compare_type": True,
            "compare_server_default": True,
            "include_object": lambda obj, nombre, tipo, reflejado, comparado: (
                nombre
                in {
                    "robot",
                    "ranura",
                    "version",
                    "version_componente",
                    "tipo_componente",
                    "componente",
                    "inventario",
                }
                if tipo == "table"
                else True
            ),
        },
    )
    assert compare_metadata(contexto, Base.metadata) == []


def test_robot_semilla_repetida_conserva_cambios(robot_bd):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        assert service.cargar_robot_inicial(session) == 1
        session.commit()
        robot = session.get(Robot, "v001")
        assert (robot.nombre, robot.codigo_corto, robot.tipo, robot.firmware) == (
            "Velocista 001",
            "001",
            "velocista",
            "0.3.1",
        )
        assert robot.version_actual_id is None
        assert robot.archivado is False
        robot.nombre = "Nombre editado"
        robot.firmware = "0.4.0"
        robot.archivado = True
        session.commit()
        assert service.cargar_robot_inicial(session) == 0
        session.commit()
        session.expire_all()
        assert (robot.nombre, robot.firmware, robot.archivado) == ("Nombre editado", "0.4.0", True)
        assert service.contar_robots(session) == 1


@pytest.mark.parametrize(
    "cambio",
    [
        {"id": " "},
        {"nombre": " "},
        {"codigo_corto": " "},
        {"tipo": "otro"},
        {"version_actual_id": 1},
    ],
)
def test_robot_rechaza_datos_invalidos(robot_bd, cambio):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        with pytest.raises(IntegrityError):
            with session.begin():
                session.add(
                    Robot(
                        **{
                            "id": "prueba",
                            "nombre": "Prueba",
                            "codigo_corto": "P",
                            "tipo": "velocista",
                            **cambio,
                        }
                    )
                )
        assert service.contar_robots(session) == 0


def test_conflicto_codigo_revierte_lote_completo(robot_bd, monkeypatch, capsys):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        session.add(Robot(id="otro", nombre="Existente", codigo_corto="001", tipo="minisumo"))
        session.commit()
    monkeypatch.setattr(
        "app.semillas.SessionLocal",
        sessionmaker(bind=conn, join_transaction_mode="create_savepoint"),
    )
    assert main() == 1
    assert "Se revirtió la carga" in capsys.readouterr().err
    assert conn.scalar(select(func.count()).select_from(Componente)) == 0
    assert conn.scalar(select(func.count()).select_from(Robot)) == 1


def test_downgrade_robot_conserva_catalogo(robot_bd):
    conn, migracion = robot_bd
    archivo = Path(__file__).resolve().parents[2] / "migrations/versions/0005_operaciones.py"
    spec = importlib.util.spec_from_file_location("operaciones_down", archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.downgrade()
    migracion.downgrade()
    assert set(inspect(conn).get_table_names()) == {
        "robot",
        "tipo_componente",
        "componente",
        "inventario",
    }


@pytest.fixture()
def cliente_robot(cliente, robot_bd):
    conn, _ = robot_bd

    def sesion_prueba():
        with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
            yield session

    anterior = cliente.app.dependency_overrides.copy()
    cliente.app.dependency_overrides[get_session] = sesion_prueba
    try:
        yield cliente
    finally:
        cliente.app.dependency_overrides.clear()
        cliente.app.dependency_overrides.update(anterior)


def test_consultar_robot_semilla(cliente_robot, robot_bd):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        service.cargar_robot_inicial(session)
        session.commit()
    respuesta = cliente_robot.get("/api/robots/v001")
    assert respuesta.status_code == 200
    esperado = {
        "id": "v001",
        "nombre": "Velocista 001",
        "codigo_corto": "001",
        "tipo": "velocista",
        "firmware": "0.3.1",
        "version_actual_id": None,
        "archivado": False,
    }
    assert respuesta.json() == esperado
    pagina = cliente_robot.get("/api/robots").json()
    assert pagina == {"items": [esperado], "total": 1, "limite": 50, "offset": 0}


def test_listar_robots_orden_paginacion_y_archivados(cliente_robot, robot_bd):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        for codigo, archivado in [("003", False), ("001", False), ("002", True)]:
            session.add(
                Robot(
                    id=codigo,
                    nombre=codigo,
                    codigo_corto=codigo,
                    tipo="velocista",
                    archivado=archivado,
                )
            )
        session.commit()
    primera = cliente_robot.get("/api/robots?limite=1").json()
    segunda = cliente_robot.get("/api/robots?limite=1&offset=1").json()
    assert primera["total"] == segunda["total"] == 2
    assert primera["items"][0]["id"] == "001"
    assert segunda["items"][0]["id"] == "003"
    assert cliente_robot.get("/api/robots?offset=99").json()["items"] == []
    assert cliente_robot.get("/api/robots/002").json()["archivado"] is True


def test_robots_base_vacia_e_id_inexistente(cliente_robot):
    respuesta = cliente_robot.get("/api/robots")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "total": 0, "limite": 50, "offset": 0}
    respuesta = cliente_robot.get("/api/robots/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"]["motivo"] == "robot_no_encontrado"


@pytest.mark.parametrize(
    "url",
    [
        "/api/robots?limite=0",
        "/api/robots?limite=201",
        "/api/robots?offset=-1",
        "/api/robots/" + "x" * 41,
    ],
)
def test_robots_valida_parametros(cliente, url):
    assert cliente.get(url).status_code == 422


@pytest.mark.parametrize(
    "url,funcion",
    [
        ("/api/robots", "listar_robots"),
        ("/api/robots/v001", "obtener_robot"),
    ],
)
def test_robots_base_caida(cliente, monkeypatch, url, funcion):
    def sin_base(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, funcion, sin_base)
    assert cliente.get(url).status_code == 503


@pytest.fixture()
def historial_inicial(robot_bd, monkeypatch):
    conn, _ = robot_bd
    monkeypatch.setattr(
        "app.semillas.SessionLocal",
        sessionmaker(bind=conn, join_transaction_mode="create_savepoint"),
    )
    assert main() == 0
    return conn


def test_historial_inicial_y_repeticion_conservan_instantaneas(historial_inicial):
    with Session(bind=historial_inicial, join_transaction_mode="create_savepoint") as session:
        versiones = session.scalars(select(Version).order_by(Version.ordinal)).all()
        assert [(v.ordinal, v.estado) for v in versiones] == [(0, "Descartada"), (1, "Actual")]
        assert [(v.fecha.month, v.fecha.day) for v in versiones] == [(9, 20), (9, 29)]
        assert session.get(Robot, "v001").version_actual_id == versiones[1].id
        assert session.scalar(select(func.count()).select_from(Ranura)) == 14
        assert session.scalar(select(func.count()).select_from(VersionComponente)) == 19
        actual_id = versiones[1].id
        pieza = session.get(VersionComponente, (actual_id, "linea"))
        original = dict(pieza.componente_snapshot)
        assert pieza.cantidad == 2
        assert "stock" not in original and "archivado" not in original
        session.get(Componente, "c05").precio = 80
        session.get(Inventario, "c05").stock = 7
        versiones[1].nota = "Nota editada"
        session.commit()
    assert main() == 0
    with Session(bind=historial_inicial, join_transaction_mode="create_savepoint") as session:
        assert session.scalar(select(func.count()).select_from(Version)) == 2
        assert session.get(VersionComponente, (actual_id, "linea")).componente_snapshot == original
        assert session.get(Version, actual_id).nota == "Nota editada"
        assert session.get(Inventario, "c05").stock == 7


def test_inventario_demanda_solo_version_vigente(cliente_robot, historial_inicial):
    pagina = cliente_robot.get("/api/inventario").json()
    items = {i["componente_id"]: i for i in pagina["items"]}
    assert items["c05"]["en_robots"] == 2
    assert items["c05"]["disponible"] == 1
    assert items["c15"]["en_robots"] == 0  # Solo usada en v0.
    respuesta = cliente_robot.put("/api/inventario/c05", json={"stock": 1, "revision": 1})
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "componente_id": "c05",
        "stock": 1,
        "revision": 2,
        "en_robots": 2,
        "disponible": -1,
        "faltante": 1,
    }


def test_inventario_archivado_con_demanda_y_robot_archivado(cliente_robot, historial_inicial):
    conn = historial_inicial
    conn.execute(update(Componente).where(Componente.id == "c05").values(archivado=True))
    conn.execute(update(Inventario).where(Inventario.componente_id == "c05").values(stock=0))
    items = {i["componente_id"]: i for i in cliente_robot.get("/api/inventario").json()["items"]}
    assert items["c05"]["faltante"] == 2
    conn.execute(update(Robot).where(Robot.id == "v001").values(archivado=True))
    items = {i["componente_id"]: i for i in cliente_robot.get("/api/inventario").json()["items"]}
    assert "c05" not in items
    assert all(i["en_robots"] == 0 for i in items.values())


def test_inventario_incluye_concepto(cliente_robot, historial_inicial):
    historial_inicial.execute(update(Version).where(Version.ordinal == 1).values(estado="Concepto"))
    items = {i["componente_id"]: i for i in cliente_robot.get("/api/inventario").json()["items"]}
    assert items["c05"]["en_robots"] == 2


def test_puntero_rechaza_version_de_otro_robot(historial_inicial):
    with Session(bind=historial_inicial, join_transaction_mode="create_savepoint") as session:
        version_id = session.get(Robot, "v001").version_actual_id
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                session.add(
                    Robot(
                        id="otro",
                        nombre="Otro",
                        codigo_corto="002",
                        tipo="velocista",
                        version_actual_id=version_id,
                    )
                )
                session.flush()


def test_version_rechaza_segunda_actual(historial_inicial):
    with Session(bind=historial_inicial, join_transaction_mode="create_savepoint") as session:
        v0 = session.scalar(select(Version).where(Version.ordinal == 0))
        with pytest.raises(IntegrityError):
            with session.begin_nested():
                v0.estado = "Actual"
                session.flush()


def test_historial_http_con_piezas_y_paginacion(cliente_robot, historial_inicial):
    respuesta = cliente_robot.get("/api/robots/v001/versiones")
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    assert (pagina["total"], pagina["limite"], pagina["offset"]) == (2, 50, 0)
    v0, v1 = pagina["items"]
    assert (v0["etiqueta"], v0["estado"], len(v0["piezas"])) == ("v0", "Descartada", 8)
    assert (v1["etiqueta"], v1["estado"], len(v1["piezas"])) == ("v1", "Actual", 11)
    assert v1["piezas"]["linea"]["cantidad"] == 2
    assert v1["piezas"]["linea"]["componente_id"] == "c05"
    assert v1["id"] == cliente_robot.get("/api/robots/v001").json()["version_actual_id"]
    for version in (v0, v1):
        detalle = cliente_robot.get(f"/api/robots/v001/versiones/{version['id']}")
        assert detalle.status_code == 200
        assert detalle.json() == version
        for pieza in version["piezas"].values():
            assert "stock" not in pieza["componente_snapshot"]
            assert "archivado" not in pieza["componente_snapshot"]
    pagina2 = cliente_robot.get("/api/robots/v001/versiones?limite=1&offset=1").json()
    assert pagina2["items"] == [v1]
    assert pagina2["total"] == 2
    assert cliente_robot.get("/api/robots/v001/versiones?offset=99").json()["items"] == []


def test_historial_http_conserva_snapshot_tras_editar_catalogo(cliente_robot, historial_inicial):
    anterior = cliente_robot.get("/api/robots/v001/versiones").json()
    assert cliente_robot.patch("/api/componentes/c05", json={"precio": 90}).status_code == 200
    assert cliente_robot.get("/api/robots/v001/versiones").json() == anterior


def test_version_de_otro_robot_no_es_accesible(cliente_robot, historial_inicial):
    version = cliente_robot.get("/api/robots/v001/versiones").json()["items"][0]
    with Session(bind=historial_inicial, join_transaction_mode="create_savepoint") as session:
        session.add(Robot(id="otro", nombre="Otro", codigo_corto="002", tipo="velocista"))
        session.commit()
    respuesta = cliente_robot.get(f"/api/robots/otro/versiones/{version['id']}")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"]["motivo"] == "version_no_encontrada"


def test_historial_robot_sin_versiones_y_no_existente(cliente_robot, robot_bd):
    conn, _ = robot_bd
    with Session(bind=conn, join_transaction_mode="create_savepoint") as session:
        service.cargar_robot_inicial(session)
        session.commit()
    respuesta = cliente_robot.get("/api/robots/v001/versiones")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "total": 0, "limite": 50, "offset": 0}
    assert cliente_robot.get("/api/robots/no-existe/versiones").status_code == 404
    assert cliente_robot.get("/api/robots/v001/versiones/999").status_code == 404


def test_historial_robot_archivado_sigue_disponible(cliente_robot, historial_inicial):
    historial_inicial.execute(update(Robot).where(Robot.id == "v001").values(archivado=True))
    respuesta = cliente_robot.get("/api/robots/v001/versiones")
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 2


@pytest.mark.parametrize(
    "url",
    [
        "/api/robots/v001/versiones?limite=0",
        "/api/robots/v001/versiones?limite=201",
        "/api/robots/v001/versiones?offset=-1",
        "/api/robots/v001/versiones/0",
        "/api/robots/v001/versiones/9007199254740992",
        "/api/robots/v001/versiones/abc",
        "/api/robots/" + "x" * 41 + "/versiones",
    ],
)
def test_historial_valida_parametros(cliente, url):
    assert cliente.get(url).status_code == 422


@pytest.mark.parametrize(
    "url,funcion",
    [
        ("/api/robots/v001/versiones", "listar_versiones"),
        ("/api/robots/v001/versiones/1", "obtener_version"),
    ],
)
def test_historial_con_base_caida(cliente, monkeypatch, url, funcion):
    def sin_base(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, funcion, sin_base)
    assert cliente.get(url).status_code == 503


def test_crear_robot_persiste_sin_versiones(cliente_robot):
    datos = {"nombre": "Robot de pruebas", "codigo_corto": "PRB", "tipo": "velocista"}
    respuesta = cliente_robot.post("/api/robots", json=datos)
    assert respuesta.status_code == 201
    robot = respuesta.json()
    assert robot == {
        **datos,
        "id": robot["id"],
        "firmware": None,
        "version_actual_id": None,
        "archivado": False,
    }
    assert cliente_robot.get(f"/api/robots/{robot['id']}").json() == robot
    assert cliente_robot.get("/api/robots").json()["items"] == [robot]
    historial = cliente_robot.get(f"/api/robots/{robot['id']}/versiones").json()
    assert historial["total"] == 0
    assert historial["items"] == []


def test_crear_robot_codigo_duplicado_conserva_existente(cliente_robot):
    datos = {"nombre": "Original", "codigo_corto": "PRB", "tipo": "velocista"}
    original = cliente_robot.post("/api/robots", json=datos).json()
    respuesta = cliente_robot.post("/api/robots", json={**datos, "nombre": "Duplicado"})
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "conflicto"
    assert cliente_robot.get("/api/robots").json()["items"] == [original]


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre": " "},
        {"nombre": "x" * 121},
        {"codigo_corto": " "},
        {"codigo_corto": "x" * 13},
        {"tipo": "otro"},
        {"firmware": "x" * 21},
        {"id": "manual"},
        {"version_actual_id": 1},
        {"archivado": True},
    ],
)
def test_crear_robot_valida_entrada(cliente_robot, cambio):
    datos = {"nombre": "Prueba", "codigo_corto": "PRB", "tipo": "velocista", **cambio}
    assert cliente_robot.post("/api/robots", json=datos).status_code == 422
    assert cliente_robot.get("/api/robots").json()["total"] == 0


def test_crear_robot_admite_firmware_y_recorta_espacios(cliente_robot):
    respuesta = cliente_robot.post(
        "/api/robots",
        json={
            "nombre": "  MiniSumo de prueba ",
            "codigo_corto": " MS2 ",
            "tipo": "minisumo",
            "firmware": " 0.3.1 ",
        },
    )
    assert respuesta.status_code == 201
    robot = respuesta.json()
    assert (robot["nombre"], robot["codigo_corto"], robot["firmware"]) == (
        "MiniSumo de prueba",
        "MS2",
        "0.3.1",
    )


def test_crear_robot_revierte_si_falla_commit(cliente_robot, monkeypatch):
    with monkeypatch.context() as parche:

        def falla_commit(session):
            raise OperationalError("COMMIT", {}, Exception("fallo al confirmar"))

        parche.setattr(Session, "commit", falla_commit)
        respuesta = cliente_robot.post(
            "/api/robots",
            json={
                "nombre": "Prueba",
                "codigo_corto": "PRB",
                "tipo": "velocista",
            },
        )
        assert respuesta.status_code == 503
    assert cliente_robot.get("/api/robots").json()["total"] == 0

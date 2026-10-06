"""Prueba la migración y restricciones en un esquema temporal de PostgreSQL.

Cada prueba revierte toda su transacción, incluido el esquema. No migra ni
inserta registros en las tablas del usuario.
"""

import importlib.util
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import delete, func, insert, inspect, select, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.db import Base, engine, get_session
from app.modulos.catalogo import service
from app.modulos.catalogo.models import Componente, Inventario, TipoComponente
from app.semillas import leer_componentes_iniciales, leer_tipos_iniciales, main

pytestmark = pytest.mark.integracion
TABLAS = {"tipo_componente", "componente", "inventario"}


@pytest.fixture()
def migracion():
    archivo = Path(__file__).resolve().parents[2] / "migrations/versions/0002_catalogo.py"
    spec = importlib.util.spec_from_file_location("migracion_catalogo", archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture()
def conexion(requiere_db, migracion):
    with engine.connect() as conn, conn.begin() as transaccion:
        esquema = f"prueba_catalogo_{uuid4().hex}"
        conn.execute(text(f'CREATE SCHEMA "{esquema}"'))
        conn.execute(text(f'SET LOCAL search_path TO "{esquema}"'))
        with Operations.context(MigrationContext.configure(conn)):
            migracion.upgrade()
            yield conn
        transaccion.rollback()


def poblar(conn):
    conn.execute(
        insert(TipoComponente).values(id="linea", nombre="Sensor de línea", color="#3DDC97")
    )
    conn.execute(
        insert(Componente).values(
            id="c05",
            tipo_id="linea",
            nombre="QTR-8A",
            precio=62,
            masa_g=3,
            especificaciones={"canales": 8},
        )
    )


def test_migracion_coincide_con_modelos(conexion):
    assert set(inspect(conexion).get_table_names()) == TABLAS
    ctx = MigrationContext.configure(
        conexion,
        opts={
            "compare_type": True,
            "compare_server_default": True,
            "include_object": lambda obj, nombre, tipo, reflejado, comparado: (
                nombre in TABLAS if tipo == "table" else True
            ),
        },
    )
    assert compare_metadata(ctx, Base.metadata) == []


def test_guardar_consultar_y_defaults(conexion):
    poblar(conexion)
    conexion.execute(insert(Inventario).values(componente_id="c05"))
    fila = conexion.execute(select(Componente.__table__)).mappings().one()
    assert fila["precio"] == Decimal("62.00")
    assert fila["especificaciones"] == {"canales": 8}
    assert fila["consumo_a"] is None
    assert fila["tienda"] == ""
    assert fila["archivado"] is False
    stock = conexion.execute(select(Inventario.__table__)).mappings().one()
    assert (stock["stock"], stock["revision"]) == (0, 1)


@pytest.mark.parametrize(
    "cambio",
    [
        {"precio": 0},
        {"precio": -1},
        {"precio": Decimal("NaN")},
        {"masa_g": -1},
        {"masa_g": Decimal("NaN")},
        {"consumo_a": -1},
        {"consumo_a": Decimal("NaN")},
        {"nombre": "   "},
        {"tipo_id": "no_existe"},
        {"especificaciones": []},
    ],
)
def test_rechaza_componente_invalido(conexion, cambio):
    conexion.execute(
        insert(TipoComponente).values(id="linea", nombre="Sensor de línea", color="#3DDC97")
    )
    datos = {"id": "c05", "tipo_id": "linea", "nombre": "QTR-8A", "precio": 62, "masa_g": 3}
    with pytest.raises(IntegrityError), conexion.begin_nested():
        conexion.execute(insert(Componente).values(**(datos | cambio)))


@pytest.mark.parametrize("cambio", [{"stock": -1}, {"revision": 0}, {"componente_id": "ausente"}])
def test_rechaza_inventario_invalido(conexion, cambio):
    poblar(conexion)
    with pytest.raises(IntegrityError), conexion.begin_nested():
        conexion.execute(insert(Inventario).values(**({"componente_id": "c05"} | cambio)))


def test_no_elimina_referencias_del_inventario(conexion):
    poblar(conexion)
    conexion.execute(insert(Inventario).values(componente_id="c05", stock=3))
    with pytest.raises(IntegrityError), conexion.begin_nested():
        conexion.execute(delete(Componente).where(Componente.id == "c05"))
    with pytest.raises(IntegrityError), conexion.begin_nested():
        conexion.execute(delete(TipoComponente).where(TipoComponente.id == "linea"))


def test_downgrade_deja_el_esquema_vacio(conexion, migracion):
    migracion.downgrade()
    assert inspect(conexion).get_table_names() == []


def test_semillas_repetidas_no_duplican_ni_sobrescriben(conexion):
    tipos = leer_tipos_iniciales()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        assert service.cargar_tipos_iniciales(session, tipos) == 14
        session.commit()
        session.execute(
            update(TipoComponente)
            .where(TipoComponente.id == "enc")
            .values(nombre="Encoder editado por el club", capacidades=[])
        )
        session.commit()
        assert service.cargar_tipos_iniciales(session, tipos) == 0
        session.commit()
        guardados = {t.id: t for t in service.listar_tipos(session)}
        assert len(guardados) == 14
        assert guardados["enc"].nombre == "Encoder editado por el club"
        assert guardados["enc"].capacidades == []
        for tipo in tipos:
            if tipo["id"] != "enc":
                assert guardados[tipo["id"]].campos == tipo["campos"]
                assert guardados[tipo["id"]].capacidades == tipo["capacidades"]


def test_semillas_completan_un_catalogo_parcial(conexion):
    tipos = leer_tipos_iniciales()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        assert service.cargar_tipos_iniciales(session, tipos[:3]) == 3
        assert service.cargar_tipos_iniciales(session, tipos) == 11
        assert len(service.listar_tipos(session)) == 14
        assert service.cargar_tipos_iniciales(session, []) == 0


def test_semillas_invalidas_revierten_el_lote(conexion):
    tipos = leer_tipos_iniciales()
    tipos[-1]["color"] = "#ZZZZZZ"
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        with pytest.raises(IntegrityError):
            with session.begin():
                service.cargar_tipos_iniciales(session, tipos)
        assert service.listar_tipos(session) == []


@pytest.fixture()
def cliente_catalogo(cliente, conexion):
    def sesion_prueba():
        with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
            yield session

    overrides = cliente.app.dependency_overrides
    previo = overrides.get(get_session)
    overrides[get_session] = sesion_prueba
    try:
        yield cliente
    finally:
        if previo is None:
            overrides.pop(get_session, None)
        else:
            overrides[get_session] = previo


def test_endpoint_tipos_consulta_los_datos_guardados(cliente_catalogo, conexion):
    tipos = leer_tipos_iniciales()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        service.cargar_tipos_iniciales(session, tipos)
        session.execute(
            update(TipoComponente)
            .where(TipoComponente.id == "enc")
            .values(nombre="Encoder del club")
        )
        session.commit()
    respuesta = cliente_catalogo.get("/api/tipos-componentes")
    assert respuesta.status_code == 200
    guardados = respuesta.json()
    assert len(guardados) == 14
    assert [t["id"] for t in guardados] == sorted(t["id"] for t in tipos)
    esperados = {t["id"]: t for t in tipos}
    esperados["enc"]["nombre"] = "Encoder del club"
    assert {t["id"]: t for t in guardados} == esperados


def test_endpoint_tipos_sin_semillas_devuelve_lista_vacia(cliente_catalogo):
    respuesta = cliente_catalogo.get("/api/tipos-componentes")
    assert respuesta.status_code == 200
    assert respuesta.json() == []


def test_endpoint_tipos_con_base_caida_devuelve_503(cliente, monkeypatch):
    def sin_base(session):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, "listar_tipos", sin_base)
    respuesta = cliente.get("/api/tipos-componentes")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"]["motivo"] == "base_no_disponible"


def test_semillas_componentes_conservan_fichas_y_stock(conexion):
    componentes = leer_componentes_iniciales()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        service.cargar_tipos_iniciales(session, leer_tipos_iniciales())
        assert service.cargar_componentes_iniciales(session, componentes) == (25, 25)
        session.commit()
        for comp in componentes:
            guardado = session.get(Componente, comp["id"])
            assert guardado.tipo_id == comp["tipo_id"]
            assert guardado.nombre == comp["nombre"]
            assert guardado.precio == Decimal(str(comp["precio"]))
            assert guardado.especificaciones == comp["especificaciones"]
            assert session.get(Inventario, comp["id"]).stock == comp["stock"]
        session.execute(update(Componente).where(Componente.id == "c05").values(precio=80))
        session.execute(
            update(Inventario).where(Inventario.componente_id == "c05").values(stock=9, revision=2)
        )
        session.commit()
        assert service.cargar_componentes_iniciales(session, componentes) == (0, 0)
        session.commit()
        session.expire_all()
        assert service.contar_catalogo(session) == (25, 25)
        assert session.get(Componente, "c05").precio == Decimal("80")
        assert session.get(Inventario, "c05").stock == 9
        assert session.get(Inventario, "c05").revision == 2


def test_semillas_reparan_inventario_ausente_sin_reemplazar_ficha(conexion):
    poblar(conexion)
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        service.cargar_tipos_iniciales(session, leer_tipos_iniciales())
        assert service.cargar_componentes_iniciales(session, leer_componentes_iniciales()) == (
            24,
            25,
        )
        assert session.get(Componente, "c05").nombre == "QTR-8A"
        assert session.get(Inventario, "c05").stock == 3
        assert service.cargar_componentes_iniciales(session, []) == (0, 0)


def test_inventario_invalido_revierte_tambien_las_fichas(conexion):
    componentes = leer_componentes_iniciales()
    componentes[-1]["stock"] = -1
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        service.cargar_tipos_iniciales(session, leer_tipos_iniciales())
        session.commit()
        with pytest.raises(IntegrityError):
            with session.begin():
                service.cargar_componentes_iniciales(session, componentes)
        assert service.contar_catalogo(session) == (0, 0)


def test_comando_semillas_se_puede_repetir(conexion, monkeypatch, capsys):
    monkeypatch.setattr(
        "app.semillas.SessionLocal",
        sessionmaker(bind=conexion, join_transaction_mode="create_savepoint"),
    )
    assert main() == 0
    assert "Componentes nuevos: 25. Inventarios nuevos: 25." in capsys.readouterr().out
    assert main() == 0
    salida = capsys.readouterr().out
    assert "Tipos nuevos: 0." in salida
    assert "Componentes nuevos: 0. Inventarios nuevos: 0." in salida
    assert "Total de componentes: 25. Total de inventarios: 25." in salida


@pytest.fixture()
def catalogo_inicial(conexion):
    componentes = leer_componentes_iniciales()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        service.cargar_tipos_iniciales(session, leer_tipos_iniciales())
        service.cargar_componentes_iniciales(session, componentes)
        session.commit()
    return componentes


def test_listar_componentes_devuelve_fichas_y_stock(cliente_catalogo, catalogo_inicial):
    respuesta = cliente_catalogo.get("/api/componentes")
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    assert (pagina["total"], pagina["limite"], pagina["offset"]) == (25, 50, 0)
    assert {c["id"]: c for c in pagina["items"]} == {
        c["id"]: {**c, "archivado": False} for c in catalogo_inicial
    }
    assert isinstance(pagina["items"][0]["precio"], (int, float))


def test_listar_componentes_pagina_sin_duplicados(cliente_catalogo, catalogo_inicial):
    primera = cliente_catalogo.get("/api/componentes?limite=4&offset=0").json()
    segunda = cliente_catalogo.get("/api/componentes?limite=4&offset=4").json()
    completa = cliente_catalogo.get("/api/componentes").json()
    assert primera["total"] == segunda["total"] == 25
    assert primera["items"] + segunda["items"] == completa["items"][:8]
    assert len({c["id"] for c in primera["items"] + segunda["items"]}) == 8
    vacia = cliente_catalogo.get("/api/componentes?offset=99").json()
    assert vacia["items"] == []
    assert vacia["total"] == 25


@pytest.mark.parametrize(
    "query,ids",
    [
        ({"q": "BATERIA"}, {"c14", "c15"}),
        ({"q": "batería"}, {"c14", "c15"}),
        ({"q": "QTR", "tipo_id": "linea"}, {"c05", "c06"}),
        ({"q": "QTR", "tipo_id": "motor"}, set()),
        ({"q": "magnetico"}, {"c22"}),
        ({"q": "  MPU-6050  "}, {"c23"}),
        ({"q": "%"}, set()),
        ({"q": "_"}, set()),
    ],
)
def test_busqueda_de_componentes(cliente_catalogo, catalogo_inicial, query, ids):
    respuesta = cliente_catalogo.get("/api/componentes", params=query)
    assert respuesta.status_code == 200
    pagina = respuesta.json()
    assert {c["id"] for c in pagina["items"]} == ids
    assert pagina["total"] == len(ids)


def test_listado_excluye_archivados(cliente_catalogo, catalogo_inicial, conexion):
    conexion.execute(update(Componente).where(Componente.id == "c05").values(archivado=True))
    pagina = cliente_catalogo.get("/api/componentes?q=QTR").json()
    assert pagina["total"] == 1
    assert [c["id"] for c in pagina["items"]] == ["c06"]


def test_componentes_sin_semillas_devuelve_pagina_vacia(cliente_catalogo):
    respuesta = cliente_catalogo.get("/api/componentes")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "total": 0, "limite": 50, "offset": 0}


@pytest.mark.parametrize(
    "query",
    [{"limite": 0}, {"limite": 201}, {"offset": -1}, {"tipo_id": "invalido"}, {"q": "x" * 121}],
)
def test_parametros_invalidos_del_listado(cliente, query):
    assert cliente.get("/api/componentes", params=query).status_code == 422


def test_listar_componentes_con_base_caida_devuelve_503(cliente, monkeypatch):
    def sin_base(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, "listar_componentes", sin_base)
    respuesta = cliente.get("/api/componentes")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"]["motivo"] == "base_no_disponible"


@pytest.fixture()
def ficha_nueva():
    return {
        "tipo_id": "enc",
        "nombre": "Encoder de prueba",
        "precio": 35,
        "masa_g": 2,
        "stock": 1,
        "especificaciones": {"cpr": 12, "tipo": "Magnético"},
    }


def test_crear_componente_persiste_ficha_e_inventario(
    cliente_catalogo, catalogo_inicial, conexion, ficha_nueva
):
    respuesta = cliente_catalogo.post("/api/componentes", json=ficha_nueva)
    assert respuesta.status_code == 201
    creado = respuesta.json()
    assert creado == {
        **ficha_nueva,
        "id": creado["id"],
        "tienda": "",
        "consumo_a": None,
        "archivado": False,
    }
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        assert session.get(Componente, creado["id"]).precio == Decimal("35")
        inventario = session.get(Inventario, creado["id"])
        assert (inventario.stock, inventario.revision) == (1, 1)
    pagina = cliente_catalogo.get("/api/componentes?q=Encoder de prueba").json()
    assert pagina["items"] == [creado]
    segunda = cliente_catalogo.post("/api/componentes", json=ficha_nueva)
    assert segunda.status_code == 201
    assert segunda.json()["id"] != creado["id"]


@pytest.mark.parametrize(
    "cambio",
    [
        {"precio": 0},
        {"precio": 1.001},
        {"masa_g": -1},
        {"stock": True},
        {"stock": 2147483648},
        {"nombre": "   "},
        {"tipo_id": "desconocido"},
        {"id": "manual"},
        {"especificaciones": {"cpr": True}},
        {"especificaciones": {"cpr": "doce"}},
        {"especificaciones": {"cpr": -1}},
        {"especificaciones": {"tipo": 12}},
        {"especificaciones": {"canales": 2}},
        {"especificaciones": {"tipo": "x" * 121}},
        {"tipo_id": "linea", "consumo_a": 0.1, "especificaciones": {"i": 0.2}},
    ],
)
def test_crear_componente_rechaza_datos_invalidos(
    cliente_catalogo, catalogo_inicial, conexion, ficha_nueva, cambio
):
    respuesta = cliente_catalogo.post("/api/componentes", json={**ficha_nueva, **cambio})
    assert respuesta.status_code == 422
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        assert service.contar_catalogo(session) == (25, 25)


def test_crear_componente_sin_tipos(cliente_catalogo, ficha_nueva):
    respuesta = cliente_catalogo.post("/api/componentes", json=ficha_nueva)
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"]["motivo"] == "tipo_no_disponible"


def test_crear_componente_revierte_ficha_si_falla_inventario(
    cliente_catalogo, catalogo_inicial, conexion, ficha_nueva, monkeypatch
):
    def inventario_fallido(**kwargs):
        raise IntegrityError("INSERT", {}, Exception("fallo de inventario"))

    monkeypatch.setattr(service, "Inventario", inventario_fallido)
    assert cliente_catalogo.post("/api/componentes", json=ficha_nueva).status_code == 409
    assert conexion.scalar(select(func.count()).select_from(Componente)) == 25
    assert conexion.scalar(select(func.count()).select_from(Inventario)) == 25


def test_crear_componente_con_base_caida(cliente, ficha_nueva, monkeypatch):
    def sin_base(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, "crear_componente", sin_base)
    assert cliente.post("/api/componentes", json=ficha_nueva).status_code == 503


def test_consultar_componente_por_id(cliente_catalogo, catalogo_inicial):
    respuesta = cliente_catalogo.get("/api/componentes/c05")
    assert respuesta.status_code == 200
    esperado = next(c for c in catalogo_inicial if c["id"] == "c05")
    assert respuesta.json() == {**esperado, "archivado": False}


def test_consultar_componente_archivado(cliente_catalogo, catalogo_inicial, conexion):
    conexion.execute(update(Componente).where(Componente.id == "c05").values(archivado=True))
    respuesta = cliente_catalogo.get("/api/componentes/c05")
    assert respuesta.status_code == 200
    assert respuesta.json()["archivado"] is True


def test_consultar_componente_inexistente(cliente_catalogo):
    respuesta = cliente_catalogo.get("/api/componentes/no-existe")
    assert respuesta.status_code == 404
    assert respuesta.json()["detail"]["motivo"] == "componente_no_encontrado"


def test_consultar_componente_id_demasiado_largo(cliente):
    assert cliente.get("/api/componentes/" + "x" * 41).status_code == 422


def test_consultar_componente_con_base_caida(cliente, monkeypatch):
    def sin_base(*args, **kwargs):
        raise OperationalError("SELECT", {}, Exception("sin conexión"))

    monkeypatch.setattr(service, "obtener_componente", sin_base)
    assert cliente.get("/api/componentes/c05").status_code == 503


def test_editar_precio_conserva_ficha_stock_y_revision(
    cliente_catalogo, catalogo_inicial, conexion
):
    anterior = cliente_catalogo.get("/api/componentes/c05").json()
    respuesta = cliente_catalogo.patch("/api/componentes/c05", json={"precio": 65.25})
    assert respuesta.status_code == 200
    assert respuesta.json() == {**anterior, "precio": 65.25}
    assert cliente_catalogo.get("/api/componentes/c05").json() == respuesta.json()
    with Session(bind=conexion, join_transaction_mode="create_savepoint") as session:
        assert session.get(Inventario, "c05").revision == 1


def test_editar_especificaciones_reemplaza_objeto(cliente_catalogo, catalogo_inicial):
    respuesta = cliente_catalogo.patch(
        "/api/componentes/c22", json={"especificaciones": {"cpr": 24}}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["especificaciones"] == {"cpr": 24}
    assert cliente_catalogo.get("/api/componentes/c22").json()["especificaciones"] == {"cpr": 24}


def test_editar_consumo_admite_null(cliente_catalogo, catalogo_inicial):
    assert (
        cliente_catalogo.patch("/api/componentes/c22", json={"consumo_a": 0.1}).status_code == 200
    )
    respuesta = cliente_catalogo.patch("/api/componentes/c22", json={"consumo_a": None})
    assert respuesta.status_code == 200
    assert respuesta.json()["consumo_a"] is None


@pytest.mark.parametrize(
    "cambio",
    [
        {},
        {"precio": 0},
        {"precio": None},
        {"masa_g": -1},
        {"nombre": "  "},
        {"tienda": None},
        {"especificaciones": None},
        {"stock": 3},
        {"tipo_id": "motor"},
        {"archivado": True},
        {"id": "otro"},
        {"especificaciones": {"canales": 8}},
        {"especificaciones": {"cpr": "doce"}},
    ],
)
def test_editar_rechazado_conserva_ficha(cliente_catalogo, catalogo_inicial, cambio):
    anterior = cliente_catalogo.get("/api/componentes/c22").json()
    assert cliente_catalogo.patch("/api/componentes/c22", json=cambio).status_code == 422
    assert cliente_catalogo.get("/api/componentes/c22").json() == anterior


def test_editar_valida_consumo_con_especificaciones_conservadas(cliente_catalogo, catalogo_inicial):
    anterior = cliente_catalogo.get("/api/componentes/c05").json()
    respuesta = cliente_catalogo.patch("/api/componentes/c05", json={"consumo_a": 1})
    assert respuesta.status_code == 422
    assert respuesta.json()["detail"]["motivo"] == "consumo_inconsistente"
    assert cliente_catalogo.get("/api/componentes/c05").json() == anterior


def test_editar_inexistente(cliente_catalogo):
    respuesta = cliente_catalogo.patch("/api/componentes/no-existe", json={"precio": 65})
    assert respuesta.status_code == 404


def test_editar_archivado(cliente_catalogo, catalogo_inicial, conexion):
    conexion.execute(update(Componente).where(Componente.id == "c22").values(archivado=True))
    anterior = cliente_catalogo.get("/api/componentes/c22").json()
    respuesta = cliente_catalogo.patch("/api/componentes/c22", json={"precio": 65})
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"]["motivo"] == "componente_archivado"
    assert cliente_catalogo.get("/api/componentes/c22").json() == anterior


def test_editar_revierte_si_falla_guardado(cliente_catalogo, catalogo_inicial, monkeypatch):
    anterior = cliente_catalogo.get("/api/componentes/c22").json()
    with monkeypatch.context() as parche:

        def falla_commit(session):
            raise OperationalError("COMMIT", {}, Exception("fallo al confirmar"))

        parche.setattr(Session, "commit", falla_commit)
        respuesta = cliente_catalogo.patch("/api/componentes/c22", json={"precio": 65})
        assert respuesta.status_code == 503
    assert cliente_catalogo.get("/api/componentes/c22").json() == anterior

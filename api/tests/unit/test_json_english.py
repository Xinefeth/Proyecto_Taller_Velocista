"""Current REST contract: English routes and the Spanish JSON consumed by the console."""

import pytest
from pydantic import ValidationError

from app.main import app
from app.modulos.armador.schemas import VersionCrear
from app.modulos.catalogo.schemas import ComponenteCrear, ComponenteEditar, TipoComponenteSalida
from app.modulos.reglamento.schemas import PerfilSalida
from app.semillas import leer_tipos_iniciales


def test_public_input_preserves_orm_and_specification_keys():
    model = ComponenteCrear.model_validate(
        {
            "tipo_id": "enc",
            "nombre": "Encoder",
            "precio": 35,
            "masa_g": 2,
            "stock": 1,
            "especificaciones": {"cpr": 12, "tipo": "Magnético"},
        }
    )
    assert model.nombre == "Encoder"
    assert model.especificaciones == {"cpr": 12, "tipo": "Magnético"}
    assert model.model_dump()["especificaciones"]["tipo"] == "Magnético"
    assert model.model_dump(by_alias=True)["especificaciones"] == {"cpr": 12, "tipo": "Magnético"}


def test_partial_patch_tracks_internal_fields_and_explicit_null():
    model = ComponenteEditar.model_validate({"precio": 40, "consumo_a": None})
    assert model.model_fields_set == {"precio", "consumo_a"}
    assert model.model_dump(exclude_unset=True) == {"precio": 40, "consumo_a": None}
    assert ComponenteEditar(precio=40).model_dump(by_alias=True, exclude_unset=True) == {
        "precio": 40
    }


def test_unsupported_aliases_are_rejected():
    # The active API has not adopted the experimental translation helper.
    with pytest.raises(ValidationError):
        ComponenteEditar.model_validate({"price": 40, "precio": 50})
    with pytest.raises(ValidationError):
        ComponenteEditar.model_validate({"specifications": {"type": "a"}})


def test_nested_pieces_keep_slot_identifiers():
    model = VersionCrear.model_validate(
        {
            "version_base_id": None,
            "nota": "",
            "estado": "Concepto",
            "piezas": {"linea": {"componente_id": "c05", "cantidad": 2}},
        }
    )
    assert model.model_dump()["piezas"]["linea"] == {"componente_id": "c05", "cantidad": 2}
    assert model.model_dump(by_alias=True)["piezas"] == {
        "linea": {"componente_id": "c05", "cantidad": 2}
    }


def test_catalogue_describes_public_specification_keys():
    types = {t["id"]: TipoComponenteSalida.model_validate(t) for t in leer_tipos_iniciales()}
    public = types["linea"].model_dump(by_alias=True)
    assert {f["clave"] for f in public["campos"]} == {"canales", "salida", "paso", "i"}
    assert public["capacidades"][0]["campo"] == "canales"
    assert types["linea"].model_dump()["capacidades"][0]["campo"] == "canales"


def test_rules_preserve_keys_labels_and_nulls():
    model = PerfilSalida(
        id="test",
        competencia="Competencia",
        etiqueta="C",
        categoria="Amateur",
        reglas={"sensMax": None, "motores": 2, "chasis": "MDF"},
    )
    assert model.model_dump(by_alias=True)["reglas"] == {
        "sensMax": None,
        "motores": 2,
        "chasis": "MDF",
    }


def test_swagger_uses_current_routes_and_fields():
    spec = app.openapi()
    component = spec["components"]["schemas"]["ComponenteCrear"]["properties"]
    assert {"nombre", "tipo_id", "precio", "masa_g", "especificaciones"} <= component.keys()
    assert "name" not in component
    for path in ("/api/components", "/api/runs", "/api/robots/v001/setups"):
        path = path.replace("v001", "{robot_id}")
        params = {p["name"] for p in spec["paths"][path]["get"]["parameters"]}
        assert "limit" in params and "limite" not in params
    assert "tipo" in spec["components"]["schemas"]["Command"]["properties"]


def test_documented_routes_operations_and_parameters_match_runtime():
    import json
    from pathlib import Path

    documented = json.loads(
        (Path(__file__).resolve().parents[3] / "docs/api/openapi.json").read_text(encoding="utf-8")
    )["paths"]
    runtime = app.openapi()["paths"]
    methods = {"get", "post", "put", "patch", "delete"}
    assert {(p, m) for p, ops in documented.items() for m in ops if m in methods} == {
        (p, m) for p, ops in runtime.items() for m in ops if m in methods
    }
    for path, ops in documented.items():
        for method, operation in ops.items():
            actual = runtime[path][method]
            assert operation["operationId"] == actual["operationId"], (path, method)
            assert {(p["name"], p["in"]) for p in operation.get("parameters", [])} == {
                (p["name"], p["in"]) for p in actual.get("parameters", [])
            }, (path, method)

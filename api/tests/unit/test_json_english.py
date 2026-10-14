"""Public English fields, legacy input compatibility and stable stored data."""

import pytest
from pydantic import ValidationError

from app.main import app
from app.modulos.armador.schemas import VersionCrear
from app.modulos.catalogo.schemas import ComponenteCrear, ComponenteEditar, TipoComponenteSalida
from app.modulos.reglamento.schemas import PerfilSalida
from app.semillas import leer_tipos_iniciales


def test_english_input_preserves_spanish_orm_and_specification_keys():
    model = ComponenteCrear.model_validate(
        {
            "type_id": "enc",
            "name": "Encoder",
            "price": 35,
            "mass_g": 2,
            "stock": 1,
            "specifications": {"cpr": 12, "type": "Magnético"},
        }
    )
    assert model.nombre == "Encoder"
    assert model.especificaciones == {"cpr": 12, "tipo": "Magnético"}
    assert model.model_dump()["especificaciones"]["tipo"] == "Magnético"
    assert model.model_dump(by_alias=True)["specifications"] == {"cpr": 12, "type": "Magnético"}


def test_partial_patch_tracks_internal_fields_and_explicit_null():
    model = ComponenteEditar.model_validate({"price": 40, "current_a": None})
    assert model.model_fields_set == {"precio", "consumo_a"}
    assert model.model_dump(exclude_unset=True) == {"precio": 40, "consumo_a": None}
    assert ComponenteEditar(precio=40).model_dump(by_alias=True, exclude_unset=True) == {
        "price": 40
    }


def test_ambiguous_input_is_rejected():
    with pytest.raises(ValidationError):
        ComponenteEditar.model_validate({"price": 40, "precio": 50})
    with pytest.raises(ValidationError):
        ComponenteEditar.model_validate({"specifications": {"type": "a", "tipo": "b"}})


def test_nested_pieces_keep_slot_identifiers():
    model = VersionCrear.model_validate(
        {
            "base_version_id": None,
            "note": "",
            "status": "Concepto",
            "parts": {"linea": {"component_id": "c05", "quantity": 2}},
        }
    )
    assert model.model_dump()["piezas"]["linea"] == {"componente_id": "c05", "cantidad": 2}
    assert model.model_dump(by_alias=True)["parts"] == {
        "linea": {"component_id": "c05", "quantity": 2}
    }


def test_catalogue_describes_public_specification_keys():
    types = {t["id"]: TipoComponenteSalida.model_validate(t) for t in leer_tipos_iniciales()}
    public = types["linea"].model_dump(by_alias=True)
    assert {f["key"] for f in public["fields"]} == {"channels", "output", "pitch", "i"}
    assert public["capabilities"][0]["field"] == "channels"
    assert types["linea"].model_dump()["capacidades"][0]["campo"] == "canales"


def test_rules_translate_keys_without_changing_labels_or_nulls():
    model = PerfilSalida(
        id="test",
        competencia="Competencia",
        etiqueta="C",
        categoria="Amateur",
        reglas={"sensMax": None, "motores": 2, "chasis": "MDF"},
    )
    assert model.model_dump(by_alias=True)["rules"] == {
        "max_sensors": None,
        "motors": 2,
        "chassis": "MDF",
    }


def test_swagger_uses_english_fields_and_queries_but_keeps_en02():
    spec = app.openapi()
    component = spec["components"]["schemas"]["ComponenteCrear"]["properties"]
    assert {"name", "type_id", "price", "mass_g", "specifications"} <= component.keys()
    assert "nombre" not in component
    for path in ("/api/componentes", "/api/corridas", "/api/robots/v001/setups"):
        path = path.replace("v001", "{robot_id}")
        params = {p["name"] for p in spec["paths"][path]["get"]["parameters"]}
        assert "limit" in params and "limite" not in params
    assert "tipo" in spec["components"]["schemas"]["Comando"]["properties"]

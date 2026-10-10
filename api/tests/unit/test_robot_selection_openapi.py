"""Documentación de selección de robots, sin PostgreSQL."""

from app.main import app


def test_manifest_example_matches_contract(ejemplo):
    operation = app.openapi()["paths"]["/api/devices/velocista/manifest"]["get"]
    example = operation["responses"]["200"]["content"]["application/json"]["example"]
    assert example == ejemplo("velocista.manifiesto.json")["datos"]


def test_builder_and_devices_document_service_unavailable():
    for path, operations in app.openapi()["paths"].items():
        for operation in operations.values():
            if set(operation.get("tags", [])) & {"builder", "devices"}:
                response = operation["responses"]["503"]
                assert "application/json" in response["content"], path
                assert "base_no_disponible" in str(response), path

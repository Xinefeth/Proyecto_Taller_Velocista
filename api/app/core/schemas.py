"""English REST field names; ORM attributes and persisted identifiers stay stable."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

JSON_FIELDS = json.loads(Path(__file__).with_name("json_fields.json").read_text(encoding="utf-8"))
DYNAMIC_FIELDS = json.loads(
    Path(__file__).with_name("json_dynamic_fields.json").read_text(encoding="utf-8")
)


def rename_keys(value, mapping):
    if not isinstance(value, dict):
        return value
    result = {}
    for key, item in value.items():
        translated = mapping.get(key, key)
        if translated in result:
            raise ValueError(f"Duplicate field: {translated}")
        result[translated] = item
    return result


def english_field(name: str) -> str:
    return JSON_FIELDS.get(name, name)


class APIModel(BaseModel):
    # Legacy names remain accepted for existing clients and internal service calls.
    # FastAPI publishes and serializes aliases; model_dump() used by services keeps ORM names.
    model_config = ConfigDict(alias_generator=english_field, populate_by_name=True)

    @field_validator("especificaciones", "reglas", mode="before", check_fields=False)
    @classmethod
    def read_dynamic_fields(cls, value, info):
        mapping = DYNAMIC_FIELDS[english_field(info.field_name)]
        return rename_keys(value, {v: k for k, v in mapping.items()})

    @field_serializer("especificaciones", "reglas", check_fields=False)
    def write_dynamic_fields(self, value, info):
        return (
            rename_keys(value, DYNAMIC_FIELDS[english_field(info.field_name)])
            if info.by_alias
            else value
        )


class HealthResponse(APIModel):
    api: str
    base_de_datos: str
    entorno: str
    dispositivos: dict[str, bool]

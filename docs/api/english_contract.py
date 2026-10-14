"""Project REST translation, independent of FastAPI and PostgreSQL."""

import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
FIELDS = json.loads((ROOT / "api/app/core/json_fields.json").read_text())
DYNAMIC = json.loads((ROOT / "api/app/core/json_dynamic_fields.json").read_text())


def payload(value, context=""):
    if isinstance(value, list):
        return [payload(v, "" if context == "parametros" else context) for v in value]
    if not isinstance(value, dict):
        return value
    if context in ("parametros", "presets", "dispositivos"):
        return value
    mapping = DYNAMIC.get(
        {"especificaciones": "specifications", "reglas": "rules"}.get(context), FIELDS
    )
    result = {}
    for key, val in value.items():
        new = key if context == "piezas" else mapping.get(key, key)
        if key == "clave" and "obligatorio" in value:
            val = DYNAMIC["specifications"].get(val, val)
        if (
            context != "especificaciones"
            and key in ("campo", "campos")
            and "agregacion" in value
        ):
            val = (
                [DYNAMIC["specifications"].get(v, v) for v in val]
                if isinstance(val, list)
                else DYNAMIC["specifications"].get(val, val)
            )
        result[new] = payload(val, key)
    return result


def schema(value, context=""):
    if isinstance(value, list):
        return [schema(v, context) for v in value]
    if not isinstance(value, dict):
        return value
    mapping = DYNAMIC.get(context, FIELDS)
    result = {}
    for key, val in value.items():
        if key == "properties":
            result[key] = {
                mapping.get(k, k): schema(v, "rules" if k == "reglas" else context)
                for k, v in val.items()
            }
        elif key == "required":
            result[key] = [mapping.get(k, k) for k in val]
        else:
            result[key] = schema(val, context)
    return result


def translate(spec):
    spec = deepcopy(spec)
    for name, value in spec["components"]["schemas"].items():
        if name.startswith("EN02_") or name in (
            "Manifiesto",
            "Comando",
            "ComandoEnviado",
        ):
            continue
        spec["components"]["schemas"][name] = schema(
            value, "specifications" if name.startswith("Specs_") else ""
        )
    for path, ops in spec["paths"].items():
        for op in ops.values():
            device = path.startswith("/api/dispositivos")
            request = op["x-ejemplo-peticion"]
            if not device and "cuerpo" in request:
                request["cuerpo"] = payload(request["cuerpo"])
            for p in op.get("parameters", []):
                if p["in"] == "query":
                    p["name"] = FIELDS.get(p["name"], p["name"])
            url = urlsplit(request["url"])
            request["url"] = urlunsplit(
                url._replace(
                    query=urlencode(
                        [(FIELDS.get(k, k), v) for k, v in parse_qsl(url.query)]
                    )
                )
            )
            if not device and "requestBody" in op:
                media = op["requestBody"]["content"]["application/json"]
                media["example"] = payload(media["example"])
            for status, response in op["responses"].items():
                if device and status.startswith("2"):
                    continue
                for media in response.get("content", {}).values():
                    if "example" in media:
                        media["example"] = payload(media["example"])
                    for example in media.get("examples", {}).values():
                        example["value"] = payload(example["value"])
    return spec


def http_examples(spec):
    lines = ["@base = http://127.0.0.1:8000", ""]
    for ops in spec["paths"].values():
        for op in ops.values():
            req = op["x-ejemplo-peticion"]
            lines += [
                f"### {op['operationId']}",
                f"{req['metodo']} {{{{base}}}}{req['url']}",
            ]
            if "cuerpo" in req:
                lines += [
                    "Content-Type: application/json",
                    "",
                    json.dumps(req["cuerpo"], ensure_ascii=False, indent=2),
                ]
            for code, response in op["responses"].items():
                if not code.startswith("2"):
                    continue
                lines += ["", f"# Respuesta: {code}"]
                media = response.get("content", {}).get("application/json", {})
                if "example" in media:
                    lines += [
                        "# " + s
                        for s in json.dumps(
                            media["example"], ensure_ascii=False, indent=2
                        ).splitlines()
                    ]
            lines.append("")
    return "\n".join(lines) + "\n"

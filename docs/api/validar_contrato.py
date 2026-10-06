"""Verifica EN-01 y su cobertura de DO-03 sin arrancar servicios."""

import ast
import json
import re
from copy import deepcopy

from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate

from generar_contrato import DESTINO, RAIZ, generar


def exigir(condicion, mensaje):
    if not condicion:
        raise AssertionError(mensaje)


def ejecutar():
    spec = json.loads((DESTINO / "openapi.json").read_text(encoding="utf-8"))
    validate(spec)
    for ruta, esperado in generar().items():
        exigir(ruta.read_text(encoding="utf-8") == esperado, f"Regenerar {ruta}")

    def validador(schema):
        raiz = {**schema, "components": spec["components"]}
        return Draft202012Validator(raiz, format_checker=FormatChecker())

    def comprobar(schema, ejemplo):
        validador(schema).validate(ejemplo)

    def comprobar_refs(valor):
        if isinstance(valor, dict):
            if "$ref" in valor:
                exigir(valor["$ref"].startswith("#/"), "Se requiere contrato portable con refs internas")
                destino = spec
                for parte in valor["$ref"][2:].split("/"):
                    destino = destino[parte.replace("~1", "/").replace("~0", "~")]
            for v in valor.values():
                comprobar_refs(v)
        elif isinstance(valor, list):
            for v in valor:
                comprobar_refs(v)

    comprobar_refs(spec)
    ids = set()
    implementadas = set()
    cantidad = 0
    ejemplos = 0
    for ruta, metodos in spec["paths"].items():
        for metodo, op in metodos.items():
            cantidad += 1
            oid = op["operationId"]
            exigir(oid not in ids, f"operationId duplicado: {oid}")
            ids.add(oid)
            exigir(op["x-estado"] in ["propuesto", "implementado"], oid)
            if op["x-estado"] == "implementado":
                implementadas.add((metodo, ruta))
            peticion = op["x-ejemplo-peticion"]
            exigir(peticion["metodo"] == metodo.upper(), oid)
            exigir("{" not in peticion["url"], f"URL sin concretar: {oid}")
            params = op.get("parameters", [])
            exigir(set(re.findall(r"{(.*?)}", ruta)) == {p["name"] for p in params if p["in"] == "path"}, f"Parámetros de ruta: {oid}")
            for p in params:
                comprobar(p["schema"], p["example"])
                ejemplos += 1
            if "requestBody" in op:
                media = op["requestBody"]["content"]["application/json"]
                comprobar(media["schema"], media["example"])
                exigir(media["example"] == peticion["cuerpo"], f"Petición divergente: {oid}")
                ejemplos += 1
            else:
                exigir("cuerpo" not in peticion, f"Cuerpo no declarado: {oid}")
            exigir(any(s.startswith("2") for s in op["responses"]), oid)
            for status, respuesta in op["responses"].items():
                if status == "204":
                    exigir("content" not in respuesta, "204 no debe tener cuerpo")
                    continue
                for media in respuesta["content"].values():
                    casos = [media["example"]] if "example" in media else [e["value"] for e in media["examples"].values()]
                    exigir(bool(casos), f"Sin ejemplo: {oid}/{status}")
                    for caso in casos:
                        comprobar(media["schema"], caso)
                        ejemplos += 1

    # Compara las declaraciones reales por AST sin importar FastAPI ni acceder a BD.
    existentes = set()
    for ruta in [RAIZ / "api/app/main.py", RAIZ / "api/app/gateway/comandos.py", *sorted((RAIZ / "api/app/modulos").glob("*/router.py"))]:
        arbol = ast.parse(ruta.read_text(encoding="utf-8"))
        prefijo = ""
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name) and nodo.func.id == "APIRouter":
                prefijo = next((k.value.value for k in nodo.keywords if k.arg == "prefix"), "")
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for d in nodo.decorator_list:
                if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr in ["get", "post", "patch", "put", "delete"]:
                    existentes.add((d.func.attr, prefijo + d.args[0].value))
    exigir(implementadas == existentes, "Actualizar x-estado: las rutas existentes cambiaron")

    # Asegura cobertura del catálogo real: todos los tipos, todas sus specs y tipos n/t.
    ts = (RAIZ / "consola/src/datos/tipos.ts").read_text(encoding="utf-8")
    bloques = re.split(r"^  (\w+): \{", ts, flags=re.M)
    tipos_ts = {}
    for i in range(1, len(bloques), 2):
        campos = re.findall(r'\["(\w+)",\s*"[^"]+",\s*"([nt])"\]', bloques[i + 1])
        tipos_ts[bloques[i]] = dict(campos)
    tipos = json.loads((RAIZ / "docs/datos/tipos-componentes.json").read_text(encoding="utf-8"))
    exigir({t["id"] for t in tipos} == set(tipos_ts), "Tipos del prototipo no cubiertos")
    for tipo in tipos:
        exigir({c["clave"]: c["tipo"] for c in tipo["campos"]} == tipos_ts[tipo["id"]], f"Specs faltantes: {tipo['id']}")
        comprobar({"$ref": "#/components/schemas/TipoComponente"}, tipo)
        campos = {c["clave"] for c in tipo["campos"]}
        for cap in tipo["capacidades"]:
            exigir(set(cap.get("campos", [])) <= campos, f"Fórmula sin campos: {tipo['id']}")
            if "campo" in cap:
                exigir(cap["campo"] in campos, f"Capacidad sin campo: {tipo['id']}")
    capacidades = {t["id"]: {c["clave"] for c in t["capacidades"]} for t in tipos}
    for tipo, capacidad in [("linea", "canales_linea"), ("enc", "pulsos_por_vuelta"), ("imu", "ejes"), ("turb", "potencia_electrica_max_w")]:
        exigir(capacidad in capacidades[tipo], f"Falta capacidad requerida: {tipo}")

    # Casos negativos útiles: stock negativo/fraccionario, campos de otro tipo,
    # tipo desconocido, cantidad cero, modificación de J y PATCH vacío.
    crear = spec["paths"]["/api/componentes"]["post"]["requestBody"]["content"]["application/json"]["example"]
    casos = []
    for cambio in [{"stock": -1}, {"stock": 1.5}, {"tipo_id": "desconocido"}, {"especificaciones": {"cpr": 12}}, {"especificaciones": {"canales": "ocho"}}]:
        casos.append(("ComponenteCrear", {**deepcopy(crear), **cambio}))
    casos += [("Pieza", {"componente_id": "c05", "cantidad": 0}), ("NotaCorrida", {"nota": "x", "j": 0}), ("ComponenteEditar", {}), ("InventarioActualizar", {"stock": 2})]
    for nombre, caso in casos:
        exigir(not validador({"$ref": f"#/components/schemas/{nombre}"}).is_valid(caso), f"Acepta entrada inválida: {nombre}/{caso}")
    print(f"OK: {cantidad} operaciones ({len(implementadas)} existentes), {ejemplos} ejemplos, {len(tipos)} tipos, {len(casos)} casos negativos; archivos sincronizados.")


if __name__ == "__main__":
    ejecutar()

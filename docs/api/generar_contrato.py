"""Fuente de EN-01. Genera OpenAPI y ejemplos HTTP sin importar ni arrancar la API.

Ejecutar desde cualquier carpeta: python docs/api/generar_contrato.py
"""

import json
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlencode

RAIZ = Path(__file__).resolve().parents[2]
DESTINO = Path(__file__).resolve().parent


def ref(nombre):
    return {"$ref": f"#/components/schemas/{nombre}"}


def texto(maximo=120, **kw):
    return {"type": "string", "maxLength": maximo, **kw}


def numero(minimo=0, **kw):
    return {"type": "number", "minimum": minimo, **kw}


def entero(minimo=0, **kw):
    return {"type": "integer", "minimum": minimo, "maximum": 9007199254740991, **kw}


def lista(item, **kw):
    return {"type": "array", "items": item, **kw}


def objeto(props, requeridos=None, **kw):
    return {
        "type": "object", "properties": props, "additionalProperties": False,
        "required": list(props) if requeridos is None else requeridos, **kw,
    }


def nullable(esquema):
    return {"anyOf": [esquema, {"type": "null"}]}


def enum(*valores):
    return {"type": "string", "enum": list(valores)}


ID = texto(40, minLength=1, pattern="^[a-zA-Z0-9_-]+$")
FECHA = {"type": "string", "format": "date-time"}
BOOL = {"type": "boolean"}
PARAMETROS = {"type": "object", "minProperties": 1, "additionalProperties": {"type": "number"}}
P = {"kp": 0.6, "ki": 0, "kd": 2.5, "base": 45, "max": 86}
FECHA_EJEMPLO = "2026-10-06T15:00:00Z"

# Clave, nombre, campos del prototipo (clave, etiqueta, tipo, unidad).
# Las capacidades son datos declarativos; no se serializan funciones de TypeScript.
TIPOS = [
    ("mcu", "Microcontrolador", "#FF5A78", [("mhz", "Frecuencia", "n", "MHz"), ("radio", "Radio", "t", ""), ("logica", "Lógica", "n", "V"), ("adc", "Entradas analógicas usables", "n", "")]),
    ("exp", "Placa de expansión", "#A2A7B8", [("bornes", "Bornes", "n", ""), ("comercial", "PCB comercial", "t", "")]),
    ("linea", "Sensor de línea", "#3DDC97", [("canales", "Canales", "n", ""), ("salida", "Salida", "t", ""), ("paso", "Paso", "n", "mm"), ("i", "Consumo", "n", "A")]),
    ("mux", "Multiplexor", "#6CB6FF", [("canales", "Canales", "n", ""), ("tipo", "Tipo", "t", "")]),
    ("motor", "Motor", "#B48CFF", [("v", "Voltaje nominal", "n", "V"), ("rpm", "RPM sin carga", "n", "rpm"), ("inom", "Corriente nominal", "n", "A"), ("ipico", "Corriente de arranque", "n", "A"), ("red", "Reducción", "t", ""), ("familia", "Familia", "t", "")]),
    ("driver", "Driver", "#FFCB57", [("canales", "Canales", "n", ""), ("icont", "Corriente continua", "n", "A"), ("ipico", "Corriente pico", "n", "A"), ("vmin", "Voltaje mínimo", "n", "V"), ("vmax", "Voltaje máximo", "n", "V")]),
    ("bat", "Batería", "#3DDC97", [("celdas", "Celdas", "n", "S"), ("mah", "Capacidad", "n", "mAh"), ("c", "Descarga", "n", "C"), ("vmax", "Voltaje a carga completa", "n", "V")]),
    ("reg", "Regulador", "#A2A7B8", [("vout", "Salida", "n", "V"), ("imax", "Corriente máxima", "n", "A"), ("tipo", "Tipo", "t", "")]),
    ("rueda", "Rueda", "#A2A7B8", [("diam", "Diámetro", "n", "mm"), ("material", "Material", "t", "")]),
    ("chasis", "Chasis", "#A2A7B8", [("ancho", "Ancho", "n", "mm"), ("largo", "Largo", "n", "mm"), ("material", "Material", "t", "")]),
    ("sw", "Interruptor", "#5E6374", [("tipo", "Tipo", "t", "")]),
    ("enc", "Encoder", "#6CB6FF", [("cpr", "Pulsos por vuelta (CPR)", "n", "pulsos/vuelta"), ("tipo", "Tipo", "t", "")]),
    ("imu", "IMU", "#6CB6FF", [("ejes", "Ejes", "n", ""), ("bus", "Bus", "t", "")]),
    ("turb", "Turbina", "#FF2D55", [("diam", "Diámetro", "n", "mm"), ("v", "Voltaje", "n", "V"), ("imax", "Corriente", "n", "A")]),
]
CAPACIDADES = {
    "linea": [{"clave": "canales_linea", "campo": "canales", "unidad": "canales", "agregacion": "suma_por_cantidad"}],
    "enc": [{"clave": "pulsos_por_vuelta", "campo": "cpr", "unidad": "pulsos/vuelta", "agregacion": "por_componente"}],
    "imu": [{"clave": "ejes", "campo": "ejes", "unidad": "ejes", "agregacion": "por_componente"}],
    "turb": [
        {"clave": "potencia_electrica_max_w", "campos": ["v", "imax"], "operacion": "producto", "unidad": "W", "agregacion": "suma_por_cantidad"},
        {"clave": "potencia_control_pct", "min": 0, "max": 100, "unidad": "%", "agregacion": "por_componente"},
    ],
    "motor": [{"clave": "pwm_pct", "min": -100, "max": 100, "unidad": "%", "agregacion": "por_componente"}],
    "mcu": [{"clave": "radio", "campo": "radio", "unidad": "", "agregacion": "por_componente"}],
    "bat": [{"clave": "bateria_v", "campo": "vmax", "unidad": "V", "agregacion": "por_componente"}],
}

SCHEMAS = {}
SCHEMAS["ErrorNegocio"] = objeto({"detail": objeto({"motivo": texto(), "detalle": texto(500)})})
SCHEMAS["ErrorValidacion"] = objeto({"detail": lista(objeto({
    "loc": lista({"anyOf": [texto(), {"type": "integer"}]}), "msg": texto(500),
    "type": texto(), "input": {}, "ctx": {"type": "object"},
}, ["loc", "msg", "type"]))})
SCHEMAS["Capacidad"] = objeto({
    "clave": ID, "campo": ID, "campos": lista(ID, minItems=2), "operacion": enum("producto"),
    "min": {"type": "number"}, "max": {"type": "number"}, "unidad": texto(20),
    "agregacion": enum("suma_por_cantidad", "por_componente"),
}, ["clave", "unidad", "agregacion"])
SCHEMAS["CampoTipo"] = objeto({"clave": ID, "etiqueta": texto(), "tipo": enum("n", "t"), "unidad": texto(20), "obligatorio": BOOL})
SCHEMAS["TipoComponente"] = objeto({"id": ID, "nombre": texto(), "color": texto(7, pattern="^#[0-9A-Fa-f]{6}$"), "campos": lista(ref("CampoTipo")), "capacidades": lista(ref("Capacidad"))})

tipo_ejemplos = []
for clave, nombre, color, campos in TIPOS:
    SCHEMAS[f"Specs_{clave}"] = objeto({k: numero() if t == "n" else texto() for k, _, t, _ in campos}, [])
    tipo_ejemplos.append({"id": clave, "nombre": nombre, "color": color, "campos": [
        {"clave": k, "etiqueta": e, "tipo": t, "unidad": u, "obligatorio": False} for k, e, t, u in campos
    ], "capacidades": CAPACIDADES.get(clave, [])})

comp_props = {"tipo_id": enum(*(x[0] for x in TIPOS)), "nombre": texto(minLength=1),
    "precio": numero(exclusiveMinimum=0), "masa_g": numero(), "tienda": texto(200),
    "consumo_a": nullable(numero()), "especificaciones": {"type": "object"}}
variantes = [objeto({**comp_props, "tipo_id": {"const": k, "type": "string"}, "especificaciones": ref(f"Specs_{k}"), "stock": entero()}, ["tipo_id", "nombre", "precio", "masa_g", "stock", "especificaciones"]) for k, *_ in TIPOS]
SCHEMAS["ComponenteCrear"] = {"oneOf": variantes}
SCHEMAS["Componente"] = {"oneOf": [objeto({**v["properties"], "id": ID, "archivado": BOOL}) for v in variantes]}
SCHEMAS["ComponenteEditar"] = objeto({k: v for k, v in comp_props.items() if k != "tipo_id"}, [], minProperties=1,
    description="PATCH parcial. especificaciones reemplaza el objeto completo y se valida contra el tipo existente; tipo_id y stock no se editan aquí.")
SCHEMAS["ComponenteEditar"]["properties"]["especificaciones"] = {"anyOf": [ref(f"Specs_{k}") for k, *_ in TIPOS]}
SCHEMAS["Inventario"] = objeto({"componente_id": ID, "stock": entero(), "en_robots": entero(), "disponible": {"type": "integer"}, "faltante": entero(), "revision": entero(1)})
SCHEMAS["InventarioActualizar"] = objeto({"stock": entero(), "revision": entero(1)}, description="Comparación de revisión y actualización atómicas; revisión obsoleta devuelve 409. Stock es total del club, no disponible.")
SCHEMAS["Ranura"] = objeto({"id": ID, "tipo_id": ID, "nombre": texto(), "obligatoria": BOOL, "cantidad_editable": BOOL, "depende_reglamento": BOOL})
SCHEMAS["Pieza"] = objeto({"componente_id": ID, "cantidad": entero(1)})
PIEZAS = {"type": "object", "additionalProperties": ref("Pieza"), "propertyNames": enum(*(x[0] for x in TIPOS))}
SCHEMAS["ComponenteHistorico"] = objeto({"id": ID, **comp_props}, allOf=[
    {"if": {"properties": {"tipo_id": {"const": k}}}, "then": {"properties": {"especificaciones": ref(f"Specs_{k}")}}}
    for k, *_ in TIPOS
])
SCHEMAS["PiezaHistorica"] = objeto({"componente_id": ID, "cantidad": entero(1), "componente_snapshot": ref("ComponenteHistorico")})
PIEZAS_HISTORICAS = {**PIEZAS, "additionalProperties": ref("PiezaHistorica")}
robot_props = {"nombre": texto(minLength=1), "codigo_corto": texto(12, minLength=1), "tipo": enum("velocista", "minisumo"), "firmware": nullable(texto(20))}
SCHEMAS["RobotCrear"] = objeto(robot_props, ["nombre", "codigo_corto", "tipo"])
SCHEMAS["RobotEditar"] = objeto({k: v for k, v in robot_props.items() if k != "tipo"}, [], minProperties=1)
SCHEMAS["Robot"] = objeto({"id": ID, **robot_props, "version_actual_id": nullable(entero(1)), "archivado": BOOL})
SCHEMAS["VersionCrear"] = objeto({"version_base_id": nullable(entero(1)), "nota": texto(1000), "estado": enum("Actual", "Concepto", "Borrador"), "piezas": PIEZAS},
    description="Crea una versión completa e inmutable. version_base_id debe ser la última versión (null solo para la primera); evita sobrescribir trabajo concurrente.")
SCHEMAS["Version"] = objeto({"id": entero(1), "robot_id": ID, "etiqueta": texto(20, pattern="^v[0-9]+$"), "fecha": FECHA, "nota": texto(1000), "estado": enum("Actual", "Anterior", "Concepto", "Borrador", "Descartada"), "piezas": PIEZAS_HISTORICAS})
SCHEMAS["ParametroControlador"] = objeto({"clave": ID, "nombre": texto(), "descripcion": texto(300), "min": {"type": "number"}, "max": {"type": "number"}, "paso": numero(exclusiveMinimum=0), "decimales": entero(0, maximum=6), "optimizable": BOOL})
SCHEMAS["Controlador"] = objeto({"id": ID, "nombre": texto(), "nombre_corto": texto(30), "descripcion": texto(500), "parametros": lista(ref("ParametroControlador"), minItems=1), "presets": {"type": "object", "additionalProperties": PARAMETROS}})
SCHEMAS["SetupCrear"] = objeto({"version_id": entero(1), "nombre": texto(minLength=1), "controlador_id": ID, "parametros": PARAMETROS},
    description="El controlador debe existir; claves y rangos se validan con su definición. max >= base; vmin <= base cuando aplica. Guardar crea una revisión inmutable en PostgreSQL.")
SCHEMAS["Setup"] = objeto({"id": entero(1), "robot_id": ID, **SCHEMAS["SetupCrear"]["properties"], "creado_en": FECHA, "archivado": BOOL})
reglas = {k: nullable(entero()) for k in ["sensMax", "motores", "ruedas", "drivers"]}
reglas.update({k: nullable(lista(texto())) for k in ["motorFam", "mcu", "chasisMat"]})
reglas.update({k: BOOL for k in ["turbina", "pcbComercial", "inal", "enc", "imu", "mapaVel", "mr4"]})
reglas.update({k: texto(300) for k in ["montaje", "chasis", "arranque"]})
reglas["dim"] = nullable(lista(numero(), minItems=2, maxItems=2))
SCHEMAS["PerfilReglamento"] = objeto({"id": ID, "competencia": texto(), "etiqueta": texto(20), "categoria": texto(), "reglas": objeto(reglas, [k for k in reglas if k != "chasisMat"])})
SCHEMAS["Segmento"] = objeto({"tipo": texto(30), "duracion_s": numero(), "angulo_grados": {"type": "number"}, "error_acumulado": numero()})
SCHEMAS["Vuelta"] = objeto({"id": entero(1), "corrida_id": entero(1), "numero": entero(1), "tiempo_s": nullable(numero()), "duracion_s": numero(), "tiempo_interno_ms": nullable(entero()), "error_acumulado": numero(), "lineas_perdidas": entero(), "bateria_v": numero(), "termino": BOOL, "fuente_tiempo": enum("meta", "telemetria"), "motivo": texto(500), "sectores_s": lista(numero()), "segmentos": lista(ref("Segmento"))})
SCHEMAS["Corrida"] = objeto({"id": entero(1), "numero": entero(1), "robot_id": ID, "version_id": entero(1), "setup_id": entero(1), "perfil_id": ID, "controlador_id": ID, "parametros": PARAMETROS, "fecha": FECHA, "fuente": enum("sim", "robot"), "modo": enum("prueba", "competencia"), "linea": enum("negra", "blanca"), "compensa_bateria": BOOL, "potencia_turbina_pct": numero(0, maximum=100), "tiempo_s": nullable(numero()), "termino": BOOL, "error_acumulado": numero(), "bateria_v": numero(), "sectores_s": lista(numero()), "fuente_tiempo": enum("meta", "telemetria"), "nota": texto(1000), "j": numero()})
SCHEMAS["NotaCorrida"] = objeto({"nota": texto(1000)})
SCHEMAS["EventoCrear"] = objeto({"sistema": texto(40), "nivel": enum("info", "aviso", "error"), "mensaje": texto(500)}, ["sistema", "mensaje"])
SCHEMAS["Evento"] = objeto({**SCHEMAS["EventoCrear"]["properties"], "id": entero(1), "fecha": FECHA})
SCHEMAS["Salud"] = objeto({"api": enum("ok"), "base_de_datos": enum("ok", "sin conexión"), "entorno": texto(), "dispositivos": objeto({"velocista": BOOL, "cronometro": BOOL})})
SCHEMAS["Comando"] = objeto({"tipo": texto(), "datos": {"type": "object"}}, ["tipo"], description="Comandos y datos se rigen por EN-02. La validación dinámica depende del dispositivo y su manifiesto.")
SCHEMAS["ComandoEnviado"] = objeto({"seq": entero(), "mensaje": texto(200)})

# Reutiliza el esquema EN-02, trasladando referencias internas al documento OpenAPI.
manifiesto = json.loads((RAIZ / "docs/contrato/schemas/velocista.manifiesto.schema.json").read_text(encoding="utf-8"))
def trasladar(valor):
    if isinstance(valor, dict):
        return {k: (v.replace("#/$defs/", "#/components/schemas/EN02_") if k == "$ref" else trasladar(v)) for k, v in valor.items()}
    if isinstance(valor, list):
        return [trasladar(v) for v in valor]
    return valor

for nombre, esquema in manifiesto.pop("$defs").items():
    SCHEMAS[f"EN02_{nombre}"] = trasladar(esquema)
SCHEMAS["Manifiesto"] = trasladar(manifiesto)

COMP = {"id": "c05", "tipo_id": "linea", "nombre": "Pololu QTR-8A", "precio": 62, "masa_g": 3, "tienda": "Importación", "stock": 3, "consumo_a": 0.1, "especificaciones": {"canales": 8, "salida": "Analógica", "paso": 9.525, "i": 0.1}, "archivado": False}
ROBOT = {"id": "v001", "nombre": "Velocista 001", "codigo_corto": "001", "tipo": "velocista", "firmware": "0.3.1", "version_actual_id": 1, "archivado": False}
parts = {"mcu": ("c01", 1), "exp": ("c04", 1), "linea": ("c05", 2), "mux": ("c08", 1), "motor": ("c09", 2), "driver": ("c12", 1), "bat": ("c14", 1), "reg": ("c16", 1), "rueda": ("c18", 1), "chasis": ("c19", 1), "sw": ("c21", 1)}
VERSION = {"id": 1, "robot_id": "v001", "etiqueta": "v0", "fecha": FECHA_EJEMPLO, "nota": "Primer armado", "estado": "Actual", "piezas": {k: {"componente_id": c, "cantidad": n} for k, (c, n) in parts.items()}}
SNAPSHOTS = [
    ("c01", "mcu", "ESP32-S3 DevKitC-1 N16R8", 48, 9, 0.24, {"mhz": 240, "radio": "WiFi + BLE", "logica": 3.3, "adc": 10}),
    ("c04", "exp", "Placa de expansión ESP32-S3", 22, 14, None, {"bornes": 44, "comercial": "Sí"}),
    ("c05", "linea", "Pololu QTR-8A", 62, 3, 0.1, COMP["especificaciones"]),
    ("c08", "mux", "CD74HC4067 · 16 canales", 12, 2, None, {"canales": 16, "tipo": "Analógico"}),
    ("c09", "motor", "Micromotor N20 10:1 · 6 V", 38, 10, 0.35, {"v": 6, "rpm": 3000, "inom": 0.35, "ipico": 1.6, "red": "10:1", "familia": "N20"}),
    ("c12", "driver", "TB6612FNG", 16, 2, None, {"canales": 2, "icont": 1.2, "ipico": 3.2, "vmin": 2.5, "vmax": 13.5}),
    ("c14", "bat", "LiPo 2S 450 mAh 30C", 55, 26, None, {"celdas": 2, "mah": 450, "c": 30, "vmax": 8.4}),
    ("c16", "reg", "Mini buck MP1584 · 5 V", 7, 2, None, {"vout": 5, "imax": 3, "tipo": "Conmutado"}),
    ("c18", "rueda", "Ruedas de silicona 22 mm (par)", 24, 6, None, {"diam": 22, "material": "Silicona"}),
    ("c19", "chasis", "Chasis PETG impreso 3D", 20, 22, None, {"ancho": 180, "largo": 215, "material": "PETG impreso 3D"}),
    ("c21", "sw", "Interruptor deslizante mini", 1.5, 1, None, {"tipo": "Deslizante"}),
]
for cid, tipo, nombre, precio, masa, consumo, specs in SNAPSHOTS:
    VERSION["piezas"][tipo]["componente_snapshot"] = {"id": cid, "tipo_id": tipo, "nombre": nombre, "precio": precio, "masa_g": masa, "tienda": "Importación" if cid == "c05" else "Proveedor de ejemplo", "consumo_a": consumo, "especificaciones": specs}
SETUP = {"id": 1, "robot_id": "v001", "version_id": 1, "nombre": "PID base", "controlador_id": "pid", "parametros": P, "creado_en": FECHA_EJEMPLO, "archivado": False}
INV = {"componente_id": "c05", "stock": 3, "en_robots": 2, "disponible": 1, "faltante": 0, "revision": 1}
CTRL = {"id": "pid", "nombre": "PID", "nombre_corto": "PID", "descripcion": "Con Ki = 0 funciona como PD.", "parametros": [
    {"clave": k, "nombre": k.upper() if k in ["kp", "ki", "kd"] else k, "descripcion": k, "min": mn, "max": mx, "paso": paso, "decimales": dec, "optimizable": k in ["kp", "kd"]}
    for k, mn, mx, paso, dec in [("kp", 0, 2, 0.01, 2), ("ki", 0, 0.3, 0.005, 3), ("kd", 0, 10, 0.1, 1), ("base", 10, 100, 1, 0), ("max", 20, 100, 1, 0)]
], "presets": {"Base": P}}
PERFIL = {"id": "mr4s", "competencia": "Muchik Rumble 4", "etiqueta": "MR4", "categoria": "Senior", "reglas": {"dim": [200, 250], "sensMax": None, "motores": 2, "motorFam": None, "ruedas": 2, "drivers": None, "mcu": None, "turbina": False, "pcbComercial": True, "montaje": "Libre", "chasis": "Libre", "arranque": "Inalámbrico", "inal": True, "enc": False, "imu": False, "mapaVel": False, "mr4": True}}
VUELTA = {"id": 1, "corrida_id": 1, "numero": 1, "tiempo_s": 10.2, "duracion_s": 10.2, "tiempo_interno_ms": 10203, "error_acumulado": 0.8, "lineas_perdidas": 0, "bateria_v": 7.8, "termino": True, "fuente_tiempo": "meta", "motivo": "", "sectores_s": [3.4, 3.2, 3.6], "segmentos": [{"tipo": "recta", "duracion_s": 1.5, "angulo_grados": 0, "error_acumulado": 0.1}]}
CORRIDA = {"id": 1, "numero": 1, "robot_id": "v001", "version_id": 1, "setup_id": 1, "perfil_id": "mr4s", "controlador_id": "pid", "parametros": P, "fecha": FECHA_EJEMPLO, "fuente": "robot", "modo": "prueba", "linea": "negra", "compensa_bateria": True, "potencia_turbina_pct": 0, "tiempo_s": 10.2, "termino": True, "error_acumulado": 0.8, "bateria_v": 7.8, "sectores_s": [3.4, 3.2, 3.6], "fuente_tiempo": "meta", "nota": "Batería cargada", "j": 11.8}
EVENTO = {"id": 1, "fecha": FECHA_EJEMPLO, "sistema": "Armador", "nivel": "info", "mensaje": "Versión v0 registrada"}

SPEC = {"openapi": "3.1.0", "info": {"title": "APAEC Lab · Contrato REST EN-01", "version": "1.0.0", "description": "Contrato de diseño para revisión (DO-03 / EN-01). x-estado distingue rutas existentes de propuestas. No reemplaza /openapi.json de la API ejecutable. Guardar un setup en BD no confirma su aplicación ni persistencia en el firmware."}, "servers": [{"url": "http://localhost:8000", "description": "Desarrollo"}, {"url": "http://192.168.50.10:8000", "description": "Red de pista"}], "paths": {}, "components": {"schemas": SCHEMAS}, "security": []}
HTTP = ["# EN-01 · Ejemplos independientes, con datos de muestra precargados.", "# Rutas propuestas: consultar x-estado en openapi.json antes de ejecutar.", "@base = http://localhost:8000", ""]


def parametro(nombre, esquema, ejemplo, ubicacion="query", requerido=False):
    return {"name": nombre, "in": ubicacion, "required": requerido or ubicacion == "path", "schema": esquema, "example": ejemplo}


def pagina(nombre):
    clave = f"Pagina{nombre}"
    SCHEMAS[clave] = objeto({"items": lista(ref(nombre)), "total": entero(), "limite": entero(1, maximum=200), "offset": entero()})
    return clave


def paginado(item):
    return {"items": [item], "total": 1, "limite": 50, "offset": 0}


PAGINACION = [parametro("limite", entero(1, maximum=200, default=50), 50), parametro("offset", entero(default=0), 0)]


def operacion(metodo, ruta, id_op, resumen, salida=None, ejemplo=None, entrada=None, cuerpo=None,
              parametros=None, codigo="200", estado="propuesto", descripcion="", errores=("422", "503", "500")):
    parametros = deepcopy(parametros or [])
    import re
    for nombre in re.findall(r"{(.*?)}", ruta):
        tipo = ID if nombre in ["robot_id", "componente_id"] else entero(1)
        valor = {"robot_id": "v001", "componente_id": "c05", "dispositivo": "velocista"}.get(nombre, 1)
        if nombre == "dispositivo":
            tipo = enum("velocista", "cronometro")
        parametros.insert(0, parametro(nombre, tipo, valor, "path"))
    url = ruta
    for p in parametros:
        if p["in"] == "path":
            url = url.replace("{" + p["name"] + "}", str(p["example"]))
    query = {p["name"]: p["example"] for p in parametros if p["in"] == "query"}
    if query:
        url += "?" + urlencode(query)
    ex_peticion = {"metodo": metodo.upper(), "url": url}
    if entrada:
        ex_peticion["cuerpo"] = cuerpo
    op = {"operationId": id_op, "summary": resumen, "description": descripcion or resumen,
          "tags": [ruta.split("/")[2]], "x-estado": estado, "x-ejemplo-peticion": ex_peticion,
          "responses": {codigo: {"description": "Sin cuerpo; archivado" if codigo == "204" else "Resultado correcto"}}}
    if parametros:
        op["parameters"] = parametros
    if entrada:
        op["requestBody"] = {"required": True, "content": {"application/json": {"schema": ref(entrada), "example": cuerpo}}}
    if salida:
        schema = ref(salida) if isinstance(salida, str) else salida
        op["responses"][codigo]["content"] = {"application/json": {"schema": schema, "example": ejemplo}}
    detalles = {"404": ("no_encontrado", "No existe el recurso solicitado"), "409": ("conflicto", "La revisión o el estado del recurso cambió"), "422": ("validacion", "El dato no cumple las reglas del dominio"), "503": ("base_no_disponible", "La base de datos no está disponible"), "500": ("error_interno", "Ocurrió un error inesperado")}
    for status in errores:
        motivo, detalle = detalles[status]
        schema = {"oneOf": [ref("ErrorNegocio"), ref("ErrorValidacion")]} if status == "422" else ref("ErrorNegocio")
        ejemplos = {"negocio": {"value": {"detail": {"motivo": motivo, "detalle": detalle}}}}
        if status == "422":
            ejemplos["formato"] = {"value": {"detail": [{"loc": ["query", "limite"], "msg": "Input should be greater than or equal to 1", "type": "greater_than_equal", "input": 0}]}}
        op["responses"][status] = {"description": detalle, "content": {"application/json": {"schema": schema, "examples": ejemplos}}}
    SPEC["paths"].setdefault(ruta, {})[metodo] = op
    HTTP.extend([f"### {id_op} · {estado}", f"{metodo.upper()} {{{{base}}}}{url}"])
    if entrada:
        HTTP.extend(["Content-Type: application/json", "", json.dumps(cuerpo, ensure_ascii=False, indent=2)])
    HTTP.extend(["", f"# Respuesta: {codigo}"])
    if salida:
        HTTP.extend("# " + line for line in json.dumps(ejemplo, ensure_ascii=False, indent=2).splitlines())
    else:
        HTTP.append("# Sin cuerpo.")
    HTTP.append("")


operacion("get", "/api/tipos-componentes", "listarTipos", "Tipos, campos y capacidades", lista(ref("TipoComponente")), tipo_ejemplos, estado="implementado", descripcion="Catálogo completo ordenado por ID, consultado en PostgreSQL. Sin semillas devuelve un arreglo vacío; base no disponible devuelve 503.")
ranuras = [{"id": k, "tipo_id": k, "nombre": n, "obligatoria": k in ["mcu", "linea", "motor", "driver", "bat", "reg", "chasis"], "cantidad_editable": k in ["linea", "motor"], "depende_reglamento": k in ["enc", "imu", "turb"]} for k, n, _, _ in TIPOS]
operacion("get", "/api/ranuras", "listarRanuras", "Ranuras del armador", lista(ref("Ranura")), ranuras, estado="implementado")
operacion("get", "/api/componentes", "listarComponentes", "Buscar componentes del catálogo", pagina("Componente"), paginado(COMP), parametros=PAGINACION + [parametro("q", texto(120), "QTR"), parametro("tipo_id", enum(*(x[0] for x in TIPOS)), "linea")], estado="implementado", descripcion="Orden por nombre e id; búsqueda sin distinguir mayúsculas ni tildes españolas en nombre, tipo, tienda y especificaciones. % y _ se buscan como texto literal. Excluye archivados. total es el conteo después de filtros y antes de paginar. Sin resultados responde una página con items vacíos.")
operacion("post", "/api/componentes", "crearComponente", "Registrar componente e inventario inicial", "Componente", COMP, "ComponenteCrear", {k: v for k, v in COMP.items() if k not in ["id", "archivado"]}, codigo="201", estado="implementado", errores=("409", "422", "503", "500"), descripcion="Genera un ID único y valida las especificaciones contra los campos del tipo. Precio admite hasta 2 decimales, masa 3 y consumo 4 (12 dígitos totales); stock admite hasta 2147483647. Crea componente e inventario en una transacción. La unidad de stock coincide con la unidad del catálogo: un par de ruedas cuenta como una unidad.")
operacion("get", "/api/componentes/{componente_id}", "obtenerComponente", "Consultar ficha de componente", "Componente", COMP, estado="implementado", descripcion="Devuelve ficha y stock actual por ID, incluidos archivados. Un ID inexistente responde 404.", errores=("404", "422", "503", "500"))
operacion("patch", "/api/componentes/{componente_id}", "editarComponente", "Editar ficha sin alterar versiones históricas", "Componente", {**COMP, "precio": 65}, "ComponenteEditar", {"precio": 65}, estado="implementado", descripcion="PATCH parcial: conserva campos omitidos. especificaciones reemplaza el objeto completo y se valida contra el tipo existente. Solo consumo_a admite null. Tipo, ID, archivado y stock no se editan aquí. Archivado responde 409; inexistente 404. Bloquea la ficha durante la edición y no modifica inventario. Las instantáneas de versiones existentes se conservan.", errores=("404", "409", "422", "503", "500"))
operacion("delete", "/api/componentes/{componente_id}", "archivarComponente", "Archivar componente", codigo="204", estado="implementado", errores=("404", "409", "422", "503", "500"), descripcion="Baja lógica con bloqueo de fila; conserva ficha, stock y revisión de inventario. Excluye del listado; la consulta por ID sigue disponible. Las versiones conservan sus instantáneas y referencias. Repetir sobre un archivado devuelve 204. Un id inexistente devuelve 404.")
operacion("get", "/api/inventario", "listarInventario", "Inventario total, asignado y faltante", pagina("Inventario"), paginado(INV), parametros=PAGINACION, estado="implementado", descripcion="No refleja robots simulados de la consola. Orden por componente_id; página vacía si no hay resultados. Incluye activos sin stock. en_robots suma cantidades en la última versión de cada robot activo, incluidos Concepto y Borrador como en el prototipo. disponible = stock - en_robots (puede ser negativo); faltante = max(0, -disponible). Incluye componentes archivados con stock o asignaciones.")
operacion("put", "/api/inventario/{componente_id}", "actualizarInventario", "Actualizar existencias con control de concurrencia", "Inventario", {**INV, "stock": 4, "disponible": 2, "revision": 2}, "InventarioActualizar", {"stock": 4, "revision": 1}, estado="implementado", descripcion="Fija stock total y compara e incrementa revisión en un único UPDATE. Revisión obsoleta responde 409 revision_obsoleta; inventario inexistente 404. Admite componentes archivados. Stock entre 0 y 2147483647; revisión entre 1 y 2147483647, límite alcanzado responde 409 revision_agotada. Calcula en_robots desde la última versión de cada robot activo, disponible=stock-en_robots y faltante=max(0,-disponible). No modifica la ficha del componente.", errores=("404", "409", "422", "503", "500"))
operacion("get", "/api/robots", "listarRobots", "Listar robots", pagina("Robot"), paginado({**ROBOT, "version_actual_id": 2}), parametros=PAGINACION, estado="implementado", descripcion="Robots no archivados ordenados por codigo_corto/id. total se calcula antes de paginar. version_actual_id es null hasta cargar una versión; la semilla v001 incluye v0/v1.")
operacion("post", "/api/robots", "crearRobot", "Registrar robot sin versiones", "Robot", {**ROBOT, "id": "v003", "codigo_corto": "003", "nombre": "Velocista 003", "version_actual_id": None, "firmware": None}, "RobotCrear", {"nombre": "Velocista 003", "codigo_corto": "003", "tipo": "velocista"}, codigo="201", estado="implementado", descripcion="Genera un ID único, recorta espacios y registra identificación sin versiones. Código corto duplicado devuelve 409. firmware es opcional, null por defecto. No crea piezas ni demanda de inventario.", errores=("409", "422", "503", "500"))
operacion("get", "/api/robots/{robot_id}", "obtenerRobot", "Consultar robot", "Robot", {**ROBOT, "version_actual_id": 2}, estado="implementado", descripcion="Devuelve identificación por ID, incluidos archivados; inexistente responde 404. version_actual_id referencia la última versión del mismo robot, o null si no tiene ninguna.", errores=("404", "422", "503", "500"))
operacion("patch", "/api/robots/{robot_id}", "editarRobot", "Editar identificación del robot", "Robot", {**ROBOT, "nombre": "Velocista de pruebas"}, "RobotEditar", {"nombre": "Velocista de pruebas"}, errores=("404", "409", "422", "503", "500"), estado="implementado")
operacion("delete", "/api/robots/{robot_id}", "archivarRobot", "Archivar robot y liberar su demanda de inventario", codigo="204", errores=("404", "409", "422", "503", "500"), descripcion="Baja lógica; mantiene versiones, setups y corridas. 409 si está corriendo. Un archivado conocido devuelve 204; un id inexistente 404.", estado="implementado")
operacion("get", "/api/robots/{robot_id}/versiones", "listarVersiones", "Historial de versiones del robot", pagina("Version"), paginado(VERSION), parametros=PAGINACION, estado="implementado", errores=("404", "422", "503", "500"), descripcion="Orden por número de versión ascendente. Incluye piezas con sus instantáneas persistidas, sin sustituirlas por el catálogo actual. Un robot existente sin versiones responde página vacía; inexistente 404. Admite robots archivados.")
operacion("post", "/api/robots/{robot_id}/versiones", "crearVersion", "Guardar una nueva versión y su lista de piezas", "Version", VERSION, "VersionCrear", {"version_base_id": None, "nota": "Primer armado", "estado": "Actual", "piezas": {k: {"componente_id": cid, "cantidad": n} for k, (cid, n) in parts.items()}}, codigo="201", errores=("404", "409", "422", "503", "500"), descripcion="El servidor asigna v0, v1… bajo bloqueo del robot. Comprueba versión base y tipos de ranuras; guarda snapshots de piezas y actualiza version_actual_id atómicamente. Actual exige ranuras obligatorias; Concepto/Borrador admite incompletas. La falta de stock es informativa. 409 si el robot está corriendo o la base quedó obsoleta.", estado="implementado")
operacion("get", "/api/robots/{robot_id}/versiones/{version_id}", "obtenerVersion", "Consultar una versión del robot", "Version", VERSION, estado="implementado", errores=("404", "422", "503", "500"), descripcion="404 si la versión no pertenece al robot, aunque exista bajo otro robot. Incluye piezas e instantáneas históricas. Admite robots archivados.")
operacion("get", "/api/controladores", "listarControladores", "Controladores, parámetros y presets", lista(ref("Controlador")), [CTRL], descripcion="Catálogo PID, adaptativo y difuso del prototipo. La disponibilidad real y rangos permitidos al enviar se confirman con EN-02.", estado="implementado")
operacion("get", "/api/perfiles", "listarPerfiles", "Perfiles de reglamento", lista(ref("PerfilReglamento")), [PERFIL], estado="implementado")
operacion("get", "/api/robots/{robot_id}/setups", "listarSetups", "Setups guardados del robot", pagina("Setup"), paginado(SETUP), parametros=PAGINACION + [parametro("version_id", entero(1), 1)], errores=("404", "422", "503", "500"), estado="implementado")
operacion("post", "/api/robots/{robot_id}/setups", "crearSetup", "Guardar setup en PostgreSQL", "Setup", SETUP, "SetupCrear", {k: SETUP[k] for k in ["version_id", "nombre", "controlador_id", "parametros"]}, codigo="201", errores=("404", "409", "422", "503", "500"), descripcion="Valida pertenencia de versión al robot y parámetros del controlador. Cada guardado crea un id nuevo; no cambia corridas previas ni envía comandos. La consola aplica luego mediante POST /api/dispositivos/{dispositivo}/comandos.", estado="implementado")
operacion("get", "/api/setups/{setup_id}", "obtenerSetup", "Recuperar setup guardado", "Setup", SETUP, errores=("404", "422", "503", "500"), estado="implementado")
operacion("delete", "/api/setups/{setup_id}", "archivarSetup", "Archivar setup conservando sus corridas", codigo="204", errores=("404", "409", "422", "503", "500"), descripcion="Baja lógica. Repetir sobre un id archivado devuelve 204; inexistente devuelve 404. Un setup usado por una corrida activa devuelve 409.", estado="implementado")
operacion("get", "/api/corridas", "listarCorridas", "Historial para tiempos, comparación y CSV", pagina("Corrida"), paginado(CORRIDA), parametros=PAGINACION + [parametro("robot_id", ID, "v001"), parametro("version_id", entero(1), 1), parametro("controlador_id", ID, "pid"), parametro("fuente", enum("sim", "robot"), "robot")], descripcion="Orden por fecha e id descendentes. En competencia una corrida contiene un intento de una vuelta; en pruebas se selecciona la mejor vuelta terminada por J, desempate por número. J se calcula en servidor: tiempo_s + 2 × error_acumulado, o 120 si ninguna termina. CSV se construye en la consola, recorriendo páginas.", estado="implementado")
operacion("get", "/api/corridas/{corrida_id}", "obtenerCorrida", "Consultar corrida y snapshot del setup aplicado", "Corrida", CORRIDA, errores=("404", "409", "422", "503", "500"), descripcion="Resumen de una corrida cerrada. Si sigue activa devuelve 409 corrida_en_curso; el progreso se consulta por WebSocket.", estado="implementado")
operacion("patch", "/api/corridas/{corrida_id}", "anotarCorrida", "Guardar nota de pista", "Corrida", {**CORRIDA, "nota": "Mejor agarre"}, "NotaCorrida", {"nota": "Mejor agarre"}, errores=("404", "409", "422", "503", "500"), estado="implementado")
operacion("get", "/api/corridas/{corrida_id}/vueltas", "listarVueltas", "Vueltas, sectores y segmentos", pagina("Vuelta"), paginado(VUELTA), parametros=PAGINACION, errores=("404", "422", "503", "500"), estado="implementado")
operacion("get", "/api/salud", "consultarSalud", "Estado de API, base y enlaces", "Salud", {"api": "ok", "base_de_datos": "ok", "entorno": "desarrollo", "dispositivos": {"velocista": False, "cronometro": False}}, estado="implementado", errores=("500",), descripcion="200 incluso si la BD no está disponible; consultar base_de_datos. No implica que el manifiesto ya esté recibido.")
operacion("get", "/api/eventos", "listarEventos", "Eventos recientes", lista(ref("Evento")), [EVENTO], parametros=[parametro("limite", entero(1, maximum=500, default=50), 50)], estado="implementado", descripcion="Conserva la respuesta actual como arreglo, sin envoltorio paginado.")
operacion("post", "/api/eventos", "registrarEvento", "Registrar evento del sistema", "Evento", EVENTO, "EventoCrear", {k: EVENTO[k] for k in ["sistema", "nivel", "mensaje"]}, codigo="201", estado="implementado")
ej_manifiesto = json.loads((RAIZ / "docs/contrato/ejemplos/velocista.manifiesto.json").read_text(encoding="utf-8"))["datos"]
operacion("get", "/api/dispositivos/velocista/manifiesto", "consultarManifiesto", "Manifiesto del dispositivo conectado", "Manifiesto", ej_manifiesto, estado="implementado", errores=("404", "500"))
operacion("post", "/api/dispositivos/{dispositivo}/comandos", "enviarComando", "Enviar un comando al dispositivo", "ComandoEnviado", {"seq": 2, "mensaje": "Enviado. La confirmación del dispositivo llega a la consola como ack."}, "Comando", {"tipo": "setup", "datos": {"controlador": "pid", "parametros": P, "id_setup": 1}}, codigo="202", estado="implementado", errores=("409", "422", "500"), descripcion="202 confirma envío, no ejecución ni guardado en flash. El ack de EN-02 llega por /ws/consola. Sin enlace: 409 desconectado; en competencia corriendo solo detener; para arrancar requiere calibración. Los comandos para cronometro son los definidos por EN-02.")


def generar():
    return {
        DESTINO / "openapi.json": json.dumps(SPEC, ensure_ascii=False, indent=2) + "\n",
        DESTINO / "ejemplos.http": "\n".join(HTTP) + "\n",
        RAIZ / "docs/datos/tipos-componentes.json": json.dumps(tipo_ejemplos, ensure_ascii=False, indent=2) + "\n",
    }


if __name__ == "__main__":
    for ruta, contenido in generar().items():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(contenido, encoding="utf-8", newline="\n")
        print(ruta.relative_to(RAIZ))

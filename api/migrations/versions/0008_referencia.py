"""Capa de estructura/referencia: tipos, ranuras, controladores y perfiles.

Datos de SOLO LECTURA que la app necesita para funcionar (no hay endpoints para crearlos).
Los datos de usuario (componentes, robots, versiones, corridas) quedan VACIOS y se cargan por la
API/consola. La BD arranca sin datos de usuario; aqui solo entra la estructura.

Revision ID: 0008_referencia
Revises: 0007_configuracion
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008_referencia"
down_revision = "0007_configuracion"
branch_labels = None
depends_on = None


TIPOS = [
    {
        "id": "bat",
        "nombre": "Batería",
        "color": "#3DDC97",
        "campos": [
            {
                "tipo": "n",
                "clave": "celdas",
                "unidad": "S",
                "etiqueta": "Celdas",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "mah",
                "unidad": "mAh",
                "etiqueta": "Capacidad",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "c",
                "unidad": "C",
                "etiqueta": "Descarga",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "vmax",
                "unidad": "V",
                "etiqueta": "Voltaje a carga completa",
                "obligatorio": False,
            },
        ],
        "capacidades": [
            {"campo": "vmax", "clave": "bateria_v", "unidad": "V", "agregacion": "por_componente"}
        ],
    },
    {
        "id": "chasis",
        "nombre": "Chasis",
        "color": "#A2A7B8",
        "campos": [
            {
                "tipo": "n",
                "clave": "ancho",
                "unidad": "mm",
                "etiqueta": "Ancho",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "largo",
                "unidad": "mm",
                "etiqueta": "Largo",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "material",
                "unidad": "",
                "etiqueta": "Material",
                "obligatorio": False,
            },
        ],
        "capacidades": [],
    },
    {
        "id": "driver",
        "nombre": "Driver",
        "color": "#FFCB57",
        "campos": [
            {
                "tipo": "n",
                "clave": "canales",
                "unidad": "",
                "etiqueta": "Canales",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "icont",
                "unidad": "A",
                "etiqueta": "Corriente continua",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "ipico",
                "unidad": "A",
                "etiqueta": "Corriente pico",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "vmin",
                "unidad": "V",
                "etiqueta": "Voltaje mínimo",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "vmax",
                "unidad": "V",
                "etiqueta": "Voltaje máximo",
                "obligatorio": False,
            },
        ],
        "capacidades": [],
    },
    {
        "id": "enc",
        "nombre": "Encoder",
        "color": "#6CB6FF",
        "campos": [
            {
                "tipo": "n",
                "clave": "cpr",
                "unidad": "pulsos/vuelta",
                "etiqueta": "Pulsos por vuelta (CPR)",
                "obligatorio": False,
            },
            {"tipo": "t", "clave": "tipo", "unidad": "", "etiqueta": "Tipo", "obligatorio": False},
        ],
        "capacidades": [
            {
                "campo": "cpr",
                "clave": "pulsos_por_vuelta",
                "unidad": "pulsos/vuelta",
                "agregacion": "por_componente",
            }
        ],
    },
    {
        "id": "exp",
        "nombre": "Placa de expansión",
        "color": "#A2A7B8",
        "campos": [
            {
                "tipo": "n",
                "clave": "bornes",
                "unidad": "",
                "etiqueta": "Bornes",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "comercial",
                "unidad": "",
                "etiqueta": "PCB comercial",
                "obligatorio": False,
            },
        ],
        "capacidades": [],
    },
    {
        "id": "imu",
        "nombre": "IMU",
        "color": "#6CB6FF",
        "campos": [
            {"tipo": "n", "clave": "ejes", "unidad": "", "etiqueta": "Ejes", "obligatorio": False},
            {"tipo": "t", "clave": "bus", "unidad": "", "etiqueta": "Bus", "obligatorio": False},
        ],
        "capacidades": [
            {"campo": "ejes", "clave": "ejes", "unidad": "ejes", "agregacion": "por_componente"}
        ],
    },
    {
        "id": "linea",
        "nombre": "Sensor de línea",
        "color": "#3DDC97",
        "campos": [
            {
                "tipo": "n",
                "clave": "canales",
                "unidad": "",
                "etiqueta": "Canales",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "salida",
                "unidad": "",
                "etiqueta": "Salida",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "paso",
                "unidad": "mm",
                "etiqueta": "Paso",
                "obligatorio": False,
            },
            {"tipo": "n", "clave": "i", "unidad": "A", "etiqueta": "Consumo", "obligatorio": False},
        ],
        "capacidades": [
            {
                "campo": "canales",
                "clave": "canales_linea",
                "unidad": "canales",
                "agregacion": "suma_por_cantidad",
            }
        ],
    },
    {
        "id": "mcu",
        "nombre": "Microcontrolador",
        "color": "#FF5A78",
        "campos": [
            {
                "tipo": "n",
                "clave": "mhz",
                "unidad": "MHz",
                "etiqueta": "Frecuencia",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "radio",
                "unidad": "",
                "etiqueta": "Radio",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "logica",
                "unidad": "V",
                "etiqueta": "Lógica",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "adc",
                "unidad": "",
                "etiqueta": "Entradas analógicas usables",
                "obligatorio": False,
            },
        ],
        "capacidades": [
            {"campo": "radio", "clave": "radio", "unidad": "", "agregacion": "por_componente"}
        ],
    },
    {
        "id": "motor",
        "nombre": "Motor",
        "color": "#B48CFF",
        "campos": [
            {
                "tipo": "n",
                "clave": "v",
                "unidad": "V",
                "etiqueta": "Voltaje nominal",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "rpm",
                "unidad": "rpm",
                "etiqueta": "RPM sin carga",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "inom",
                "unidad": "A",
                "etiqueta": "Corriente nominal",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "ipico",
                "unidad": "A",
                "etiqueta": "Corriente de arranque",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "red",
                "unidad": "",
                "etiqueta": "Reducción",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "familia",
                "unidad": "",
                "etiqueta": "Familia",
                "obligatorio": False,
            },
        ],
        "capacidades": [
            {
                "max": 100,
                "min": -100,
                "clave": "pwm_pct",
                "unidad": "%",
                "agregacion": "por_componente",
            }
        ],
    },
    {
        "id": "mux",
        "nombre": "Multiplexor",
        "color": "#6CB6FF",
        "campos": [
            {
                "tipo": "n",
                "clave": "canales",
                "unidad": "",
                "etiqueta": "Canales",
                "obligatorio": False,
            },
            {"tipo": "t", "clave": "tipo", "unidad": "", "etiqueta": "Tipo", "obligatorio": False},
        ],
        "capacidades": [],
    },
    {
        "id": "reg",
        "nombre": "Regulador",
        "color": "#A2A7B8",
        "campos": [
            {
                "tipo": "n",
                "clave": "vout",
                "unidad": "V",
                "etiqueta": "Salida",
                "obligatorio": False,
            },
            {
                "tipo": "n",
                "clave": "imax",
                "unidad": "A",
                "etiqueta": "Corriente máxima",
                "obligatorio": False,
            },
            {"tipo": "t", "clave": "tipo", "unidad": "", "etiqueta": "Tipo", "obligatorio": False},
        ],
        "capacidades": [],
    },
    {
        "id": "rueda",
        "nombre": "Rueda",
        "color": "#A2A7B8",
        "campos": [
            {
                "tipo": "n",
                "clave": "diam",
                "unidad": "mm",
                "etiqueta": "Diámetro",
                "obligatorio": False,
            },
            {
                "tipo": "t",
                "clave": "material",
                "unidad": "",
                "etiqueta": "Material",
                "obligatorio": False,
            },
        ],
        "capacidades": [],
    },
    {
        "id": "sw",
        "nombre": "Interruptor",
        "color": "#5E6374",
        "campos": [
            {"tipo": "t", "clave": "tipo", "unidad": "", "etiqueta": "Tipo", "obligatorio": False}
        ],
        "capacidades": [],
    },
    {
        "id": "turb",
        "nombre": "Turbina",
        "color": "#FF2D55",
        "campos": [
            {
                "tipo": "n",
                "clave": "diam",
                "unidad": "mm",
                "etiqueta": "Diámetro",
                "obligatorio": False,
            },
            {"tipo": "n", "clave": "v", "unidad": "V", "etiqueta": "Voltaje", "obligatorio": False},
            {
                "tipo": "n",
                "clave": "imax",
                "unidad": "A",
                "etiqueta": "Corriente",
                "obligatorio": False,
            },
        ],
        "capacidades": [
            {
                "clave": "potencia_electrica_max_w",
                "campos": ["v", "imax"],
                "unidad": "W",
                "operacion": "producto",
                "agregacion": "suma_por_cantidad",
            },
            {
                "max": 100,
                "min": 0,
                "clave": "potencia_control_pct",
                "unidad": "%",
                "agregacion": "por_componente",
            },
        ],
    },
]

RANURAS = [
    {
        "id": "bat",
        "tipo_id": "bat",
        "nombre": "Batería",
        "obligatoria": True,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "chasis",
        "tipo_id": "chasis",
        "nombre": "Chasis",
        "obligatoria": True,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "driver",
        "tipo_id": "driver",
        "nombre": "Driver",
        "obligatoria": True,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "enc",
        "tipo_id": "enc",
        "nombre": "Encoders",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": True,
    },
    {
        "id": "exp",
        "tipo_id": "exp",
        "nombre": "Placa de expansión",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "imu",
        "tipo_id": "imu",
        "nombre": "IMU",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": True,
    },
    {
        "id": "linea",
        "tipo_id": "linea",
        "nombre": "Sensores de línea",
        "obligatoria": True,
        "cantidad_editable": True,
        "depende_reglamento": False,
    },
    {
        "id": "mcu",
        "tipo_id": "mcu",
        "nombre": "Microcontrolador",
        "obligatoria": True,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "motor",
        "tipo_id": "motor",
        "nombre": "Motores",
        "obligatoria": True,
        "cantidad_editable": True,
        "depende_reglamento": False,
    },
    {
        "id": "mux",
        "tipo_id": "mux",
        "nombre": "Multiplexor",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "reg",
        "tipo_id": "reg",
        "nombre": "Regulador",
        "obligatoria": True,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "rueda",
        "tipo_id": "rueda",
        "nombre": "Ruedas (par)",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "sw",
        "tipo_id": "sw",
        "nombre": "Interruptor",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": False,
    },
    {
        "id": "turb",
        "tipo_id": "turb",
        "nombre": "Turbina",
        "obligatoria": False,
        "cantidad_editable": False,
        "depende_reglamento": True,
    },
]

CONTROLADORES = [
    {
        "id": "adapt",
        "nombre": "PID adaptativo",
        "nombre_corto": "Adaptativo",
        "descripcion": "PID con velocidad base variable: frena según el error (Kv) sin bajar de Vmín. "
        "Rápido en rectas, prudente en curvas.",
        "parametros": [
            {
                "max": 2,
                "min": 0,
                "paso": 0.01,
                "clave": "kp",
                "nombre": "Kp",
                "decimales": 2,
                "descripcion": "Proporcional",
                "optimizable": True,
            },
            {
                "max": 0.3,
                "min": 0,
                "paso": 0.005,
                "clave": "ki",
                "nombre": "Ki",
                "decimales": 3,
                "descripcion": "Integral",
                "optimizable": False,
            },
            {
                "max": 10,
                "min": 0,
                "paso": 0.1,
                "clave": "kd",
                "nombre": "Kd",
                "decimales": 1,
                "descripcion": "Derivativo",
                "optimizable": True,
            },
            {
                "max": 100,
                "min": 10,
                "paso": 1,
                "clave": "base",
                "nombre": "Base",
                "decimales": 0,
                "descripcion": "Velocidad base (%)",
                "optimizable": False,
            },
            {
                "max": 100,
                "min": 20,
                "paso": 1,
                "clave": "max",
                "nombre": "Máx",
                "decimales": 0,
                "descripcion": "PWM máximo (%)",
                "optimizable": False,
            },
            {
                "max": 1,
                "min": 0,
                "paso": 0.05,
                "clave": "kv",
                "nombre": "Kv",
                "decimales": 2,
                "descripcion": "Frenado: cuánto baja la velocidad con el error",
                "optimizable": True,
            },
            {
                "max": 60,
                "min": 10,
                "paso": 1,
                "clave": "vmin",
                "nombre": "Vmín",
                "decimales": 0,
                "descripcion": "Velocidad mínima en curva (%)",
                "optimizable": False,
            },
        ],
        "presets": {
            "Base": {"kd": 2.8, "ki": 0, "kp": 0.6, "kv": 0.55, "max": 86, "base": 65, "vmin": 32},
            "Seguro": {"kd": 3, "ki": 0, "kp": 0.5, "kv": 0.5, "max": 86, "base": 55, "vmin": 30},
            "Agresivo": {
                "kd": 3.5,
                "ki": 0,
                "kp": 0.75,
                "kv": 0.6,
                "max": 86,
                "base": 78,
                "vmin": 35,
            },
        },
    },
    {
        "id": "fuzzy",
        "nombre": "Difuso",
        "nombre_corto": "Difuso",
        "descripcion": "Reglas difusas: corrige suave con error chico y fuerte con error grande. Para "
        "comparar contra el PID en el informe.",
        "parametros": [
            {
                "max": 2,
                "min": 0,
                "paso": 0.01,
                "clave": "g",
                "nombre": "G",
                "decimales": 2,
                "descripcion": "Ganancia de las reglas difusas",
                "optimizable": True,
            },
            {
                "max": 10,
                "min": 0,
                "paso": 0.1,
                "clave": "d",
                "nombre": "D",
                "decimales": 1,
                "descripcion": "Amortiguamiento (derivativo)",
                "optimizable": True,
            },
            {
                "max": 100,
                "min": 10,
                "paso": 1,
                "clave": "base",
                "nombre": "Base",
                "decimales": 0,
                "descripcion": "Velocidad base (%)",
                "optimizable": False,
            },
            {
                "max": 100,
                "min": 20,
                "paso": 1,
                "clave": "max",
                "nombre": "Máx",
                "decimales": 0,
                "descripcion": "PWM máximo (%)",
                "optimizable": False,
            },
        ],
        "presets": {
            "Base": {"d": 2.6, "g": 0.65, "max": 86, "base": 50},
            "Seguro": {"d": 3, "g": 0.5, "max": 86, "base": 42},
            "Agresivo": {"d": 3.6, "g": 0.85, "max": 86, "base": 60},
        },
    },
    {
        "id": "pid",
        "nombre": "PID",
        "nombre_corto": "PID",
        "descripcion": "Clásico. Con Ki = 0 funciona como PD, lo más usado en velocistas.",
        "parametros": [
            {
                "max": 2,
                "min": 0,
                "paso": 0.01,
                "clave": "kp",
                "nombre": "Kp",
                "decimales": 2,
                "descripcion": "Proporcional",
                "optimizable": True,
            },
            {
                "max": 0.3,
                "min": 0,
                "paso": 0.005,
                "clave": "ki",
                "nombre": "Ki",
                "decimales": 3,
                "descripcion": "Integral",
                "optimizable": False,
            },
            {
                "max": 10,
                "min": 0,
                "paso": 0.1,
                "clave": "kd",
                "nombre": "Kd",
                "decimales": 1,
                "descripcion": "Derivativo",
                "optimizable": True,
            },
            {
                "max": 100,
                "min": 10,
                "paso": 1,
                "clave": "base",
                "nombre": "Base",
                "decimales": 0,
                "descripcion": "Velocidad base (%)",
                "optimizable": False,
            },
            {
                "max": 100,
                "min": 20,
                "paso": 1,
                "clave": "max",
                "nombre": "Máx",
                "decimales": 0,
                "descripcion": "PWM máximo (%)",
                "optimizable": False,
            },
        ],
        "presets": {
            "Base": {"kd": 2.5, "ki": 0, "kp": 0.6, "max": 86, "base": 45},
            "Seguro": {"kd": 3.5, "ki": 0, "kp": 0.45, "max": 80, "base": 38},
            "Agresivo": {"kd": 4, "ki": 0, "kp": 0.8, "max": 86, "base": 62},
        },
    },
]

PERFILES = [
    {
        "id": "club",
        "competencia": "Pruebas del club",
        "etiqueta": "Club",
        "categoria": "Libre",
        "reglas": {
            "dim": None,
            "enc": True,
            "imu": True,
            "mcu": None,
            "mr4": False,
            "inal": False,
            "chasis": "Libre",
            "ruedas": None,
            "drivers": None,
            "mapaVel": True,
            "montaje": "Libre",
            "motores": None,
            "sensMax": None,
            "turbina": True,
            "arranque": "Libre",
            "motorFam": None,
            "pcbComercial": True,
        },
    },
    {
        "id": "mr4a",
        "competencia": "Muchik Rumble 4",
        "etiqueta": "MR4",
        "categoria": "Amateur",
        "reglas": {
            "dim": [200, 250],
            "enc": False,
            "imu": False,
            "mcu": ["Arduino UNO", "Arduino Nano", "Raspberry Pi Pico", "ESP32"],
            "mr4": True,
            "inal": False,
            "chasis": "Obligatorio: impresión 3D o MDF",
            "ruedas": 2,
            "drivers": 1,
            "mapaVel": False,
            "montaje": "Protoboard, cableado directo, shield genérico o PCB propia",
            "motores": 2,
            "sensMax": 8,
            "turbina": False,
            "arranque": "Interruptor, pulsador, IR o Bluetooth",
            "motorFam": ["TT amarillo"],
            "chasisMat": ["3D", "MDF"],
            "pcbComercial": False,
        },
    },
    {
        "id": "mr4m",
        "competencia": "Muchik Rumble 4",
        "etiqueta": "MR4",
        "categoria": "Master",
        "reglas": {
            "dim": [300, 300],
            "enc": False,
            "imu": False,
            "mcu": None,
            "mr4": True,
            "inal": True,
            "chasis": "Libre",
            "ruedas": None,
            "drivers": None,
            "mapaVel": False,
            "montaje": "Libre (se admiten robots comerciales)",
            "motores": None,
            "sensMax": None,
            "turbina": True,
            "arranque": "Inalámbrico",
            "motorFam": None,
            "pcbComercial": True,
        },
    },
    {
        "id": "mr4s",
        "competencia": "Muchik Rumble 4",
        "etiqueta": "MR4",
        "categoria": "Senior",
        "reglas": {
            "dim": [200, 250],
            "enc": False,
            "imu": False,
            "mcu": None,
            "mr4": True,
            "inal": True,
            "chasis": "Libre",
            "ruedas": 2,
            "drivers": None,
            "mapaVel": False,
            "montaje": "Libre",
            "motores": 2,
            "sensMax": None,
            "turbina": False,
            "arranque": "Inalámbrico",
            "motorFam": None,
            "pcbComercial": True,
        },
    },
]


_tipo = sa.table(
    "tipo_componente",
    sa.column("id", sa.String),
    sa.column("nombre", sa.String),
    sa.column("color", sa.String),
    sa.column("campos", postgresql.JSONB),
    sa.column("capacidades", postgresql.JSONB),
)
_ranura = sa.table(
    "ranura",
    sa.column("id", sa.String),
    sa.column("tipo_id", sa.String),
    sa.column("nombre", sa.String),
    sa.column("obligatoria", sa.Boolean),
    sa.column("cantidad_editable", sa.Boolean),
    sa.column("depende_reglamento", sa.Boolean),
)
_controlador = sa.table(
    "controlador",
    sa.column("id", sa.String),
    sa.column("nombre", sa.String),
    sa.column("nombre_corto", sa.String),
    sa.column("descripcion", sa.Text),
    sa.column("parametros", postgresql.JSONB),
    sa.column("presets", postgresql.JSONB),
)
_perfil = sa.table(
    "perfil_reglamento",
    sa.column("id", sa.String),
    sa.column("competencia", sa.String),
    sa.column("etiqueta", sa.String),
    sa.column("categoria", sa.String),
    sa.column("reglas", postgresql.JSONB),
)


def upgrade() -> None:
    op.bulk_insert(_tipo, TIPOS)
    op.bulk_insert(_ranura, RANURAS)
    op.bulk_insert(_controlador, CONTROLADORES)
    op.bulk_insert(_perfil, PERFILES)


def downgrade() -> None:
    op.execute("DELETE FROM perfil_reglamento")
    op.execute("DELETE FROM controlador")
    op.execute("DELETE FROM ranura")
    op.execute("DELETE FROM tipo_componente")

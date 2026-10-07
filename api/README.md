# API

Backend en **Python 3.12 + FastAPI**, desplegado como **monolito modular** (DO-02): un solo proceso con canales de entrada (REST y WebSocket) y siete módulos de negocio.

## Arranque

```bash
cd api
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
pip install -r requirements.lock          # versiones exactas
pip install -e . --no-deps
alembic upgrade head                      # requiere PostgreSQL (docker compose up -d)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva: http://localhost:8000/docs · Salud: http://localhost:8000/api/salud

El contrato de diseño completo está en [EN-01](../docs/api/README.md), con ejemplos
y estado de implementación por operación. El [modelo DO-03](../docs/datos/README.md)
define las tablas y relaciones pendientes de migrar. `/docs` describe solamente
los endpoints que el backend tiene implementados.

## CRUD y consultas EN-04

Las **32 operaciones de EN-01** están implementadas. Componentes y robots admiten
alta, consulta, edición y archivado. El inventario compara revisión al actualizar.
Crear una versión bloquea el robot, verifica `version_base_id`, valida ranuras y
piezas, guarda instantáneas y mueve el puntero en una transacción. La demanda
cuenta solo la última versión de robots activos, incluidos Concepto/Borrador.

Los setups son configuraciones históricas: cada guardado crea un nuevo ID y congela
la definición del controlador. Valida claves, rangos, pasos y relaciones entre
parámetros. Se pueden consultar y archivar, conservando corridas previas.
Las corridas permiten listado con filtros, detalle, notas y vueltas con sectores/segmentos.
El resumen selecciona la mejor vuelta terminada por J y desempata por número.
Los catálogos de tipos, ranuras, controladores y perfiles son de lectura por API.

### Aplicar a una instalación existente

Desde `api/`, en PowerShell:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\python.exe -m app.semillas
```

Head esperado: `0005_operaciones`. Las semillas agregan lo ausente y conservan
precios, stock, revisiones, robots e historial existentes. Incluyen 14 tipos,
25 componentes, 14 ranuras, Velocista 001 con v0/v1, 3 controladores y 4 perfiles.
Las fechas del prototipo tienen precisión de día y se cargan a medianoche de Lima;
las instantáneas iniciales usan las fichas persistidas al cargar, no precios históricos comprobados.

Para disponer de una corrida **simulada** y un setup de ejemplo (opcional y repetible):

```powershell
.\.venv\Scripts\python.exe -m app.demo
```

La demo informa el ID para consultar corrida y vueltas; no envía comandos físicos.
La guía [pruebas-crud.md](../docs/api/pruebas-crud.md) permite probar el conjunto en Swagger.

### Verificación

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check .
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

Las pruebas de escritura, incluidos eventos, usan esquemas temporales. Las pruebas
de concurrencia confirman transacciones solo en esos esquemas y los eliminan al terminar.
Requieren PostgreSQL; se omiten si no está disponible. El validador de diseño está
en `docs/api/validar_contrato.py` y usa las dependencias de `docs/api/requirements-validation.txt`.

### Alcance de esta entrega

Completa el backend REST EN-01. La consola todavía usa datos simulados y necesita
sus adaptadores. El gateway conserva su validación y difusión EN-02; la captura
persistente automática de corridas físicas requiere integrar el ciclo de adquisición.
Mapas, optimizadores y autenticación de usuarios corresponden a historias posteriores.

## Estructura

```
app/
├── main.py            create_app(): middlewares, errores, canales y módulos
├── core/              Infraestructura transversal
│   ├── config.py      Configuración desde ../.env
│   ├── db.py          Motor, sesiones (una por petición) y base declarativa
│   ├── errores.py     ErrorDeNegocio y formato estándar de errores
│   ├── registro.py    Logs y registro de cada petición
│   └── seguridad.py   Tokens de dispositivo (usuarios: módulo auth)
├── contrato/          Contrato de mensajes v1.0 (EN-02): sobre, manifiesto, mensajes, validación
├── gateway/
│   ├── ws.py          /ws/robot · /ws/cronometro · /ws/consola (valida con el contrato)
│   └── comandos.py    Manifiesto del robot y comandos hacia los dispositivos
└── modulos/           catalogo · armador · reglamento · corridas · optimizacion · eventos · auth
    └── <modulo>/
        ├── router.py      Controller: endpoints; sin reglas de negocio
        ├── service.py     Lógica de negocio; única interfaz pública del módulo
        ├── models.py      Tablas SQLAlchemy del módulo
        └── schemas.py     DTO Pydantic de entrada y salida
migrations/            Alembic (0001_base: evento; 0002_catalogo: catálogo; 0003_robot: robots; 0004_versiones: versiones; 0005_operaciones: setups/corridas)
herramientas/          robot_falso.py: robot simulado para desarrollo (no es parte del sistema)
tests/
├── contract/          Ejemplos y reglas del contrato de mensajes
├── unit/              Lógica pura, comandos y reglas de arquitectura
├── integration/       Endpoints y base de datos real (se omiten si no hay PostgreSQL)
└── websocket/         Gateway
```

## Reglas del monolito modular

- Un módulo solo usa de otro su `service.py`; nunca `models`, `router` ni `schemas`.
- Cada módulo es dueño de sus tablas.
- Los módulos no importan nada de `app.gateway`.
- `tests/unit/test_arquitectura.py` verifica estas reglas en cada PR.

## Comandos

| Qué | Comando |
| --- | --- |
| Pruebas | `pytest` |
| Pruebas con cobertura | `pytest --cov=app` |
| Solo unitarias | `pytest tests/unit` |
| Formato y lint | `ruff format . && ruff check .` |
| Nueva migración | `alembic revision --autogenerate -m "crea tabla componente"` |
| Aplicar / revertir | `alembic upgrade head` · `alembic downgrade -1` |
| Actualizar versiones fijadas | `pip freeze --exclude-editable > requirements.lock` |

## Agregar un endpoint

1. Esquemas de entrada y salida en `schemas.py`.
2. Regla de negocio en `service.py` (lanza `ErrorDeNegocio` si no se cumple).
3. Endpoint en `router.py`, que solo valida y delega.
4. Prueba unitaria del service y, si toca la base, de integración.

## Contrato de mensajes (EN-02)

- Documento y ejemplos: [`docs/contrato/`](../docs/contrato/).
- Modelos: `app/contrato/`. Regenerar los JSON Schema: `python -m app.contrato.exportar`.
- Probar sin el robot (solo desarrollo; no guarda corridas):

```bash
python herramientas/robot_falso.py            # con la API levantada
```

Luego envía comandos desde http://localhost:8000/docs → `POST /api/dispositivos/velocista/comandos`, por ejemplo `{"tipo": "calibrar"}` y `{"tipo": "arrancar"}`.

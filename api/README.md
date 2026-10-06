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

EN-04, primer paso: `0002_catalogo` agrega las tablas `tipo_componente`, `componente`
e `inventario` con sus restricciones y claves foráneas. Se aplica con `alembic upgrade head`.
Publica `GET /api/tipos-componentes`, que consulta PostgreSQL y devuelve los tipos
con sus campos y capacidades, ordenados por ID. Una base sin semillas devuelve `[]`;
una base no disponible devuelve 503. También publica `GET /api/componentes`, con stock,
búsqueda `q` sin distinguir tildes españolas/mayúsculas, filtro `tipo_id`, `limite` (50 por
defecto, máximo 200) y `offset`. Responde `{items,total,limite,offset}` y excluye archivados.
Ejemplos: `/api/componentes`, `/api/componentes?tipo_id=motor` y
`/api/componentes?q=QTR&tipo_id=linea`. También está disponible `POST /api/componentes`: genera el ID y guarda la ficha y su stock inicial en una transacción; valida los campos según el tipo. Precio admite 2 decimales, masa 3 y consumo 4 (12 dígitos totales); stock es un entero entre 0 y 2147483647. `GET /api/componentes/{componente_id}` devuelve la ficha y su stock actual, incluidos archivados; responde 404 si no existe. `PATCH /api/componentes/{componente_id}` edita solo los campos enviados, sin cambiar tipo, ID ni stock; `especificaciones` reemplaza el objeto completo. Solo `consumo_a` admite null. No se editan archivados (409). Los demás endpoints del catálogo siguen pendientes.
Sus pruebas de integración
(`pytest tests/integration/test_catalogo_bd.py`) usan esquemas temporales y revierten
todos los cambios, sin modificar las tablas de trabajo.

### Datos iniciales de EN-04

Después de aplicar las migraciones, desde `api/`:

```powershell
.\.venv\Scripts\python.exe -m app.semillas
```

Carga los 14 tipos de `docs/datos/tipos-componentes.json`, incluidos encoder, IMU y
turbina, y los 25 componentes de `app/datos/componentes.json`, adaptados del catálogo
del prototipo. Crea también su inventario inicial. Los archivos se incluyen en el
repositorio y no requieren internet. Una primera carga en una base vacía informa
14 tipos, 25 componentes y 25 inventarios nuevos. Repetirla informa cero nuevos.
Si ya cargaste los tipos, se conservan y se agregan únicamente los componentes y stocks ausentes.

Solo inserta IDs ausentes, sin borrar ni sobrescribir fichas, especificaciones,
precios, stock ni revisiones existentes. Si una ficha no tiene inventario, completa
esa fila con su stock inicial. Tipos, componentes e inventario se cargan en una
transacción: un error revierte todo el lote. Los valores de stock son los del
prototipo, no un conteo físico nuevo del club. Velocista 001 y los demás endpoints
se incorporarán en los siguientes pasos de EN-04.

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
migrations/            Alembic (0001_base: evento; 0002_catalogo: tipos, componentes e inventario)
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

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
migrations/            Alembic (0001_base crea la tabla evento)
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

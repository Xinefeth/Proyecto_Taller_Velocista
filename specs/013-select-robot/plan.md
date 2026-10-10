# Plan técnico · HU-13 Seleccionar el robot

Cómo está construido hoy, leído del código. No describe lo deseado, sino lo que existe.

## Módulos involucrados

- **builder** (`api/app/modulos/armador/`): robots y versiones.
- **devices** (`api/app/gateway/comandos.py`): manifiesto del robot conectado.
- **catalog** (`api/app/modulos/catalogo/`): tipos de componente y ranuras que alimentan
  los paneles.
- **Consola** (`consola/src/`): selección de robot y paneles por manifiesto.

## Endpoints REST

| Método | Ruta | operation_id |
|---|---|---|
| GET | `/api/robots` | `listRobots` |
| GET | `/api/robots/{robot_id}` | `getRobot` |
| GET | `/api/robots/{robot_id}/versions` | `listRobotVersions` |
| GET | `/api/robots/{robot_id}/versions/{version_id}` | `getRobotVersion` |
| GET | `/api/slots` | `listSlots` |
| GET | `/api/devices/velocista/manifest` | `getRacerManifest` |

`GET /api/robots` devuelve por robot: `id`, `nombre`, `codigo_corto`, `tipo`, `firmware`,
`version_actual_id`, `archivado` (`RobotSalida`). El manifiesto trae `sensores`,
`actuadores`, `canales` y `controladores` para armar los paneles.

## Mensajes WebSocket

- `manifiesto` (robot → API, primer mensaje en `/ws/robot`): declara qué sensores,
  actuadores, canales y controladores tiene el robot. Es la base de los paneles.

## Tablas

- `robot`, `version`, `version_componente` (builder); `ranura`, `tipo_componente`,
  `componente` (catalog). Modelos en `api/app/modulos/armador/models.py` y
  `.../catalogo/models.py`.

## Componentes de la consola

- `consola/src/datos/robots.ts`: fixtures del prototipo, inyectadas en tests;
  la lista de producción proviene de `api.robots.selection()`.
- `consola/src/components/ManifiestoModal.tsx`: muestra el manifiesto del robot.
- Paneles por tipo de componente: `consola/src/datos/tipos.ts`, `components/gestion/*`.

## Tests que lo cubren

- `api/tests/integration/test_robot_bd.py`: CRUD de robots y versiones (requiere
  PostgreSQL; hoy **skipped** sin BD).
- `api/tests/websocket/test_gateway.py`: recepción del `manifiesto` y lectura por
  `GET /api/devices/velocista/manifest`.
- `consola/src/types/contrato.test.ts`: separa los canales del manifiesto por grupo.

## Estado de los criterios

| Criterio | Estado | Nota |
|---|---|---|
| Lista robots con tipo, versión y firmware | **Cumplido** | `api.robots.selection()` recorre `/api/robots` y consulta la versión actual por ID para obtener etiqueta y piezas. Incluye robots exclusivos del backend. La consola muestra carga, vacío y error con reintento, sin fallback local. Armador lista tipo, versión y firmware. Verificación: **120 tests aprobados**, TypeScript y ESLint sin errores; HTTP probado con mocks, sin verificar CRUD PostgreSQL. |
| Paneles según sensores/actuadores; sin encoder no aparece | **Cumplido** | Armador y modal derivan los paneles de los sensores/actuadores del mismo manifiesto esperado, calculado con las piezas de la versión mostrada. No se declara batería si falta. Se actualizan al cambiar de robot o piezas. Verificación: **39 tests aprobados**, incluyendo robot sin piezas y cambio con/sin encoder; TypeScript y ESLint sin errores. El manifiesto físico en vivo queda fuera de esta HU, como indica `spec.md`. |

## Pendientes conocidos

- Campos del manifiesto aún en **español** por el renombrado (`tipo_robot`, `sensores`,
  `actuadores`, `canales`, `controlador_activo`, `compensa_bateria`…). Ver
  `docs/rename-glosario.md`. Renombrarlos toca el **firmware** (contrato 2.0).
- ~~El **ejemplo del manifiesto en Swagger** sale con **texto aleatorio** (lo genera el
  esquema).~~ **Resuelto**: el endpoint `getRacerManifest` usa como `example` de la
  respuesta 200 el ejemplo real de `docs/contrato/ejemplos/velocista.manifiesto.json`
  (`api/app/gateway/comandos.py`).
  Verificación HU-13: ejemplo OpenAPI idéntico al JSON del contrato y gateway REST/WS:
  **12 tests aprobados**. El endpoint declara explícitamente `status_code=200`.
- ~~La respuesta **503** (base de datos no disponible) no está documentada en Swagger.~~
  **Resuelto** en ambos routers con ejemplos `base_no_disponible`. El gateway aclara
  que actualmente no consulta BD; sus comandos conservan el ejemplo 503 por pérdida del
  enlace. Esto documenta el error de infraestructura solicitado, sin añadir dependencia
  de BD al gateway. Verificación: **26 tests aprobados** (Swagger, comandos, arquitectura y gateway).
- ~~Integración consola→API de robots pendiente~~ **Resuelta**: lista paginada y versión
  actual de la API, sin fallback local cuando falla.

## Propuestas pendientes de confirmación

No ejecutadas; se mantienen `[ ]` en `tasks.md` por instrucción del usuario.

### Campos del manifiesto en inglés

1. Inventariar los campos actuales y completar el mapa de `docs/rename-glosario.md`.
2. Acordar la versión y la estrategia de transición del contrato antes de romper
   compatibilidad (rechazo explícito o compatibilidad temporal, a decidir).
3. Actualizar de forma coordinada modelos/validación de API, firmware del robot,
   tipos y consumidores de consola, simulador y ejemplos JSON.
4. Verificar tests de contrato, REST/WS, consola y compilación del firmware; comprobar
   conexión y envío de manifiesto con hardware disponible antes de retirar compatibilidad.

### CRUD con PostgreSQL

Hace falta una instancia accesible de PostgreSQL (el Compose del repo usa PostgreSQL 16),
credenciales válidas y permisos para crear esquemas/tablas de prueba. La configuración se
lee de `.env`: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y
`POSTGRES_PORT`; `DATABASE_URL`, si existe, tiene prioridad. El entorno Python con
dependencias de desarrollo ya ejecuta las pruebas sin BD de esta revisión.

Tras confirmación: elegir la BD de pruebas, levantar `docker compose up -d db` si se usa
Docker y comprobar su salud; después ejecutar desde `api/`:
`./.venv/Scripts/python.exe -m pytest tests/integration/test_robot_bd.py -q -rs`.
La fixture aplica las migraciones en esquemas temporales y revierte su transacción.
Para validar además la consola con datos persistidos, acordar antes aplicar
`alembic upgrade head` y `python -m app.semillas` en la BD elegida.
Registrar resultados reales, incluidos skips y fallos. No se ha comprobado disponibilidad
de PostgreSQL ni se ha ejecutado ese CRUD; los tests HTTP de la consola usan mocks.

## Alcance de esta revisión

Sin commit ni push. Se preservan los cambios previos del workspace, incluidos los de
firmware y contrato; esta revisión no ejecutó la migración de campos a inglés.

# Prueba completa de la API

La API publica las 32 operaciones de EN-01. No todas las entidades admiten borrado físico:
DELETE archiva componentes, robots y setups; las versiones son históricas y se reemplazan
creando otra versión. Los tipos, ranuras, controladores y perfiles son catálogos de consulta.

## Preparación

Desde la carpeta `api`, con PostgreSQL y el entorno virtual preparados:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
.\.venv\Scripts\python.exe -m app.semillas
```

La revisión debe ser `0005_operaciones`. Reinicia Uvicorn si no usas `--reload`.
Abre http://127.0.0.1:8000/docs. Conserva los IDs devueltos; los ejemplos del contrato
son ilustrativos y no sustituyen los IDs de tu base.

## 1. Catálogos y datos iniciales

Ejecuta GET `/api/tipos-componentes`, `/api/ranuras`, `/api/controladores` y `/api/perfiles`.
En una instalación inicial deben devolver 14, 14, 3 y 4 registros, respectivamente.
GET `/api/robots/v001/versiones` conserva v0/v1; el inventario refleja la demanda de v1.

## 2. Componente y stock

POST `/api/componentes`:

```json
{"tipo_id":"enc","nombre":"Encoder CRUD","precio":35,"masa_g":2,"stock":1,"especificaciones":{"cpr":12,"tipo":"Magnético"}}
```

Espera 201 y guarda `id` como COMPONENTE. GET por ID debe devolverlo.
PATCH `/api/componentes/COMPONENTE` con `{"precio":40}` devuelve 200.
PUT `/api/inventario/COMPONENTE` con `{"stock":2,"revision":1}` devuelve revisión 2.
Repetir usando revisión 1 debe devolver 409 y conservar stock 2.
Un precio negativo, un campo desconocido o una especificación de otro tipo devuelve 422.

## 3. Robot y primera versión

POST `/api/robots`:

```json
{"nombre":"Robot CRUD","codigo_corto":"CRUD1","tipo":"velocista"}
```

Espera 201 y guarda `id` como ROBOT. Repetir el código corto devuelve 409.
PATCH `/api/robots/ROBOT` con `{"nombre":"Robot CRUD editado"}` debe persistir el cambio.
POST `/api/robots/ROBOT/versiones`:

```json
{"version_base_id":null,"nota":"Concepto de prueba","estado":"Concepto","piezas":{"mcu":{"componente_id":"c01","cantidad":1}}}
```

Espera 201, etiqueta v0 y guarda el ID numérico como VERSION.
GET del historial y GET de esa versión deben incluir la pieza y su instantánea.
Repetir con `version_base_id:null` debe devolver 409: hay una versión más reciente.
Para crear v1, envía el mismo objeto con `version_base_id` igual al ID de v0.
Un estado Actual requiere todas las ranuras obligatorias de GET `/api/ranuras`.
Los conceptos pueden estar incompletos; la falta de stock no impide guardarlos.

## 4. Setup

POST `/api/robots/ROBOT/setups`, sustituyendo VERSION por su entero real:

```text
{"version_id":VERSION,"nombre":"PID CRUD","controlador_id":"pid","parametros":{"kp":0.6,"ki":0,"kd":2.5,"base":45,"max":86}}
```

Espera 201 y guarda el ID como SETUP. GET por ID y listado de setups del robot deben
coincidir. Un kp=3, kp=0.605, max=20, una clave extra o un parámetro omitido devuelve
422. Una versión de otro robot devuelve 404. Guardar crea una configuración nueva;
no la aplica al firmware. Aplicarla al robot físico utiliza la ruta de comandos EN-02.

## 5. Corridas simuladas para verificar consultas

Carga opcionalmente una corrida de demostración:

```powershell
.\.venv\Scripts\python.exe -m app.demo
```

La salida informa CORRIDA. Repetir conserva la demo existente. Se marca `fuente: sim`.
GET `/api/corridas?fuente=sim` debe incluirla, con J=11.8 inicialmente.
GET `/api/corridas/CORRIDA/vueltas` devuelve dos vueltas y sus sectores/segmentos.
PATCH `/api/corridas/CORRIDA` con `{"nota":"Prueba completa"}` conserva esa nota.
Prueba los filtros robot_id, version_id, controlador_id, fuente y la paginación.
Las pruebas automatizadas cubren también corridas activas, que bloquean el archivado
de su robot/setup y devuelven 409 al consultar un resumen todavía sin cerrar.

## 6. Archivado e historial

DELETE `/api/setups/SETUP`, `/api/robots/ROBOT` y `/api/componentes/COMPONENTE` deben
responder 204 sin cuerpo. Repetir responde 204. Sus fichas permanecen consultables
por ID con `archivado:true`, pero desaparecen de los listados activos. El robot
archivado deja de aportar demanda; el componente con stock continúa en inventario.
Un ID inexistente responde 404. No se permite editar un robot/componente archivado
ni usar componentes archivados en nuevos armados.

## 7. Pruebas automáticas

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

Usan PostgreSQL en esquemas temporales; no insertan datos de prueba en tus tablas.
Cubren alta, consulta, edición, archivo, errores, snapshots, pasos/rangos, pertenencia,
reversión y dos escrituras simultáneas. Ruff y el validador del contrato completan la verificación.

## Pendientes fuera del CRUD REST

La consola aún necesita conectarse a estos endpoints. El gateway valida y redistribuye
telemetría; el ciclo que persiste automáticamente corridas físicas sigue pendiente.
Por eso la prueba de históricos utiliza la demo simulada. Mapas, autenticación y ejecución
de optimizadores no forman parte de las 32 operaciones de EN-01.

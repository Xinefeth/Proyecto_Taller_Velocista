# Prueba completa de la API

La API publica las 32 operaciones de EN-01. No todas las entidades admiten borrado físico:
DELETE archiva componentes, robots y setups; las versiones son históricas y se reemplazan
creando otra versión. Los tipos, ranuras, controladores y perfiles son catálogos de solo lectura.

Las rutas ya están en inglés; los cuerpos JSON conservan de momento sus claves en español
(el renombrado de campos sigue en curso, ver `docs/rename-glosario.md`). Los ejemplos usan las
claves tal como las acepta el backend hoy.

## Preparación

Desde la carpeta `api`, con PostgreSQL y el entorno virtual preparados:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\alembic.exe current
```

La revisión debe ser `0007_configuracion`. Reinicia Uvicorn si no usas `--reload`.
Abre http://127.0.0.1:8000/docs. Conserva los IDs devueltos; los ejemplos del contrato
son ilustrativos y no sustituyen los IDs de tu base.

## Datos de ejemplo (requisito)

La base **arranca vacía**: las migraciones solo crean el esquema, sin catálogo ni robots.
Los catálogos de solo lectura (tipos de componente, ranuras, controladores y perfiles) y el
robot de ejemplo `v001` **no tienen endpoint de alta**, así que sobre una base recién migrada
devuelven listas vacías y los POST que referencian catálogo responden 422/404.

Los pasos 1–5 asumen el **dataset de ejemplo** cargado (14 tipos, 14 ranuras, 3 controladores,
4 perfiles y el robot `v001` con sus versiones). Hoy ese dataset vive como fixture de
integración (`api/tests/integration/_seed.py`): es `pytest` quien lo siembra en esquemas
temporales y ejerce el recorrido completo (paso 7). Para probar a mano en Swagger necesitas
una base que ya contenga ese dataset.

## 1. Catálogos y datos iniciales

Ejecuta GET `/api/component-types`, `/api/slots`, `/api/controllers` y `/api/profiles`.
Con el dataset cargado deben devolver 14, 14, 3 y 4 registros, respectivamente; una base vacía
devuelve `[]`. GET `/api/robots/v001/versions` conserva v0/v1; GET `/api/inventory` refleja la
demanda de la versión actual (v1) de `v001`.

## 2. Componente y stock

POST `/api/components`:

```json
{"tipo_id":"enc","nombre":"Encoder CRUD","precio":35,"masa_g":2,"stock":1,"especificaciones":{"cpr":12,"tipo":"Magnético"}}
```

Espera 201 y guarda `id` como COMPONENTE. GET `/api/components/COMPONENTE` debe devolverlo.
PATCH `/api/components/COMPONENTE` con `{"precio":40}` devuelve 200.
PUT `/api/inventory/COMPONENTE` con `{"stock":2,"revision":1}` devuelve revisión 2.
Repetir usando revisión 1 debe devolver 409 y conservar stock 2.
Un precio negativo, un campo desconocido o una especificación de otro tipo devuelve 422.

## 3. Robot y primera versión

POST `/api/robots`:

```json
{"nombre":"Robot CRUD","codigo_corto":"CRUD1","tipo":"velocista"}
```

Espera 201 y guarda `id` como ROBOT. Repetir el código corto devuelve 409.
PATCH `/api/robots/ROBOT` con `{"nombre":"Robot CRUD editado"}` debe persistir el cambio.
POST `/api/robots/ROBOT/versions`:

```json
{"version_base_id":null,"nota":"Concepto de prueba","estado":"Concepto","piezas":{"mcu":{"componente_id":"c01","cantidad":1}}}
```

Espera 201, es la primera versión (ordinal 0, etiqueta `v0`); guarda el ID numérico como VERSION.
GET `/api/robots/ROBOT/versions` y GET `/api/robots/ROBOT/versions/VERSION` deben incluir la
pieza y su instantánea. Repetir con `version_base_id:null` debe devolver 409: hay una versión
más reciente. Para crear v1, envía el mismo objeto con `version_base_id` igual al ID de v0.
Un `estado` "Actual" requiere todas las ranuras obligatorias de GET `/api/slots` (el alta solo
admite `Actual`, `Concepto` o `Borrador`). Los conceptos pueden estar incompletos; la falta de
stock no impide guardarlos.

## 4. Setup

POST `/api/robots/ROBOT/setups`, sustituyendo VERSION por su entero real:

```text
{"version_id":VERSION,"nombre":"PID CRUD","controlador_id":"pid","parametros":{"kp":0.6,"ki":0,"kd":2.5,"base":45,"max":86}}
```

Espera 201 y guarda el ID como SETUP. GET `/api/setups/SETUP` y GET `/api/robots/ROBOT/setups`
deben coincidir. Un kp=3, kp=0.605, max=20, una clave extra o un parámetro omitido devuelve
422. Una versión de otro robot devuelve 404. Guardar crea una configuración nueva; no la aplica
al firmware. Aplicarla al robot físico usa POST `/api/robots/ROBOT/setups/SETUP/apply` (HU-17),
con el robot conectado; sin manifiesto responde 409 y el ack del robot llega por `/ws/consola`.

## 5. Corridas históricas para verificar consultas

Crea y guarda una corrida simulada con POST `/api/runs/simulated` (lo que la consola invoca al
ARRANCAR en modo Simulado). Espera 201, guarda el `id` como CORRIDA y queda marcada `fuente:sim`.
No es idempotente: cada llamada crea una corrida nueva. Usa el robot `v001` y el controlador
`pid` del dataset.

Alternativa determinista por script, desde `api`:

```powershell
.\.venv\Scripts\python.exe -m app.demo
```

Carga una única corrida de demostración idempotente (dos vueltas, J=11.8 en la mejor) e informa
CORRIDA; repetir conserva la demo existente. `python -m app.generador --corridas 40` puebla un
lote. Ambos scripts requieren `v001`, controladores y perfiles ya cargados.

GET `/api/runs?source=sim` debe incluir la corrida.
GET `/api/runs/CORRIDA/laps` devuelve las vueltas con sus sectores/segmentos.
PATCH `/api/runs/CORRIDA` con `{"nota":"Prueba completa"}` conserva esa nota.
Prueba los filtros `robot_id`, `version_id`, `controller_id`, `source` y la paginación.
Las pruebas automatizadas cubren también corridas activas (sin cerrar), que bloquean el
archivado de su robot/setup y devuelven 409 al pedir su detalle todavía sin cerrar.

## 6. Archivado e historial

DELETE `/api/setups/SETUP`, `/api/robots/ROBOT` y `/api/components/COMPONENTE` deben
responder 204 sin cuerpo. Repetir responde 204. Sus fichas permanecen consultables
por ID con `archivado:true`, pero desaparecen de los listados activos. El robot
archivado deja de aportar demanda; el componente con stock continúa en inventario.
Un ID inexistente responde 404. No se permite editar un robot/componente archivado
ni usar componentes archivados en nuevos armados.

## 7. Pruebas automáticas

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

Usan PostgreSQL en esquemas temporales; no insertan datos de prueba en tus tablas. Siembran el
dataset de ejemplo (fixture `tests/integration/_seed.py`) y cubren alta, consulta, edición,
archivo, errores, snapshots, pasos/rangos, pertenencia, reversión y dos escrituras simultáneas.
Ruff y el validador del contrato completan la verificación.

## Pendientes fuera del CRUD REST

La consola aún necesita conectarse a estos endpoints. El gateway valida y redistribuye
telemetría; el ciclo que persiste automáticamente corridas físicas sigue pendiente.
Por eso la prueba de históricos utiliza la corrida simulada. Mapas, autenticación y ejecución
de optimizadores no forman parte de las 32 operaciones de EN-01.

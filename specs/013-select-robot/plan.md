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

- `consola/src/datos/robots.ts`: catálogo de robots **local** (datos de prototipo).
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
| Lista robots con tipo, versión y firmware | **Parcial** | La API lo cumple (`GET /api/robots`). La **consola usa `datos/robots.ts` local y no consume el endpoint** todavía: falta la integración consola→API. |
| Paneles según sensores/actuadores; sin encoder no aparece | **Por verificar** | El manifiesto declara los dispositivos y `ManifiestoModal` los muestra; falta confirmar que los paneles se **ocultan dinámicamente** cuando el robot no declara ese dispositivo. |

## Pendientes conocidos

- Campos del manifiesto aún en **español** por el renombrado (`tipo_robot`, `sensores`,
  `actuadores`, `canales`, `controlador_activo`, `compensa_bateria`…). Ver
  `docs/rename-glosario.md`. Renombrarlos toca el **firmware** (contrato 2.0).
- El **ejemplo del manifiesto en Swagger** sale con **texto aleatorio** (lo genera el
  esquema). Existe un ejemplo real en `docs/contrato/ejemplos/velocista.manifiesto.json`
  que el endpoint no está usando como `example`.
- La respuesta **503** (base de datos no disponible) no está documentada en Swagger.
- Integración consola→API de robots pendiente (hoy la selección es sobre datos locales).

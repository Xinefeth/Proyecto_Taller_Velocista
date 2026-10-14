# Design Document — HU-13 · Seleccionar el robot

## Introduction

This feature bridges three existing parts of the system so the pilot can pick a robot and get a
view tailored to it: the **builder** module (robots and versions in PostgreSQL), the **catalog**
module (slots and component types that define which panels exist), and the **gateway** (the live
manifest of the connected robot). The console lists robots from the builder over REST, reads a
robot's current version to label it, and derives the visible panels from the sensors/actuators the
robot declares — from the live manifest when the robot is connected, or from the version's pieces
otherwise. Nothing new is persisted; this story composes existing read endpoints into a selection
flow and wires the console to consume the API instead of local fixtures.

## Goals & Non-Goals

**Goals**

- Expose the registered robots with type, firmware, and current version (builder REST).
- Expose a robot's declared devices (live manifest over REST; slots/component types for panels).
- Render only the panels for the devices a robot declares; hide the rest (e.g. no encoder panel).
- Consume the API for the production list with loading/empty/error-retry states and no local
  fallback.

**Non-Goals**

- Creating, editing, or archiving robots and versions — that is the builder story.
- Live telemetry (battery, link, loop, sensor strip) — HU-14/HU-15.
- Changing the manifest contract or the WebSocket message shapes.
- Renaming the Spanish manifest fields to English — tracked as cross-cutting debt (contract 2.0).

## Architecture Overview

The codebase is a modular monolith: DB-backed domain modules (`app.modulos.*`) and an in-memory
gateway (`app.gateway`). Selection is read-only: the builder and catalog serve robots/versions and
slots from PostgreSQL; the gateway serves the live manifest from memory. The console composes them.

```
                 Consola (selección de robot)
                     │  REST
          ┌──────────┼───────────────────────┐
          ▼          ▼                        ▼
┌── armador (DB) ──┐ ┌── catalogo (DB) ──┐ ┌── gateway (memoria) ──┐
│ GET /api/robots  │ │ GET /api/slots    │ │ GET /api/devices/      │
│ GET …/versions   │ │ tipos de componente│ │     velocista/manifest │
│ RobotSalida      │ │ ranuras → paneles │ │ manifiesto vivo        │
└──────────────────┘ └───────────────────┘ └────────────────────────┘
      models.py (robot, version, version_componente, ranura, tipo_componente, componente)
```

The console calls `api.robots.selection()` to page `/api/robots` and resolve each robot's current
version by id; it reads the manifest (or the version pieces) to compute the expected devices, and
renders one panel per declared device.

## Component Design

### 3.1 Endpoints (REST surface the console calls)

| Method | Path | operation_id | Module | Returns |
|---|---|---|---|---|
| GET | `/api/robots` | `listRobots` | armador | página de `RobotSalida` |
| GET | `/api/robots/{robot_id}` | `getRobot` | armador | `RobotSalida` |
| GET | `/api/robots/{robot_id}/versions` | `listRobotVersions` | armador | versiones |
| GET | `/api/robots/{robot_id}/versions/{version_id}` | `getRobotVersion` | armador | versión + piezas |
| GET | `/api/slots` | `listSlots` | catalogo | ranuras |
| GET | `/api/devices/velocista/manifest` | `getRacerManifest` | gateway | manifiesto vivo |

`RobotSalida` carries `id`, `nombre`, `codigo_corto`, `tipo`, `firmware`, `version_actual_id`,
`archivado`. The manifest carries `sensores`, `actuadores`, `canales`, `controladores`.

### 3.2 Deriving the panels

The visible panels are a function of the robot's declared devices, not a fixed list:

1. Load the robot's current version (`version_actual_id`) and its pieces.
2. Compute the expected devices (sensors/actuators) from the pieces and the component types
   (`app.modulos.catalogo`), or read them directly from the live manifest when connected.
3. Render one panel per declared device; a device absent from the declaration yields no panel.

Builder view and `ManifiestoModal` both derive panels from the **same** expected manifest computed
from the shown version's pieces, so the two stay consistent and update together when the robot or
its pieces change.

### 3.3 OpenAPI quality and the 503

- `getRacerManifest` uses the real contract example from
  `docs/contrato/ejemplos/velocista.manifiesto.json` as its 200 `example`, and declares
  `status_code=200` explicitly, so Swagger shows the real shape instead of schema-random text.
- Both the builder router and the gateway document a `503` response. The builder's `503` is
  `base_no_disponible` (DB down). The gateway does not query the DB; it keeps the `503` example for
  the link-drop case on its command endpoints and states this explicitly.

## Data Flow

### Selecting a robot

```
Consola ──GET /api/robots (paged)──▶ armador → [RobotSalida…]
   for each robot: GET /api/robots/{id}/versions/{version_actual_id} → label + pieces
Consola ── render list (tipo, versión, firmware) ──▶ pilot picks a robot
   expected devices = manifest(connected) OR devices(version pieces, catalog)
   render one panel per declared device; encoder absent → no encoder panel
```

### Reading the live manifest

```
Robot ──/ws/robot (first message: manifiesto)──▶ gateway (held in memory)
Consola ──GET /api/devices/velocista/manifest──▶ gateway → manifiesto vivo
```

## Design Decisions & Trade-offs

- **Compose existing read endpoints, add nothing new.** Selection is a read-only composition; no new
  table, migration, or write path is introduced.
- **Panels derived, never hard-coded.** Deriving panels from the declared devices (manifest or
  version pieces) is what makes "no encoder → no encoder panel" fall out for free and stay correct
  when the robot changes.
- **No local fallback in production.** The console shows loading/empty/error-retry and reads the API
  only; prototype fixtures (`consola/src/datos/robots.ts`) are injected solely in tests. Trade-off:
  the console shows an error instead of stale data when the API is down — intentional.
- **Spanish manifest fields kept.** Renaming to English touches the firmware (contract 2.0) and is
  out of scope here; tracked in `docs/rename-glosario.md`.

## Testing Strategy

**Unit / component tests (console):** builder and `ManifiestoModal` derive panels from the expected
manifest; robot without pieces, and switching between robots with/without an encoder, change the
panels; loading/empty/error-retry states render without local fallback.

**Integration tests (API, `requiere_db`):** CRUD of robots and versions against PostgreSQL
(`api/tests/integration/test_robot_bd.py`, skipped without a DB).

**Contract / gateway tests:** receiving the `manifiesto` over `/ws/robot` and reading it via
`GET /api/devices/velocista/manifest`; OpenAPI example identical to the real contract JSON.

## Correctness Properties

### Property 1: The robot list carries type, version, and firmware for every robot

For any set of registered robots, `GET /api/robots` returns exactly those robots, each with `tipo`,
`firmware`, and a resolvable `version_actual_id`.

**Validates: Requirements 1.1, 1.2**

### Property 2: Panels match the declared devices exactly

For any robot declaration (live manifest or version pieces), the rendered panels are exactly the
devices that declaration contains — no panel for an undeclared device (e.g. encoder), and one panel
per declared device.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: The production list never falls back to local fixtures

For any API response state (loading, empty, error), the console's production robot list reflects
that state (spinner / empty / error-retry) and never shows local prototype fixtures.

**Validates: Requirements 4.1, 4.2**

### Property 4: The manifest endpoint example equals the real contract JSON

The OpenAPI `example` of `getRacerManifest` is byte-equal in content to
`docs/contrato/ejemplos/velocista.manifiesto.json`.

**Validates: Requirements 2.2**

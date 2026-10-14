# Design Document — en-26-persistencia-flujo-principal (EN-26)

## Introduction

This enabler wires the console's main flow (catalog, builder, runs) to the API so the user data
lives in PostgreSQL instead of the browser. The database starts with only the reference structure
(types, slots, controllers, profiles), seeded by a migration; components, robots, versions, and
runs start empty and are created from the console through the API.

Before EN-26 the console read robots and simulated runs from the API but created robots, edited
builds, and registered components only in `localStorage` (see `logica/persistencia.ts`, explicitly
marked temporary pending T-21/T-22). The catalog came from bundled frontend files. EN-26 completes
that wiring for the vertical flow and removes the dependency on preloaded data.

## Goals & Non-Goals

**Goals**

- Seed only the reference structure by migration; keep the migration chain linear (single head).
- Persist component registration and read the catalog from the API (`POST`/`GET /components`).
- Persist robot creation (`POST /robots`) and render a usable empty state (no blank screen).
- Persist the robot build/version (`POST /robots/{id}/versions`) referencing DB components.
- Make the simulated run use the selected robot (`POST /runs/simulated?robot_id=…`), not a fixed one.
- Preserve the local/fixture behavior for tests.

**Non-Goals**

- Endpoints to create component types, slots, controllers, or profiles (they are reference data,
  seeded, read-only; out of scope).
- Persisting the live browser simulation lap-by-lap: the persisted run is the backend-generated
  simulated run for the selected robot's version.
- Rewriting the console's domain logic (`logica/dominio.ts`) or the inventory/edit flows beyond
  what the vertical flow needs.
- Updating the `docs/api/openapi.json` contract snapshot (belongs to the English-rename refactor).

## Architecture Overview

The codebase is a modular monolith: DB-backed domain modules (`app.modulos.*`) behind a FastAPI
surface, plus an in-memory gateway. The console (Vite SPA) is served by the API and talks to it
through `consola/src/services/api.ts`, the single HTTP layer.

```
         Consola (apiMode)                         API (FastAPI)                 PostgreSQL
  ┌───────────────────────────┐   REST   ┌──────────────────────────┐   SQLAlchemy  ┌──────────┐
  │ RegistroModal ─ crearComp.│ ───────▶ │ POST /components          │ ───────────▶ │componente│
  │ Catálogo      ─ catalog   │ ◀─────── │ GET  /components          │ ◀─────────── │inventario│
  │ Armador ─ crearRobot      │ ───────▶ │ POST /robots              │ ───────────▶ │ robot    │
  │ Armador ─ guardarVersion  │ ───────▶ │ POST /robots/{id}/versions│ ───────────▶ │version(+)│
  │ Control ─ arrancar(sim)   │ ───────▶ │ POST /runs/simulated?robot│ ───────────▶ │corrida,  │
  │ ProveedorConsola (gate)   │          │      _id=<seleccionado>   │              │vuelta    │
  └───────────────────────────┘          └──────────────────────────┘              └──────────┘
```

`apiMode = !initialRobots`: production renders without `initialRobots`, so the source is the API.
Tests inject `initialRobots`, keeping the local/`localStorage` path untouched.

## Backend

### Reference-structure seed (migration 0008)

- `api/migrations/versions/0008_referencia.py`, `down_revision = "0007_configuracion"`, so the
  chain is `0001→…→0005→0007→0008` with a single head.
- `upgrade()` bulk-inserts only `tipo_componente` (14), `ranura` (14), `controlador` (3),
  `perfil_reglamento` (4). `downgrade()` deletes those four tables.
- No components, robots, versions, or runs are inserted. The full historical dataset remains only
  as the test fixture `api/tests/integration/_seed.py`.

### Simulated run per selected robot

- `POST /api/runs/simulated` gains an optional `robot_id` query param (default `"v001"` for
  backward compatibility with existing tests).
- `service.crear_corrida_simulada(session, robot_id)` forwards it to
  `generador.crear_una_simulada(session, robot_id, rng=None)`, which uses
  `armador.robot_para_escritura(session, robot_id)` instead of a hardcoded `"v001"`. It still
  reuses the seeded `"pid"` controller and `"club"` profile, applied to the selected robot's
  current version. If the robot has no current version (or `pid`/`club` are missing), it raises a
  clear error.

### Reused endpoints (already present)

- `POST /components`, `GET /components` (catalog), `POST /robots`, `POST /robots/{id}/versions`,
  `GET /robots/{id}/versions/{version_id}`, `GET /runs/{id}/laps`. EN-26 only adds the console
  wiring and the `robot_id` param.

## Frontend

### HTTP layer (`services/api.ts`)

- `api.catalogo.listar()` → paginated `GET /components`, mapped to the console `Componente`
  (`tipo_id→t`, `nombre→nm`, `masa_g→masa`, `consumo_a→i`, `especificaciones→s`).
- `api.catalogo.crear(datos)` → `POST /components`, returns the mapped `Componente`.
- `api.robots.crear(datos)` → `POST /robots`.
- `api.robots.crearVersion(robotId, datos)` → `POST /robots/{id}/versions`.
- `api.robots.selection()` now also carries `verActualId` (= `version_actual_id`) so a build can
  send `version_base_id`.
- `api.corridas.crearSimulada(robotId)` → `POST /runs/simulated?robot_id=…`.

### Context (`stores/ConsolaContext.tsx`)

- `apiMode = !initialRobots`, exposed in the context.
- In apiMode, the catalog state is loaded from `api.catalogo.listar()` (effect keyed on a
  `catalogRequest` counter for refetch); `localStorage` persistence runs only in fixture mode.
- `crearComponente(datos)` → `api.catalogo.crear` + refetch; `crearRobot()` → `api.robots.crear` +
  refetch + select; `guardarVersion(robotId, versionBaseId, piezas, nota)` →
  `api.robots.crearVersion` + refetch.
- The provider gate `if (!robot)` renders a `PrimerRobot` empty state (message + "Crear primer
  robot" button calling `crearRobot`) instead of a dead-end paragraph.
- The Simulated start calls `api.corridas.crearSimulada(live.current.robotId)`.

### Screens

- `components/RegistroModal.tsx`: in apiMode, `guardar()` posts via `crearComponente` (sending only
  filled specs, since the API rejects empty strings in numeric fields); in fixture mode, local.
- `pages/Armador.tsx`: `nuevoRobot` and `guardar` (save version) use the API in apiMode; local path
  in fixture mode. Slot keys (`RANURAS[].k`) and type keys match the DB `ranura`/`tipo_componente`
  ids 1:1, so builds and registrations are accepted.

## Testing

- Backend: existing integration/unit suites (schema built from explicit migration lists + the
  `_seed` fixture) remain green. The full vertical flow was verified end-to-end against the real
  database via the FastAPI `TestClient` (7 components → robot → version with 7 pieces → simulated
  run with 8 laps).
- Frontend: `tsc -b`, full `vitest` suite, and `vite build` pass. Fixture-mode tests are unchanged;
  an apiMode test covers robot creation via the API.
- Known pre-existing failure outside this scope: `test_contrato_completo_registrado_en_fastapi`
  fails because `docs/api/openapi.json` is stale relative to the English-rename refactor; EN-26 did
  not change the operation set.

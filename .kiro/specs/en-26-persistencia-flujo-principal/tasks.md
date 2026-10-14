# Implementation Plan: en-26-persistencia-flujo-principal (EN-26)

## Overview

Wire the console's main flow (catalog, builder, runs) to the API so user data persists in
PostgreSQL, with the database seeded only with the reference structure. Backend changes: a
structure-only seed migration and a robot-scoped simulated run. Frontend changes: an API HTTP
layer for catalog/robots/versions, API-backed state in the context behind `apiMode`, an empty-robot
state, and the screen wiring. Fixture/local behavior is preserved for tests. The full vertical flow
was verified end-to-end against the real database.

All tasks below are complete ([x]).

## Tasks

- [x] 1. Seed only the reference structure (migration 0008)
  - [x] 1.1 Create `api/migrations/versions/0008_referencia.py`
    - `down_revision = "0007_configuracion"`; bulk-insert only `tipo_componente`, `ranura`,
      `controlador`, `perfil_reglamento`; `downgrade()` deletes those four tables
    - Generated from `api/tests/integration/_seed.py` constants; no component/robot/version/run
    - Verify the Alembic chain stays linear with a single head (`0008_referencia`)
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Make the simulated run use the selected robot (backend)
  - [x] 2.1 Add `robot_id` to the endpoint and thread it through
    - `POST /api/runs/simulated`: add `robot_id: Query(...) = "v001"` (default keeps tests working)
    - `service.crear_corrida_simulada(session, robot_id)` → `generador.crear_una_simulada(session, robot_id, rng)`
    - Use `armador.robot_para_escritura(session, robot_id)` instead of hardcoded `"v001"`; keep the
      seeded `"pid"` controller and `"club"` profile; raise a clear error if the robot has no
      current version
    - _Requirements: 5.1, 5.2, 5.4_

- [x] 3. HTTP layer for catalog, robots, and versions (`services/api.ts`)
  - [x] 3.1 Catalog methods and types
    - Add `ComponenteApi`, `PaginaComponentes` to `types/api.ts`; add `aComponente` mapper
    - `api.catalogo.listar()` (paginated `GET /components`) and `api.catalogo.crear(datos)` (`POST`)
    - _Requirements: 2.1, 2.2_
  - [x] 3.2 Robot creation, version creation, and run-by-robot
    - `api.robots.crear(datos)` → `POST /robots`; `api.robots.crearVersion(robotId, datos)` → `POST /robots/{id}/versions`
    - `api.robots.selection()` carries `verActualId` (from `version_actual_id`); add `verActualId?`
      to `RobotDef`
    - `api.corridas.crearSimulada(robotId)` → `POST /runs/simulated?robot_id=…`
    - _Requirements: 3.2, 4.1, 5.1_

- [x] 4. API-backed state in the context (`stores/ConsolaContext.tsx`)
  - [x] 4.1 apiMode and catalog from the API
    - `apiMode = !initialRobots`, exposed in the context
    - Catalog state initialized empty in apiMode and loaded via `api.catalogo.listar()` (effect
      keyed on `catalogRequest`); `localStorage` persistence guarded to fixture mode
    - _Requirements: 2.2, 6.2_
  - [x] 4.2 Create/persist actions
    - `crearComponente`, `crearRobot`, `guardarVersion` (each posts to the API and refetches);
      exposed in the `Consola` type and value
    - _Requirements: 2.1, 3.2, 4.1, 4.2_
  - [x] 4.3 Empty-robot state
    - Replace the `if (!robot)` dead-end with a `PrimerRobot` component (keeps the "No hay robots…"
      text, adds a "Crear primer robot" button → `crearRobot`)
    - _Requirements: 3.1_
  - [x] 4.4 Run the selected robot
    - Simulated start calls `api.corridas.crearSimulada(live.current.robotId)`
    - _Requirements: 5.1_

- [x] 5. Screen wiring
  - [x] 5.1 Register component (`components/RegistroModal.tsx`)
    - In apiMode, `guardar()` posts via `crearComponente`, sending only filled specs (the API
      rejects empty strings in numeric fields); fixture mode keeps the local path
    - _Requirements: 2.1, 2.4, 6.2_
  - [x] 5.2 Create and build robot (`pages/Armador.tsx`)
    - `nuevoRobot` and the save-version `guardar` use the API in apiMode (`crearRobot`,
      `guardarVersion`); fixture mode keeps the local path
    - _Requirements: 3.2, 4.1, 4.3, 6.2_

- [x] 6. Verification
  - [x] 6.1 Backend and frontend checks
    - Backend suite green except the pre-existing `openapi.json` snapshot test (out of scope);
      frontend `tsc -b`, `vitest`, and `vite build` pass; slot/type keys match DB ids 1:1
    - _Requirements: 6.2_
  - [x] 6.2 End-to-end flow against the real database
    - Verified via `TestClient`: 7 components → robot → version (7 pieces) → simulated run tied to
      the created robot → 8 laps persisted and retrievable; DB left clean (structure only)
    - _Requirements: 2.1, 3.2, 4.2, 5.2, 5.3, 6.1, 6.3_

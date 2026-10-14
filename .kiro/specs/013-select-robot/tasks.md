# Implementation Plan — HU-13 · Seleccionar el robot

## Overview

The feature composes existing read endpoints into a robot-selection flow and derives the console
panels from each robot's declared devices. It touches four areas: the **builder** endpoints (robots
and versions), the **catalog** endpoint (slots/component types for panels), the **gateway** manifest
endpoint (live declaration + OpenAPI quality), and the **console** (consume the API, hide undeclared
panels, no local fallback). No new DB tables or migrations.

`[x]` marks work already done and verified in the code; `[ ]` marks pending work. Tasks marked `*`
are optional (property/integration tests that need PostgreSQL or a real robot).

## Tasks

- [x] 1. Builder endpoints for robots and versions
  - [x] 1.1 `GET /api/robots` lists robots with `tipo`, `firmware`, current version — `api/app/modulos/armador/router.py`
  - [x] 1.2 Version endpoints (`GET /api/robots/{id}/versions`, `.../{version_id}`) — `api/app/modulos/armador/router.py`
  - [x] 1.3 Quality OpenAPI (summary/description/responses) on the selection endpoints — `api/app/modulos/armador/router.py`
  - [x] 1.4 Document the `503` `base_no_disponible` response — builder router (verified: 26 tests)
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Catalog + gateway device declaration
  - [x] 2.1 `GET /api/slots` (armador slots that define panels) — `api/app/modulos/armador/router.py`
  - [x] 2.2 `GET /api/devices/velocista/manifest` (live panels source) — `api/app/gateway/comandos.py`
  - [x] 2.3 Use the real `docs/contrato/ejemplos/velocista.manifiesto.json` as the 200 `example`; declare `status_code=200` — `api/app/gateway/comandos.py` (verified: 12 tests, OpenAPI == contract JSON)
  - _Requirements: 2.1, 2.2, 2.3_

- [x] 3. Console: consume the API for selection
  - [x] 3.1 `api.robots.selection()` pages `/api/robots` and resolves each robot's current version by id — production list from API only, with loading/empty/error-retry, no local fallback (verified: 120 tests, TS + ESLint clean)
  - [x] 3.2 Manifest modal shows the robot's declaration — `consola/src/components/ManifiestoModal.tsx`
  - _Requirements: 1.1, 1.2, 4.1, 4.2_

- [x] 4. Console: derive panels from the declared devices
  - [x] 4.1 Builder view and `ManifiestoModal` derive panels from the expected manifest (version pieces / live manifest); undeclared device → no panel (verified: 39 tests incl. robot without pieces and encoder on/off)
  - _Requirements: 3.1, 3.2, 3.3_

- [ ] 5. Cross-cutting rename (migration in progress — requires confirmation)
  - [ ] 5.1 Manifest fields to English (`tipo_robot→robot_type`, `sensores→sensors`, …) — contract 2.0, touches firmware — `api/app/contract/manifest.py`, `firmware/`
  - _See `docs/rename-glosario.md`; not executed in this revision._

- [ ]* 6. Verify robot/version CRUD against PostgreSQL
  - [ ]* 6.1 Run `api/tests/integration/test_robot_bd.py` with a live DB (today skipped) — needs `docker compose up -d db`, migrations, and `.env` credentials
  - _Requirements: 1.1 (end-to-end persistence)_

## Notes

- `[x]` tasks are verified in the current code; `[ ]` tasks are pending and the two at the end need
  user confirmation (DB environment / contract 2.0 rename) per the original `plan.md`.
- No new DB tables or migrations: robots, versions, slots, and component types already exist.
- Panels are derived from the declared devices, never hard-coded, so "no encoder → no panel" holds
  automatically.
- The console reads the API exclusively for the production list; prototype fixtures are test-only.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "2.3"] },
    { "id": 1, "tasks": ["3.1", "3.2"] },
    { "id": 2, "tasks": ["4.1"] },
    { "id": 3, "tasks": ["5.1", "6.1"] }
  ]
}
```

# Implementation Plan: configurar-controlador (HU-17)

## Overview

The feature adds a "configure and apply controller" workflow to the API: a reconciled controller
catalog (DB catalog overlaid with live manifest values), a live-configuration view, and a
single-action apply for saved setups and catalog presets. The implementation touches four areas:

1. **Pydantic schemas** — seven new response/request contracts in `optimizacion/schemas.py`.
2. **Contract validation** — a `check_setup_completo` sibling to the existing `check_setup` in
   `contract/validation.py` (additive, does not modify the raw command path).
3. **Gateway apply port** — a new `app/gateway/aplicacion.py` with `manifiesto_velocista()` and
   `aplicar_setup_velocista()`, reusing `validar_comando` + `ws.send` and layering the
   apply-specific completeness check and delivery-failure handling.
4. **Optimizacion service + router** — `reconciliar_catalogo`, `configuracion_viva`,
   `aplicar_setup`, `aplicar_preset` in `service.py`, and four new endpoints in `router.py`.

No new DB tables or migrations. The design specifies 12 correctness properties, each tested with
property-based tests (Hypothesis, min 100 iterations) alongside unit and integration tests.

## Tasks

- [x] 1. Set up foundation: schemas, contract validation, and test infrastructure
  - [x] 1.1 Add new Pydantic schemas to `app/modulos/optimizacion/schemas.py`
    - Add `ParametroReconciliado` (extends `ParametroControlador` with optional `valor: float | None`)
    - Add `ControladorReconciliado` (id, nombre, nombre_corto, descripcion, parametros, presets, activo)
    - Add `CatalogoReconciliado` (controlador_activo: str | None, controladores: list)
    - Add `ParametroVivo` (nombre: str, valor: float) and `ConfiguracionViva` (controlador_activo, parametros)
    - Add `PresetAplicar` (controlador_id, preset_id) and `ComandoAceptado` (seq, mensaje)
    - All with `ConfigDict(extra="forbid", allow_inf_nan=False)`; `ComandoAceptado` mirrors the gateway `CommandAccepted`
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 4.1, 5.1_

  - [x] 1.2 Add `check_setup_completo` to `app/contract/validation.py`
    - Sibling to existing `check_setup`; does NOT modify `check_setup`
    - First checks controller exists (→ `controlador_no_disponible`)
    - Then checks every controller parameter is present in the setup (→ `parametro_desconocido` for missing)
    - Then delegates per-value existence/range/type to `check_setup` (→ `fuera_de_rango`)
    - Returns `tuple[str, str] | None`
    - _Requirements: 4.5_

  - [x] 1.3 Add Hypothesis to dev dependencies in `api/pyproject.toml`
    - Add `"hypothesis>=6.100"` to `[project.optional-dependencies].dev`
    - Install into the virtual environment (`api/.venv`)
    - _Requirements: 3.3, 3.4_ (enables property-based validation tests)

- [x] 2. Implement the gateway apply port
  - [x] 2.1 Create `app/gateway/aplicacion.py`
    - Implement `manifiesto_velocista(robot_id) -> Manifest | None`: returns the live manifest only if the
      connected velocista's manifest `id` matches `robot_id` (different robot → None)
    - Implement `async aplicar_setup_velocista(robot_id, controlador, parametros, id_setup) -> int`:
      1. Verify connection + manifest + manifest.id == robot_id (→ 409 `sin_manifiesto`)
      2. Call `validar_comando("velocista", "setup", {...}, manifest, last_status)` (→ 409 `bloqueado_competencia`)
      3. Call `check_setup_completo(manifest, modelo)` (→ 422 `controlador_no_disponible` / `parametro_desconocido` / `fuera_de_rango`)
      4. `await ws.send("velocista", "setup", ...)` wrapped in try/except (→ 503 `dispositivo_no_disponible`)
      5. Return the `seq`
    - Reuse `validar_comando` from `app.gateway.comandos`, `ws.send` and `ws.connections` from `app.gateway.ws`
    - _Requirements: 6.1, 6.2, 6.3, 4.2, 4.3, 4.4, 4.5, 5.2, 5.3_

  - [ ]* 2.2 Write unit tests for the gateway apply port
    - Test `manifiesto_velocista`: returns manifest when robot matches, None when disconnected / different robot / no manifest
    - Test `aplicar_setup_velocista`: guards fire before send (assert `ws.send` not called on guard failure);
      `dispositivo_no_disponible` when a fake `ws.send` raises `KeyError`/`RuntimeError`/`OSError`
    - Mock `ws.connections` with in-memory fixtures; use the example manifest from `docs/contrato/ejemplos`
    - _Requirements: 6.1, 6.2, 6.3_

  - [ ]* 2.3 Write property test for apply validation against the live manifest
    - **Property 9: Apply validates the configuration against the live manifest with precise reasons**
    - **Validates: Requirements 4.2, 4.3, 4.4, 4.5, 5.2, 5.3**
    - Generate configurations (controller present/absent, parameters complete/incomplete, values in/out of range,
      correct/wrong type); assert the apply is accepted iff all constraints hold, else rejected before send
      with the precise reason (`controlador_no_disponible`, `parametro_desconocido`, `fuera_de_rango`)

  - [ ]* 2.4 Write property test for pre-send state guards
    - **Property 11: Pre-send state guards reject without delivering a command**
    - **Validates: Requirements 6.1, 6.2**
    - Assert: no matching manifest → `sin_manifiesto` with zero sends; competition + running →
      `bloqueado_competencia` with zero sends; mock `ws.send` to assert call count is 0 in both cases

  - [ ]* 2.5 Write property test for link-drop delivery failure
    - **Property 12: A link drop between validation and delivery surfaces dispositivo_no_disponible**
    - **Validates: Requirements 6.3**
    - Assert: apply that passes validation but whose `ws.send` raises returns `dispositivo_no_disponible`
      (503), allowing retry

- [x] 3. Implement the reconciled-catalog service
  - [x] 3.1 Implement `reconciliar_catalogo(session, robot_id)` in `app/modulos/optimizacion/service.py`
    - Load all DB controllers via existing `listar_controladores(session)` (source of truth for the list)
    - Call `gateway.aplicacion.manifiesto_velocista(robot_id)` (Manifest or None)
    - For each DB controller `c`: match `manifiesto.controlador(c.id)` (DB id == manifest nombre);
      set `activo = manifiesto and manifiesto.controlador_activo == c.id`
    - For each DB parameter `p`: match manifest parameter by `p.clave == m_param.nombre`;
      overlay `valor = m_param.valor` only on match, else `None`
    - Return `CatalogoReconciliado(controlador_activo=manifiesto.controlador_activo if manifiesto else None, ...)`
    - Mismatches (e.g. DB `adapt` vs manifest `pid_adaptativo`) surface as "no live value", never an error
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 3.2 Write unit tests for reconciled-catalog reconciliation
    - Test overlay applied only on match (controller id == nombre, parameter clave == nombre)
    - Test offline / different robot: no `valor`, `controlador_activo` is null, catalog ranges/presets intact
    - Test `activo` flag set only for the manifest's `controlador_activo`
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 3.3 Write property test for reconciled-catalog completeness
    - **Property 1: Reconciled catalog always contains every catalog controller with its definitions**
    - **Validates: Requirements 1.1**
    - For any DB catalog and robot state, assert exactly one entry per catalog controller, each preserving
      catalog `min`, `max`, `paso`, and `presets`

  - [ ]* 3.4 Write property test for live-value overlay rules
    - **Property 2: Live values are overlaid only from a matching manifest and never when offline**
    - **Validates: Requirements 1.2, 1.3**
    - Assert `valor` and `activo` appear only when manifest exists and ids/names match; when offline or a
      different robot is connected, no `valor` and `controlador_activo` is null

- [x] 4. Implement the live-configuration service
  - [x] 4.1 Implement `configuracion_viva(robot_id)` in `app/modulos/optimizacion/service.py`
    - Call `gateway.aplicacion.manifiesto_velocista(robot_id)`
    - If None → raise `ErrorDeNegocio(404, "sin_manifiesto", ...)`
    - `ctrl = manifiesto.controlador(manifiesto.controlador_activo)`
    - Return `ConfiguracionViva(controlador_activo=..., parametros=[{nombre: p.nombre, valor: p.valor} ...])`
    - Sync function (reads in-memory `connections` dict, no `await`)
    - _Requirements: 2.1, 2.2_

  - [ ]* 4.2 Write unit tests for live configuration
    - Test round-trip: response has `controlador_activo` from manifest, one `{nombre, valor}` per active
      controller parameter
    - Test `sin_manifiesto` error when robot offline / different robot / no manifest
    - _Requirements: 2.1, 2.2_

  - [ ]* 4.3 Write property test for current-config round-trip
    - **Property 3: Current configuration round-trips the active controller from the manifest**
    - **Validates: Requirements 2.1**
    - For any live manifest whose `id` matches `robot_id`, assert `controlador_activo` equals the manifest's
      and one parameter per controller parameter with matching `valor`

  - [ ]* 4.4 Write property test for current-config sin_manifiesto
    - **Property 4: Current configuration returns sin_manifiesto without a live manifest**
    - **Validates: Requirements 2.2**
    - For any state where `manifiesto_velocista(robot_id)` is None, assert the endpoint returns `sin_manifiesto`

- [x] 5. Implement the apply-setup and apply-preset service
  - [x] 5.1 Implement `aplicar_setup` and `aplicar_preset` in `app/modulos/optimizacion/service.py`
    - `async aplicar_setup(session, robot_id, setup_id)`:
      1. `setup = obtener_setup(session, setup_id)` (→ 404 `setup_no_encontrado`)
      2. `seq = await gateway.aplicacion.aplicar_setup_velocista(robot_id, setup.controlador_id, setup.parametros, setup.id)`
      3. Return `ComandoAceptado(seq=seq)` (id_setup = setup.id)
    - `async aplicar_preset(session, robot_id, controlador_id, preset_id)`:
      1. `ctrl = session.get(Controlador, controlador_id)` (→ 404 `controlador_no_encontrado`)
      2. `valores = ctrl.presets.get(preset_id)` (→ 422 `preset_no_encontrado`)
      3. `seq = await gateway.aplicacion.aplicar_setup_velocista(robot_id, controlador_id, valores, id_setup=None)`
      4. Return `ComandoAceptado(seq=seq)` (id_setup = null)
    - _Requirements: 3.5, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3_

  - [ ]* 5.2 Write unit tests for the apply service
    - Test with a fake `ws.send`: command carries `id_setup` = setup.id (setup apply) and `None` (preset apply)
    - Test guards fire before send (assert `ws.send` call count is 0 on `sin_manifiesto` / `bloqueado_competencia`)
    - Test `dispositivo_no_disponible` when fake `send` raises; test `setup_no_encontrado` / `controlador_no_encontrado`
    - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3_

  - [ ]* 5.3 Write property test for apply requiring a persisted setup id
    - **Property 8: Applying requires a persisted setup id**
    - **Validates: Requirements 3.5**
    - Assert: apply with a non-existent `setup_id` is rejected with `setup_no_encontrado` and no command sent

  - [ ]* 5.4 Write property test for apply command carrying the source's id_setup
    - **Property 10: Apply sends the setup command with the source's controlador, parameters, and id_setup**
    - **Validates: Requirements 4.1, 5.1**
    - Assert: accepted setup-apply sends `id_setup` = setup.id; accepted preset-apply sends `id_setup` = null;
      both carry the source's `controlador` and `parametros`

- [x] 6. Wire the four new endpoints in the optimizacion router
  - [x] 6.1 Add endpoints to `app/modulos/optimizacion/router.py`
    - `GET /api/robots/{robot_id}/controllers` → `service.reconciliar_catalogo` → `CatalogoReconciliado`
    - `GET /api/robots/{robot_id}/configuracion` → `service.configuracion_viva` → `ConfiguracionViva`
    - `POST /api/robots/{robot_id}/setups/{setup_id}/apply` → `service.aplicar_setup` → `ComandoAceptado` (status 202)
    - `POST /api/robots/{robot_id}/presets/apply` → `service.aplicar_preset` → `ComandoAceptado` (status 202, body `PresetAplicar`)
    - Reuse existing `DbSession`, `RobotId`, `SetupId` annotations; add `operation_id` for each
    - Apply endpoints are `async def` (they `await` the gateway); catalog/config endpoints are sync
    - Document error responses via `error_responses(...)` (sin_manifiesto, bloqueado_competencia, etc.)
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.2, 4.1, 5.1_

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Hecho: 69 pruebas sin BD pasan (unit/contract/websocket), incluida la de arquitectura;
    ruff limpio. Las de integración requieren PostgreSQL (no levantado en este entorno).

- [ ] 8. Add property tests for existing save/list/validation functionality
  - [ ]* 8.1 Write property test for setup create→get round-trip
    - **Property 5: Setup create→get round-trip preserves controlador and parameters**
    - **Validates: Requirements 3.1**
    - For valid parameter values satisfying catalog constraints, assert creating then fetching by id returns
      the same `controlador_id`, `nombre`, and `parametros` (requires DB session)

  - [ ]* 8.2 Write property test for listing setups
    - **Property 6: Listing setups returns exactly the saved, non-archived setups of the robot**
    - **Validates: Requirements 3.2**
    - For a robot with saved setups (some archived), assert listing returns exactly the non-archived setups tied
      to that robot, ordered by `creado_en` descending (requires DB session)

  - [ ]* 8.3 Write property test for save validation with precise reasons
    - **Property 7: Save validation accepts iff constraints hold and rejects with the precise reason**
    - **Validates: Requirements 3.3, 3.4**
    - For any controller definition and parameter values, assert accept iff within range, step-aligned,
      `max >= base`, `vmin <= base`; else reject with `fuera_de_rango`, `paso_invalido`, or
      `parametros_incompatibles` (pure function, no DB)

- [ ] 9. Add integration tests for the full apply/reconcile flow
  - [ ]* 9.1 Write integration test for setup apply round-trip
    - Create a setup in the DB, apply it against a manifest fixture (mock `ws.connections`), assert the command
      carries `id_setup` = setup.id and returns `ComandoAceptado`; use `requiere_db` fixture
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 9.2 Write integration test for catalog reconciliation end-to-end
    - Seed the DB catalog, connect a robot with a manifest fixture, call `GET /api/robots/{r}/controllers`,
      assert overlay and `controlador_activo`; use `requiere_db` fixture
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 9.3 Write integration test for preset apply end-to-end
    - Apply a catalog preset against a manifest fixture, assert `id_setup` = null and `ComandoAceptado`;
      use `requiere_db` fixture
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (12 properties from the design, min 100 iterations each)
- Unit tests validate specific examples and edge cases with the example manifest fixture
- Integration tests require PostgreSQL (`requiere_db` fixture) and exercise the full router→service→gateway path
- The design uses Python throughout (FastAPI + Pydantic + SQLAlchemy); no language selection needed
- `check_setup_completo` is additive — it does NOT modify the existing `check_setup` or the raw command path
- The gateway port (`aplicacion.py`) is the only place optimizacion reaches into the gateway; it reuses
  `validar_comando` and `ws.send` rather than duplicating their logic
- No new DB tables or migrations: controllers and setups already exist in the optimizacion module


## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "8.1", "8.2", "8.3"] },
    { "id": 2, "tasks": ["3.1", "2.2", "2.3", "2.4", "2.5"] },
    { "id": 3, "tasks": ["4.1", "3.2", "3.3", "3.4"] },
    { "id": 4, "tasks": ["5.1", "4.2", "4.3", "4.4"] },
    { "id": 5, "tasks": ["6.1", "5.2", "5.3", "5.4"] },
    { "id": 6, "tasks": ["9.1", "9.2", "9.3"] }
  ]
}
```

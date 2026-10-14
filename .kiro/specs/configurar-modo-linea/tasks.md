# Implementation Plan: configurar-modo-linea (HU-18)

## Overview

The feature lets the pilot choose the robot's functioning mode (`prueba`/`competencia`) and the
track line color (`negra`/`blanca`) through two dedicated, higher-level gateway endpoints, plus a
read endpoint that returns the current `modo`/`linea` from the robot's last `Status`. Mode and line
are pure device commands with no database footprint, so everything lives in one new gateway module
`app/gateway/configuracion.py` that reuses the existing `validar_comando` + `ws.send` machinery.

The implementation touches three areas:

1. **Foundation** — create `app/gateway/configuracion.py` with a new router (prefix `/api/devices`,
   tag `devices`), three loose Pydantic request/response models (`ConfigViva`, `CambioModo`,
   `CambioLinea`), the new `validar_cambio_config` helper (the `ocupado` guard for
   `prueba`+`running`), and add Hypothesis for property-based tests.
2. **Endpoints** — the sync read `GET /api/devices/velocista/config` (`sin_estado` guard) and the
   two async writes `POST .../config/modo` and `POST .../config/linea` (full guard ordering:
   `comando_invalido` → `sin_manifiesto` → `comando_desconocido` → `bloqueado_competencia` →
   `ocupado` → `dispositivo_no_disponible`), reusing `CommandAccepted` and `validar_comando` from
   `comandos.py`.
3. **Wiring + tests** — register `configuracion.router` in `app/main.py`; add unit tests, the 7
   correctness properties as property-based tests, and integration tests driving the full guard
   matrix end-to-end through the FastAPI `TestClient`.

No new DB tables or migrations. `validar_comando` is reused unchanged; only `validar_cambio_config`
is new and local to this feature. The design specifies 7 correctness properties, each tested with
property-based tests (Hypothesis, min 100 iterations) alongside unit and integration tests.

## Tasks

- [x] 1. Set up foundation: gateway module, models, the ocupado guard, and test infrastructure
  - [x] 1.1 Create `app/gateway/configuracion.py` with router and Pydantic models
    - Create `app/gateway/configuracion.py`; add `router = APIRouter(prefix="/api/devices", tags=["devices"])`
      matching the existing `comandos.py` prefix/tag
    - Add `ConfigViva(BaseModel)` with `model_config = ConfigDict(extra="forbid", allow_inf_nan=False)`
      and `modo: Literal["prueba", "competencia"]`, `linea: Literal["negra", "blanca"]`
    - Add `CambioModo(BaseModel)` with `model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"modo": "prueba"}})`
      and `modo: Any = Field(default=None, description="...", examples=["prueba", "competencia"])`
    - Add `CambioLinea(BaseModel)` with `model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"color": "negra"}})`
      and `color: Any = Field(default=None, description="...", examples=["negra", "blanca"])`
    - Import `ws` from `app.gateway`, `validar_comando` and `CommandAccepted` from `app.gateway.comandos`,
      `Status` from `app.contract.robot`, and `ErrorDeNegocio`, `error_responses` from `app.core.errores`
    - Loose `Any` fields (with `None` default) are intentional so invalid values route through
      `validar_comando` → `comando_invalido` instead of a generic FastAPI 422
    - _Requirements: 1.1, 2.1, 2.2, 3.1, 3.2_

  - [x] 1.2 Implement `validar_cambio_config` helper in `app/gateway/configuracion.py`
    - Sibling guard to `validar_comando`; do NOT modify `validar_comando`
    - `def validar_cambio_config(ultimo_estado: Status | None) -> None`
    - Raise `ErrorDeNegocio(409, "ocupado", "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea")`
      when `ultimo_estado and ultimo_estado.estado == "running" and ultimo_estado.modo == "prueba"`
    - Otherwise return `None` (no raise): `competencia`+`running` is already blocked by `validar_comando`
      with `bloqueado_competencia`, and all non-running estados / `None` pass
    - Explicit check on `modo == "prueba"` keeps the helper self-contained and unit-testable in isolation
    - _Requirements: 4.2, 4.3_

  - [x] 1.3 Add Hypothesis to dev dependencies in `api/pyproject.toml`
    - Add `"hypothesis>=6.100"` to `[project.optional-dependencies].dev`
    - Install into the virtual environment (`api/.venv`)
    - _Requirements: 2.2, 3.2, 4.1, 4.2, 4.4, 4.5, 4.6_ (enables property-based validation tests)

- [x] 2. Implement the read endpoint
  - [x] 2.1 Implement `get_robot_config` in `app/gateway/configuracion.py`
    - `@router.get("/velocista/config", response_model=ConfigViva, operation_id="getRobotConfig", ...)`
      with sync `def get_robot_config() -> ConfigViva`
    - `connection = ws.connections.get("velocista")`; if `connection is None or connection.last_status is None`
      → raise `ErrorDeNegocio(404, "sin_estado", "El robot aún no ha enviado su estado")`
    - Else return `ConfigViva(modo=connection.last_status.modo, linea=connection.last_status.linea)`
    - Document the `404 sin_estado` response via `error_responses(...)` (mirrors the existing
      `404 sin_manifiesto` of `GET /api/devices/velocista/manifest`)
    - Read is sync: it only touches the in-memory `connections` dict, no `await`
    - _Requirements: 1.1, 1.2_

  - [x] 2.2 Write unit tests for the read endpoint
    - New `tests/unit/test_configuracion.py`; test `get_robot_config` directly with an in-memory
      `ws.connections` fixture (set/restore `ws.connections["velocista"]`)
    - Returns `modo`/`linea` equal to `connection.last_status.modo`/`.linea` when a `Status` exists
    - Raises `sin_estado` when `connection is None` and when `connection.last_status is None` (two cases)
    - _Requirements: 1.1, 1.2_

  - [x] 2.3 Write property test for the read projection
    - **Property 1: Read projects the live status, or returns sin_estado**
    - **Validates: Requirements 1.1, 1.2**
    - Generate arbitrary `velocista` connection states (no connection, connection with no `last_status`,
      connection with a random `Status`); assert the response equals the live `modo`/`linea` when a
      `Status` exists and `sin_estado` when the connection is `None` or `last_status` is `None`

- [x] 3. Implement the write endpoints (mode and line)
  - [x] 3.1 Implement `set_mode` in `app/gateway/configuracion.py`
    - `@router.post("/velocista/config/modo", status_code=202, response_model=CommandAccepted, operation_id="setMode", ...)`
      with `async def set_mode(body: CambioModo) -> CommandAccepted`
    - `connection = ws.connections.get("velocista")`; `manifest = connection.manifest if connection else None`;
      `last_status = connection.last_status if connection else None`
    - `model = validar_comando("velocista", "modo", {"modo": body.modo}, manifest, last_status)`
      (shared guards: `comando_invalido` → `sin_manifiesto` → `comando_desconocido` → `bloqueado_competencia`)
    - `validar_cambio_config(last_status)` (new `ocupado` guard, after `validar_comando`)
    - `seq = await ws.send("velocista", "modo", model.model_dump(exclude_none=True))` wrapped in
      `try/except (KeyError, RuntimeError, OSError)` → raise `ErrorDeNegocio(503, "dispositivo_no_disponible", ...)`
    - `return CommandAccepted(seq=seq)`
    - Document write error responses via a shared `CONFIG_RESPONSES` built once with `error_responses(...)`
      for `comando_invalido`, `sin_manifiesto`, `comando_desconocido`, `bloqueado_competencia`, `ocupado`,
      `dispositivo_no_disponible`
    - _Requirements: 2.1, 2.2, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 3.2 Implement `set_line` in `app/gateway/configuracion.py`
    - Same structure as `set_mode` with `operation_id="setLine"`, body `CambioLinea`, tipo `"linea"`,
      payload `{"color": body.color}`, and the same shared `CONFIG_RESPONSES`
    - `model = validar_comando("velocista", "linea", {"color": body.color}, manifest, last_status)`;
      then `validar_cambio_config(last_status)`; then `ws.send(...)` with the same `dispositivo_no_disponible` catch
    - `return CommandAccepted(seq=seq)`
    - _Requirements: 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 3.3 Write unit tests for the write endpoints
    - In `tests/unit/test_configuracion.py`; call `set_mode`/`set_line` directly with mocked `ws.send`
      (e.g. an `AsyncMock` capturing args) and an in-memory `ws.connections`
    - Valid value sends exactly one command with the right shape `("velocista", "modo", {"modo": <value>})`
      / `("velocista", "linea", {"color": <value>})` and returns the captured `seq`
    - Every guard failure sends nothing: assert `ws.send` call count is 0 on `comando_invalido`,
      `sin_manifiesto`, `comando_desconocido`, `bloqueado_competencia`, and `ocupado`
    - `dispositivo_no_disponible` (503) when the fake `send` raises `KeyError`/`RuntimeError`/`OSError`
    - Use the example manifest fixture from `docs/contrato/ejemplos` for a declaring manifest
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 4. Wire the router in the application
  - [x] 4.1 Register `configuracion.router` in `app/main.py`
    - Add `from app.gateway import configuracion` alongside the existing `from app.gateway import comandos, ws`
    - Add `app.include_router(configuracion.router)` next to `app.include_router(comandos.router)`
    - Two routers share the same `/api/devices` prefix/tag; paths do not collide
    - _Requirements: 1.1, 2.1, 3.1_

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Add property-based tests for the write endpoints
  - [x] 6.1 Write property test for valid change delivery
    - **Property 2: A valid change sends the matching command and returns its seq, for any non-running estado**
    - **Validates: Requirements 2.1, 3.1, 4.3**
    - Generate valid `modo`/`linea` and `estado` in `ready`/`stopped`/`calibrating`/`error` with a manifest
      declaring the command; assert exactly one `ws.send` with the matching shape and the returned `seq`
      equals the one the gateway assigned

  - [x] 6.2 Write property test for invalid value rejection
    - **Property 3: An invalid value is rejected with comando_invalido and sends nothing, regardless of estado**
    - **Validates: Requirements 2.2, 3.2**
    - Generate invalid values (wrong string, wrong JSON type, `null`, missing field) and any `estado`
      (including `running`); assert rejection with `comando_invalido` and `ws.send` called zero times

  - [x] 6.3 Write property test for running-state rejection
    - **Property 4: A running robot rejects every change with the mode-specific reason and sends nothing**
    - **Validates: Requirements 4.1, 4.2**
    - Generate valid values and `estado == running`; assert rejection before send with
      `bloqueado_competencia` when `modo == competencia` and `ocupado` when `modo == prueba`
      (`ws.send` called zero times)

  - [x] 6.4 Write property test for no-manifest rejection
    - **Property 5: No manifest rejects with sin_manifiesto and sends nothing**
    - **Validates: Requirements 4.4**
    - Generate valid values and any state with no manifest (connection `None` or
      `connection.manifest is None`); assert `sin_manifiesto` and `ws.send` called zero times

  - [x] 6.5 Write property test for undeclared-command rejection
    - **Property 6: An undeclared command rejects with comando_desconocido and sends nothing**
    - **Validates: Requirements 4.5**
    - Generate valid values and a manifest that does not list `modo`/`linea` in its `comandos`;
      assert `comando_desconocido` and `ws.send` called zero times

  - [x] 6.6 Write property test for link-drop delivery failure
    - **Property 7: A link drop after validation returns dispositivo_no_disponible**
    - **Validates: Requirements 4.6**
    - Generate valid values and an accepting state (manifest present and declaring the command,
      non-running); if `ws.send` raises `KeyError`/`RuntimeError`/`OSError` after validation passes,
      assert `dispositivo_no_disponible` and no successful `seq` returned

- [x] 7. Add integration tests for the full guard matrix
  - [x] 7.1 Write integration test for the read endpoint end-to-end
    - Use the `cliente` fixture (real FastAPI `TestClient`); drive `GET /api/devices/velocista/config`
      against an in-memory `velocista` connection with a manifest fixture and a hand-built `Status`
    - Assert `200` with the live `modo`/`linea`; assert `404 sin_estado` when the connection is absent
      or has no `last_status`
    - _Requirements: 1.1, 1.2_

  - [x] 7.2 Write integration test for the full write guard matrix end-to-end
    - Use the `cliente` fixture; populate `ws.connections["velocista"]` with a manifest fixture and a
      hand-built `Status` (mock `ws.send` or consume a connected robot ws)
    - Verify acceptance on `ready`/`stopped`/`calibrating`/`error`; rejection on `running` with the
      mode-specific reason (`bloqueado_competencia` / `ocupado`); and `sin_estado`/`sin_manifiesto`/
      `comando_desconocido`/`dispositivo_no_disponible` end-to-end
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Hecho: 113 pruebas sin BD en verde (incluye unit/propiedades de test_configuracion.py, la
    integración end-to-end por TestClient y la de arquitectura/OpenAPI); ruff limpio. HU-18 no
    usa base de datos, así que no requiere PostgreSQL. Nota: se renombró el operation_id del
    endpoint de HU-17 (`GET /api/robots/{id}/configuracion`) a `getRobotControllerConfig` para
    evitar el choque con `getRobotConfig` de este endpoint.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties (7 properties from the design, min 100
  iterations each); unit tests cover specific examples and edge cases; integration tests exercise the
  full router→gateway path through the FastAPI `TestClient`
- The design uses Python throughout (FastAPI + Pydantic); no language selection needed
- `validar_comando` is reused unchanged — the new `validar_cambio_config` is a sibling that runs after
  it, scoped to mode/linea only; it does not affect the raw command path (HU-16) or HU-17's `setup` apply
- No new DB tables or migrations: mode/line are pure device commands, not persisted
- Loose `Any` request fields route every invalid value (wrong string/type/null/missing) through the
  contract layer to produce the business `comando_invalido` reason, matching the raw command path;
  the response models (`ConfigViva`, `CommandAccepted`) stay strict
- `sin_estado` (404) for the read needs a `Status`; `sin_manifiesto` (409) for the writes needs a
  `Manifest` — these are distinct preconditions by design
- Async writes (`ws.send` is async); sync read (only touches the in-memory `connections` dict)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.3"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["2.1"] },
    { "id": 3, "tasks": ["3.1", "2.2", "2.3"] },
    { "id": 4, "tasks": ["3.2"] },
    { "id": 5, "tasks": ["4.1", "3.3", "6.1"] },
    { "id": 6, "tasks": ["7.1", "6.2"] },
    { "id": 7, "tasks": ["7.2", "6.3"] },
    { "id": 8, "tasks": ["6.4"] },
    { "id": 9, "tasks": ["6.5"] },
    { "id": 10, "tasks": ["6.6"] }
  ]
}
```

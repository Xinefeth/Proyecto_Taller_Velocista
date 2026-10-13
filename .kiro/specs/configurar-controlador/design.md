# Design Document — configurar-controlador (HU-17)

## Introduction

This feature lets the pilot choose the robot's controller, tune its parameters from the
configuration panel, save named setups, and apply them (or a catalog preset) to the live robot
in one action — all without reflashing firmware. It bridges two existing, until-now separate
parts of the API:

- **optimizacion** — persists controllers and named setups in PostgreSQL (DB catalog, seeded from
  `controladores.json`).
- **gateway** — holds the live robot manifest in memory, sends commands over WebSocket, and
  enforces state guards.

The new capability is a dedicated **apply** action that loads a saved setup (or a catalog preset),
validates it against the *live* manifest, and sends the `setup` command with the setup's `id_setup`
in a single step. The panel also gets a **reconciled catalog** (DB catalog overlaid with live
ranges/values) and a **current configuration** view from the live manifest.

## Goals & Non-Goals

**Goals**

- Expose a reconciled controller catalog (DB catalog + live manifest overlay).
- Expose the configuration currently loaded on the robot (from the live manifest).
- Apply a saved setup to the robot in one action (validate + send, carrying `id_setup`).
- Apply a catalog preset to the robot (validate + send, `id_setup` null).
- Enforce state guards on apply: require connection + manifest, block during a competition run,
  surface link-drop between validation and delivery.

**Non-Goals**

- Auto-tuning / optimization algorithms (Twiddle, Bayesian) — those consume the raw catalog; not
  changed here.
- The console UI itself — this spec covers the API surface the panel calls.
- Changing the WebSocket message contract (`Setup` command shape, `Ack` reasons) — reused as-is.
- Persisting apply history / audit log of which setup was applied (the robot's own `id_setup`
  echo and the manifest already reflect the active config).

## Architecture Overview

The codebase is a modular monolith: DB-backed domain modules (`app.modulos.*`) and an in-memory
gateway (`app.gateway`). Dependency direction is one-way: domain modules may depend on the
gateway; the gateway never depends on domain modules. The composition root (`app.main`) wires
ports to implementations (e.g. `actividad.robot_running = ws.robot_running`).

```
                 Panel_de_configuración (consola)
                            │  REST
                            ▼
┌──────────────────── optimizacion (DB) ────────────────────┐
│  router.py   POST /api/robots/{r}/setups/{id}/apply        │
│              POST /api/robots/{r}/presets/apply            │
│              GET  /api/robots/{r}/controllers   (reconciled)│
│              GET  /api/robots/{r}/configuracion (live)      │
│  service.py  cargar/validar setups, cargar presets,        │
│              reconciliar catálogo, configuracion viva      │
│  models.py   Controlador, Setup (PostgreSQL)               │
│  schemas.py  contratos Pydantic                            │
└────────────────────────┬───────────────────────────────────┘
                         │  llama al puerto del gateway
                         ▼
┌──────────────────── gateway (in-memory) ──────────────────┐
│  aplicacion.py  aplicar_setup_velocista(robot_id, ctrl,    │
│                 params, id_setup) → seq                    │
│                 manifiesto_velocista(robot_id) → Manifest|None│
│  comandos.py    validar_comando (guards + check_setup)      │
│  ws.py          connections, send, robot_running           │
└────────────────────────┬───────────────────────────────────┘
                         │  WebSocket /ws/robot
                         ▼
                    Robot_velocista
```

The apply path is the only place optimizacion reaches into the gateway. It does so through a
small, focused port (`aplicacion.py`) so the gateway keeps ownership of the live manifest, the
state guards, and the WebSocket send — and optimizacion keeps ownership of the DB (loading the
setup/preset). Nothing in the gateway learns about setups.

## Component Design

### 3.1 Endpoints (optimizacion router)

All new endpoints live on the existing `optimizacion` router (`/api`, tag `control`) because they
are verbs on setups/presets/controllers — the configuration panel's domain — and they need a DB
session. The existing raw command endpoint (`POST /api/devices/{device}/commands`) stays for
ad-hoc commands; the panel's apply buttons use the new, higher-level endpoints that do load +
validate + send in one step.

| Method | Path | Operation | Body / Params | Returns |
|---|---|---|---|---|
| GET | `/api/robots/{robot_id}/controllers` | `listReconciledControllers` | — | `CatalogoReconciliado` |
| GET | `/api/robots/{robot_id}/configuracion` | `getRobotConfig` | — | `ConfiguracionViva` |
| POST | `/api/robots/{robot_id}/setups/{setup_id}/apply` | `applySetup` | — | `ComandoAceptado` |
| POST | `/api/robots/{robot_id}/presets/apply` | `applyPreset` | `PresetAplicar` | `ComandoAceptado` |

The existing `GET /api/controllers` (raw catalog, no live overlay) is unchanged; it serves the
optimization algorithms that work offline on the catalog.

**Why robot-scoped paths.** There is a single `velocista` WebSocket connection, but the panel
configures a *specific* robot. Scoping the reconciled catalog and the apply actions by
`robot_id` makes the target explicit and lets the panel render a robot's catalog even when that
robot is not the one currently connected (degrades to catalog-only / `sin_manifiesto`).

### 3.2 The "apply" bridge — where it lives and why

**Decision: the endpoints live in the optimizacion router; the gateway interaction is exposed
through a new port `app/gateway/aplicacion.py`.**

Rationale:

1. **Ownership matches the trigger.** "Apply a setup" is an action on a setup (optimizacion
   domain). The panel already calls `/api/robots/{robot_id}/setups` to create/list; applying is
   the natural next verb on the same resource. Keeping it here means the DB session
   (`DbSession` dependency) is available to load the setup/preset without a cross-module
   session dance.
2. **No new dependency cycle.** optimizacion → gateway is already an allowed direction (it
   already uses `actividad.robot_running`, wired to `ws.robot_running`). The gateway never
   imports optimizacion, so adding an optimizacion→gateway call introduces no cycle.
3. **Gateway keeps its concerns.** The live manifest, the state guards (manifest present,
   competition running), the manifest validation (`check_setup`), and the WebSocket send stay
   in the gateway. optimizacion does not touch `ws.connections` directly; it calls the port.
4. **Why not reuse `POST /api/devices/{device}/commands` directly.** That endpoint expects the
   caller to *already* have an assembled `setup` command. Requirement 4.1/5.1 ask the API to
   *load* the setup/preset and assemble the command in one step. Routing apply through the raw
   endpoint would push assembly onto the console and lose the single-action guarantee.
   Instead, the apply service assembles the command and delegates the *validate + send* to the
   gateway port, which reuses the exact same `validar_comando` + `ws.send` machinery.

```python
# app/gateway/aplicacion.py  (new — the focused port)
from app.contract import Manifest
from app.contract.robot import Setup
from app.contract.validation import check_setup_completo
from app.core.errores import ErrorDeNegocio
from app.gateway import ws
from app.gateway.comandos import validar_comando


def manifiesto_velocista(robot_id: str) -> Manifest | None:
    """Live manifest of the velocista, only if it is the requested robot."""
    conexion = ws.connections.get("velocista")
    if conexion is None or conexion.manifest is None:
        return None
    if conexion.manifest.id != robot_id:
        return None  # a different robot is connected → treat as no manifest for this robot
    return conexion.manifest


async def aplicar_setup_velocista(
    robot_id: str, controlador: str, parametros: dict, id_setup: int | None
) -> int:
    """Validate against the live manifest + guards, then send. Returns the seq used."""
    conexion = ws.connections.get("velocista")
    if conexion is None or conexion.manifest is None or conexion.manifest.id != robot_id:
        raise ErrorDeNegocio(409, "sin_manifiesto",
                            "El robot no está conectado o aún no envió su manifiesto")
    modelo = validar_comando("velocista", "setup",
                             {"controlador": controlador, "parametros": parametros,
                              "id_setup": id_setup},
                             conexion.manifest, conexion.last_status)
    # stronger, apply-specific completeness check (see §3.5)
    if problema := check_setup_completo(conexion.manifest, modelo):
        raise ErrorDeNegocio(422, problema[0], problema[1])
    try:
        return await ws.send("velocista", "setup", modelo.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        raise ErrorDeNegocio(503, "dispositivo_no_disponible",
                            "No se pudo entregar el comando: el dispositivo dejó de responder") from e
```

The port reuses `validar_comando` for the shared guards (`sin_manifiesto`, `bloqueado_competencia`,
`comando_desconocido`) and the per-value manifest check (`check_setup` →
`controlador_no_disponible` / `parametro_desconocido` / `fuera_de_rango`), then adds the
apply-specific completeness check and the delivery-failure handling.

### 3.3 Reconciling the catalog with the live manifest

`GET /api/robots/{robot_id}/controllers` returns the **DB catalog as the source of truth for the
list**, overlaid with live values where the manifest matches.

**Matching keys** (the two sides use different field names for the same concept):

- Controller: DB `Controlador.id` == manifest `Controller.nombre`.
- Parameter: DB parameter `clave` == manifest parameter `nombre`.

**Algorithm** (`service.reconciliar_catalogo(session, robot_id)`):

1. Load all DB controllers → `list[ControladorSalida]` (reuse `listar_controladores`).
2. `manifiesto = manifiesto_velocista(robot_id)` (Manifest or None).
3. For each DB controller `c`:
   - `m_ctrl = manifiesto.controlador(c.id)` if manifiesto else None.
   - `activo = manifiesto and manifiesto.controlador_activo == c.id`.
   - For each DB parameter `p`:
     - `m_param = m_ctrl.parametro(p.clave)` if `m_ctrl` else None.
     - `valor = m_param.valor` if `m_param` else None.
4. Return `CatalogoReconciliado(controlador_activo=manifiesto.controlador_activo if manifiesto else None, controladores=[...])`.

**Properties of the reconciliation:**

- The list of controllers and their catalog ranges/steps/presets **always** come from the DB
  catalog (Requirement 1.1, holds online and offline).
- `valor` and `controlador_activo` are overlaid **only** from a matching live manifest; a DB
  controller/parameter with no manifest counterpart is returned with catalog data and no `valor`
  (Requirement 1.2). This matters because the seed data and the manifest example intentionally
  diverge (e.g. DB `adapt` vs manifest `pid_adaptativo`; DB pid params `base`/`max` vs manifest
  `vel_base`) — mismatches are surfaced as "no live value", never as an error.
- When the robot is offline (or a different robot is connected), no overlay is applied
  (Requirement 1.3).

### 3.4 Exposing the current configuration from the live manifest

`GET /api/robots/{robot_id}/configuracion` is a focused projection of the live manifest onto the
*active* controller:

1. `manifiesto = manifiesto_velocista(robot_id)`.
2. If None → `ErrorDeNegocio(404, "sin_manifiesto", ...)` (Requirement 2.2).
3. `ctrl = manifiesto.controlador(manifiesto.controlador_activo)`.
4. Return `ConfiguracionViva(controlador_activo=manifiesto.controlador_activo,
   parametros=[{nombre: p.nombre, valor: p.valor} for p in ctrl.parametros])`.

This reuses the live manifest already exposed by the gateway (`GET /api/devices/velocista/manifest`)
but presents only the control-relevant slice, scoped to the requested robot, with a dedicated
`sin_manifiesto` error when the requested robot is not the connected one.

### 3.5 Validation: catalog vs. manifest, and the completeness check

There are two validation regimes, by design:

- **Save** (Requirement 3.3/3.4) validates against the **DB catalog** (`validar_parametros`):
  exact key match, within range, step-aligned, `max >= base`, `vmin <= base`. Reused unchanged.
- **Apply** (Requirement 4.2–4.5, 5.2/5.3) validates against the **live manifest**, because the
  robot declares its real, current ranges.

The existing `check_setup(manifiesto, setup)` validates per-value (controller exists →
`controlador_no_disponible`; each *setup* param exists in the controller → `parametro_desconocido`;
range/type → `fuera_de_rango`). It does **not** require the setup to include every controller
parameter — and the existing tests rely on that (`({"kp": 0.5}, "pid", None)` passes even though
the manifest `pid` has four parameters). Requirement 4.5 adds a **completeness** requirement
*specific to the apply flow*: a parameter the controller declares but the setup omits must be
rejected with `parametro_desconocido`.

**Decision: do not modify `check_setup`.** Modifying it would change the raw
`POST /api/devices/{device}/commands` behavior and break `test_check_setup` /
`test_setup_validado_contra_el_manifiesto` (which assert partial setups are accepted). Instead,
add a sibling function in the contract validation module:

```python
# app/contract/validation.py  (additive — check_setup unchanged)
def check_setup_completo(manifiesto: Manifest, setup: Setup) -> tuple[str, str] | None:
    """Like check_setup, but also requires every controller parameter to be present."""
    controlador = manifiesto.controlador(setup.controlador)
    if controlador is None:
        return "controlador_no_disponible", f"el robot no tiene el controlador {setup.controlador}"
    for p in controlador.parametros:                     # completeness (Req 4.5)
        if p.nombre not in setup.parametros:
            return "parametro_desconocido", f"falta el parámetro {p.nombre} del controlador"
    return check_setup(manifiesto, setup)               # per-value existence/range/type (Req 4.3/4.4)
```

This keeps one source of truth for per-value manifest validation and layers the apply-only
completeness rule on top. The apply port calls `check_setup_completo`; the raw command path keeps
`check_setup`.

> Note: a saved setup already has the full DB-controller parameter set (enforced at save time by
> `validar_parametros`'s exact-key-match). The completeness check against the *live manifest*
> catches the case where the connected robot's controller declares parameters the saved setup
> lacks (different firmware/manifest than the catalog seed).

### 3.6 Error handling and state guards

All business errors use the existing `ErrorDeNegocio` → `{"detail": {"motivo", "detalle"}}`
format (see `app/core/errores.py`). Reason codes are stable strings the console maps to UI text.

| Condition | HTTP | Reason | Where enforced |
|---|---|---|---|
| Robot not connected / no manifest / different robot connected (apply) | 409 | `sin_manifiesto` | apply port (pre-send) — Req 6.1 |
| Robot in `competencia` + `running` (apply) | 409 | `bloqueado_competencia` | `validar_comando` (pre-send) — Req 6.2 |
| Link drops between validation and delivery | 503 | `dispositivo_no_disponible` | apply port (catch `ws.send`) — Req 6.3 |
| Setup controller not in live manifest | 422 | `controlador_no_disponible` | `check_setup_completo` — Req 4.3/5.2 |
| Setup param outside manifest range / wrong type | 422 | `fuera_de_rango` | `check_setup(_completo)` — Req 4.4/5.3 |
| Manifest controller param missing from setup/preset | 422 | `parametro_desconocido` | `check_setup_completo` — Req 4.5 |
| Save param out of range | 422 | `fuera_de_rango` | `validar_parametros` — Req 3.4 |
| Save param not step-aligned | 422 | `paso_invalido` | `validar_parametros` — Req 3.4 |
| Save `max < base` or `vmin > base` | 422 | `parametros_incompatibles` | `validar_parametros` — Req 3.4 |
| Apply a non-existent setup id | 404 | `setup_no_encontrado` | `obtener_setup` — Req 3.5 |
| Preset / controller not in catalog | 404 | `controlador_no_encontrado` | catalog load — Req 5.1 |
| No manifest for current-config | 404 | `sin_manifiesto` | current-config service — Req 2.2 |

**Ordering of guards on apply** (fail fast, never send on a guard failure):

1. Load the setup/preset from the DB (→ `setup_no_encontrado` / `controlador_no_encontrado`).
2. Connection + manifest present and matches `robot_id` (→ `sin_manifiesto`, no command sent).
3. Competition running (→ `bloqueado_competencia`, no command sent) — inside `validar_comando`.
4. Manifest validation: controller exists, complete, in range, type (→
   `controlador_no_disponible` / `parametro_desconocido` / `fuera_de_rango`, no command sent).
5. `ws.send` (→ `dispositivo_no_disponible` if the link drops here, after validation passed).

Steps 2–4 all happen before `ws.send`, so a guard failure guarantees **zero** commands delivered
(Requirement 6.1's "before sending any command"). Only step 5 can fail after validation, which is
exactly the `dispositivo_no_disponible` case (Requirement 6.3).

### 3.7 Data models and schemas (new Pydantic contracts)

```python
# app/modulos/optimizacion/schemas.py  (additions)

class ParametroReconciliado(ParametroControlador):
    """A catalog parameter, optionally carrying the live value loaded on the robot."""
    valor: float | None = None          # None when offline or no manifest match (Req 1.3)

class ControladorReconciliado(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    id: str
    nombre: str
    nombre_corto: str
    descripcion: str
    parametros: list[ParametroReconciliado]
    presets: dict[str, dict[str, float]]
    activo: bool                        # True iff this is the manifest's controlador_activo (Req 1.2)

class CatalogoReconciliado(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_activo: str | None      # None when offline (Req 1.3)
    controladores: list[ControladorReconciliado]

class ParametroVivo(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    nombre: str
    valor: float

class ConfiguracionViva(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_activo: str
    parametros: list[ParametroVivo]      # valor of each param of the active controller (Req 2.1)

class PresetAplicar(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    controlador_id: str = Field(min_length=1, max_length=40)
    preset_id: str = Field(min_length=1, max_length=40)   # e.g. "Seguro", "Base", "Agresivo"

class ComandoAceptado(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seq: int
    mensaje: str = "Enviado. La confirmación del robot llega a la consola como ack."
```

`ComandoAceptado` mirrors the gateway's `CommandAccepted` so the apply responses are consistent
with the raw command endpoint. No new DB tables or migrations: controllers/setups already exist.

## Data Flow

### Apply a saved setup

```
Panel ──POST /api/robots/{r}/setups/{id}/apply──▶ optimizacion router
   service.aplicar_setup(session, robot_id, setup_id):
     1. setup = obtener_setup(session, setup_id)         # DB  → 404 setup_no_encontrado (Req 3.5)
     2. await gateway.aplicar_setup_velocista(
            robot_id, setup.controlador_id, setup.parametros, setup.id)
        └─ aplicacion.py:
             a. conexion.manifest?.id == robot_id?        # → 409 sin_manifiesto (Req 6.1)
             b. validar_comando("velocista","setup",…)    # → 409 bloqueado_competencia (Req 6.2)
             c. check_setup_completo(manifest, modelo)    # → 422 controlador_no_disponible /
             #                                            #    parametro_desconocido / fuera_de_rango
             d. seq = await ws.send("velocista","setup",  # → 503 dispositivo_no_disponible (Req 6.3)
                  {controlador, parametros, id_setup=setup.id})
     3. return ComandoAceptado(seq)                       # id_setup = setup.id (Req 4.1)
Panel ◀── 202 {seq, mensaje}                              # robot ack arrives later on /ws/consola
```

### Apply a preset

```
Panel ──POST /api/robots/{r}/presets/apply {controlador_id, preset_id}──▶ router
   service.aplicar_preset(session, robot_id, controlador_id, preset_id):
     1. ctrl = session.get(Controlador, controlador_id)  # → 404 controlador_no_encontrado
     2. valores = ctrl.presets[preset_id]                # → 422 preset_no_encontrado
     3. await gateway.aplicar_setup_velocista(
            robot_id, controlador_id, valores, id_setup=None)   # id_setup = null (Req 5.1)
        └─ same guards + check_setup_completo as above (Req 5.2/5.3)
     4. return ComandoAceptado(seq)
```

### Reconciled catalog

```
Panel ──GET /api/robots/{r}/controllers──▶ router
   service.reconciliar_catalogo(session, robot_id):
     catalogo = listar_controladores(session)           # all DB controllers (Req 1.1)
     manifiesto = gateway.manifiesto_velocista(robot_id) # Manifest | None
     for c in catalogo:
        m_ctrl = manifiesto?.controlador(c.id)           # match id == nombre
        activo = manifiesto?.controlador_activo == c.id
        for p in c.parametros:
            valor = m_ctrl?.parametro(p.clave)?.valor    # match clave == nombre; None if no match/offline
     return CatalogoReconciliado(controlador_activo=manifiesto?.controlador_activo, …)
Panel ◀── 200 {controlador_activo?, controladores:[{…, activo, parametros:[{…, valor?}]}]}
```

### Current configuration

```
Panel ──GET /api/robots/{r}/configuracion──▶ router
   service.configuracion_viva(robot_id):
     manifiesto = gateway.manifiesto_velocista(robot_id) # → 404 sin_manifiesto if None (Req 2.2)
     ctrl = manifiesto.controlador(manifiesto.controlador_activo)
     return ConfiguracionViva(controlador_activo=…, parametros=[{nombre, valor}…])  # Req 2.1
```

## Design Decisions & Trade-offs

- **Apply endpoints in optimizacion, not in the gateway comandos router.** The gateway router is
  device-oriented and stateless w.r.t. the DB; it has no session and no concept of setups. Putting
  apply there would force the gateway to depend on optimizacion (a forbidden direction) or
  require passing a session through. The chosen split keeps each module's dependencies legal.
- **Robot-scoped reconciled catalog & config.** Slightly redundant with the global
  `GET /api/controllers` and `GET /api/devices/velocista/manifest`, but it gives the panel a
  single, robot-specific, degraded-gracefully view (catalog-only when the robot is offline).
  The global endpoints remain for other consumers.
- **`check_setup_completo` as a sibling, not a modification of `check_setup`.** Avoids changing
  the raw command path and breaking existing tests. Cost: two setup-validation functions with
  overlapping per-value logic (the new one delegates to the old). Acceptable, and documented.
- **"Different robot connected" → `sin_manifiesto`.** When robot B is connected but the request
  targets robot A, A effectively has no live manifest. We reuse `sin_manifiesto` rather than
  inventing a new reason, since the requirements only distinguish "connected + manifest" vs "not".
- **No apply-history persistence.** The active config is already observable via the manifest's
  `controlador_activo` + `valor`, and the robot echoes `id_setup`. An audit table is out of scope.
- **Async apply.** `ws.send` is async, so the apply service functions are `async` and the router
  handlers are `async def` (FastAPI supports mixing). The reconciled-catalog and current-config
  reads are sync (they only read the in-memory `connections` dict, no `await`).

## Testing Strategy

**Unit tests** (no network, in-memory `ws.connections`):

- `validar_parametros` accepts/rejects with exact reasons (range, step, `max<base`, `vmin>base`).
- `check_setup_completo`: controller missing → `controlador_no_disponible`; param missing →
  `parametro_desconocido`; out of range / wrong type → `fuera_de_rango`; complete + valid → None.
- `reconciliar_catalogo`: overlay applied only on match; absent offline; `controlador_activo`
  set only online.
- `configuracion_viva`: round-trips the active controller; `sin_manifiesto` when no manifest.
- Apply service with a fake `ws.send`: command carries `id_setup` (setup id / null); guards fire
  before send (assert `ws.send` call count is 0 on guard failures); `dispositivo_no_disponible`
  when the fake `send` raises.

**Integration tests** (`requiere_db`, real PostgreSQL): create setup → apply round-trip against a
manifest fixture; catalog reconciliation end-to-end; preset apply.

**Property-based tests** (see below): the pure functions (`validar_parametros`,
`check_setup_completo`, `reconciliar_catalogo`, `configuracion_viva`) and the command-construction
logic with a mocked gateway. Minimum 100 iterations per property. Mock `ws.connections` /
`ws.send` to keep the apply properties in-memory and deterministic.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a
system — essentially, a formal statement about what the system should do. Properties serve as the
bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Reconciled catalog always contains every catalog controller with its definitions

For any DB catalog and any robot state (connected with a manifest, or not), the reconciled catalog
returned by `GET /api/robots/{robot_id}/controllers` contains exactly one entry per catalog
controller, and each entry preserves that controller's parameters with their catalog-defined
`min`, `max`, `paso`, and `presets`.

**Validates: Requirements 1.1**

### Property 2: Live values are overlaid only from a matching manifest and never when offline

For any DB catalog and any robot state, the reconciled catalog overlays `valor` on a parameter
and marks a controller `activo` only when a live manifest exists whose `id` equals the requested
`robot_id` and whose controller/parameter names match (controller `nombre` == DB `id`; parameter
`nombre` == DB `clave`). When the robot is offline (or a different robot is connected), no
parameter carries a `valor` and `controlador_activo` is `null`.

**Validates: Requirements 1.2, 1.3**

### Property 3: Current configuration round-trips the active controller from the manifest

For any live manifest whose `id` equals the requested `robot_id`, the response of
`GET /api/robots/{robot_id}/configuracion` has `controlador_activo` equal to the manifest's
`controlador_activo`, and one parameter `{nombre, valor}` per parameter of that controller, with
`valor` equal to the manifest parameter's `valor`.

**Validates: Requirements 2.1**

### Property 4: Current configuration returns sin_manifiesto without a live manifest

For any `robot_id` and any state in which `manifiesto_velocista(robot_id)` is `None`, the
current-configuration endpoint returns a `sin_manifiesto` error.

**Validates: Requirements 2.2**

### Property 5: Setup create→get round-trip preserves controlador and parameters

For any robot/version and any parameter values that satisfy the controller's catalog constraints,
creating a setup and then fetching it by id returns the same `controlador_id`, `nombre`, and
`parametros` that were submitted.

**Validates: Requirements 3.1**

### Property 6: Listing setups returns exactly the saved, non-archived setups of the robot

For any robot and any collection of saved setups (some archived), listing that robot's setups
returns exactly the non-archived setups tied to that robot, ordered by `creado_en` descending, and
no others.

**Validates: Requirements 3.2**

### Property 7: Save validation accepts iff constraints hold and rejects with the precise reason

For any controller definition and any parameter values, creating/editing a setup is accepted if
and only if every value is within `[min, max]`, aligned to `paso`, `max >= base`, and
`vmin <= base`. Otherwise it is rejected, and the reason is `fuera_de_rango` for an out-of-range
value, `paso_invalido` for a step misalignment, and `parametros_incompatibles` for `max < base` or
`vmin > base`.

**Validates: Requirements 3.3, 3.4**

### Property 8: Applying requires a persisted setup id

For any apply request whose `setup_id` does not identify an existing setup, the apply is rejected
with `setup_no_encontrado` and no setup command is sent to the gateway. (There is no endpoint to
apply an unsaved configuration; the only apply-setup entry point requires an existing id.)

**Validates: Requirements 3.5**

### Property 9: Apply validates the configuration against the live manifest with precise reasons

For any configuration (saved setup or catalog preset) and any live manifest, the apply is accepted
if and only if the controller exists among the manifest's controllers, every parameter the
controller declares is present, and every present value is within the manifest range and matches
the declared type. Otherwise it is rejected before sending any command, with `controlador_no_disponible`
when the controller is absent, `parametro_desconocido` when a required parameter is missing, and
`fuera_de_rango` when a value is out of range or of the wrong type.

**Validates: Requirements 4.2, 4.3, 4.4, 4.5, 5.2, 5.3**

### Property 10: Apply sends the setup command with the source's controlador, parameters, and id_setup

For any accepted apply, the command delivered to the gateway carries the source's `controlador`
and `parametros`, and `id_setup` equal to the setup's id when applying a saved setup, and `null`
when applying a catalog preset.

**Validates: Requirements 4.1, 5.1**

### Property 11: Pre-send state guards reject without delivering a command

For any apply request, when the requested robot has no matching live manifest the apply is
rejected with `sin_manifiesto`, and when the robot's state is `modo = competencia` and
`estado = running` the apply is rejected with `bloqueado_competencia`; in both cases no setup
command is sent to the gateway.

**Validates: Requirements 6.1, 6.2**

### Property 12: A link drop between validation and delivery surfaces dispositivo_no_disponible

For any apply that passes validation, if the gateway send fails after validation (the robot stops
responding), the apply returns `dispositivo_no_disponible` so the pilot can retry.

**Validates: Requirements 6.3**

# Design Document — configurar-modo-linea (HU-18)

## Introduction

This feature lets the pilot choose the robot's functioning mode (`prueba` or `competencia`) and
the track line color (`negra` or `blanca`) from the configuration panel, through two independent,
dedicated, higher-level endpoints — one for mode, one for line, with no combined endpoint. Each
write endpoint validates the command against the live robot manifest and the robot's current
state, forwards it to the robot through the gateway, and returns the command sequence number.
A dedicated read endpoint returns the current mode and line from the robot's live status so the
panel can render its initial state without subscribing to the WebSocket.

Mode and line are pure device commands: there is no database persistence. They live only as the
last command sent and the last status received, both held in memory by the gateway. Because
there is nothing to load from the DB and no cross-module call, the feature lives entirely inside
the gateway — it reuses the existing `validar_comando` + `ws.send` machinery and adds one
stricter state guard (`ocupado`) that the raw command path does not enforce.

## Goals & Non-Goals

**Goals**

- Expose a read of the current `modo` and `linea` from the robot's last `Status`.
- Expose two dedicated write endpoints (mode, line) that validate against the manifest and the
  live state, send the command via the gateway, and return the `seq`.
- Reject invalid mode/line values with `comando_invalido` before any command is sent.
- Enforce state guards on every mode/line change: block while running in **either** mode
  (`bloqueado_competencia` for `competencia`, `ocupado` for `prueba`), require a manifest
  (`sin_manifiesto`), require the command to be declared (`comando_desconocido`), and surface a
  link drop between validation and delivery (`dispositivo_no_disponible`).

**Non-Goals**

- The console UI itself — this spec covers the API surface the panel calls.
- Changing the WebSocket message contract (`Mode`/`Line` command shapes, `Ack` reasons) —
  reused as-is from `app/contract/robot.py`.
- Any database table, migration, or persistence — mode/line are not stored.
- Changing the raw command endpoint `POST /api/devices/{device}/commands` or its
  `validar_comando`. The raw path keeps its existing (looser) guard semantics; the stricter
  `ocupado` guard is layered on top, scoped to mode/line only.
- Blocking controller/parameter (`setup`) changes during a `prueba` run — that is HU-17's
  concern and intentionally stays allowed; only mode/line changes are blocked while running.

## Architecture Overview

The codebase is a modular monolith: DB-backed domain modules (`app.modulos.*`) and an in-memory
gateway (`app.gateway`). The gateway owns the live robot state (`ws.connections`, `Connection`
with `manifest` and `last_status`) and the WebSocket send. The composition root (`app.main`)
wires channels and registers routers.

Mode/line are device commands with no DB footprint. They do not need a domain module, a DB
session, or a cross-module port (unlike HU-17's `apply`, which loads a setup from the DB and
therefore lives in `optimizacion` behind a gateway port). Here the gateway talks to itself, so
the new endpoints live in the gateway and reuse its own `validar_comando` + `ws.send` directly.

```
                 Panel_de_configuración (consola)
                            │  REST
                            ▼
┌──────────────── gateway (in-memory) ───────────────────────┐
│  configuracion.py  GET  /api/devices/velocista/config        │
│                     POST /api/devices/velocista/config/modo   │
│                     POST /api/devices/velocista/config/linea  │
│                     validar_cambio_config (ocupado guard)     │
│  comandos.py        validar_comando (shared guards)           │
│                     CommandAccepted (reused response model)   │
│  ws.py             connections, Connection, send              │
└────────────────────────┬────────────────────────────────────┘
                         │  WebSocket /ws/robot
                         ▼
                    Robot_velocista
```

The new module `app/gateway/configuracion.py` owns the HU-18 REST surface. It imports the shared
`validar_comando` and `CommandAccepted` from `comandos.py` and `ws` from the gateway, so the
live manifest, the shared guards (`sin_manifiesto`, `comando_desconocido`, `bloqueado_competencia`,
`comando_invalido`), and the WebSocket send stay in their existing owners. Nothing in the gateway
learns about anything new except the one `ocupado` guard, which is local to this feature.

## Component Design

### 3.1 Endpoints (gateway `configuracion.py`)

All three endpoints live on a new router in the gateway, prefixed `/api/devices` and tagged
`devices` — the same prefix/tag as the existing `comandos.py` router. They are device-oriented:
they read from and send to the single `velocista` connection, need no DB session, and reuse the
gateway's own validation and send.

| Method | Path | Operation | Body | Returns |
|---|---|---|---|---|
| GET | `/api/devices/velocista/config` | `getRobotConfig` | — | `ConfigViva` |
| POST | `/api/devices/velocista/config/modo` | `setMode` | `CambioModo` | `CommandAccepted` |
| POST | `/api/devices/velocista/config/linea` | `setLine` | `CambioLinea` | `CommandAccepted` |

The existing `GET /api/devices/velocista/manifest` (raw manifest) and
`POST /api/devices/{device}/commands` (raw command) stay in `comandos.py`, unchanged. The panel's
config buttons use the new, higher-level endpoints; ad-hoc commands still go through the raw path.

**Why the gateway, not `optimizacion` or a new config router.**

1. **No DB, no session.** Mode/line are pure commands; there is no setup to load and no row to
   read or write. Putting them in `optimizacion` (the DB config-panel module) would force a
   `DbSession` dependency that is never used and a cross-module call into the gateway — exactly
   the port HU-17 needed, but pointless here because there is nothing on the DB side.
2. **Ownership matches the data.** The read projects `Connection.last_status`; the writes call
   `validar_comando` and `ws.send`. All three are gateway-owned. Keeping them in the gateway
   means no module boundary is crossed and no port is introduced.
3. **Consistency with the existing device surface.** `GET /api/devices/velocista/manifest` already
   exposes live gateway state over REST under the `devices` tag; the new config read and writes
   are its natural siblings. The raw command endpoint already returns `CommandAccepted` with
   `seq`; the new writes reuse that exact response model so the panel sees one ack shape.

### 3.2 The `ocupado` guard — where it lives and why

**Decision: add a focused helper `validar_cambio_config` in `configuracion.py`; do **not** modify
`validar_comando`.**

The existing `validar_comando` blocks every non-`stop` command during `competencia`+`running`
with `bloqueado_competencia`, but it deliberately allows commands (including `modo`/`linea`) during
`prueba`+`running`. HU-18 is stricter: a mode or line change must be refused while the robot is
running in **either** mode. Requirement 4.1 (`bloqueado_competencia` for `competencia`+`running`)
is already satisfied by `validar_comando`. Requirement 4.2 (`ocupado` for `prueba`+`running`) is
new.

Modifying `validar_comando` to add the `ocupado` check would change the raw command path
(`POST /api/devices/{device}/commands`) — which is HU-16's surface and is unit-tested directly in
`test_comandos.py` — and would also tighten HU-17's `setup` apply (HU-17 intentionally allows
`setup` during a `prueba` run). Both are out of scope for HU-18. Following the HU-17 precedent
(`check_setup_completo` layered on top of `check_setup` rather than modifying it), the new guard is
a sibling that runs **after** `validar_comando` passes, scoped to mode/line only:

```python
# app/gateway/configuracion.py  (new)
from app.contract.robot import Status
from app.core.errores import ErrorDeNegocio


def validar_cambio_config(ultimo_estado: Status | None) -> None:
    """Guarda de HU-18: rechazar cambios de modo/linea durante una carrera en modo prueba.

    validar_comando ya bloquea competencia+running con bloqueado_competencia; esta guarda
    extiende el bloqueo a prueba+running, que la vía cruda permite. Es específica de modo/linea:
    no aplica a otros comandos (p. ej. setup, que HU-17 permite durante una carrera de prueba).
    """
    e = ultimo_estado
    if e and e.estado == "running" and e.modo == "prueba":
        raise ErrorDeNegocio(
            409, "ocupado",
            "El robot está corriendo en prueba; detén la carrera para cambiar modo o línea",
        )
```

Because `validar_comando` runs first and raises `bloqueado_competencia` for `competencia`+`running`,
`validar_cambio_config` only ever reaches its `ocupado` branch in the live path. The check on
`modo == "prueba"` is explicit so the helper is self-contained and directly unit-testable (and so a
future caller that does not route through `validar_comando` still gets correct behavior). The
`Status.modo` literal is `prueba | competencia`, so `estado == "running"` is fully partitioned by
the two guards.

### 3.3 The read endpoint

`GET /api/devices/velocista/config` projects the two relevant fields out of the live status. It
does **not** consult the manifest: requirement 1.1 returns mode/line from the last `Status`, and
1.2 returns `sin_estado` whenever there is no `Status` — whether because the robot is not
connected or because it has not sent a `Status` yet.

```python
class ConfigViva(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    modo: Literal["prueba", "competencia"]
    linea: Literal["negra", "blanca"]


@router.get(
    "/velocista/config",
    response_model=ConfigViva,
    operation_id="getRobotConfig",
    summary="Consultar el modo y el color de línea actuales",
    responses=error_responses(
        (404, "sin_estado", "El robot aún no ha enviado su estado",
         "El velocista no está conectado o todavía no envió un estado; no hay modo ni línea que mostrar."),
    ),
)
def get_robot_config() -> ConfigViva:
    connection = ws.connections.get("velocista")
    if connection is None or connection.last_status is None:
        raise ErrorDeNegocio(404, "sin_estado", "El robot aún no ha enviado su estado")
    return ConfigViva(modo=connection.last_status.modo, linea=connection.last_status.linea)
```

`sin_estado` is a new business reason (it is not an `Ack` reason; business reasons are free
strings carried by `ErrorDeNegocio`). Its HTTP code is `404`, mirroring the existing `404
sin_manifiesto` of `GET /api/devices/velocista/manifest` ("not available yet"). The read is a
sync handler: it only reads the in-memory `connections` dict, no `await`.

### 3.4 The write endpoints and the `comando_invalido` choice

Each write endpoint accepts a focused body, validates it through `validar_comando` (which
produces `comando_invalido` via the contract's `Mode`/`Line` models), applies the `ocupado` guard,
then sends and returns the `seq`. The same shape is used for both, differing only in the command
type and field.

**Request bodies are intentionally loose.** The requirements say a value that is neither
`prueba`/`competencia` (or `negra`/`blanca`) must be rejected with `comando_invalido` — the
business reason the console maps to a message — not with a generic FastAPI 422. If the request
field were typed as `Literal["prueba", "competencia"]`, FastAPI would reject a typo like
`"prueba"` with a 422 before the handler runs. To route every invalid value (wrong string, wrong
JSON type, `null`, or a missing field) through the contract layer and get `comando_invalido`, the
field is typed `Any` with a `None` default; the strict literal validation happens in
`validar_comando` → `validate_data` (the catalog's `Mode`/`Line` models). This matches the raw
command path, which accepts a loose `datos: dict[str, Any]` and produces `comando_invalido` for
all bad payloads. The two valid values are documented in the field description and examples.

```python
class CambioModo(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"modo": "prueba"}})
    modo: Any = Field(
        default=None,
        description="Modo de funcionamiento: 'prueba' o 'competencia'.",
        examples=["prueba", "competencia"],
    )


class CambioLinea(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"color": "negra"}})
    color: Any = Field(
        default=None,
        description="Color de la línea de la pista: 'negra' o 'blanca'.",
        examples=["negra", "blanca"],
    )
```

`extra="forbid"` keeps the body to its single field; an extra field is a structural error and
yields a 422 (as the raw `Command` model does). A missing field defaults to `None`, which the
contract rejects as `comando_invalido` — consistent with "neither valid value → comando_invalido".

The handler reuses `validar_comando` for the shared guards. When the connection is missing,
`connection.manifest` would be `None`, so the manifest/last_status are passed as `None` and
`validar_comando` raises `sin_manifiesto` (requirement 4.4 collapses "not connected" and "no
manifest" into the single `sin_manifiesto` reason, unlike the raw path which distinguishes
`desconectado`).

```python
@router.post(
    "/velocista/config/modo",
    status_code=202,
    response_model=CommandAccepted,
    operation_id="setMode",
    summary="Configurar el modo de funcionamiento",
    responses=CONFIG_RESPONSES,  # see §3.6
)
async def set_mode(body: CambioModo) -> CommandAccepted:
    connection = ws.connections.get("velocista")
    manifest = connection.manifest if connection else None
    last_status = connection.last_status if connection else None
    model = validar_comando("velocista", "modo", {"modo": body.modo}, manifest, last_status)
    validar_cambio_config(last_status)            # HU-18 stricter guard (ocupado)
    try:
        seq = await ws.send("velocista", "modo", model.model_dump(exclude_none=True))
    except (KeyError, RuntimeError, OSError) as e:
        raise ErrorDeNegocio(
            503, "dispositivo_no_disponible",
            "No se pudo entregar el comando: el dispositivo dejó de responder",
        ) from e
    return CommandAccepted(seq=seq)
```

`set_line` is identical in structure, with `"linea"` / `CambioLinea` / `{"color": body.color}` /
`CommandAccepted`. `CommandAccepted` is imported from `comandos.py` (the gateway already owns
it), so the panel sees the same `{seq, mensaje}` ack shape as the raw command endpoint.

### 3.5 Guard ordering

The guards run fail-fast, before `ws.send`, so any guard failure guarantees zero commands
delivered. The order is inherited from `validar_comando` with the `ocupado` guard appended:

1. Data shape (contract `Mode`/`Line`) → `comando_invalido` (Req 2.2/3.2). Runs first because
   `validar_comando` calls `validate_data` before anything else.
2. Connection/manifest present → `sin_manifiesto` (Req 4.4). Reached only with a valid value.
3. Command declared in `manifest.comandos` → `comando_desconocido` (Req 4.5).
4. `competencia` + `running` → `bloqueado_competencia` (Req 4.1). Existing `validar_comando` arm.
5. `prueba` + `running` → `ocupado` (Req 4.2). New `validar_cambio_config`, after `validar_comando`.
6. `ws.send` → `dispositivo_no_disponible` (Req 4.6). The only failure that can occur after
   validation passed; the link dropped between validation and delivery.

**Precedence note.** `comando_invalido` precedes the state/manifest guards because
`validar_comando` validates the data shape first: an invalid value during a run still yields
`comando_invalido`, not `ocupado`/`bloqueado_competencia`. This is the existing convention of the
raw command path (and keeps `validar_comando` untouched), so the dedicated endpoints match it.
Non-running estados (`ready`, `stopped`, `calibrating`, `error`) and the no-status-yet case all
pass the running guards (Req 4.3), so a change is accepted whenever the robot is not known to be
running.

### 3.6 Error handling

All business errors use the existing `ErrorDeNegocio` → `{"detail": {"motivo", "detalle"}}`
format (see `app/core/errores.py`). The shared `error_responses(...)` helper documents them in
OpenAPI, grouping same-code reasons into one response with named examples.

| Condition | HTTP | Reason | Enforced by | Requirement |
|---|---|---|---|---|
| Invalid modo/linea value (wrong string/type/null/missing) | 422 | `comando_invalido` | `validar_comando` → `validate_data` | 2.2 / 3.2 |
| Not connected or no manifest | 409 | `sin_manifiesto` | `validar_comando` | 4.4 |
| Command not declared in manifest | 422 | `comando_desconocido` | `validar_comando` | 4.5 |
| Running in `competencia` | 409 | `bloqueado_competencia` | `validar_comando` | 4.1 |
| Running in `prueba` | 409 | `ocupado` | `validar_cambio_config` | 4.2 |
| Link drops between validation and delivery | 503 | `dispositivo_no_disponible` | `set_mode`/`set_line` catch | 4.6 |
| No `Status` to read | 404 | `sin_estado` | `get_robot_config` | 1.2 |

The two write endpoints share one `responses` dict (built once with `error_responses(...)` for
all the rows above that apply to writes) so their OpenAPI is identical and neither reason is lost.

### 3.7 Data models (new Pydantic contracts)

```python
# app/gateway/configuracion.py  (additions — no DB tables, no migrations)

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class ConfigViva(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    modo: Literal["prueba", "competencia"]
    linea: Literal["negra", "blanca"]

class CambioModo(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"modo": "prueba"}})
    modo: Any = Field(default=None, description="Modo de funcionamiento: 'prueba' o 'competencia'.",
                      examples=["prueba", "competencia"])

class CambioLinea(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"color": "negra"}})
    color: Any = Field(default=None, description="Color de la línea: 'negra' o 'blanca'.",
                       examples=["negra", "blanca"])
```

`CommandAccepted` is reused from `comandos.py` (already `{seq, mensaje}`). No new DB tables or
migrations: mode/line are not persisted.

### 3.8 Wiring

`configuracion.router` (prefix `/api/devices`, tag `devices`) is registered in `app/main.py`
alongside `comandos.router`. Two routers sharing the same prefix/tag is fine in FastAPI; paths do
not collide (`/velocista/config`, `/velocista/config/modo`, `/velocista/config/linea` are new).

```python
# app/main.py  (addition)
from app.gateway import configuracion
...
app.include_router(configuracion.router)
```

## Data Flow

### Read current configuration

```
Panel ──GET /api/devices/velocista/config──▶ get_robot_config()
   connection = ws.connections.get("velocista")
   if connection is None or connection.last_status is None:
       → 404 sin_estado (Req 1.2)
   return ConfigViva(modo=connection.last_status.modo,
                    linea=connection.last_status.linea)   # Req 1.1
Panel ◀── 200 {modo, linea}
```

### Set mode (set line is the same shape with tipo "linea" / field "color")

```
Panel ──POST /api/devices/velocista/config/modo {modo}──▶ set_mode()
   connection = ws.connections.get("velocista")
   manifest    = connection?.manifest
   last_status = connection?.last_status
   model = validar_comando("velocista","modo",{"modo":body.modo}, manifest, last_status)
       └─ validate_data → 422 comando_invalido   (Req 2.2, bad value; runs first)
       └─ manifest None  → 409 sin_manifiesto     (Req 4.4)
       └─ "modo" not in comandos → 422 comando_desconocido (Req 4.5)
       └─ competencia+running → 409 bloqueado_competencia (Req 4.1)
   validar_cambio_config(last_status)
       └─ prueba+running → 409 ocupado           (Req 4.2)
   seq = await ws.send("velocista","modo",{"modo":<value>})
       └─ raises → 503 dispositivo_no_disponible  (Req 4.6)
   return CommandAccepted(seq)                    # Req 2.1
Panel ◀── 202 {seq, mensaje}  (robot ack arrives later on /ws/consola)
```

## Design Decisions & Trade-offs

- **Endpoints in the gateway, not `optimizacion`.** Mode/line are device commands with no DB
  footprint; there is no setup to load and no row to read or write. Placing them in the gateway
  avoids a pointless `DbSession` dependency and a cross-module port. HU-17 needed `optimizacion` +
  a port because `apply` loads a DB setup; HU-18 needs neither.
- **A sibling `validar_cambio_config`, not a modification of `validar_comando`.** Keeps the raw
  command path (HU-16) and HU-17's `setup` apply unchanged and their tests green; layers the new
  `ocupado` guard on top, scoped to mode/line. Cost: one small extra function and a guard that
  runs after `validar_comando`. Acceptable, and documented.
- **`ocupado` scoped to mode/line only.** A controller/parameter change during a `prueba` run is a
  legitimate tuning experiment (HU-17 allows it); a mode or line change mid-run is always wrong.
  The guard lives in `configuracion.py` and is not wired into the shared `validar_comando`, so it
  cannot accidentally tighten `setup`.
- **Loose request bodies (`Any`) to produce `comando_invalido`.** Sacrifices the OpenAPI enum on
  the request field (documented via description + examples) so that every invalid value — wrong
  string, wrong type, `null`, missing — is rejected with the business `comando_invalido` rather
  than a generic 422, matching the raw command path. The response models stay strict.
- **`sin_estado` (404) for the read vs `sin_manifiesto` (409) for the writes.** The read needs a
  `Status`; the writes need a `Manifest`. A robot can be connected with a manifest but no status
  yet — then the read returns `sin_estado` while a mode/line change is accepted (manifest present,
  not running). These are distinct preconditions by design.
- **`sin_manifiesto` collapses "not connected" and "no manifest" for the writes.** The raw path
  distinguishes `desconectado` from `sin_manifiesto`; HU-18's requirement 4.4 names only
  `sin_manifiesto` for both, so the dedicated endpoints pass `None` when the connection is missing
  and let `validar_comando` raise `sin_manifiesto`.
- **Async writes, sync read.** `ws.send` is async, so `set_mode`/`set_line` are `async def`; the
  read only touches the in-memory `connections` dict, so it is sync.

## Testing Strategy

**Unit tests** (no network, in-memory `ws.connections`, mocked `ws.send`):

- `validar_cambio_config`: `prueba`+`running` → `ocupado`; `competencia`+`running` and all
  non-running estados and `None` → no raise.
- `validar_comando` additions (no behavior change, just coverage): `modo`/`linea` during
  `competencia`+`running` → `bloqueado_competencia`; valid `modo`/`linea` accepted.
- `get_robot_config`: returns `modo`/`linea` from `last_status`; `sin_estado` when connection is
  `None` or `last_status` is `None` (two cases).
- `set_mode`/`set_line` with a fake `ws.send`: valid value sends the right command shape and
  returns the captured `seq`; guards fire before send (assert `ws.send` call count is 0 on every
  guard failure); `dispositivo_no_disponible` when the fake `send` raises
  `KeyError`/`RuntimeError`/`OSError`.

**Integration tests** (`cliente` fixture, real FastAPI `TestClient`): drive the three endpoints
against an in-memory `velocista` connection with a manifest fixture and a hand-built `Status`;
verify the full guard matrix end-to-end (accept on `ready`/`stopped`/`calibrating`/`error`;
reject on `running` with the right reason; `sin_estado`/`sin_manifiesto`/`comando_desconocido`).

**Property-based tests** (see below): the pure read projection, the command-construction + guard
logic, and the error paths, with `ws.connections`/`ws.send` mocked to stay in-memory and
deterministic. Minimum 100 iterations per property. Generators cover: random `modo`/`linea`,
random `estado` (incl. `running` with both modos), random invalid values (strings, numbers,
bools, `None`, lists), manifests with/without the command declared, and `ws.send` raising.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a
system — essentially, a formal statement about what the system should do. Properties serve as the
bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Read projects the live status, or returns sin_estado

For any `velocista` connection state, `GET /api/devices/velocista/config` returns `modo` and
`linea` equal to the `modo` and `linea` of `connection.last_status` when a `Status` exists, and
returns a `sin_estado` error when the connection is `None` or `connection.last_status` is `None`.

**Validates: Requirements 1.1, 1.2**

### Property 2: A valid change sends the matching command and returns its seq, for any non-running estado

For any valid `modo` (`prueba`/`competencia`) or `linea` (`negra`/`blanca`) and any `estado` in
`ready`, `stopped`, `calibrating`, or `error` (with a manifest that declares the command), the
corresponding write endpoint sends exactly one command to the gateway — `("velocista", "modo",
{"modo": <value>})` for mode, `("velocista", "linea", {"color": <value>})` for line — and returns
the `seq` that the gateway assigned to that send.

**Validates: Requirements 2.1, 3.1, 4.3**

### Property 3: An invalid value is rejected with comando_invalido and sends nothing, regardless of estado

For any `modo`/`linea` request whose value is not one of the two valid values (including a wrong
string, a wrong JSON type, `null`, or a missing field) and for any `estado` (including `running`),
the corresponding write endpoint is rejected with `comando_invalido` before any command is sent
(the gateway `send` is called zero times).

**Validates: Requirements 2.2, 3.2**

### Property 4: A running robot rejects every change with the mode-specific reason and sends nothing

For any valid `modo`/`linea` value and `estado == running`, the corresponding write endpoint is
rejected before any command is sent (the gateway `send` is called zero times): with
`bloqueado_competencia` when `modo == competencia`, and with `ocupado` when `modo == prueba`.

**Validates: Requirements 4.1, 4.2**

### Property 5: No manifest rejects with sin_manifiesto and sends nothing

For any valid `modo`/`linea` value and any `velocista` state in which no manifest is available
(connection `None`, or `connection.manifest is None`), the corresponding write endpoint is rejected
with `sin_manifiesto` before any command is sent (the gateway `send` is called zero times).

**Validates: Requirements 4.4**

### Property 6: An undeclared command rejects with comando_desconocido and sends nothing

For any valid `modo`/`linea` value and any manifest that does not list that command in its
`comandos` (a manifest is valid without declaring every command), the corresponding write endpoint
is rejected with `comando_desconocido` before any command is sent (the gateway `send` is called
zero times).

**Validates: Requirements 4.5**

### Property 7: A link drop after validation returns dispositivo_no_disponible

For any valid `modo`/`linea` value and any accepting state (manifest present and declaring the
command, non-running), if the gateway `send` raises `KeyError`, `RuntimeError`, or `OSError` after
validation has passed, the corresponding write endpoint returns `dispositivo_no_disponible` and no
successful `seq` is returned.

**Validates: Requirements 4.6**

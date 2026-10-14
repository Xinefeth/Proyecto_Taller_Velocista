# Implementation Plan — HU-14 · Consultar el estado del robot

## Overview

The feature renders a live status bar from the robot's `Status` telemetry and a `GET /api/health`
read. It touches the **contract** (`Status` message), the **gateway** (validate/rebroadcast
`Status`, emit `enlace`), the **system** (`GET /api/health`), and the **console** (the top bar fed
from real WebSocket data with a simulated fallback). No DB tables or migrations — status is live.

`[x]` marks work already done and verified; `[ ]` marks pending work. Tasks marked `*` need a real
robot or a `robot_falso.py` with simulated timing.

## Tasks

- [x] 1. Contract + gateway for live status
  - [x] 1.1 `Status` message (battery, loop, rssi, state, calibrado, modo, linea) — `api/app/contract/robot.py`
  - [x] 1.2 Gateway validates and rebroadcasts `Status` to the console — `api/app/gateway/ws.py`
  - [x] 1.3 `enlace` message on connect/disconnect — `api/app/gateway/ws.py`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 3.1_

- [x] 2. System health endpoint
  - [x] 2.1 `GET /api/health` with connected devices, 200 without DB — `api/app/main.py`
  - _Requirements: 4.1, 4.2_

- [x] 3. Console: the status bar
  - [x] 3.1 Top bar with link (dBm, ms), loop (Hz), battery, and state — `consola/src/components/Strip.tsx`
  - [x] 3.2 "SIN ENLACE" indication with freshness in seconds — `consola/src/components/Strip.tsx`
  - [x] 3.3 Feed the bar from real WebSocket data (pure `robotStatus.ts` + test), mount `ProveedorConexion` — `consola/src/logica/robotStatus.ts`, `consola/src/stores/ConexionContext.tsx` (`useConexionOpcional`), `consola/src/main.tsx`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 3.2_

- [ ] 4. Resolve the link latency ("ms") source
  - [ ] 4.1 Decide where the real link latency in ms comes from (contract adds a field, or the gateway measures round-trip); today the "ms" is console-simulated and omitted in real mode — contract/gateway
  - _Requirements: 1.2 (the "ms" half of the official criterion)_

- [ ] 5. Cross-cutting rename (migration in progress — requires confirmation)
  - [ ] 5.1 `Status` fields to English (`estado→state`, `calibrado→calibrated`, `lazo_hz→loop_hz`, `bateria_v→battery_v`, …) — contract 2.0, touches firmware — `api/app/contract/robot.py`, `firmware/`
  - _See `docs/rename-glosario.md`; not executed in this revision._

- [ ]* 6. Verify real timings
  - [ ]* 6.1 Verify refresh ≥ 1/s and link-loss indication < 2 s with a real robot or `robot_falso.py`
  - _Requirements: 2.2, 3.2_

## Tests

- [x] `enlace` and `GET /api/health` — `api/tests/websocket/test_gateway.py`, `api/tests/integration/test_salud.py`
- [x] `robotStatus.ts` maps a `Status` to the bar values — console unit test
- [ ]* Timing test (1 s / 2 s) — pending a robot/`robot_falso.py` environment

## Notes

- `[x]` tasks are verified in the current code; `[ ]` tasks are pending. Task 4 is an open design
  question (no real "ms" source today); tasks 5 and 6 need user confirmation / a hardware environment.
- No DB tables or migrations: status and link are live, in-memory gateway state.
- The bar uses real `Status` values when a robot is linked and simulated values otherwise; in real
  mode the "ms" is omitted and the state text still derives from the simulation (pending).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "2.1"] },
    { "id": 1, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 2, "tasks": ["4.1", "5.1", "6.1"] }
  ]
}
```

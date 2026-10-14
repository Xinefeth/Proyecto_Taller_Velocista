# Implementation Plan — HU-16 · Calibrar los sensores y arrancar

## Overview

The feature wires calibrate/start/stop to the robot over the existing command path and enforces two
safety rules: start is blocked until calibrated, and stop is always available. It touches the
**gateway** (`send_command`, `validar_comando` guards, delivery + `ack`) and the **console**
(buttons, calibration panel, guards). No DB tables or migrations — commands are not persisted.

`[x]` marks work already done and verified; `[ ]` marks pending work. Tasks marked `*` need a real
robot or a `robot_falso.py` that simulates calibration timing.

## Tasks

- [x] 1. Gateway command path and guards
  - [x] 1.1 `POST /api/devices/{device}/commands` endpoint (202 + `ack`) — `api/app/gateway/comandos.py`
  - [x] 1.2 Block `arrancar` while not calibrated (409 `no_calibrado`) — `api/app/gateway/comandos.py`
  - [x] 1.3 Competition rule (only `detener` while running) and `comando_desconocido` — `api/app/gateway/comandos.py`
  - [x] 1.4 Forward the command and relay `ack` to `/ws/consola` — `api/app/gateway/ws.py`
  - [x] 1.5 Link-drop on send → 503 `dispositivo_no_disponible`, documented and tested — `api/app/gateway/comandos.py` (verified 2026-10-10: 11 gateway tests; OpenAPI 503 example)
  - _Requirements: 1.1, 2.1, 2.2, 4.2, 5.1, 5.2, 5.3_

- [x] 2. Console buttons and calibration panel
  - [x] 2.1 Combined ARRANCAR/DETENER button — `consola/src/pages/Control.tsx`
  - [x] 2.2 Block start until calibrated (notice "Calibra los sensores antes de arrancar") — `consola/src/pages/Control.tsx`
  - [x] 2.3 Calibration panel with `calibrating`/`calibrated`/`running`; disable calibrate while running/calibrating — `consola/src/pages/Control.tsx`
  - [x] 2.4 Confirm DETENER is never disabled (always available) — `consola/src/pages/Control.tsx` (verified: `Control.test.tsx` 5 passed, 2026-10-10)
  - _Requirements: 1.2, 2.3, 4.1_

- [ ] 3. Cross-cutting rename (migration in progress — requires confirmation)
  - [ ] 3.1 Commands and states to English (`calibrar→calibrate`, `arrancar→start`, `detener→stop`; `listo/calibrando/...→ready/calibrating/...`) — contract 2.0, touches firmware — `api/app/contract/robot.py`, `api/app/contract/catalog.py`, `firmware/`
  - _See `docs/rename-glosario.md`; the console already uses some English states; not executed in this revision._

- [ ]* 4. Verify calibration time < 20 s
  - [ ]* 4.1 **Blocked**: `robot_falso.py` sets `calibrado=true` instantly (no `calibrating` state, no timed wait), so it cannot measure a real duration. Simulate timing in the fake robot: on `calibrar` → `estado=calibrating` (`calibrado:false`), non-blocking wait (`asyncio.sleep`, configurable < 20 s), then `estado=ready` + `calibrado:true`; measure `calibrar` → `Status calibrado:true`. Or verify on a real robot.
  - _Requirements: 3.1_

## Tests

- [x] Commands validated and sent; rejection by invalid state; `no_calibrado`; competition; 503 link-drop — `api/tests/websocket/test_gateway.py` (11 passed, 2026-10-10)
- [x] Stop always enabled across 5 states; DETENER only while running — `consola/src/pages/Control.test.tsx` (5 passed)
- [ ]* Calibration < 20 s end-to-end — blocked on the instant-stub fake robot (direct stub call ~0.0000018 s does not satisfy Req 3.1)

## Notes

- `[x]` tasks are verified in the current code; the start guard, the stop-always rule, and the error
  reasons are implemented and tested.
- Task 3 (rename) and task 4 (< 20 s verification) need user confirmation / a hardware or timed-stub
  environment; the API cannot enforce calibration time (it is a robot/firmware property).
- No DB tables or migrations: commands are not persisted.
- The start guard lives in both the API (authoritative `no_calibrado`) and the console (fast notice).

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3", "1.4", "1.5"] },
    { "id": 1, "tasks": ["2.1", "2.2", "2.3", "2.4"] },
    { "id": 2, "tasks": ["3.1", "4.1"] }
  ]
}
```

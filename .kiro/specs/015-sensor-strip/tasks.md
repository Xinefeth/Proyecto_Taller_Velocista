# Implementation Plan — HU-15 · Visualizar la regleta de sensores

## Overview

The feature draws the 16 sensor channels and the derived line state from the live `Signals` stream.
It touches the **contract** (`Signals`, strip in the manifest), the **gateway** (validate/rebroadcast
`Signals`), and the **console** (pure `strip.ts` derivation + `Regleta()` drawing, with a simulated
fallback). No REST endpoint and no DB — the strip is WebSocket-only live telemetry.

`[x]` marks work already done and verified; `[ ]` marks pending work. Tasks marked `*` are optional.

## Tasks

- [x] 1. Contract + gateway for the strip stream
  - [x] 1.1 `Signals` message (signals-group channels, ~20 Hz) — `api/app/contract/robot.py`
  - [x] 1.2 Manifest declares the strip (16 channels, 2× QTR-8A) — `api/app/contract/manifest.py`
  - [x] 1.3 Gateway validates and rebroadcasts `Signals`; `check_channels` warns, does not discard — `api/app/gateway/ws.py`, `api/app/contract/validation.py`
  - _Requirements: 3.1, 3.2, 3.3_

- [x] 2. Fake robot emits the 16 strip channels
  - [x] 2.1 `robot_falso.py` emits `canales.regleta` as a list of 16 values in each `Signals` — `api/herramientas/robot_falso.py`
  - [x] 2.2 Confirm emission with a no-network capture — `api/tests/unit/test_sensor_strip.py` (44 tests)
  - _Requirements: 1.1, 3.1_

- [x] 3. Console: derive the strip view (pure logic)
  - [x] 3.1 `strip.ts` derives 16 bars + position (mm) + error + centered/lost from the latest `Signals`; accepts only exactly 16 finite values, else fallback — `consola/src/logica/strip.ts`
  - _Requirements: 1.2, 1.3, 2.1, 2.2, 2.3_

- [x] 4. Console: draw the strip
  - [x] 4.1 Draw the 16 bars with their values — `consola/src/pages/Control.tsx` (`Regleta()`)
  - [x] 4.2 Show the position (mm) — `Regleta()`
  - [x] 4.3 Show the error and the centered / "Línea perdida" / side label — `Regleta()`
  - [x] 4.4 Feed `Regleta()` from the real channels of the last `Signals`, simulation as fallback — `consola/src/pages/Control.tsx`
  - _Requirements: 1.1, 2.1, 2.2, 2.3_

- [ ] 5. Cross-cutting rename (migration in progress — requires confirmation)
  - [ ] 5.1 `senales→signals`, `canales→channels`, `regleta→sensor_bar` — contract 2.0, touches firmware — `api/app/contract/robot.py`, `firmware/`
  - _See `docs/rename-glosario.md`; not executed in this revision._

- [ ]* 6. Physical calibration of scale/extents
  - [ ]* 6.1 Confirm the 0–1000 scale and the ±72 mm extents with real hardware
  - _Requirements: 2.1 (physical accuracy of the mm mapping)_

## Tests

- [x] `Signals` / channel validation in the gateway — `api/tests/websocket/test_gateway.py`
- [x] Strip view test (16 bars + position + centered) — `consola/src/pages/Regleta.test.tsx`
- [x] Derive error from 16 channels; reject incomplete / non-finite samples — `consola/src/logica/strip.test.ts`
- [x] Center, extents, lost line, latest message, simulated fallback — 17 HU-15 tests (11 logic + 6 view)

## Notes

- `[x]` tasks are verified in the current code; the strip is fully functional over WebSocket.
- No REST endpoint and no DB by design — a future `GET /api/devices/{device}/sensors` would need the
  gateway to retain the last `Signals`; not asked for.
- Everything (position, error, centered) derives by centroid from the 16 channels; malformed samples
  fall back to the simulation.
- The full console suite has 3 unrelated failures in `RegistroManual.test.tsx` (robot loading),
  outside HU-15.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "1.3"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["3.1"] },
    { "id": 3, "tasks": ["4.1", "4.2", "4.3", "4.4"] },
    { "id": 4, "tasks": ["5.1", "6.1"] }
  ]
}
```

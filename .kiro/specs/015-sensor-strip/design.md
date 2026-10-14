# Design Document — HU-15 · Visualizar la regleta de sensores

## Introduction

This feature draws the robot's 16 line-sensor channels and the line state derived from them. It is
pure live telemetry with **no REST endpoint**: the robot declares the strip (16 channels, two QTR-8A
modules via a multiplexer) in its manifest and streams the channel values in the `Signals` message
(~20 Hz while running) over `/ws/robot`. The gateway validates the channels against the manifest and
rebroadcasts the sample to the console over `/ws/consola`. The console derives the 16 bars, the
position (mm), the error, and the centered/lost state from the latest valid `Signals`, and falls
back to a simulation only when no valid sample is available. Nothing is persisted.

## Goals & Non-Goals

**Goals**

- Draw 16 bars with their values from the real strip channels of the latest `Signals`.
- Derive and show the line position (mm), the error, and centered / "Línea perdida" / side.
- Validate the `Signals` channels against the manifest in the gateway without discarding on warning.
- Fall back to the simulation only when the sample is missing, incomplete, or non-finite.

**Non-Goals**

- A REST endpoint (by design; strip is WebSocket-only).
- The rest of the telemetry — lap times, motor PWM.
- Launching calibration or start — HU-16.
- Renaming `senales`/`canales`/`regleta` to English (contract 2.0, touches firmware).
- Physical calibration of the 0–1000 scale and the ±72 mm extents (needs hardware).

## Architecture Overview

```
        Robot_velocista
            │  /ws/robot  (manifiesto: regleta 16ch; Signals ~20 Hz al correr)
            ▼
┌──────────── gateway (memoria) ─────────────┐
│  ws.py          recibe Signals              │
│  validation.py  check_channels vs manifiesto│  (avisa, no descarta)
│                 redifunde a la consola      │──/ws/consola──▶ Consola
└─────────────────────────────────────────────┘
                                                      │
                                   strip.ts (lógica pura): último Signals →
                                   16 barras · posición (mm) · error · centrada/perdida
                                                      ▼
                                          Control.tsx :: Regleta()  (dibujo)
```

The console keeps the WebSocket wiring and the drawing thin; the derivation lives in a pure module
(`consola/src/logica/strip.ts`) that is unit-tested without a network.

## Component Design

### 3.1 Contract and emission

- `app/contract/robot.py :: Signals` — `t_ms` plus `canales` of the signals group (includes the
  strip's 16 channels). `ChannelValue` admits `list[int]`, so `canales.regleta` is a list of 16
  values (0–1000).
- `app/contract/manifest.py` — the manifest declares the strip (`regleta`, 16 channels, 2 modules).
- `api/herramientas/robot_falso.py` — emits `canales.regleta` as a list of 16 values in each
  `Signals`, confirmed by a no-network capture test.

### 3.2 Gateway validation and rebroadcast

`app/gateway/ws.py` receives `Signals`, validates the channels against the manifest with
`app/contract/validation.py :: check_channels`, warns on a mismatch but does **not** discard the
sample, and rebroadcasts it to the console.

### 3.3 Console derivation (`strip.ts`) and drawing (`Regleta()`)

- `consola/src/logica/strip.ts` — pure logic: extracts the latest `Signals` from the `/ws/consola`
  messages and derives the view: 16 normalized bars, position in mm, error, centered, lost, and the
  active bars. Accepts **only** exactly 16 finite numeric values; otherwise the caller uses the
  simulated fallback.
- `consola/src/pages/Control.tsx :: Regleta()` — draws the 16 bars with their values, the position
  (mm), the error, and the label "Centrada" / "Línea perdida" / "Hacia la derecha/izquierda", fed
  from the real channels of the last `Signals` (via `ConexionContext`), with `c.simRef` as fallback.
- `consola/src/logica/dominio.ts` — computes compatibility (e.g. the multiplexer covers 16 channels),
  not the strip drawing.

The error is derived from the 16 channels (not a separate `error` channel), so a failed or missing
channel shows up in both the bars and the derived position/error.

## Data Flow

```
Robot ──manifiesto (regleta 16ch)──▶ gateway (held)
Robot ──Signals (~20 Hz)──▶ gateway.ws: check_channels (warn, keep) → rebroadcast
Consola ◀──/ws/consola── strip.ts(latest Signals):
            exactly 16 finite values? → 16 bars + position(mm) + error + centered/lost
            else → simulated fallback
         └─▶ Control.tsx :: Regleta() draws the strip
```

## Design Decisions & Trade-offs

- **No REST endpoint.** The strip is live telemetry; a read endpoint would require the gateway to
  retain the last `Signals` (it keeps only the last `Status`) and is not asked for. Documented as a
  possible future `GET /api/devices/{device}/sensors` for evidence only.
- **Derive everything from the 16 channels.** Position, error, and centered are computed by centroid
  from the same 16 values, so one bad channel is visible everywhere consistently, and no separate
  `error` channel is trusted.
- **Strict sample acceptance, simulated fallback.** Only exactly 16 finite values are accepted; any
  malformed sample routes to the simulation so the view never draws garbage. Trade-off: a transient
  bad sample briefly shows simulated data rather than a broken strip.
- **Warn, don't discard, on channel mismatch.** The gateway surfaces a channel warning but keeps the
  sample, so a minor manifest/stream divergence does not blank the strip.

## Testing Strategy

**Backend:** `api/tests/websocket/test_gateway.py` — reception and channel validation of `Signals`;
`api/tests/unit/test_sensor_strip.py` — the fake robot emits the 16 strip channels (no-network
capture). 44 passing (emitter, contract, gateway, architecture).

**Console:** `consola/src/pages/Regleta.test.tsx` — draws 16 bars + position (mm) + centered/lost
from an injected real `Signals`; `consola/src/logica/strip.test.ts` — center, extents, lost line,
latest-message selection, and simulated fallback; rejects incomplete / non-finite samples. 17
HU-15-specific tests passing (11 logic + 6 view).

**Known:** the full console suite had 3 unrelated failures in
`src/components/gestion/RegistroManual.test.tsx` (robot loading), outside HU-15.

## Correctness Properties

### Property 1: 16 bars drawn from the latest valid Signals

For any `Signals` with exactly 16 finite strip values, `Regleta()` draws exactly 16 bars whose
values come from those channels.

**Validates: Requirements 1.1, 1.2**

### Property 2: Position, error, and centered derive by centroid from the 16 channels

For any valid 16-channel sample, the position (mm), the error, and the centered/lost label are a
function of the centroid of those 16 channels and nothing else.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Malformed samples fall back to the simulation

For any sample that is missing, not exactly 16 values, or contains a non-finite value, the console
uses the simulated fallback instead of drawing from that sample.

**Validates: Requirements 1.3**

### Property 4: The gateway validates channels but keeps the sample

For any `Signals` whose channels mismatch the manifest, the gateway emits a warning and still
rebroadcasts the sample (does not discard it), and exposes no REST endpoint for the strip.

**Validates: Requirements 3.2, 3.3**

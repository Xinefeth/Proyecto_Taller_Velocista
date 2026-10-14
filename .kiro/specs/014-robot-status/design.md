# Design Document — HU-14 · Consultar el estado del robot

## Introduction

This feature renders a top status bar from the robot's live telemetry. The robot emits a periodic
`Status` (~1 Hz) over `/ws/robot`; the gateway validates it, holds the last one, and rebroadcasts it
to the console over `/ws/consola`. The gateway also emits a `enlace` message when a device connects
or disconnects, which drives the "SIN ENLACE" indication. A single REST endpoint, `GET /api/health`,
reports which devices are connected so the bar can render before telemetry arrives. Nothing is
persisted — status and link are purely live, in-memory state owned by the gateway.

## Goals & Non-Goals

**Goals**

- Show battery (V), link (dBm), loop (Hz), and operating state from the live `Status`.
- Refresh the bar at least once per second by rebroadcasting each `Status`.
- Indicate link loss in under 2 seconds via the `enlace` message and a freshness counter.
- Report device connection state over `GET /api/health`, independent of the database.

**Non-Goals**

- Sending commands to the robot (HU-16).
- The per-channel sensor strip detail (HU-15).
- A real source for the link latency in **ms** (open question; today simulated).
- Renaming the Spanish `Status` fields to English (contract 2.0, touches firmware).
- Persisting status or link history.

## Architecture Overview

```
        Robot_velocista
            │  /ws/robot  (Status ~1 Hz)
            ▼
┌──────────── gateway (memoria) ─────────────┐
│  ws.py   recibe y valida Status             │
│          guarda last_status                 │
│          redifunde a la consola             │──/ws/consola──▶ Consola (Strip.tsx)
│          emite enlace {dispositivo,conectado}│
│  main.py GET /api/health (dispositivos)     │──REST──────────▶ useSalud / ConexionContext
└─────────────────────────────────────────────┘
```

The console mounts `ProveedorConexion` (in `main.tsx`), subscribes to `/ws/consola`, and derives the
bar values from the last `Status` with a pure function (`consola/src/logica/robotStatus.ts`). The
`enlace` message and a freshness timer drive the "SIN ENLACE" chip.

## Component Design

### 3.1 The `Status` message (contract)

`app/contract/robot.py :: Status` carries: `estado`
(`ready`/`calibrating`/`running`/`stopped`/`error`), `calibrado`, `modo`, `linea`, `controlador`,
`lazo_hz` (measured loop frequency), `rssi_dbm` (−120…0), and `canales` (status group, includes
`bateria_v`). Emitted at `estado_hz` (1 Hz default).

### 3.2 Gateway: rebroadcast and link events

`app/gateway/ws.py` validates each `Status`, stores it as the connection's `last_status`, and
rebroadcasts it to the console. On connect/disconnect it emits `enlace {dispositivo, conectado}`; on
console connect it sends `hola` with the initial device state.

### 3.3 REST health

`GET /api/health` (`app/main.py`, operation `getHealth`) returns `dispositivos`
(`{velocista, cronometro}`: connected or not). It reads in-memory connection state, so it responds
200 even with the database down. It does **not** return live battery/loop — those travel over the
WebSocket only.

### 3.4 Console: deriving the bar

- `consola/src/logica/robotStatus.ts` — pure function mapping the last `Status` to the bar values
  (battery, dBm, Hz, state); covered by its own test.
- `consola/src/components/Strip.tsx` — renders link (dBm, and a simulated ms in sim mode), loop
  (Hz), battery, the freshness-in-seconds, and the "SIN ENLACE" chip.
- `consola/src/stores/ConexionContext.tsx` (`useConexionOpcional`), `consola/src/hooks/useSalud.ts`,
  `consola/src/main.tsx` (mounts `ProveedorConexion`) — connection state and health polling.

When a robot is linked, the bar uses real `Status` values; with no robot it falls back to simulated
values. In real mode the **ms** is omitted (no real source) and the state text still derives from the
simulation — both tracked as pending.

## Data Flow

### Live status refresh

```
Robot ──Status (~1 Hz)──▶ gateway.ws: validate → last_status → rebroadcast
Consola ◀──/ws/consola──  robotStatus.ts(last Status) → {battery, dBm, Hz, state} → Strip.tsx
```

### Link loss

```
Robot disconnects ──▶ gateway emits enlace{conectado:false}
Consola ◀── freshness timer + enlace ──▶ "SIN ENLACE" within < 2 s
```

### Initial health

```
Consola ──GET /api/health──▶ main.py → {dispositivos:{velocista,cronometro}} (200, no DB needed)
```

## Design Decisions & Trade-offs

- **Live-only, no persistence.** Status and link are ephemeral; the gateway holds just the last
  `Status`. No table, no migration.
- **Pure derivation function.** `robotStatus.ts` isolates the Status→bar mapping so it is unit-tested
  without a WebSocket; `Strip.tsx` stays presentational.
- **Simulated fallback.** With no robot, the bar shows simulated values so the UI is never blank;
  real values take over when a robot links. Trade-off: the "ms" and the state text still lean on the
  simulation and are flagged as pending rather than hidden.
- **`GET /api/health` is DB-independent.** It only reflects in-memory connections, so it answers 200
  regardless of the database, matching its purpose.

## Testing Strategy

**Gateway tests** (`api/tests/websocket/test_gateway.py`): `enlace` on connect/disconnect and
`GET /api/health` reflecting the connected device.

**Integration test** (`api/tests/integration/test_salud.py`): the shape of `GET /api/health`.

**Console unit test:** `robotStatus.ts` maps a `Status` to the expected bar values; "SIN ENLACE"
renders on link loss.

**Pending (needs a real robot or `robot_falso.py` with timing):** verify refresh ≥ 1/s and link-loss
indication < 2 s against real timings.

## Correctness Properties

### Property 1: The bar reflects the last Status when a robot is linked

For any `Status` received while a robot is linked, the bar's battery, dBm, and Hz equal
`bateria_v`, `rssi_dbm`, and `lazo_hz` of that `Status`, and the state equals its `estado`.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4**

### Property 2: Every Status is rebroadcast to the console

For any valid `Status` the gateway receives, it stores it as `last_status` and emits it on
`/ws/consola`, so a 1 Hz stream yields at least one bar refresh per second.

**Validates: Requirements 2.1, 2.2**

### Property 3: Disconnect raises a link-loss indication

For any device disconnect, the gateway emits `enlace{conectado:false}` and the console shows "SIN
ENLACE" driven by the freshness timer within the 2 s budget.

**Validates: Requirements 3.1, 3.2**

### Property 4: Health reports connections regardless of the database

For any database state, `GET /api/health` responds 200 with the current in-memory connection state
of `velocista` and `cronometro`.

**Validates: Requirements 4.1, 4.2**

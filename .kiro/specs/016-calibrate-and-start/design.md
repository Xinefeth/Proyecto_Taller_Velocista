# Design Document — HU-16 · Calibrar los sensores y arrancar

## Introduction

This feature wires the console's calibrate and start/stop buttons to the robot through the existing
command path. The console sends `{tipo, datos}` to `POST /api/devices/{device}/commands`; the gateway
validates the command against the robot's manifest and current state (`validar_comando`), forwards it
over the WebSocket, and the robot confirms with an `ack` on `/ws/consola`. Two safety rules shape the
design: **start is blocked until the robot is calibrated** (`no_calibrado`), and **stop is always
available** (the console never disables the stop action, and the competition guard allows only
`detener` while running in `competencia`). Calibration timing (< 20 s) is enforced by the
robot/firmware, not the API. Nothing is persisted for commands.

## Goals & Non-Goals

**Goals**

- Send calibrate/start/stop via the existing `POST /api/devices/{device}/commands` with 202 + `ack`.
- Block start until the robot is calibrated (`no_calibrado`), in both API and console.
- Keep stop always available in the console and allow only `detener` during a competition run.
- Reject unknown/undeliverable commands with precise reasons (`comando_desconocido`,
  `desconectado`, `dispositivo_no_disponible`).

**Non-Goals**

- Controller tuning / optimization (setup) — HU-17.
- The sensor strip view during calibration — HU-15.
- Enforcing the < 20 s calibration time in the API (it is a robot/firmware property).
- Persisting commands (runs are persisted, but that is another story).
- Renaming the Spanish command types/states to English (contract 2.0, touches firmware).

## Architecture Overview

```
                 Consola (Control.tsx: ARRANCAR/DETENER, calibrar)
                            │  REST  POST /api/devices/{device}/commands {tipo,datos}
                            ▼
┌──────────────── gateway (devices) ─────────────────┐
│  comandos.py  send_command (202)                    │
│               validar_comando (guards)              │
│  ws.py        ws.enviar → robot ; ack → consola     │
└────────────────────────┬────────────────────────────┘
                         │  /ws/robot  (calibrar/arrancar/detener)
                         ▼
                    Robot_velocista ──Status(estado,calibrado), ack──▶ consola
```

The command path already exists; HU-16 is the calibrate/start/stop verbs on it plus the console's
buttons and guards. `validar_comando` owns the state guards; `ws.enviar` owns delivery.

## Component Design

### 3.1 Endpoint and body

`POST /api/devices/{device}/commands` (`app/gateway/comandos.py`, operation `sendCommand`). Body is
`{tipo, datos}`. For the velocista, `tipo` must be declared in the manifest (`calibrar`, `arrancar`,
`detener`, `setup`, `modo`, `linea`, `cierre_vuelta`). Returns 202; the robot's confirmation arrives
as an `ack` on `/ws/consola`.

### 3.2 State guards (`validar_comando`)

| Condition | HTTP | Reason |
|---|---|---|
| `arrancar` while not `calibrado` | 409 | `no_calibrado` ("Calibra el robot antes de arrancar") |
| Any non-`detener` command while `modo competencia` + `running` | 409 | `bloqueado_competencia` |
| `tipo` not declared in the manifest | 422 | `comando_desconocido` |
| Device not connected | 409 | `desconectado` |
| Link drops between pre-check and `ws.enviar` | 503 | `dispositivo_no_disponible` |

All guards run **before** `ws.enviar` except the link-drop case, which is the one failure that can
happen after validation — caught around `ws.enviar` and surfaced as 503.

### 3.3 WebSocket messages

- `calibrar` / `arrancar` / `detener` (API → robot): commands with no data.
- `Status` (robot → API): exposes `estado` (`ready`/`calibrating`/`running`/`stopped`/`error`) and
  `calibrado` — the basis for the start guard and the console buttons.
- `ack` (robot → API → console): confirms each command, repeating its `seq`.

### 3.4 Console (`Control.tsx`)

- Combined **ARRANCAR/DETENER** button: it is never `disabled`; DETENER is shown only while
  `running`, ARRANCAR otherwise — so stop is always reachable (Req 4.1).
- Calibration panel with `calibrating` / `calibrated` / `running` states; the notice "Calibra los
  sensores antes de arrancar" blocks start until calibrated; the calibrate button is disabled while
  running or calibrating.
- `consola/src/services/api.ts` and `consola/src/stores/ConsolaContext.tsx` send the commands and
  hold the console state.

## Data Flow

```
Consola ──POST /api/devices/velocista/commands {tipo:"calibrar"}──▶ comandos.send_command
   validar_comando(manifest, status): tipo declared? connected? guards OK?
   ws.enviar("velocista","calibrar") ──▶ robot            # 202 accepted
Robot ──ack(seq)──▶ gateway ──/ws/consola──▶ Consola
Robot ──Status(estado:"calibrating", calibrado:false) … Status(calibrado:true)──▶ Consola

Consola ──{tipo:"arrancar"}──▶ validar_comando:
   calibrado == false → 409 no_calibrado  (no ws.enviar)
   calibrado == true  → ws.enviar → 202 → ack

Consola ──{tipo:"detener"}──▶ allowed in every state (incl. competencia+running)
```

## Design Decisions & Trade-offs

- **Reuse the existing command path.** Calibrate/start/stop are ordinary declared commands; no new
  endpoint. The guards live in `validar_comando`, one source of truth for all commands.
- **Start guard in both layers.** The API rejects `arrancar` without `calibrado` (authoritative) and
  the console blocks the button with a notice (fast feedback). Defense in depth.
- **Stop always available by construction.** The combined button is never disabled and DETENER is the
  rendered action while running; the competition guard explicitly whitelists `detener`.
- **< 20 s is a robot property, not an API check.** The API cannot enforce calibration time; it is
  measured end-to-end (`calibrar` → `Status calibrado:true`). The fake robot sets `calibrado=true`
  instantly, so it cannot measure a real duration — flagged as pending, needs a timed simulation or
  real hardware.
- **503 on link drop.** `send_command` catches a failed `ws.enviar` and returns
  `dispositivo_no_disponible`, documented in `responses=` and covered by a test.

## Testing Strategy

**Gateway tests** (`api/tests/websocket/test_gateway.py`): commands validated and sent; rejection by
invalid state; `no_calibrado`; competition guard; `comando_desconocido`; the link-drop 503
(`test_comando_con_enlace_caido_al_enviar_devuelve_503`). 11 passing (2026-10-10). OpenAPI 503
example confirmed via `app.openapi()`.

**Console tests** (`consola/src/pages/Control.test.tsx`): 5 passing (2026-10-10) across not
calibrated, calibrating, calibrated, running, and no link — the ARRANCAR/DETENER button is enabled in
all five; DETENER appears only while running. Sim mode; does not assert physical stop delivery.

**Pending (needs real robot or a timed `robot_falso.py`):** verify calibration < 20 s end-to-end. A
direct stub call measured ~0.0000018 s — only in-process stub time, not a real calibration; it does
**not** satisfy Req 3.1.

## Correctness Properties

### Property 1: Start is rejected until calibrated

For any `arrancar` request while `calibrado` is false, the API rejects it with `no_calibrado` (409)
and no command is sent to the robot; once `calibrado` is true, `arrancar` is forwarded.

**Validates: Requirements 1.1**

### Property 2: Stop is always available

For every console state (not calibrated, calibrating, calibrated, running, no link), the stop action
is enabled, and the API allows `detener` even while `modo competencia` + `running`.

**Validates: Requirements 4.1, 4.2**

### Property 3: Only declared commands are forwarded

For any command whose `tipo` is not declared in the manifest, the API rejects it with
`comando_desconocido` (422) and sends nothing; a disconnected device yields `desconectado` (409).

**Validates: Requirements 5.1, 5.2**

### Property 4: A link drop after validation surfaces dispositivo_no_disponible

For any command that passes validation, if `ws.enviar` fails (the device stops responding), the API
returns `dispositivo_no_disponible` (503) so the pilot can retry.

**Validates: Requirements 5.3**

### Property 5: Calibration finishes within the time budget

For a real robot, the interval between sending `calibrar` and receiving a `Status` with
`calibrado: true` is under 20 seconds. (Not verifiable with the current instant-stub fake robot.)

**Validates: Requirements 3.1**

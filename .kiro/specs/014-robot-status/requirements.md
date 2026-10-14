# Requirements Document — HU-14 · Consultar el estado del robot

## Introduction

The robot-status feature shows the pilot a top bar with the robot's health so they can tell whether
it is ready to run: battery (V), link (dBm and ms), control loop (Hz), and operating state. These
values are live telemetry, not persisted: the robot sends a periodic `Status` message (~1 Hz) over
the WebSocket, the gateway rebroadcasts it to the console, and the gateway emits a `enlace` message
when a device connects or disconnects. A single REST endpoint (`GET /api/health`) reports which
devices are connected so the console can render an initial state before the WebSocket delivers data.
This story covers reading and displaying the live status; it does not cover sending commands (HU-16)
or the per-channel sensor strip (HU-15).

## Glossary

- **API**: Servicio backend que recibe el `Status` del robot, lo redifunde a la consola y expone la
  salud de los dispositivos.
- **Gateway**: Capa en memoria (`app.gateway.ws`) que mantiene el último `Status`, redifunde la
  telemetría y emite `enlace` al conectar/desconectar.
- **Consola**: Interfaz con la barra superior de estado (`Strip.tsx`).
- **Robot_velocista**: Dispositivo que envía su `Status` periódico por `/ws/robot`.
- **Status**: Mensaje periódico del robot (~1 Hz) con `estado`, `calibrado`, `modo`, `linea`,
  `controlador`, `lazo_hz`, `rssi_dbm` y `canales` (incluye `bateria_v`). Definido en
  `app/contract/robot.py`.
- **estado**: Estado operativo: `ready`, `calibrating`, `running`, `stopped`, `error`.
- **enlace**: Mensaje API→consola `{dispositivo, conectado}` al conectar o desconectar un dispositivo.
- **lazo_hz**: Frecuencia real medida del lazo de control.
- **rssi_dbm**: Intensidad del enlace de radio en dBm.
- **bateria_v**: Voltaje de la batería, expuesto como canal del grupo estado.

## Requirements

### Requirement 1: Mostrar el estado del robot en la barra superior

**User Story:** As a pilot, I want the top bar to show battery, link, loop, and state, so that I
know whether the robot is ready to run.

#### Acceptance Criteria

1. WHILE a Robot_velocista is connected and sending `Status`, THE Consola SHALL show the battery in
   volts from `bateria_v`.
2. WHILE a Robot_velocista is connected and sending `Status`, THE Consola SHALL show the link in dBm
   from `rssi_dbm`.
3. WHILE a Robot_velocista is connected and sending `Status`, THE Consola SHALL show the control
   loop in Hz from `lazo_hz`.
4. WHILE a Robot_velocista is connected and sending `Status`, THE Consola SHALL show the operating
   `estado`.
5. WHERE no robot is linked, THE Consola SHALL fall back to simulated values rather than showing
   empty fields.

### Requirement 2: Refrescar el estado al menos una vez por segundo

**User Story:** As a pilot, I want the bar to refresh continuously, so that the reading reflects the
robot right now.

#### Acceptance Criteria

1. THE Robot_velocista SHALL emit `Status` at `estado_hz` (1 Hz by default).
2. WHEN a new `Status` arrives, THE Gateway SHALL rebroadcast it to the Consola so the bar refreshes
   at least once per second.

### Requirement 3: Indicar la pérdida de enlace en menos de 2 segundos

**User Story:** As a pilot, I want to be told quickly when the link drops, so that I do not trust a
stale reading.

#### Acceptance Criteria

1. WHEN a device disconnects, THE Gateway SHALL emit a `enlace` message with `conectado=false`.
2. WHEN the link is lost, THE Consola SHALL show a "SIN ENLACE" indication with the link freshness in
   seconds, in under 2 seconds.

### Requirement 4: Consultar la salud de los dispositivos

**User Story:** As a pilot, I want the console to know which devices are connected, so that it can
render an initial state without waiting for the WebSocket.

#### Acceptance Criteria

1. WHEN the Consola requests `GET /api/health`, THE API SHALL return the connection state of each
   device (`velocista`, `cronometro`).
2. THE `GET /api/health` endpoint SHALL respond 200 even when the database is unavailable, since it
   reports in-memory connection state only.

## Known mismatch

The official criterion asks for the link in **dBm and ms**, but the `Status` contract carries
`rssi_dbm` and no latency in ms. Today the "ms" shown in the bar is a **console-side simulated**
metric and is omitted in real mode. The real source of the latency must be decided before the "ms"
can be considered satisfied (see `tasks.md`, task 2.1).

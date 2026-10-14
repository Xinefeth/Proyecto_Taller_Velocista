# Requirements Document — HU-16 · Calibrar los sensores y arrancar

## Introduction

The calibrate-and-start feature lets the pilot calibrate the robot's sensors and start/stop it from
the console, so the robot is quickly ready on the track. Calibrate, start, and stop are device
commands: the console sends them through `POST /api/devices/{device}/commands`; the gateway validates
each against the robot's manifest and current state, forwards it to the robot over the WebSocket, and
the robot confirms with an `ack`. The key safety rules are that **start is blocked until the robot is
calibrated** and that **stop is always available**. Calibration itself runs on the robot/firmware and
must finish in under 20 s (the rules give one minute for everything). This story covers the command
path and its state guards; it does not cover controller tuning/optimization (setup) or the sensor
strip view during calibration (HU-15).

## Glossary

- **API**: Servicio backend que valida los comandos contra el manifiesto y el estado, y los reenvía
  al robot por el gateway.
- **Gateway**: Capa que valida (`validar_comando`), envía el comando al robot y devuelve el `ack`.
- **Consola**: Interfaz con los botones de calibrar y arrancar/detener (`Control.tsx`).
- **Robot_velocista**: Dispositivo que ejecuta la calibración, el arranque y la parada.
- **comando**: Mensaje `{tipo, datos}`; para el velocista, `tipo` debe estar declarado en el
  manifiesto: `calibrar`, `arrancar`, `detener`, `setup`, `modo`, `linea`, `cierre_vuelta`.
- **estado**: Estado operativo: `ready`, `calibrating`, `running`, `stopped`, `error`.
- **calibrado**: Bandera del `Status` que indica si el robot está calibrado.
- **ack**: Confirmación del robot por `/ws/consola` para cada comando.
- **seq**: Número de secuencia del comando; el `ack` lo repite.

## Requirements

### Requirement 1: Bloquear el arranque hasta calibrar

**User Story:** As a pilot, I want start to be blocked until the robot is calibrated, so that I never
launch an uncalibrated robot.

#### Acceptance Criteria

1. WHEN the pilot requests `arrancar` WHILE the robot is not `calibrado`, THE API SHALL reject the
   command with a `no_calibrado` error (409) before forwarding anything.
2. WHILE the robot is not `calibrado`, THE Consola SHALL block the start action and show the notice
   "Calibra los sensores antes de arrancar".

### Requirement 2: Lanzar la calibración

**User Story:** As a pilot, I want to launch calibration from the console, so that I can prepare the
robot without touching the firmware.

#### Acceptance Criteria

1. WHEN the pilot requests `calibrar`, THE API SHALL validate it against the manifest and forward it
   to the Robot_velocista via the Gateway, returning 202 (accepted).
2. THE robot confirmation SHALL arrive as an `ack` over `/ws/consola`.
3. WHILE the robot is calibrating or running, THE Consola SHALL disable the calibrate button.

### Requirement 3: Calibración en menos de 20 segundos

**User Story:** As a pilot, I want calibration to finish quickly, so that it fits the one-minute
budget the rules give for everything.

#### Acceptance Criteria

1. THE calibration (run by the robot/firmware) SHALL finish in under 20 seconds, measured between
   sending `calibrar` and the arrival of a `Status` with `calibrado: true`.

### Requirement 4: Detener siempre disponible

**User Story:** As a pilot, I want stop to always be available, so that I can halt the robot in any
state.

#### Acceptance Criteria

1. THE Consola SHALL never disable the stop action, in any state (not calibrated, calibrating,
   calibrated, running, no link).
2. WHILE the robot is in `modo competencia` and `running`, THE API SHALL allow only `detener`,
   rejecting other commands with `bloqueado_competencia` (409).

### Requirement 5: Guardas del comando y entrega

**User Story:** As a pilot, I want the system to reject unsafe or undeliverable commands clearly, so
that I know whether a command reached the robot.

#### Acceptance Criteria

1. IF the command `tipo` is not declared in the robot's manifest, THEN THE API SHALL reject it with
   `comando_desconocido` (422).
2. IF the target device is not connected, THEN THE API SHALL reject the command with `desconectado`
   (409).
3. IF the link to the device drops between the pre-check and `ws.enviar`, THEN THE API SHALL return
   `dispositivo_no_disponible` (503) so the pilot can retry.

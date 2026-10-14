# Requirements Document — HU-15 · Visualizar la regleta de sensores

## Introduction

The sensor-strip feature shows the pilot the robot's 16 line-sensor channels (two QTR-8A modules via
a multiplexer) as bars with their values, plus the derived line position (mm), the error, and
whether the line is centered — so the pilot can calibrate and spot a failed sensor. This is pure
live telemetry with **no REST endpoint**: the robot declares the strip in its manifest and streams
channel values in the `Signals` message (~20 Hz while running) over `/ws/robot`; the gateway
validates the channels against the manifest and rebroadcasts them to the console over `/ws/consola`.
The console derives the 16 bars, the position, the error, and the centered/lost state from those
real channels, falling back to a simulation only when no valid sample is available. This story
covers displaying the strip; it does not cover the rest of the telemetry (lap times, motor PWM) or
launching calibration/start (HU-16).

## Glossary

- **API**: Servicio backend que valida las `Signals` contra el manifiesto y las redifunde a la consola.
- **Gateway**: Capa en memoria (`app.gateway.ws`) que recibe `Signals`, revisa sus canales y las
  redifunde.
- **Consola**: Interfaz que dibuja la regleta (`Control.tsx :: Regleta()`).
- **Robot_velocista**: Dispositivo que declara la regleta en el manifiesto y emite `Signals`.
- **Regleta (sensor bar)**: Sensor de 16 canales (2 módulos QTR-8A vía multiplexor) declarado en el
  manifiesto; en el prototipo `v001` expone `regleta` con `canales: 16, modulos: 2`.
- **Signals**: Mensaje del robot (~20 Hz mientras corre) con `t_ms` y `canales` del grupo señales,
  incluidos los 16 canales de la regleta. Definido en `app/contract/robot.py`.
- **canal (channel)**: Valor de un sensor; `ChannelValue` admite una lista de enteros
  (`list[int]`, 0–1000 para la regleta).
- **posición**: Posición de la línea en mm, derivada por centroide de los 16 canales (±72 mm).
- **error**: Error de seguimiento normalizado, derivado de los 16 canales.
- **centrada**: Indicación de que la línea está en el centro; si no, "Línea perdida" o hacia un lado.

## Requirements

### Requirement 1: Mostrar las 16 lecturas como barras con su valor

**User Story:** As a pilot, I want to see the 16 sensor channels as bars with their values, so that
I can calibrate and detect a failed sensor.

#### Acceptance Criteria

1. WHEN valid `Signals` are received, THE Consola SHALL draw 16 bars, one per strip channel.
2. THE Consola SHALL show each bar's value derived from the real strip channels of the latest
   `Signals`.
3. IF no valid sample is available (missing, not exactly 16, or non-finite values), THEN THE Consola
   SHALL fall back to the simulation rather than drawing an invalid strip.

### Requirement 2: Mostrar posición, error y si está centrada

**User Story:** As a pilot, I want to see the line position, the error, and whether it is centered,
so that I can judge the follower's state at a glance.

#### Acceptance Criteria

1. WHEN valid `Signals` are received, THE Consola SHALL show the line position in mm derived by
   centroid of the 16 channels.
2. WHEN valid `Signals` are received, THE Consola SHALL show the error derived from the 16 channels.
3. THE Consola SHALL indicate whether the line is centered, and otherwise "Línea perdida" or toward
   the left/right.

### Requirement 3: Flujo por WebSocket y validación en el gateway

**User Story:** As a pilot, I want the strip to reflect the robot's live stream, so that what I see
matches the sensors right now.

#### Acceptance Criteria

1. THE Robot_velocista SHALL declare the strip (16 channels, 2× QTR-8A) in its manifest and stream
   the strip channels in `Signals`.
2. WHEN `Signals` arrive, THE Gateway SHALL validate the channels against the manifest
   (`app/contract/validation.py :: check_channels`), rebroadcast the sample to the console, and NOT
   discard the sample on a channel warning.
3. THE feature SHALL NOT expose a REST endpoint; the strip is live telemetry over `/ws/consola`.

## Nota de arquitectura

HU-15 **no tiene endpoint REST** por diseño: su flujo es por **WebSocket**. Si en el futuro se
quisiera un `GET /api/devices/{device}/sensors` (última lectura), habría que hacer que el gateway
retenga la última `Signals` (hoy solo guarda el último `Status`). No lo piden los criterios.

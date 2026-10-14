# Requirements Document — HU-13 · Seleccionar el robot

## Introduction

The select-robot feature lets the pilot choose which robot the console works with and renders a
view tailored to that robot. The list of robots and their type/version/firmware comes from the
builder module (PostgreSQL, via REST), and the panels shown for a robot are derived from the
devices (sensors and actuators) that robot declares — so a robot without an encoder shows no
encoder panel. Robot declarations reach the console two ways: the catalog of registered robots and
their current version (REST, from the builder/catalog modules) and, when a robot is physically
connected, the live manifest the gateway exposes. This story covers the API surface the console
calls to list robots and read a robot's declared devices; it does not cover creating or editing
robots (that is the builder story) nor live telemetry (HU-14/HU-15).

## Glossary

- **API**: Servicio backend que lista robots y versiones desde la base de datos y expone el
  manifiesto del robot conectado por el gateway.
- **Consola**: Interfaz web donde el piloto elige el robot y ve los paneles que ese robot declara.
- **Armador (builder)**: Módulo que persiste robots y versiones (`app.modulos.armador`).
- **Catálogo (catalog)**: Módulo que persiste tipos de componente y ranuras que alimentan los
  paneles (`app.modulos.catalogo`).
- **Robot**: Velocista registrado en el armador, con tipo, firmware y una versión actual.
- **Versión**: Configuración de piezas de un robot (`version`, `version_componente`).
- **Manifiesto (Manifest)**: Declaración que el robot envía al conectarse; lista sensores,
  actuadores, canales y controladores. Base para armar los paneles.
- **Panel**: Vista de la consola asociada a un dispositivo (sensor o actuador) que el robot declara.
- **Ranura (slot)**: Posición del armador donde se monta un componente; define qué paneles existen.

## Requirements

### Requirement 1: Listar los robots del armador

**User Story:** As a pilot, I want to see the list of registered robots with their type, version,
and firmware, so that I can choose which robot to work with.

#### Acceptance Criteria

1. WHEN the Consola requests the robot list, THE API SHALL return every registered Robot with its
   `id`, `nombre`, `codigo_corto`, `tipo`, `firmware`, `version_actual_id`, and `archivado`.
2. WHEN the Consola requests a Robot's current version, THE API SHALL return that version's label
   and component pieces so the console can show type, version, and firmware.
3. WHILE the database is unavailable, THE API SHALL return a `base_no_disponible` error (503)
   documented in the OpenAPI schema, and the Consola SHALL show an error state with retry and no
   local fallback.

### Requirement 2: Consultar los dispositivos declarados por el robot

**User Story:** As a pilot, I want the console to know which sensors and actuators a robot declares,
so that it can render only the panels that robot supports.

#### Acceptance Criteria

1. WHEN a Robot is physically connected and has sent its Manifiesto, THE API SHALL expose the
   Manifiesto (sensores, actuadores, canales, controladores) over REST at
   `GET /api/devices/velocista/manifest`.
2. THE API SHALL use the real contract example
   (`docs/contrato/ejemplos/velocista.manifiesto.json`) as the OpenAPI `example` of that endpoint's
   200 response.
3. WHERE the panels are derived from a Robot's declared pieces, THE API SHALL provide the slots and
   component types (`GET /api/slots`) needed to compute the expected devices.

### Requirement 3: Armar la vista según los dispositivos del robot

**User Story:** As a pilot, I want the console to show only the panels for the devices my robot has,
so that I am not shown controls the robot cannot use.

#### Acceptance Criteria

1. WHEN the pilot selects a Robot, THE Consola SHALL render only the panels for the sensors and
   actuators that Robot declares.
2. IF a Robot does not declare a given device (e.g. an encoder), THEN THE Consola SHALL NOT render
   that device's panel.
3. WHEN the pilot changes the selected Robot or its pieces, THE Consola SHALL recompute the panels
   from the new declaration.

### Requirement 4: Degradación sin datos locales

**User Story:** As a pilot, I want the console to reflect the real backend state, so that I never
act on stale local data.

#### Acceptance Criteria

1. THE Consola SHALL obtain the production robot list exclusively from the API, with explicit
   loading, empty, and error/retry states.
2. WHILE the API list is loading, empty, or failing, THE Consola SHALL NOT fall back to local
   prototype fixtures; local fixtures SHALL be used only when explicitly injected in tests.

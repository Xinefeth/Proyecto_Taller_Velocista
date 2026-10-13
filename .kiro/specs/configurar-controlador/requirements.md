# Requirements Document

## Introduction

The configurar-controlador feature lets the pilot select the robot's controller and tune its parameters from the configuration panel, then save those configurations and apply them to the robot to test different setups without reprogramming the firmware. It bridges two existing parts of the system: the optimization module, which persists controllers and named setups in the database, and the gateway, which sends the setup command to the connected robot. The key new capability is a dedicated "apply setup" action that loads a saved setup (or a catalog preset), validates it against the live robot manifest, and sends the setup command with the setup's id in a single step. The panel also reconciles the database catalog with the live manifest so the pilot sees the real ranges and the values currently loaded on the robot.

## Glossary

- **API**: Servicio backend que persiste configuraciones, valida contra el manifiesto y envía comandos al robot por el gateway.
- **Panel_de_configuración**: Interfaz donde el piloto selecciona el controlador y ajusta sus parámetros.
- **Robot_velocista**: Dispositivo robot al que se aplica la configuración de control; declara su manifiesto al conectarse.
- **Controlador**: Algoritmo de control del robot (p. ej. PID, PID adaptativo, Difuso), declarado en el manifiesto del robot y sembrado en el catálogo de la base de datos.
- **Parámetro**: Valor de ajuste individual de un controlador (Kp, Ki, Kd, base, máx, etc.) con rango mínimo/máximo, paso, tipo y valor definidos.
- **Preset**: Configuración inicial nombrada (Seguro, Base, Agresivo) que pertenece a un controlador del catálogo.
- **Setup**: Configuración nombrada y persistida (controlador más valores de parámetros) asociada a un robot y versión en la base de datos de la API.
- **Catálogo**: Conjunto de definiciones de controladores persistido en la base de datos, sembrado desde controladores.json, que provee presets y rangos por defecto.
- **Manifiesto**: Declaración que el robot envía al conectarse; contiene los controladores y parámetros con sus rangos reales, el controlador activo y el valor cargado de cada parámetro.
- **valor**: Valor del parámetro cargado ahora en el robot, expuesto en el manifiesto vivo.
- **controlador_activo**: Nombre del controlador actualmente cargado en el robot, expuesto en el manifiesto.
- **id_setup**: Identificador del setup guardado en la base de datos, enviado con el comando de setup para vincular el robot y la API.
- **Gateway**: Capa de la API que envía comandos al robot por WebSocket y expone el manifiesto vivo.
- **Estado_del_robot**: Estado del velocista (ready, calibrating, running, stopped, error) y modo (prueba, competencia) reportados por el robot.

## Requirements

### Requirement 1: Consultar el catálogo de controladores reconciliado

**User Story:** As a pilot, I want to see the available controllers and their parameters with the live ranges and the values currently loaded on the robot, so that I can choose and tune a configuration based on what the connected robot actually supports.

#### Acceptance Criteria

1. WHEN the Panel_de_configuración requests the controller catalog, THE API SHALL return every Catálogo controller with its Parámetros, ranges, steps, and Presets.
2. WHILE the Robot_velocista is connected and has sent its Manifiesto, THE API SHALL reconcile the Catálogo with the Manifiesto, exposing the controlador_activo and the valor of each Parámetro.
3. WHILE the Robot_velocista is not connected or has not sent its Manifiesto, THE API SHALL return the Catálogo controllers with catalog-defined ranges and Presets and without the valor field.

### Requirement 2: Consultar la configuración actualmente cargada en el robot

**User Story:** As a pilot, I want to see which controller and parameter values are currently loaded on the robot, so that I know my starting point before tuning.

#### Acceptance Criteria

1. WHEN the Robot_velocista is connected and has sent its Manifiesto, THE API SHALL expose the controlador_activo and the valor of each Parámetro from the live Manifiesto.
2. IF the Robot_velocista is not connected or has not sent its Manifiesto, THEN THE API SHALL return a sin_manifiesto error.

### Requirement 3: Ajustar y guardar configuraciones de control

**User Story:** As a pilot, I want to adjust parameter values and save them as a named setup, so that I can reuse the configuration later.

#### Acceptance Criteria

1. THE API SHALL persist a Setup (Controlador plus Parámetro values) tied to a robot and version in the database.
2. THE API SHALL list the saved Setups of a robot so the Panel_de_configuración can recall them.
3. WHEN a Setup is created or edited, THE API SHALL validate every Parámetro value against the Controlador definition: within range, aligned to step, with max greater than or equal to base and vmin less than or equal to base.
4. IF a Parámetro value violates the Controlador constraints, THEN THE API SHALL reject the save and return the violated constraint as fuera_de_rango, paso_invalido, or parametros_incompatibles.
5. WHEN the pilot wants to apply an unsaved configuration, THE API SHALL require the configuration to be persisted as a Setup before applying it to the robot.

### Requirement 4: Aplicar un setup guardado al robot

**User Story:** As a pilot, I want to apply a saved setup to the robot in one action, so that I can test a configuration without manually assembling the command.

#### Acceptance Criteria

1. WHEN the pilot requests to apply a saved Setup by id, THE API SHALL load the Setup from the database and send the setup command to the Robot_velocista via the Gateway with the id_setup of the Setup.
2. WHILE validating the Setup before sending, THE API SHALL validate the loaded Setup against the live Manifiesto: the Controlador exists among the Manifiesto controllers and each Parámetro value is within the Manifiesto range and matches the declared type.
3. IF the Controlador of the Setup does not exist in the live Manifiesto, THEN THE API SHALL reject the apply with controlador_no_disponible.
4. IF a Parámetro of the Setup is outside the live Manifiesto range or does not match the declared type, THEN THE API SHALL reject the apply with fuera_de_rango.
5. IF a Parámetro required by the Controlador is missing from the Setup, THEN THE API SHALL reject the apply with parametro_desconocido.

### Requirement 5: Aplicar un preset del catálogo al robot

**User Story:** As a pilot, I want to apply a preset directly, so that I can quickly test a known starting point without first saving a setup.

#### Acceptance Criteria

1. WHEN the pilot requests to apply a Preset, THE API SHALL load the Preset values from the Catálogo, validate them against the live Manifiesto, and send the setup command to the Robot_velocista via the Gateway with id_setup set to null.
2. IF the Controlador of the Preset does not exist in the live Manifiesto, THEN THE API SHALL reject the apply with controlador_no_disponible.
3. IF a Parámetro of the Preset is outside the live Manifiesto range, THEN THE API SHALL reject the apply with fuera_de_rango.

### Requirement 6: Guardas de estado al aplicar configuración

**User Story:** As a pilot, I want the system to refuse applying a configuration when it is unsafe, so that I do not disturb the robot during a competition run or when it is not connected.

#### Acceptance Criteria

1. IF the Robot_velocista is not connected or has not sent its Manifiesto, THEN THE API SHALL reject the apply with sin_manifiesto before sending any command.
2. WHILE the Estado_del_robot is modo competencia and estado running, THE API SHALL reject any apply action with bloqueado_competencia.
3. IF the Robot_velocista stops responding between validation and delivery of the apply command, THEN THE API SHALL return dispositivo_no_disponible so the pilot can retry.

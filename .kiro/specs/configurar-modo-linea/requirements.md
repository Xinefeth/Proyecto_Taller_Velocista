# Requirements Document

## Introduction

The configurar-modo-linea feature lets the pilot choose the robot's functioning mode (prueba or competencia) and the track line color (negra or blanca) from the configuration panel. Mode and line are pure commands: the panel sends them through two independent, dedicated, higher-level endpoints — one for mode and one for line, with no combined endpoint — that validate each command against the live robot manifest and the robot's current state, then forward the command to the robot through the gateway and return the command sequence number. A dedicated read endpoint returns the current mode and line from the robot's live status so the panel can render its initial state without subscribing to the WebSocket. No database persistence is involved: mode and line live only as the last command sent and the last status received.

The feature adds a stricter state guard than the existing raw command path: mode and line changes are rejected whenever the robot is running, regardless of the current mode, so the pilot cannot disturb an active run in either prueba or competencia.

## Glossary

- **API**: Servicio backend que valida los comandos contra el manifiesto y el estado vivos, y los envía al robot por el gateway.
- **Panel_de_configuración**: Interfaz donde el piloto selecciona el modo de funcionamiento y el color de la línea de la pista.
- **Robot_velocista**: Dispositivo robot cuyo modo y color de línea se configuran; declara su manifiesto al conectarse y reporta su estado periódicamente.
- **Gateway**: Capa de la API que mantiene el estado vivo del robot en memoria (manifiesto y último Status) y envía comandos por WebSocket.
- **Manifiesto**: Declaración que el Robot_velocista envía al conectarse; lista los comandos que acepta, incluidos modo y linea.
- **Status**: Mensaje periódico del Robot_velocista que reporta el estado, el modo, el color de línea y otros canales; la API conserva el último recibido en el estado vivo.
- **estado**: Estado operativo del Robot_velocista: ready, calibrating, running, stopped o error.
- **modo**: Modo de funcionamiento del Robot_velocista: prueba o competencia.
- **linea**: Color de la línea de la pista que el Robot_velocista sigue: negra o blanca.
- **seq**: Número de secuencia del comando enviado al Robot_velocista; el ack del robot lo repite para confirmar la entrega.

## Requirements

### Requirement 1: Consultar el modo y el color de línea actuales

**User Story:** As a pilot, I want to see the current mode and line color of the robot, so that the configuration panel can render its initial state without subscribing to the WebSocket.

#### Acceptance Criteria

1. WHEN the Panel_de_configuración requests the current configuration, THE API SHALL return the modo and linea from the last Status received from the Robot_velocista.
2. IF the Robot_velocista is not connected or has not sent a Status, THEN THE API SHALL return a sin_estado error.

### Requirement 2: Configurar el modo de funcionamiento

**User Story:** As a pilot, I want to select the functioning mode (prueba or competencia) from the configuration panel, so that the robot operates in the appropriate mode for testing or for competition.

#### Acceptance Criteria

1. WHEN the Panel_de_configuración sends a modo change request with the value prueba or competencia, THE API SHALL validate the command against the Manifiesto, send the modo command to the Robot_velocista via the Gateway, and return the seq.
2. IF the modo value is neither prueba nor competencia, THEN THE API SHALL reject the request with comando_invalido before sending any command.

### Requirement 3: Configurar el color de la línea

**User Story:** As a pilot, I want to select the track line color (negra or blanca) from the configuration panel, so that the robot follows the correct line on the track.

#### Acceptance Criteria

1. WHEN the Panel_de_configuración sends a linea change request with the value negra or blanca, THE API SHALL validate the command against the Manifiesto, send the linea command to the Robot_velocista via the Gateway, and return the seq.
2. IF the linea value is neither negra nor blanca, THEN THE API SHALL reject the request with comando_invalido before sending any command.

### Requirement 4: Guardas de estado al configurar modo y línea

**User Story:** As a pilot, I want the system to refuse mode and line changes while the robot is running, so that I do not disturb an active run in either mode.

#### Acceptance Criteria

1. WHILE the Robot_velocista's estado is running and the modo is competencia, THE API SHALL reject any modo or linea change with bloqueado_competencia before sending any command.
2. WHILE the Robot_velocista's estado is running and the modo is prueba, THE API SHALL reject any modo or linea change with ocupado before sending any command.
3. WHILE the Robot_velocista's estado is ready, stopped, calibrating, or error, THE API SHALL accept modo and linea changes.
4. IF the Robot_velocista is not connected or has not sent its Manifiesto, THEN THE API SHALL reject the modo or linea change with sin_manifiesto before sending any command.
5. IF the Manifiesto does not declare the modo or linea command, THEN THE API SHALL reject the change with comando_desconocido before sending any command.
6. IF the Robot_velocista stops responding between validation and delivery of a modo or linea command, THEN THE API SHALL return dispositivo_no_disponible so the pilot can retry.

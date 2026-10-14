# Requirements Document

## Introduction

EN-26 is an enabler: it connects the console's main flow — catalog, builder, and runs — to the
API so that it stops living in the browser (bundled data and `localStorage`) and persists in
PostgreSQL. The database starts with the **reference structure only** (component types, slots,
controllers, and regulation profiles, seeded by an Alembic migration); all **user data**
(components, robots, versions, runs) starts empty and is created from the console, persisting in
the database. The flow is vertical and end-to-end: register a component → create a robot → build
it with those components → run it in Simulated mode, with each step reflected in the database.

This enabler does not change the interface; it wires the existing screens to the API. In
fixture/test mode the previous local behavior (bundled catalog + `localStorage`) is preserved so
the unit tests keep running without a backend.

## Glossary

- **Consola**: Frontend SPA (Vite) served by the API; registers data and drives the flow.
- **API**: FastAPI backend that validates and persists the domain data in PostgreSQL.
- **Estructura_de_referencia**: Read-only catalog layer the app needs to work — component types,
  slots (ranuras), controllers, and regulation profiles. No endpoints create it; it is seeded.
- **Dato_de_usuario**: Data the user creates from the console — components, robots, versions, runs.
- **apiMode**: Console runtime mode where the robot/catalog source is the API (production). Its
  opposite is fixture mode (`initialRobots` injected), which keeps the local/`localStorage` path.
- **Componente**: Catalog entry of a given component type, with price, mass, specs, and stock.
- **Robot**: Velocista/minisumo identity; may have versions. Its current version is `version_actual`.
- **Version**: A build of a robot: the pieces placed in each slot, persisted with a snapshot.
- **Corrida**: A run with its laps (vueltas), associated to a robot version.
- **Migración_0008**: Alembic migration that seeds the Estructura_de_referencia and nothing else.

## Requirements

### Requirement 1: Sembrar solo la estructura de referencia

**User Story:** As the system owner, I want the database to start with only the reference
structure and no preloaded user data, so that everything the console shows is what the user
created and persistence can be demonstrated.

#### Acceptance Criteria

1. WHEN `alembic upgrade head` runs on an empty database, THE API SHALL create the schema and seed
   exactly the reference structure (component types, slots, controllers, profiles).
2. THE Migración_0008 SHALL NOT insert any component, robot, version, or run.
3. THE migration chain SHALL remain linear with a single head (`0008_referencia`).

### Requirement 2: Registrar componentes en la base de datos

**User Story:** As a club member, I want the components I register to be saved in the database and
the catalog to come from the database, so that my catalog persists and is not lost.

#### Acceptance Criteria

1. WHEN the user registers a component in the Catálogo in apiMode, THE Consola SHALL send it to the
   API (`POST /components`) and the component SHALL be stored in the `componente` table.
2. WHILE in apiMode, THE Consola SHALL read the catalog from the API (`GET /components`).
3. WHEN the catalog is reloaded after a successful registration, THE registered component SHALL
   still be present.
4. IF the API rejects the component, THEN THE Consola SHALL surface the error and SHALL NOT claim
   it was saved.

### Requirement 3: Crear robots en la base de datos

**User Story:** As a club member, I want to create a robot from the console and have it saved in
the database, so that the builder reflects real persisted robots.

#### Acceptance Criteria

1. WHILE the database has no robots in apiMode, THE Consola SHALL render a "Crear primer robot"
   state instead of a blank screen.
2. WHEN the user creates a robot in apiMode, THE Consola SHALL send it to the API (`POST /robots`)
   and the robot SHALL be stored in the `robot` table.
3. WHEN the robot list is refreshed after creation, THE new robot SHALL appear and be selectable.

### Requirement 4: Guardar el armado del robot en la base de datos

**User Story:** As a club member, I want to build a robot with the components I saved and persist
that build, so that the robot's configuration is stored and reused.

#### Acceptance Criteria

1. WHEN the user saves a version of a robot in apiMode, THE Consola SHALL send it to the API
   (`POST /robots/{id}/versions`) with the chosen pieces.
2. THE saved version SHALL reference components that exist in the database and SHALL be stored in
   `version` and `version_componente`, becoming the robot's current version.
3. IF a mandatory slot is missing for an "Actual" version, THEN THE API SHALL reject the save and
   THE Consola SHALL surface the error.

### Requirement 5: Guardar las corridas del robot seleccionado

**User Story:** As a pilot, I want the laps of a run to be saved in the database for the robot I
selected, so that I can review the run afterwards.

#### Acceptance Criteria

1. WHEN the user starts a run in Simulated mode with a selected robot, THE Consola SHALL request a
   simulated run for that robot (`POST /runs/simulated?robot_id=<selected>`).
2. THE API SHALL generate and persist the run and its laps associated to the selected robot's
   current version (not to a fixed robot), in `corrida` and `vuelta`.
3. THE run's laps SHALL be retrievable (`GET /runs/{id}/laps`).
4. IF the selected robot has no current version, THEN THE API SHALL reject the run with a clear
   error.

### Requirement 6: Verificabilidad y modo fixture

**User Story:** As the system owner, I want every record visible in its table and the test suite
unaffected, so that I can demonstrate persistence and keep development safe.

#### Acceptance Criteria

1. THE records of the flow SHALL be visible in `componente`, `robot`, `version`,
   `version_componente`, `corrida`, and `vuelta` (e.g. via Adminer).
2. WHILE in fixture mode (`initialRobots` injected), THE Consola SHALL keep the local behavior
   (bundled catalog + `localStorage`) so the unit tests run without a backend.
3. THE full flow SHALL work end-to-end in the deployed environment (console + API + PostgreSQL).

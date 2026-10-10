# Constitución · APAEC Lab

Sistema de gestión y optimización para competencia robótica (velocista de línea).
Monolito modular en monorepo: backend **FastAPI**, consola **React** y firmware **ESP32**.

- **Versión:** 1.0.0
- **Ratificada:** 2026-10-10
- **Última enmienda:** 2026-10-10

Esta constitución es la fuente de verdad de las reglas del proyecto. Toda spec, plan y
tarea debe respetarla. Donde el código actual no la cumpla, se marca como pendiente en el
`plan.md` y el `tasks.md` de la HU correspondiente, no se silencia.

---

## Principio 1 · Idioma del código

Los **identificadores** van en **inglés**: nombres de módulos, archivos, clases,
funciones y variables; tablas y columnas de la base de datos; rutas de la API; campos
JSON; tipos y campos de los mensajes WebSocket; valores de enum.

Los **textos que ve el usuario** van en **español**: etiquetas de la interfaz y los
mensajes de error mostrados (p. ej. el `detalle` de un error de negocio).

Pueden ir en **español**: las descripciones de Swagger (`summary`/`description`), los
comentarios, los docstrings y los mensajes de commit.

El renombrado a inglés es una **migración en curso**; su mapa canónico es
[`docs/rename-glosario.md`](../../docs/rename-glosario.md). Mientras dure, parte del
contrato de mensajes y de la consola sigue en español (ver cada `plan.md`).

## Principio 2 · Arquitectura: monolito modular en monorepo

Un solo repositorio con tres piezas: `api/` (FastAPI), `consola/` (React) y
`firmware/` (ESP32). El backend es un **monolito modular**: un proceso con canales de
entrada (REST y WebSocket) y módulos de negocio independientes.

Los **límites entre módulos** se verifican con `api/tests/unit/test_arquitectura.py`;
ninguna HU puede romper esas reglas (p. ej. los módulos no importan de `app.gateway`).

## Principio 3 · Framework

Backend en **FastAPI**; consola en **React** (Vite + TypeScript). No se introducen
frameworks alternativos para el mismo fin sin enmendar esta constitución.

## Principio 4 · Swagger obligatorio

Cada endpoint REST debe documentarse en OpenAPI/Swagger con: `tags`, `operation_id`
(en inglés), `summary`, `description`, `response_model` y `status_code` explícitos, y
las **respuestas de error documentadas con ejemplos** (`responses={...}`).

## Principio 5 · Persistencia primero

La base de datos es la fuente de verdad: **PostgreSQL + SQLAlchemy + Alembic**. Todo
cambio de esquema se hace con una **migración de Alembic** (renombrar, nunca borrar
datos) y se actualizan semillas y generador. El registro integral en BD es el punto de
partida del trabajo de hardware/servicio.

## Principio 6 · WebSockets para el robot

El tiempo real va por **WebSocket**, no por REST. Canales: `/ws/robot`,
`/ws/cronometro` y `/ws/consola`. Todo mensaje viaja en el **sobre**
`{tipo, seq, ts, datos}` (contrato de mensajes EN-02). REST se reserva para CRUD e
historial; la telemetría (estado, señales/regleta) va por WebSocket.

## Principio 7 · Desarrollo guiado por especificaciones (SDD)

Cada historia de usuario tiene, **antes de implementar**, su `spec.md` (qué y por qué,
sin tecnología), su `plan.md` (cómo, con la tecnología) y su `tasks.md` (tareas
accionables). Viven en `specs/<nnn-nombre>/` y se versionan en el repo para que todo el
equipo trabaje sobre la misma especificación.

## Principio 8 · Renombrado como migración referenciada

El plan de paso a inglés de [`docs/rename-glosario.md`](../../docs/rename-glosario.md) es
una migración viva y referenciada. Cualquier identificador nuevo nace en inglés; los que
siguen en español se tratan como deuda registrada, no como estado deseado.

---

## Gobernanza

- Esta constitución prevalece sobre cualquier práctica previa en conflicto.
- Enmendarla requiere acuerdo del equipo y subir la versión (SemVer): **MAJOR** para
  cambios incompatibles de principios, **MINOR** para un principio nuevo, **PATCH** para
  aclaraciones.
- Las PR y revisiones verifican el cumplimiento; las desviaciones justificadas se anotan
  en el `plan.md` de la HU.
- No se hace commit ni push sin aprobación explícita.

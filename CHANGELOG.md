# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones con [SemVer](https://semver.org/lang/es/): `v0.1.0` al cerrar el Sprint 1 y `v0.2.0` al cerrar el Sprint 2.

## [Sin publicar]

### Agregado
- EN-04 (edición): `PATCH /api/componentes/{componente_id}` edita parcialmente la ficha con validación según el tipo y bloqueo de fila; conserva stock y revisión, rechaza archivados y revierte ante fallos. Contrato EN-01 actualizado. Versiones históricas pendientes.
- EN-04 (ficha): `GET /api/componentes/{componente_id}` consulta ficha y stock, incluidos archivados; valida el ID y responde 404 si no existe. Pruebas HTTP y contrato EN-01 actualizado.
- EN-04 (registro): `POST /api/componentes` crea ficha e inventario juntos, genera IDs y valida especificaciones según el tipo. Pruebas de persistencia, rechazo de datos inválidos y reversión ante fallos; contrato EN-01 actualizado.
- EN-04 (consulta): `GET /api/componentes` con stock, paginación, filtro por tipo y búsqueda sin tildes españolas/mayúsculas; excluye archivados y valida parámetros. Pruebas HTTP y contrato EN-01 actualizado.
- EN-04 (catálogo inicial): semillas de los 25 componentes del prototipo y su inventario; repetir la carga conserva fichas, precios, stock y revisiones existentes. Velocista 001 pendiente.
- EN-04 (API): `GET /api/tipos-componentes` consulta los tipos, campos y capacidades en PostgreSQL, con pruebas HTTP de datos persistidos, base vacía y error 503. Contrato EN-01 actualizado.
- EN-04 (semillas): comando `python -m app.semillas` para cargar los 14 tipos de componente, con campos/capacidades y carga repetible que conserva los registros existentes. Velocista 001 pendiente.
- EN-04 (catálogo): modelos SQLAlchemy y migración `0002_catalogo` para tipos de componente, componentes e inventario, con pruebas en esquemas temporales de PostgreSQL. Semillas de robots y demás endpoints pendientes.
- DO-03: modelo entidad-relación, diccionario de datos y trazabilidad de campos del prototipo, con capacidades declarativas de los 14 tipos de componente.
- EN-01: contrato OpenAPI REST con ejemplos por operación, distinción de rutas existentes/propuestas y validación automática del contrato y de su cobertura del catálogo.
- Consola: componentes comunes de gestión (EN-06) — tabla, buscador, chips, pestañas y formularios con validación — usados en el Catálogo y en el registro manual de componentes (HU-02); la búsqueda ya no distingue tildes.
- Contrato de mensajes v1.0 (EN-02): sobre común, manifiesto, telemetría, comandos y eventos del robot y del cronómetro, con versión.
- Gateway: validación de cada mensaje, ack de mensajes críticos, descarte de duplicados y de señales fuera de orden, avisos de canales.
- API: `GET /api/dispositivos/velocista/manifiesto` y `POST /api/dispositivos/{d}/comandos` validados contra el manifiesto y las reglas de competencia.
- Ejemplos JSON y JSON Schema del contrato; pruebas de contrato, de comandos y del gateway; herramienta `robot_falso.py`.
- Firmware del robot y del cronómetro según el contrato.
- Monorepo con `api/`, `consola/`, `firmware/` y `docs/` (EN-03).
- API: estructura de 7 módulos (router, service, models, schemas), gateway WebSocket, formato estándar de errores, registro de peticiones, migración inicial y pruebas por tipo.
- Consola: estructura por páginas con el sistema visual del prototipo y verificación del entorno.
- Firmware: estructura base del robot y del cronómetro con lógica pura probada en PC.
- Entorno: Docker Compose para PostgreSQL, scripts de arranque, CI y convenciones de trabajo.

# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones con [SemVer](https://semver.org/lang/es/): `v0.1.0` al cerrar el Sprint 1 y `v0.2.0` al cerrar el Sprint 2.

## [Sin publicar]

### Agregado
- EN-04: completadas las 32 operaciones REST de EN-01, con edición/archivado de robots, creación transaccional de versiones, catálogos de control y reglamento, setups y consultas/notas de corridas y vueltas.
- Migración `0005_operaciones`, semillas repetibles de 3 controladores y 4 perfiles, demo opcional de corrida simulada y guía de pruebas CRUD.
- Verificación de pertenencia, parámetros de control, conservación de historial, bloqueo por corrida activa y concurrencia real de versión/stock; pruebas de escritura aisladas de las tablas del usuario.
- EN-04 (registro de robots): `POST /api/robots` crea identificación sin versiones, con ID generado, código corto único y firmware opcional. Pruebas de persistencia, conflictos, validación y reversión; contrato EN-01 actualizado.
- EN-04 (consulta de historial): GET de versiones paginadas y de una versión por robot, con piezas e instantáneas persistidas. Pruebas de pertenencia, archivados y conservación del historial al editar catálogo; contrato EN-01 actualizado.
- EN-04 (historial inicial): migración `0004_versiones`, ranuras y semilla v0/v1 de Velocista 001 con instantáneas de piezas, conservando historial existente. Inventario calcula demanda de la última versión de robots activos, disponibilidad y faltantes. Endpoints de versiones pendientes.
- EN-04 (consulta de robots): `GET /api/robots` lista activos con paginación; `GET /api/robots/{robot_id}` consulta identificación, incluidos archivados. Pruebas HTTP y contrato EN-01 actualizado; versiones y piezas pendientes.
- EN-04 (robot inicial): modelo y migración `0003_robot`, con código corto único; la carga transaccional agrega la identificación de Velocista 001 sin sobrescribir existentes. Versiones, piezas, endpoints de robots y demanda de inventario pendientes.
- EN-04 (ajuste de existencias): `PUT /api/inventario/{componente_id}` fija stock y compara/incrementa revisión en un único UPDATE; rechaza revisiones obsoletas y admite archivados. Pruebas de persistencia, conflicto, validación y reversión; contrato EN-01 actualizado. Demanda de robots pendiente.
- EN-04 (existencias): `GET /api/inventario` consulta stock y revisión reales con paginación, incluidos archivados con stock. Etapa previa al armador persistido: asignaciones en cero; cálculo de demanda de robots pendiente. Pruebas HTTP y contrato EN-01 actualizado.
- EN-04 (archivado): `DELETE /api/componentes/{componente_id}` realiza una baja lógica repetible, conserva ficha e inventario y responde 204 sin cuerpo. Pruebas de consulta posterior, exclusión del listado y reversión ante fallos; contrato EN-01 actualizado.
- EN-04 (edición): `PATCH /api/componentes/{componente_id}` edita parcialmente la ficha con validación según el tipo y bloqueo de fila; conserva stock y revisión, rechaza archivados y revierte ante fallos. Contrato EN-01 actualizado. Versiones históricas pendientes.
- EN-04 (ficha): `GET /api/componentes/{componente_id}` consulta ficha y stock, incluidos archivados; valida el ID y responde 404 si no existe. Pruebas HTTP y contrato EN-01 actualizado.
- EN-04 (registro): `POST /api/componentes` crea ficha e inventario juntos, genera IDs y valida especificaciones según el tipo. Pruebas de persistencia, rechazo de datos inválidos y reversión ante fallos; contrato EN-01 actualizado.
- EN-04 (consulta): `GET /api/componentes` con stock, paginación, filtro por tipo y búsqueda sin tildes españolas/mayúsculas; excluye archivados y valida parámetros. Pruebas HTTP y contrato EN-01 actualizado.
- EN-04 (catálogo inicial): semillas de los 25 componentes del prototipo y su inventario; repetir la carga conserva fichas, precios, stock y revisiones existentes. Velocista 001 pendiente.
- EN-04 (API): `GET /api/tipos-componentes` consulta los tipos, campos y capacidades en PostgreSQL, con pruebas HTTP de datos persistidos, base vacía y error 503. Contrato EN-01 actualizado.
- EN-04 (semillas): comando `python -m app.semillas` para cargar los 14 tipos de componente, con campos/capacidades y carga repetible que conserva los registros existentes. Velocista 001 pendiente.
- EN-04 (catálogo): modelos SQLAlchemy y migración `0002_catalogo` para tipos de componente, componentes e inventario, con pruebas en esquemas temporales de PostgreSQL. Semillas de robots y demás endpoints pendientes.
- Consola: lo que se registra a mano (componentes y robots) se conserva en el navegador y se puede restablecer a los datos de ejemplo (HU-02, HU-06); no se pueden registrar componentes repetidos.
- Consola: 52 pruebas del resumen del robot (costo, masa y consumo), la compatibilidad, el reglamento, la ficha, el inventario y el armador (HU-03, HU-04, HU-06, HU-07).
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

### Corregido
- Consola: un robot nuevo queda con su versión 1 y su lista de piezas; antes el primer guardado creaba una v2 y dejaba la v1 vacía (HU-06).

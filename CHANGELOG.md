# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones con [SemVer](https://semver.org/lang/es/): `v0.1.0` al cerrar el Sprint 1 y `v0.2.0` al cerrar el Sprint 2.

## [Sin publicar]

### Agregado
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

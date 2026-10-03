# Cambios

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versiones con [SemVer](https://semver.org/lang/es/): `v0.1.0` al cerrar el Sprint 1 y `v0.2.0` al cerrar el Sprint 2.

## [Sin publicar]

### Agregado
- Monorepo con `api/`, `consola/`, `firmware/` y `docs/` (EN-03).
- API: estructura de 7 módulos (router, service, models, schemas), gateway WebSocket, formato estándar de errores, registro de peticiones, migración inicial y pruebas por tipo.
- Consola: estructura por páginas con el sistema visual del prototipo y verificación del entorno.
- Firmware: estructura base del robot y del cronómetro con lógica pura probada en PC.
- Entorno: Docker Compose para PostgreSQL, scripts de arranque, CI y convenciones de trabajo.

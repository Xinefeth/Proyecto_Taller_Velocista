# Tareas · HU-13 Seleccionar el robot

Marcadas `[x]` las ya hechas (verificadas en el código); `[ ]` las pendientes.

## Backend (builder / devices)

- [x] Endpoint `GET /api/robots` lista robots con tipo, firmware y versión actual — `api/app/modulos/armador/router.py`
- [x] Endpoints de versiones (`GET /api/robots/{robot_id}/versions`, `.../{version_id}`) — `api/app/modulos/armador/router.py`
- [x] Endpoint `GET /api/slots` (ranuras del armador) — `api/app/modulos/armador/router.py`
- [x] Endpoint `GET /api/devices/velocista/manifest` (paneles) — `api/app/gateway/comandos.py`
- [x] Swagger de calidad en los endpoints de selección (summary/description/responses) — `api/app/modulos/armador/router.py`
- [x] Usar el ejemplo real `docs/contrato/ejemplos/velocista.manifiesto.json` como `example` del endpoint de manifiesto — `api/app/gateway/comandos.py`. Verificado: OpenAPI coincide con el JSON real; 12 tests aprobados (documentación + gateway).
- [x] Documentar la respuesta `503` en Swagger — routers del armador y gateway, con ejemplo `base_no_disponible`. El gateway conserva además el 503 de pérdida del enlace y aclara que actualmente no consulta BD. Verificado: 26 tests aprobados (Swagger, comandos, arquitectura y gateway).

## Consola

- [x] Modal de manifiesto — `consola/src/components/ManifiestoModal.tsx`
- [x] Catálogo de robots (prototipo, datos locales) — `consola/src/datos/robots.ts`
- [x] Consumir `GET /api/robots` en vez de datos locales para listar robots — `api.robots.selection()` recorre las páginas y consulta la versión actual por ID. Lista de producción exclusivamente de la API, con carga, vacío y error/reintento. Armador muestra tipo, versión y firmware. Fixtures locales por inyección explícita en tests. Verificado: 120 tests aprobados; TypeScript y ESLint sin errores.
- [x] Ocultar dinámicamente los paneles de dispositivos que el robot no declara (p. ej. sin encoder) — Armador y ManifiestoModal usan los sensores/actuadores del manifiesto esperado. Sin batería tampoco se declara ese panel. Verificado: 39 tests aprobados (dominio, Armador y modal), incluyendo cambio entre robots con/sin encoder y robot sin piezas; TypeScript y ESLint sin errores.

## Renombrado (migración en curso)

- [ ] Campos del manifiesto a inglés (`tipo_robot→robot_type`, `sensores→sensors`, …) — contrato 2.0, toca firmware — `api/app/contrato/manifiesto.py` y `firmware/`

## Tests

- [x] Lectura del manifiesto por REST y WS — `api/tests/websocket/test_gateway.py`
- [ ] Verificar CRUD de robots con PostgreSQL levantado — `api/tests/integration/test_robot_bd.py` (hoy skipped)

Las dos tareas pendientes requieren confirmación del usuario. Plan y requisitos en
`plan.md`, sección «Propuestas pendientes de confirmación». No se ejecutaron en esta revisión.

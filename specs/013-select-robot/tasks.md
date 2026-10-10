# Tareas · HU-13 Seleccionar el robot

Marcadas `[x]` las ya hechas (verificadas en el código); `[ ]` las pendientes.

## Backend (builder / devices)

- [x] Endpoint `GET /api/robots` lista robots con tipo, firmware y versión actual — `api/app/modulos/armador/router.py`
- [x] Endpoints de versiones (`GET /api/robots/{robot_id}/versions`, `.../{version_id}`) — `api/app/modulos/armador/router.py`
- [x] Endpoint `GET /api/slots` (ranuras del armador) — `api/app/modulos/armador/router.py`
- [x] Endpoint `GET /api/devices/velocista/manifest` (paneles) — `api/app/gateway/comandos.py`
- [x] Swagger de calidad en los endpoints de selección (summary/description/responses) — `api/app/modulos/armador/router.py`
- [ ] Usar el ejemplo real `docs/contrato/ejemplos/velocista.manifiesto.json` como `example` del endpoint de manifiesto — `api/app/gateway/comandos.py`
- [ ] Documentar la respuesta `503` en Swagger — `api/app/modulos/armador/router.py`, `api/app/gateway/comandos.py`

## Consola

- [x] Modal de manifiesto — `consola/src/components/ManifiestoModal.tsx`
- [x] Catálogo de robots (prototipo, datos locales) — `consola/src/datos/robots.ts`
- [ ] Consumir `GET /api/robots` en vez de datos locales para listar robots — `consola/src/services/api.ts`
- [ ] Ocultar dinámicamente los paneles de dispositivos que el robot no declara (p. ej. sin encoder) — `consola/src/pages/Armador.tsx`, `consola/src/components/ManifiestoModal.tsx`

## Renombrado (migración en curso)

- [ ] Campos del manifiesto a inglés (`tipo_robot→robot_type`, `sensores→sensors`, …) — contrato 2.0, toca firmware — `api/app/contrato/manifiesto.py` y `firmware/`

## Tests

- [x] Lectura del manifiesto por REST y WS — `api/tests/websocket/test_gateway.py`
- [ ] Verificar CRUD de robots con PostgreSQL levantado — `api/tests/integration/test_robot_bd.py` (hoy skipped)

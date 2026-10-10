# Tareas · HU-16 Calibrar los sensores y arrancar

## Backend (devices / gateway)

- [x] Endpoint `POST /api/devices/{device}/commands` — `api/app/gateway/comandos.py`
- [x] Bloqueo de `arrancar` sin calibrar (409 `no_calibrado`) — `api/app/gateway/comandos.py`
- [x] Reglas de competencia (solo `detener` corriendo) y comando desconocido — `api/app/gateway/comandos.py`
- [x] Envío del comando al robot y `ack` por `/ws/consola` — `api/app/gateway/ws.py`
- [x] Swagger de calidad con respuestas de error y ejemplos — `api/app/gateway/comandos.py`
- [x] Documentar la respuesta `503` en Swagger — `api/app/gateway/comandos.py`. Revisión 2026-10-10: ejemplo confirmado en OpenAPI y 11 pruebas del gateway aprobadas.

## Consola

- [x] Botón ARRANCAR/DETENER — `consola/src/pages/Control.tsx`
- [x] Bloqueo de arranque hasta calibrar (aviso "Calibra los sensores antes de arrancar") — `consola/src/pages/Control.tsx`
- [x] Panel de calibración con estados calibrating/calibrated/running — `consola/src/pages/Control.tsx`
- [x] Confirmar que DETENER nunca queda deshabilitado (criterio "siempre disponible") — `consola/src/pages/Control.tsx` (prueba: `consola/src/pages/Control.test.tsx`: 5 passed, 2026-10-10). Alcance: botón combinado habilitado en los cinco estados; DETENER solo aparece corriendo. No valida parada física.

## Renombrado (migración en curso)

- [ ] Comandos y estados a inglés (`calibrar→calibrate`, `arrancar→start`, `detener→stop`; estados `listo/calibrando/...`) — contrato 2.0, toca firmware — `api/app/contrato/robot.py`, `api/app/contrato/catalogo.py`, `firmware/`

## Tests

- [x] Comandos validados y enviados; rechazo por estado inválido — `api/tests/websocket/test_gateway.py`
- [ ] Verificar que la calibración termina en < 20 s — **bloqueado**: `api/herramientas/robot_falso.py` marca `calibrado = True` al instante (sin estado `calibrando` ni espera temporizada), así que no permite medir una duración real. Falta simular el tiempo en el robot falso (ver nota en `plan.md`).
  Revisión 2026-10-10: ejecución directa del stub `calibrate`: 0.0000018 s;
  no acredita calibración real ni tiempo de ida/vuelta por WebSocket. No se marca [x].

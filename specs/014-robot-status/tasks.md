# Tareas · HU-14 Consultar el estado del robot

## Backend (gateway / system)

- [x] Mensaje `estado` del robot (batería, lazo, rssi, estado) en el contrato — `api/app/contrato/robot.py`
- [x] Gateway valida y redifunde `estado` a la consola — `api/app/gateway/ws.py`
- [x] Mensaje `enlace` (conectado/desconectado) a la consola — `api/app/gateway/ws.py`
- [x] `GET /api/health` con dispositivos conectados — `api/app/main.py`
- [ ] Definir el origen real del "ms" del enlace (latencia) — contrato/gateway

## Consola

- [x] Barra superior con enlace (dBm y ms), lazo (Hz), batería y estado — `consola/src/components/Strip.tsx`
- [x] Indicación de "SIN ENLACE" con frescura en segundos — `consola/src/components/Strip.tsx`
- [ ] Alimentar la barra con datos reales del WebSocket en vez de simulados — `consola/src/stores/ConexionContext.tsx`, `consola/src/components/Strip.tsx`
- [ ] Verificar refresco ≥ 1/s y pérdida de enlace < 2 s con robot real o `robot_falso.py`

## Renombrado (migración en curso)

- [ ] Campos de `estado` a inglés (`estado→state`, `calibrado→calibrated`, `lazo_hz→loop_hz`, `bateria_v→battery_v`, …) — contrato 2.0, toca firmware — `api/app/contrato/robot.py`, `firmware/`

## Tests

- [x] `enlace` y `GET /api/health` — `api/tests/websocket/test_gateway.py`, `api/tests/integration/test_salud.py`
- [ ] Prueba de tiempos (1 s / 2 s) — pendiente de entorno con robot/robot_falso

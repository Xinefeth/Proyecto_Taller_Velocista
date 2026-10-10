# Tareas · HU-15 Visualizar la regleta de sensores

## Backend (gateway / devices)

- [x] Mensaje `senales` en el contrato (canales del grupo señales, ~20 Hz) — `api/app/contrato/robot.py`
- [x] El manifiesto declara la regleta (16 canales, 2× QTR-8A) — `api/app/contrato/manifiesto.py`
- [x] Gateway valida y redifunde `senales`; revisa canales contra el manifiesto — `api/app/gateway/ws.py`, `api/app/contrato/validacion.py`
- [ ] Verificar que `robot_falso.py` emita los 16 canales de la regleta en `senales` — `api/herramientas/robot_falso.py`

## Consola

- [ ] Dibujar las **16 lecturas como barras** con su valor — `consola/src/pages/Telemetria.tsx` (o componente nuevo de regleta)
- [ ] Calcular y mostrar la **posición (mm)** a partir de los 16 canales — `consola/src/logica/`
- [ ] Mostrar el **error** y si la línea está **centrada** — `consola/src/pages/Telemetria.tsx`
- [x] Vista de telemetría base (error/PWM de motores) — `consola/src/pages/Telemetria.tsx`

## Renombrado (migración en curso)

- [ ] `senales→signals`, `canales→channels`, `regleta→sensor_bar` — contrato 2.0, toca firmware — `api/app/contrato/robot.py`, `firmware/`

## Tests

- [x] Validación de `senales`/canales en el gateway — `api/tests/websocket/test_gateway.py`
- [ ] Prueba de la vista de regleta (16 barras + posición + centrada) — pendiente al implementar la vista

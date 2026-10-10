# Tareas · HU-15 Visualizar la regleta de sensores

## Backend (gateway / devices)

- [x] Mensaje `senales` en el contrato (canales del grupo señales, ~20 Hz) — `api/app/contrato/robot.py`
- [x] El manifiesto declara la regleta (16 canales, 2× QTR-8A) — `api/app/contrato/manifiesto.py`
- [x] Gateway valida y redifunde `senales`; revisa canales contra el manifiesto — `api/app/gateway/ws.py`, `api/app/contrato/validacion.py`
- [x] Verificar que `robot_falso.py` emita los 16 canales de la regleta en `senales` — `api/herramientas/robot_falso.py` (ya emite `canales.regleta` como lista de 16; contrato lo admite vía `ValorCanal=list[int]`)
- [x] Comprobar la emisión con una captura sin red — `api/tests/unit/test_sensor_strip.py`; 44 pruebas de emisor, contrato, gateway y arquitectura aprobadas.

## Consola

- [x] Dibujar las **16 lecturas como barras** con su valor — `consola/src/pages/Control.tsx` (`Regleta()`)
- [x] Mostrar la **posición (mm)** — `consola/src/pages/Control.tsx` (`Regleta()`)
- [x] Mostrar el **error** y si la línea está **centrada** — `consola/src/pages/Control.tsx` (`Regleta()`)
- [x] Vista de telemetría base (error/PWM de motores) — `consola/src/pages/Control.tsx`
- [x] Alimentar la regleta con los canales reales del mensaje `senales` del WebSocket en lugar de la simulación (calcular posición/error/centrada desde los 16 canales; simulación como respaldo) — `consola/src/logica/strip.ts`, `consola/src/pages/Control.tsx`

## Renombrado (migración en curso)

- [ ] `senales→signals`, `canales→channels`, `regleta→sensor_bar` — contrato 2.0, toca firmware — `api/app/contrato/robot.py`, `firmware/`

## Tests

- [x] Validación de `senales`/canales en el gateway — `api/tests/websocket/test_gateway.py`
- [x] Prueba de la vista de regleta (16 barras + posición + centrada) — `consola/src/pages/Regleta.test.tsx`
- [x] Derivar el error de los 16 canales y rechazar muestras incompletas o no finitas — `consola/src/logica/strip.ts`.
- [x] Verificar centro, extremos, línea perdida, último mensaje y respaldo simulado — 17 pruebas específicas HU-15 aprobadas (11 de lógica y 6 de vista).

## Resultado de la revisión

- Backend: 44 pruebas aprobadas; Ruff sin errores en emisor y prueba nueva.
- Consola: HU-15 aprobada. Última suite completa: 114 aprobadas y 3 fallidas en
  `src/components/gestion/RegistroManual.test.tsx` (carga de robots; fuera de HU-15).
- Renombrado del contrato/firmware pendiente de confirmación; sin commit ni push.

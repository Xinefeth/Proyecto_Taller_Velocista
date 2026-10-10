# Plan técnico · HU-15 Visualizar la regleta de sensores

Cómo está construido hoy, leído del código. **HU-15 no tiene endpoint REST.**

## Módulos involucrados

- **gateway** (`api/app/gateway/ws.py`): recibe `senales` del robot y las redifunde a la
  consola; revisa los canales contra el manifiesto.
- **devices** (`api/app/gateway/comandos.py`): el manifiesto declara la regleta.
- **Consola** (`consola/src/`): dibujo de la telemetría.

## Endpoints REST

Ninguno (por diseño). La regleta es telemetría en vivo.

## Mensajes WebSocket

- `manifiesto`: declara el sensor **regleta** (16 canales, 2 módulos QTR-8A vía
  multiplexor). En el prototipo, `v001` expone `regleta` con `canales: 16, modulos: 2`
  (ver `consola/src/logica/dominio.test.ts`).
- `senales` (robot → API por `/ws/robot`, ~20 Hz mientras corre): valores de los canales
  del grupo `senales`; incluye los canales de la regleta. Definido en
  `api/app/contrato/robot.py` (`Senales`).
- El gateway valida los canales contra el manifiesto con
  `api/app/contrato/validacion.py` (`revisar_canales`), avisa pero no descarta la muestra.

## Tablas

- Ninguna: telemetría en vivo, no se persiste.

## Componentes de la consola

- `consola/src/pages/Telemetria.tsx`: vista de telemetría; hoy dibuja **error y PWM de
  los motores** (canvas) y permite alternar señales (`toggleSenal`).
- `consola/src/logica/dominio.ts`: calcula compatibilidad (p. ej. que el multiplexor
  alcance para los 16 canales), no la visualización de la regleta.

## Tests que lo cubren

- `api/tests/websocket/test_gateway.py`: recepción y validación de `senales`/canales.
- `consola/src/types/contrato.test.ts`: separa los canales del manifiesto por grupo.
- `consola/src/logica/dominio.test.ts`: la regleta de `v001` tiene 16 canales y 2 módulos.

## Estado de los criterios

| Criterio | Estado | Nota |
|---|---|---|
| 16 lecturas como barras con su valor | **No cumplido / pendiente** | El dato existe (`senales` trae los canales), pero **no se encontró el componente que dibuje las 16 barras de la regleta**. `Telemetria.tsx` muestra error/PWM de motores, no la regleta. |
| Posición (mm), error y si está centrada | **No cumplido / pendiente** | No se encontró en la consola el cálculo de posición en mm ni de "centrada" a partir de los 16 canales. |

## Pendientes conocidos

- **Falta la visualización de la regleta**: 16 barras con valor + posición (mm) + error +
  centrada. Es el grueso de HU-15 y hoy no está en la consola.
- Falta confirmar que `robot_falso.py` emite en `senales` los **16 canales** de la
  regleta (y no solo `error`), para poder capturar la vista animada como evidencia.
- Campos en **español** por el renombrado (`senales→signals`, `canales→channels`,
  `regleta→sensor_bar`). Ver `docs/rename-glosario.md` (toca el firmware, contrato 2.0).
- Si se quisiera un `GET /api/devices/{device}/sensors` (última lectura), habría que hacer
  que el gateway retenga la última `senales` (hoy solo guarda el último `estado`). No está
  pedido por los criterios; sería solo para evidencia.

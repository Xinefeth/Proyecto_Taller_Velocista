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

- `consola/src/pages/Control.tsx` (`Regleta()`): dibuja la regleta — las 16 barras con su
  valor, la posición en mm, el error y la etiqueta "Centrada" / "Línea perdida" / "Hacia la
  derecha/izquierda". Se alimenta de los **canales reales** del último `senales` del robot
  (vía `ConexionContext`); si aún no hay datos reales, cae a la **simulación** (`c.simRef`).
- `consola/src/logica/strip.ts`: lógica pura que extrae el último `senales` de los mensajes
  de `/ws/consola` y deriva la vista (16 barras normalizadas, posición en mm, error,
  centrada, perdida, barras activas). Cubierto por `consola/src/logica/strip.test.ts`.
- `consola/src/logica/dominio.ts`: calcula compatibilidad (p. ej. que el multiplexor
  alcance para los 16 canales), no la visualización de la regleta.

## Tests que lo cubren

- `api/tests/websocket/test_gateway.py`: recepción y validación de `senales`/canales.
- `consola/src/types/contrato.test.ts`: separa los canales del manifiesto por grupo.
- `consola/src/logica/dominio.test.ts`: la regleta de `v001` tiene 16 canales y 2 módulos.
- `consola/src/pages/Regleta.test.tsx`: la vista dibuja las 16 barras, la posición (mm), el
  error y "centrada" / "línea perdida" a partir de un `senales` real inyectado por WebSocket.

## Estado de los criterios

| Criterio | Estado | Nota |
|---|---|---|
| 16 lecturas como barras con su valor | **Cumplido** | `Regleta()` dibuja las 16 barras con su valor desde los canales reales del `senales` del robot (`consola/src/logica/strip.ts`); la simulación queda como respaldo cuando no hay datos. |
| Posición (mm), error y si está centrada | **Cumplido** | `strip.ts` calcula la posición (mm), el error normalizado y "centrada" por centroide de los 16 canales; `Regleta()` los muestra. Respaldo simulado si no hay una muestra válida. |

## Pendientes conocidos

- ~~**Alimentar la regleta con los canales reales de `senales`**~~ **Hecho**: `Regleta()`
  deriva las 16 barras, la posición (mm), el error y "centrada" de los canales reales del
  último `senales` (`consola/src/logica/strip.ts`); la simulación queda como respaldo cuando
  no hay datos reales.
- ~~Falta confirmar que `robot_falso.py` emite en `senales` los **16 canales** de la
  regleta~~ **Confirmado**: `robot_falso.py` emite `canales.regleta` como lista de 16
  valores (0–1000) en cada `senales`; el contrato lo admite (`ValorCanal = list[int]`).
- Campos en **español** por el renombrado (`senales→signals`, `canales→channels`,
  `regleta→sensor_bar`). Ver `docs/rename-glosario.md` (toca el firmware, contrato 2.0).
- **Plan de migración, pendiente de confirmación:** acordar el contrato 2.0 y las
  unidades; actualizar coordinadamente firmware, contrato/validación del backend,
  manifiestos/ejemplos, robot falso y consumidores de consola; ejecutar pruebas de
  contrato, gateway y vista, y verificar con hardware antes de retirar el contrato
  anterior. No se ejecuta esta migración en HU-15.

## Verificación de la implementación existente

- La revisión encontró la vista ya conectada al WebSocket y las tareas marcadas;
  no corresponde retroceder el estado a «Parcial: la vista existe con datos simulados».
- Tarea 1: comprobada la emisión real del robot falso con una captura sin red en
  `api/tests/unit/test_sensor_strip.py`. Emisor, contrato, gateway y arquitectura:
  **44 pruebas aprobadas**.
- Tarea 2: el error se deriva de los 16 canales, sin usar el canal `error` independiente.
  Solo se aceptan exactamente 16 valores numéricos finitos; si no, se usa el respaldo.
- La escala de 0–1000 y los extremos de ±72 mm conservan los valores de la vista
  existente; requieren confirmación/calibración física con el hardware.
- Tarea 3: 6 pruebas de vista y 11 de lógica aprobadas. La vista de prueba inyecta
  `initialRobots` para no depender de la carga de red del proveedor.
- Última suite completa de consola: **114 aprobadas, 3 fallidas** en
  `src/components/gestion/RegistroManual.test.tsx`, por espera de carga de robots;
  no se modifican esas pruebas, ajenas a HU-15. El workspace cambió durante la revisión.
- Los nombres existentes `Regleta`, `Senales` y los proveedores/hooks en español
  permanecen como deuda de migración local; los identificadores añadidos en esta
  revisión están en inglés, conservando las claves actuales del contrato WebSocket.
- Si se quisiera un `GET /api/devices/{device}/sensors` (última lectura), habría que hacer
  que el gateway retenga la última `senales` (hoy solo guarda el último `estado`). No está
  pedido por los criterios; sería solo para evidencia.

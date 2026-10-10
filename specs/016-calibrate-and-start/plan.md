# Plan técnico · HU-16 Calibrar los sensores y arrancar

Cómo está construido hoy, leído del código.

## Módulos involucrados

- **devices** (`api/app/gateway/comandos.py`): recibe los comandos de la consola, los
  valida y los reenvía al robot por WebSocket.
- **gateway** (`api/app/gateway/ws.py`): envía el comando al robot y devuelve el `ack`.
- **Consola** (`consola/src/`): botones de calibrar y arrancar/detener.

## Endpoints REST

| Método | Ruta | operation_id |
|---|---|---|
| POST | `/api/devices/{device}/commands` | `sendCommand` |

El cuerpo es `{tipo, datos}`. Para el velocista, `tipo` debe estar declarado en su
manifiesto: `calibrar`, `arrancar`, `detener`, `setup`, `modo`, `linea`, `cierre_vuelta`.
La respuesta es 202 (aceptado); la confirmación del robot llega como `ack` por
`/ws/consola`.

### Validación de negocio (`validar_comando`)

- `arrancar` con el robot **sin calibrar** → 409 `no_calibrado` ("Calibra el robot antes
  de arrancar").
- En `modo` competencia y `corriendo`, solo se permite `detener` → 409
  `bloqueado_competencia`.
- Comando no declarado en el manifiesto → 422 `comando_desconocido`.
- Dispositivo no conectado → 409 `desconectado`.
- Enlace con el dispositivo caído **al enviar** (entre el pre-chequeo y `ws.enviar`) →
  503 `dispositivo_no_disponible` ("No se pudo entregar el comando: el dispositivo dejó
  de responder").

## Mensajes WebSocket

- `calibrar` / `arrancar` / `detener` (API → robot): comandos sin datos.
- `estado` (robot → API): expone `estado`
  (`listo`/`calibrando`/`corriendo`/`detenido`/`error`) y `calibrado`.
- `ack` (robot → API → consola): confirma cada comando.

## Tablas

- Ninguna propia (los comandos no se persisten; las corridas sí, pero son otra historia).

## Componentes de la consola

- `consola/src/pages/Control.tsx`: botón **ARRANCAR/DETENER**, panel de calibración,
  estados `calibrating` / `calibrated` / `running`, aviso "Calibra los sensores antes de
  arrancar", el botón de calibrar se deshabilita mientras corre o calibra.
- `consola/src/services/api.ts` y `consola/src/stores/ConsolaContext.tsx`: envío de
  comandos y estado de la consola.

## Tests que lo cubren

- `api/tests/websocket/test_gateway.py`: comandos validados y enviados; rechazo por
  estado inválido.

## Estado de los criterios

| Criterio | Estado | Nota |
|---|---|---|
| ARRANCAR bloqueado hasta calibrar | **Cumplido** | Backend: `validar_comando` rechaza `arrancar` sin `calibrado` (409 `no_calibrado`). Consola: `Control.tsx` muestra el aviso y bloquea hasta calibrar. |
| Calibración < 20 s | **No verificado** | La duración la maneja el robot/firmware. No se pudo medir con `api/herramientas/robot_falso.py`: hoy pone `calibrado = True` al instante (sin estado `calibrando` ni `asyncio.sleep`), por lo que daría ~0 s, un artefacto del stub, no una verificación real. Pendiente de robot real o de simular el tiempo en el robot falso (ver "Pendientes conocidos"). |
| Detener siempre disponible | **Verificado: habilitación del botón; alcance limitado** | `Control.tsx` no aplica `disabled` al botón ARRANCAR/DETENER. `consola/src/pages/Control.test.tsx`: **5 passed** (2026-10-10), cubriendo sin calibrar, calibrando, calibrado, corriendo y sin enlace. DETENER aparece solo cuando `running` es verdadero; en los demás estados aparece ARRANCAR. Las pruebas usan modo simulado y no acreditan el envío de parada al robot físico. |

## Pendientes conocidos

- Tipos de comando y estados aún en **español** por el renombrado (`calibrar→calibrate`,
  `arrancar→start`, `detener→stop`; `listo/calibrando/corriendo/detenido` →
  `ready/calibrating/running/stopped`). Ver `docs/rename-glosario.md` (toca el firmware,
  contrato 2.0). La consola ya usa parcialmente nombres en inglés (`calibrating`,
  `calibrated`, `running`).
- ~~La respuesta **503** no está documentada en Swagger para este endpoint.~~ Hecho:
  `send_command` captura el fallo de `ws.enviar` y devuelve 503 `dispositivo_no_disponible`,
  documentado en `responses=` y cubierto por `test_comando_con_enlace_caido_al_enviar_devuelve_503`.
  Revisión 2026-10-10: `pytest tests/websocket/test_gateway.py -q`: **11 passed**;
  una advertencia de deprecación de Starlette/httpx.
  Comprobado también en `app.openapi()`: 503 incluye el ejemplo
  `dispositivo_no_disponible` con `BusinessError`.
- Validar el tiempo de calibración (< 20 s) con el robot real o `robot_falso.py`. Para medirlo
  con el robot falso falta que simule la calibración con tiempo: al recibir `calibrar`, pasar a
  `estado = "calibrando"` (enviando un `estado` con `calibrado: false`), esperar una duración
  simulada sin bloquear la telemetría (p. ej. `asyncio.sleep` con un valor configurable < 20 s) y
  al terminar poner `estado = "listo"` y `calibrado = true`. El tiempo se mide entre el envío de
  `calibrar` y la llegada del `estado` con `calibrado: true`.

## Revisión de calibración (2026-10-10)

Se ejecutó `RobotFalso.comando("calibrate", {})` con `time.perf_counter`:
**0.0000018 s**, ack positivo, `calibrado = True`, estado `ready`.
Es exclusivamente el tiempo de ejecución del stub en proceso, sin transporte WebSocket
ni calibración de sensores; **no verifica FR-003**. El `asyncio.sleep(0.05)` existente
pertenece a la telemetría, no a la calibración. La tarea de < 20 s permanece sin marcar.
Faltan las transiciones de inicio/fin, una duración de calibración representativa y la
medición completa comando → estado final. Una espera elegida por debajo de 20 s solo
verificaría la simulación; para acreditar el criterio físico se necesita el robot real.

## Propuesta de migración a inglés (sin ejecutar; requiere confirmación del usuario)

Hay cambios locales previos que ya usan `calibrate/start/stop` y estados en inglés en
API, consola, simulador y firmware. Esta revisión no los amplía ni los revierte;
la descripción histórica anterior usa el contrato en español y debe reconciliarse
cuando se autorice la migración.

1. Revisar el diff previo y acordar el mapa canónico y la versión del contrato 2.0.
2. Actualizar coordinadamente esquemas, manifiestos, ejemplos y pruebas de contrato.
3. Adaptar API, consola, robot falso y firmware al mismo contrato, manteniendo textos
   al usuario en español; definir cómo evitar mezclas de versiones desplegadas.
4. Ejecutar pruebas de contrato/gateway/consola y compilar el firmware; validar en el
   robot real calibración, arranque y parada antes de desplegar el conjunto.

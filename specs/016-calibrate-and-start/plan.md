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
| Calibración < 20 s | **No verificado** | La duración la maneja el robot/firmware; no se pudo verificar sin robot real (el reglamento da 1 min para todo). |
| Detener siempre disponible | **Cumplido (por confirmar en UI)** | `validar_comando` no bloquea `detener` en ningún estado; en `Control.tsx` DETENER está disponible mientras corre. Falta confirmar que detener nunca quede deshabilitado. |

## Pendientes conocidos

- Tipos de comando y estados aún en **español** por el renombrado (`calibrar→calibrate`,
  `arrancar→start`, `detener→stop`; `listo/calibrando/corriendo/detenido` →
  `ready/calibrating/running/stopped`). Ver `docs/rename-glosario.md` (toca el firmware,
  contrato 2.0). La consola ya usa parcialmente nombres en inglés (`calibrating`,
  `calibrated`, `running`).
- La respuesta **503** no está documentada en Swagger para este endpoint.
- Validar el tiempo de calibración (< 20 s) con el robot real o `robot_falso.py`.

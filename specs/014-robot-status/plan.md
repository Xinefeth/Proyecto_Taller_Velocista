# Plan técnico · HU-14 Consultar el estado del robot

Cómo está construido hoy, leído del código.

## Módulos involucrados

- **gateway** (`api/app/gateway/ws.py`): recibe `estado` del robot y lo redifunde a la
  consola; emite `enlace` al conectar/desconectar.
- **system** (`api/app/main.py`): `GET /api/health` con los dispositivos conectados.
- **Consola** (`consola/src/`): barra superior de estado.

## Endpoints REST

| Método | Ruta | operation_id |
|---|---|---|
| GET | `/api/health` | `getHealth` |

`GET /api/health` devuelve `dispositivos` (`{velocista, cronometro}`: conectado o no).
No da batería/lazo en vivo; eso va por WebSocket.

## Mensajes WebSocket

- `estado` (robot → API por `/ws/robot`, ~1 Hz): `estado`
  (`listo`/`calibrando`/`corriendo`/`detenido`/`error`), `calibrado`, `modo`, `linea`,
  `controlador`, `lazo_hz`, `rssi_dbm` y `canales` (incluye `bateria_v`). Definido en
  `api/app/contrato/robot.py` (`Estado`).
- `enlace` (API → consola): `{dispositivo, conectado}` cuando un dispositivo se conecta o
  se desconecta (`api/app/gateway/ws.py`).
- `hola` (API → consola al conectar): estado inicial de dispositivos.

## Tablas

- Ninguna propia: es estado en vivo, no se persiste.

## Componentes de la consola

- `consola/src/components/Strip.tsx`: barra superior (Enlace WiFi en dBm y ms, Lazo en
  Hz, Batería, frescura del enlace en segundos, chip "SIN ENLACE").
- `consola/src/stores/ConexionContext.tsx`, `consola/src/hooks/useSalud.ts`: estado de
  conexión y sondeo de salud.

## Tests que lo cubren

- `api/tests/websocket/test_gateway.py`: `enlace` al conectar/desconectar y
  `GET /api/health` reflejando el dispositivo conectado.
- `api/tests/integration/test_salud.py`: forma de la respuesta de `GET /api/health`.

## Estado de los criterios

| Criterio | Estado | Nota |
|---|---|---|
| Barra con batería (V), enlace (dBm y ms), lazo (Hz) y estado | **Parcial** | La barra existe (`Strip.tsx`) pero hoy con **datos simulados** (comentario "enlace simulados"; la batería cambia por clic). El contrato real trae `bateria_v`, `rssi_dbm`, `lazo_hz` y `estado`. |
| Se actualiza ≥ 1 vez por segundo | **No verificado** | El contrato define `estado` a `estado_hz` = 1 Hz, pero no se pudo verificar el tiempo real sin robot (hoy simulado). |
| Pérdida de enlace indicada en < 2 s | **No verificado** | El gateway emite `enlace` conectado=false al desconectar y la consola muestra "SIN ENLACE"; el umbral de 2 s no se verificó con robot real. |

## Pendientes conocidos

- El **"ms" del enlace no viene del robot**: el contrato `Estado` trae `rssi_dbm` pero no
  una latencia en ms; hoy el "ms" es una métrica **simulada en la consola** (`Strip.tsx`).
  Hay que decidir de dónde sale la latencia real (mismatch con el criterio oficial).
- Campos aún en **español** por el renombrado (`estado`, `calibrado`, `lazo_hz`,
  `rssi_dbm`, `bateria_v`). Ver `docs/rename-glosario.md` (toca el firmware, contrato 2.0).
- La respuesta **503** de `GET /api/health` no aplica (responde 200 aun sin BD), pero el
  503 en otros endpoints sigue sin documentarse en Swagger.
- Falta validar tiempos reales (1 s, 2 s) con el robot físico o con `robot_falso.py`.

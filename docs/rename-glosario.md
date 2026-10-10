# Glosario de renombrado español → inglés

Mapa canónico para pasar **todo el código** a inglés (identificadores, funciones,
atributos, clases, archivos, módulos, columnas de BD, rutas, campos JSON, valores de
enum y tipos/campos de mensajes WebSocket). **En español se quedan:** comentarios,
docstrings, mensajes de commit y los **valores de texto que ve el usuario** (etiquetas de
la interfaz y el `detalle`/`mensaje` de los errores mostrados).

Vive en el working tree, no se commitea. Se extiende a medida que se renombra cada módulo.

## Contrato de mensajes (`app/contrato/` → `app/contract/`)

### Sobre y base (`base.py`)
| Actual | Inglés |
|---|---|
| `Sobre` | `Envelope` |
| `tipo` (campo del sobre) | `type` |
| `datos` | `data` |
| `Emisor` | `Sender` |
| `Estricto` | `Strict` |
| `PATRON_NOMBRE` | `NAME_PATTERN` |
| `VERSION_CONTRATO` | `CONTRACT_VERSION` |
| `misma_version_mayor` | `same_major_version` |

### Emisores (valores, van en el cable → firmware)
| Actual | Inglés |
|---|---|
| `velocista` | `racer` |
| `cronometro` | `timer` |
| `api` | `api` |

### Tipos de mensaje (valores en el cable → firmware)
| Actual | Inglés |
|---|---|
| `manifiesto` | `manifest` |
| `estado` | `status` |
| `senales` | `signals` |
| `vuelta` | `lap` |
| `evento` | `event` |
| `calibrar` | `calibrate` |
| `arrancar` | `start` |
| `detener` | `stop` |
| `modo` | `mode` |
| `linea` | `line` |
| `cierre_vuelta` | `lap_close` |
| `hola` | `hello` |
| `corte` | `crossing` |
| `rearmar` | `rearm` |

### Robot (`robot.py`)
| Actual | Inglés |
|---|---|
| `Estado` | `Status` |
| `estado` (campo) | `state` |
| `calibrado` | `calibrated` |
| `modo` | `mode` |
| `linea` | `line` |
| `controlador` | `controller` |
| `lazo_hz` | `loop_hz` |
| `canales` | `channels` |
| `Senales` | `Signals` |
| `Vuelta` | `Lap` |
| `id_vuelta` | `lap_id` |
| `tiempo_interno_ms` | `internal_time_ms` |
| `error_acumulado` | `accumulated_error` |
| `lineas_perdidas` | `lines_lost` |
| `bateria_v` | `battery_v` |
| `Sync.vueltas` | `laps` |
| `Evento` | `Event` |
| `codigo` | `code` |
| `nivel` | `level` |
| `mensaje` (campo) | `message` |
| `SinDatos` | `NoData` |
| `Setup.parametros` | `parameters` |
| `id_setup` | `setup_id` |
| `Modo` / `Linea` / `CierreVuelta` | `Mode` / `Line` / `LapClose` |
| `MotivoRechazo` | `RejectReason` |
| `Ack.motivo` / `.detalle` | `reason` / `detail` |
| `ValorCanal` | `ChannelValue` |

Valores de enum de estado: `listo→ready`, `calibrando→calibrating`, `corriendo→running`,
`detenido→stopped`, `error→error`. Modo: `prueba→test`, `competencia→competition`.
Línea: `negra→black`, `blanca→white`. Nivel: `aviso→warning`.
`MotivoRechazo`: `bloqueado_competencia→competition_locked`, `no_calibrado→not_calibrated`,
`fuera_de_rango→out_of_range`, `parametro_desconocido→unknown_parameter`,
`controlador_no_disponible→controller_unavailable`, `comando_desconocido→unknown_command`,
`ocupado→busy`.

### Manifiesto (`manifiesto.py` → `manifest.py`)
| Actual | Inglés |
|---|---|
| `Manifiesto` | `Manifest` |
| `contrato` (campo) | `contract` |
| `tipo_robot` | `robot_type` |
| `sensores` | `sensors` |
| `actuadores` | `actuators` |
| `canales` | `channels` |
| `controladores` | `controllers` |
| `controlador_activo` | `active_controller` |
| `comandos` | `commands` |
| `frecuencias` | `frequencies` |
| `arranque` | `start_mode` |
| `compensa_bateria` | `battery_compensation` |
| `Canal` | `Channel` (`nombre→name`, `descripcion→description`, `tipo→type`, `longitud→length`, `unidad→unit`, `grupo→group`) |
| `Parametro` | `Parameter` (`etiqueta→label`, `paso→step`, `valor→value`) |
| `Controlador` | `Controller` |
| `Sensor` | `Sensor` (`modelo→model`, `detalles→details`) |
| `Actuador` | `Actuator` |
| `Frecuencias` | `Frequencies` (`lazo_hz→loop_hz`, `estado_hz→status_hz`, `senales_hz→signals_hz`) |
| `CANALES_REQUERIDOS` | `REQUIRED_CHANNELS` |
| `COMANDOS_ROBOT` | `ROBOT_COMMANDS` |

Grupo de canal: `estado→status`, `senales→signals`. Actuador tipo: `turbina→turbine`,
`otro→other`. Arranque: `comando→command`, `modulo_arranque→start_module`.

### Cronómetro (`cronometro.py` → `timer.py`)
| Actual | Inglés |
|---|---|
| `Hola` | `Hello` (`antirrebote_ms→debounce_ms`) |
| `Corte` | `Crossing` (`n_corte→crossing_number`, `tiempo_vuelta_ms→lap_time_ms`, `marca_us→timestamp_us`) |
| `EstadoCronometro` | `TimerStatus` (`barrera→barrier`, `pendientes→pending`) |
| `Rearmar` | `Rearm` |

Barrera: `bloqueada→blocked`, `sin_senal→no_signal`.

### Validación y catálogo de mensajes
| Actual | Inglés |
|---|---|
| `validacion.py` | `validation.py` |
| `catalogo.py` (contrato) | `catalog.py` |
| `CATALOGO` | `CATALOG` |
| `Definicion` | `Definition` (`modelo→model`, `requiere_ack→requires_ack`, `frecuencia→frequency`) |
| `MensajeInvalido` | `InvalidMessage` |
| `validar_datos` | `validate_data` |
| `requiere_ack` | `requires_ack` |
| `revisar_canales` | `check_channels` |
| `revisar_setup` | `check_setup` |

## Pendiente de mapear al renombrar cada uno
- Gateway (`app/gateway/`): `Conexion→Connection`, `conexiones→connections`, `consolas→consoles`, `difundir→broadcast`, `enviar→send`, `estado_dispositivos→device_status`, `robot_corriendo→robot_running`, `enlace→link`, rutas `/ws/robot` etc.
- Módulos: `catalogo`, `armador→builder`, `corridas→runs`, `reglamento→rules`, `optimizacion→optimization`, `eventos→events`, `auth` (columnas de BD + migración Alembic).
- Semillas/generador/demo.
- Consola (TS): `types/`, `services/`, `stores/`, componentes.
- Firmware (C++): `firmware/velocista`, `firmware/cronometro`.

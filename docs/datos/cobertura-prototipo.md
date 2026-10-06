# DO-03 · Trazabilidad con el prototipo

La cobertura incluye datos persistentes, derivados y transitorios. «Transitorio» es una decisión del modelo, no un campo olvidado. Las rutas REST propuestas se especifican en [EN-01](../api/README.md); todavía no están conectadas a la consola.

| Fuente / campo del prototipo | Destino o tratamiento |
| --- | --- |
| `TipoComponente.nm`, `c` | tipo_componente.nombre, color |
| `TipoComponente.f` | campos: clave, etiqueta, tipo n/t, unidad y obligatoriedad |
| `TipoComponente.sum`, `cap` | Funciones de presentación; specs y capacidades son los datos persistentes. No guardar código JavaScript en BD. |
| `Componente.id`, `t`, `nm` | componente.id, tipo_id, nombre |
| `precio`, `masa`, `tienda`, `i`, `s` | precio (PEN), masa_g, tienda, consumo_a nullable, especificaciones |
| `stock`; catálogo «En robots», «Disponible», «Faltan» | inventario.stock; sumas sobre últimas versiones y diferencia calculada, incluida demanda de conceptos |
| RegistroModal `link`, `rt`, `busy`, `aviso` | Entrada temporal del importador y estado de pantalla; el prototipo no conserva la URL. La extracción/importación HU-05 es posterior y no se promete como endpoint operativo. |
| `Ranura.k`, `t`, `nm`, `req`, `q`, `opt` | ranura.id, tipo_id, nombre, obligatoria, cantidad_editable, depende_reglamento; 0/1 se normaliza a boolean |
| `PiezaRef.id`, `q`; `Version.parts` | version_componente.componente_id/cantidad agrupados por ranura; instantánea por pieza |
| `Version.v`, `fecha`, `nota`, `estado` | etiqueta derivada del ordinal, fecha ISO 8601, nota, estado. «hoy», «—», «20 set 2026» son presentación/importación, no fechas persistidas. |
| `RobotDef.id`, `nm`, `short`, `tipo`, `fw`, `ver` | robot.id/nombre/codigo_corto/tipo/firmware; ver se obtiene de versiones ordenadas por ordinal |
| `Hechos.cost`, `mass`, `cur` | Totales calculados con snapshots × cantidad; mass agrega los 8 g de montaje que usa `facts()` cuando hay piezas. Esa constante debe centralizarse al implementar. |
| Resto de `Hechos`: line, sensores, sensMods, motor, motores, mcu, driver, drivers, bat, reg, mux, exp, rueda, chasis, ancho, largo, enc, imu, turb, radio | Derivado de ranuras, cantidades y especificaciones congeladas; chequeos de compatibilidad y reglamento se recalculan, no son columnas independientes. |
| `Perfil.id`, `comp`, `tag`, `cat`, `r` | perfil_reglamento.id/competencia/etiqueta/categoria/reglas |
| `ReglasPerfil.dim`, `sensMax`, `motores`, `motorFam`, `ruedas`, `drivers`, `mcu` | reglas con mismas claves; null significa sin límite. dim en mm. |
| `ReglasPerfil.turbina`, `pcbComercial`, `montaje`, `chasis`, `chasisMat`, `arranque`, `inal`, `enc`, `imu`, `mapaVel`, `mr4` | reglas, conservando booleanos, textos y listas; chasisMat opcional |
| `Controlador.nm`, `short`, `keys`, `tw`, `desc`, `pre` | nombre/nombre_corto; parametros ordenados; optimizable; descripcion; presets |
| `DefParam.nm`, `t`, `min`, `max`, `step`, `dec` | definición de parámetro: nombre, descripcion, min, max, paso, decimales |
| `Setup.ctrl`, `p` | setup.controlador_id/parametros y snapshot en corrida |
| `draft`, `applied`, `saved`, `preset` | Borrador local, último ack aplicado, persistencia en dispositivo y preset seleccionado. Guardado en BD usa un ID propio. El diseño no equipara estas confirmaciones. |
| `Corrida.n`, `robot`, `ver`, `ctrl`, `p` | corrida.numero; robot/etiqueta de versión por FK; controlador/valores del snapshot |
| `Corrida.t`, `fin`, `iae`, `vbat`, `sec`, `src`, `J` | Proyección de vuelta: tiempo_s, termino, error_acumulado, bateria_v, sectores_s, fuente_tiempo; J calculado. `src` Meta/Telemetría se normaliza a meta/telemetria. |
| `Corrida.note` | corrida.nota, único dato editable al cerrar |
| `Vuelta.n`, `t`, `iae`, `vbat`, `fin`, `lost`, `src`, `why` | numero, duracion_s (incluso al fallar), error_acumulado, bateria_v, termino, lineas_perdidas, fuente_tiempo, motivo |
| `Vuelta.ctrl`, `p`, `robot` | Se derivan de la corrida; cambiar setup requiere otra corrida |
| `Vuelta.segs` y `Segmento.k`, `dur`, `deg`, `ie` | segmento_vuelta ordenado: tipo, duracion_s, angulo_grados, error_acumulado |
| `Vuelta.sec`, `col` | sector_vuelta; colores purple/green/yellow se calculan frente a mejores sectores, no se persisten |
| `EventoLog.t`, `sys`, `msg`, `lv` | evento.fecha/sistema/mensaje/nivel. UI warn→aviso, bad→error; good/best/neutral→info con código/datos opcionales para recuperar el matiz visual |
| `source`, `mode`, `line`, `comp`, `turb` | corrida.fuente/modo/linea/compensa_bateria/potencia_turbina_pct capturados al inicio |
| `robotId`, `profileId`, `engMethod` | Selecciones de sesión; sus IDs quedan fijados en corrida/estudio. Cambiar selección no reescribe el historial. |
| `connected`, `link.dbm/ms`, `gate`, `calibrated`, `calibrating`, `calProgress`, `running`, `locked`, `vbat` | Estado vivo por EN-02 o simulación. Batería se muestrea en cada vuelta; las transiciones relevantes generan eventos. Estado perdido al desconectar nunca se interpreta como calibración válida tras reiniciar. |
| Telemetría `error`, PWM izq/der, sensores, lazo Hz, batería, RSSI y canales dinámicos | Manifiesto y muestras por WebSocket; búfer de visualización transitorio. IAE, pérdidas y resúmenes por vuelta persistentes; el diseño no guarda indefinidamente cada muestra de 20 Hz. |
| `MapaState.path/raw/corr`, `source`, `stats.len/closeErr/errH` | mapa_analisis puntos_corregidos/puntos_crudos, fuente, longitud_m/error_cierre_m/error_rumbo_rad |
| `MapaState.pending/recording/est/bias`; `trail`, `bins`, `hist` | Estado de cálculo, deriva simulada y búferes de dibujo; transitorios. Un resultado final guardado usa mapa_analisis. |
| Mapa desde foto: archivo, `corners`, `pw/ph`, `thr`, color | Referencia al archivo y foto_config: dimensiones físicas, esquinas, umbral y color; imagen corregida regenerable |
| `Ingeniero.method/ctrl/dp/i/phase/best/base/prop` | estudio_optimizacion y estado_algoritmo; propuestas/resultados en ensayo_optimizacion |
| `VistaIngeniero.msg/nx/mini/hasProp/ctrlNm` | Presentación derivada del estado del estudio y definiciones de controlador |
| CSV, gráfico de comparación, mejores tiempos/sectores | Proyecciones del historial; sin tablas separadas |
| `tab`, filtros, búsqueda, orden, modales, ficha, backlog, `scope`, `showPbi`, toasts, señales visibles, encuadre, `tick` | Preferencias y estado de interfaz/localStorage; fuera del dominio persistente del servidor |
| `Simulador.s/e/th/wl/wr/I/prev/last/es/p/pl/pr/lapT/iae/lost/...` y pista `TRACK/EXAMPLE` | Estado numérico y fixture del simulador; guardar sus vueltas/corridas como fuente=sim, no todo el integrador físico |

## Correspondencia de DTO

Los nombres de REST son explícitos (`nombre`, `masa_g`, `controlador_id`) y los del prototipo son abreviados (`nm`, `masa`, `ctrl`). La integración futura deberá convertirlos en `services/`, no renombrar silenciosamente los datos de maqueta. En particular:

- GET robots devuelve metadatos; GET versiones obtiene `ver` y reconstruye `parts`, conservando las instantáneas históricas incluidas en cada pieza.
- Inventario tiene un endpoint propio; GET componentes incluye stock por conveniencia de la lista. Solo PUT inventario modifica existencias después del alta.
- Guardar una versión envía la colección completa de piezas, no un diff parcial. El servidor crea ordinal y fecha.
- Las respuestas paginadas usan `{items,total,limite,offset}`; `/api/eventos` conserva su arreglo existente.
- Identidad REST del robot (`v001`) y canal de dispositivo (`velocista`) son conceptos distintos. La asignación se confirma con `Manifiesto.id` y debe validarse antes de enviar un setup.

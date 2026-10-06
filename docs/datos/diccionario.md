# DO-03 · Diccionario de datos

`evento` está definido en `0001_base`; `tipo_componente`, `componente` e `inventario` están implementados en los modelos y la migración `0002_catalogo`. Las demás entidades siguen propuestas. Tipos físicos para PostgreSQL; `?` significa nullable, el resto es NOT NULL. IDs `bigint` se generan por identidad y se exponen hasta `9007199254740991`. Fechas en `timestamptz`, JSON REST en ISO 8601 con zona; la consola presenta la zona del usuario. Los JSONB solo contienen datos, nunca funciones ejecutables.

## Catálogo

| Entidad | Campos y tipos | Claves y reglas |
| --- | --- | --- |
| `tipo_componente` | `id varchar(40)`, `nombre varchar(120)`, `color varchar(7)`, `campos jsonb`, `capacidades jsonb` | PK id; claves iniciales: mcu, exp, linea, mux, motor, driver, bat, reg, rueda, chasis, sw, enc, imu, turb. Esquemas `CampoTipo`/`Capacidad` en OpenAPI. Claves de campos y capacidades únicas por tipo. |
| `componente` | `id varchar(40)`, `tipo_id varchar(40)`, `nombre varchar(120)`, `precio numeric(12,2)`, `masa_g numeric(12,3)`, `tienda varchar(200) = ''`, `consumo_a numeric(12,4)?`, `especificaciones jsonb = {}`, `archivado boolean = false` | PK id; FK tipo_id → tipo_componente. Precio > 0, masa y consumo ≥ 0. Nombre no vacío. Moneda del prototipo: PEN, soles. Precio por unidad de catálogo. No se cambia tipo_id después del alta. |
| `inventario` | `componente_id varchar(40)`, `stock integer = 0`, `revision integer = 1` | PK/FK componente_id → componente, relación 1:1 creada atómicamente; stock ≥ 0, revision ≥ 1. `en_robots`, `disponible`, `faltante` son derivados, no columnas. |

`campos` es un arreglo ordenado de `{clave, etiqueta, tipo: n|t, unidad, obligatorio}`. `capacidades` declara clave, unidad y agregación, con un campo fuente, una operación sobre varios campos o un rango de control. Todos los campos concretos de los 14 tipos figuran en [tipos-componentes.json](tipos-componentes.json), incluidos los campos numéricos que el formulario permite omitir. Nuevos tipos exigen actualizar catálogo de campos, esquema REST y pruebas de cobertura juntos.

## Armador

| Entidad | Campos y tipos | Claves y reglas |
| --- | --- | --- |
| `ranura` | `id varchar(40)`, `tipo_id varchar(40)`, `nombre varchar(120)`, `obligatoria boolean`, `cantidad_editable boolean`, `depende_reglamento boolean` | PK id; FK tipo_id → tipo_componente. Inicialmente una ranura por tipo. La cantidad de una ranura no editable es 1. |
| `robot` | `id varchar(40)`, `nombre varchar(120)`, `codigo_corto varchar(12)`, `tipo varchar(20)`, `firmware varchar(20)?`, `version_actual_id bigint?`, `archivado boolean = false` | PK id; UNIQUE codigo_corto; tipo velocista/minisumo. FK compuesta `(version_actual_id,id)` → version `(id,robot_id)` garantiza que el puntero es del mismo robot. Null hasta crear la primera versión. |
| `version` | `id bigint`, `robot_id varchar(40)`, `ordinal integer`, `fecha timestamptz`, `nota text`, `estado varchar(20)` | PK id; FK robot_id → robot. UNIQUE `(robot_id,ordinal)` y `(id,robot_id)`. ordinal ≥ 0; etiqueta REST = `v` + ordinal. Estados Actual/Anterior/Descartada/Concepto/Borrador; índice único parcial sobre robot_id WHERE estado='Actual'. Nota ≤ 1000 caracteres. |
| `version_componente` | `version_id bigint`, `ranura_id varchar(40)`, `componente_id varchar(40)`, `cantidad integer`, `componente_snapshot jsonb` | PK `(version_id,ranura_id)`; FK a version, ranura y componente. cantidad > 0; servicio valida tipo del componente = tipo de ranura. Snapshot con id, tipo, nombre, precio, masa, consumo, tienda y especificaciones al guardar; nunca stock mutable. |

Para crear la primera versión se inserta el robot con puntero null; dentro de la siguiente transacción se inserta versión/piezas y se actualiza el puntero. La FK del puntero puede agregarse después de crear ambas tablas. `version_base_id` es una precondición de la petición, no una columna adicional. La falta de inventario se muestra para planificar compras y no impide guardar conceptos. Un armado Actual exige las ranuras obligatorias. Compatibilidad eléctrica y cumplimiento de perfiles producen chequeos derivados de las instantáneas y las reglas del perfil.

## Control y reglamento

| Entidad | Campos y tipos | Claves y reglas |
| --- | --- | --- |
| `controlador` | `id varchar(40)`, `nombre varchar(120)`, `nombre_corto varchar(30)`, `descripcion text`, `parametros jsonb`, `presets jsonb` | PK id; iniciales pid/adapt/fuzzy. Parámetros ordenados `{clave,nombre,descripcion,min,max,paso,decimales,optimizable}`; min < max, paso > 0; claves únicas. Presets: nombre → valores por clave. Cada preset valida todos los parámetros. |
| `perfil_reglamento` | `id varchar(40)`, `competencia varchar(120)`, `etiqueta varchar(20)`, `categoria varchar(120)`, `reglas jsonb` | PK id; conserva exactamente las reglas de `ReglasPerfil`. null significa sin límite, false prohibición. Dimensiones en mm, cantidades enteras. No inferir false desde null. |
| `setup` | `id bigint`, `version_id bigint`, `controlador_id varchar(40)`, `nombre varchar(120)`, `parametros jsonb`, `controlador_snapshot jsonb`, `creado_en timestamptz`, `archivado boolean = false` | PK id; FK version/controlador; UNIQUE `(id,version_id)` para pertenencia de corridas. Valores finitos y conjunto exacto de parámetros del controlador. El robot se deriva de version; no se duplica físicamente. |

Parámetros iniciales, tomados de `PDEF`: kp 0–2/paso 0.01, ki 0–0.3/0.005, kd 0–10/0.1, base 10–100/1, max 20–100/1, kv 0–1/0.05, vmin 10–60/1, g 0–2/0.01, d 0–10/0.1. PID usa kp/ki/kd/base/max y optimiza kp/kd; adapt agrega kv/vmin y optimiza kp/kd/kv; fuzzy usa g/d/base/max y optimiza g/d. Los presets Seguro/Base/Agresivo se cargan de `datos/controladores.ts`. Estos rangos del catálogo no reemplazan los del manifiesto físico.

## Corridas y vueltas

| Entidad | Campos y tipos | Claves y reglas |
| --- | --- | --- |
| `corrida` | `id bigint`, `numero integer`, `version_id bigint`, `setup_id bigint`, `perfil_id varchar(40)`, `fecha timestamptz`, `cerrada_en timestamptz?`, `fuente varchar(10)`, `modo varchar(15)`, `linea varchar(10)`, `compensa_bateria boolean`, `potencia_turbina_pct numeric(5,2)`, `contexto_snapshot jsonb`, `nota text = ''` | PK id; número positivo único global para mantener `Corrida.n`; FK version/perfil; FK `(setup_id,version_id)` → setup `(id,version_id)`. fuente sim/robot, modo prueba/competencia, línea negra/blanca; potencia 0–100. Fecha de cierre ≥ fecha; nota ≤ 1000. |
| `vuelta` | `id bigint`, `corrida_id bigint`, `numero integer`, `tiempo_s numeric(14,6)?`, `duracion_s numeric(14,6)`, `tiempo_interno_ms bigint?`, `error_acumulado numeric(18,9)`, `lineas_perdidas integer`, `bateria_v numeric(8,4)`, `termino boolean`, `fuente_tiempo varchar(15)`, `motivo text = ''` | PK id; FK corrida; UNIQUE `(corrida_id,numero)`; número > 0. Magnitudes ≥ 0. `termino=true` exige tiempo_s; false exige tiempo_s=null. duración conserva el tiempo transcurrido incluso al fallar. fuente meta/telemetria. Motivo ≤ 500. |
| `sector_vuelta` | `vuelta_id bigint`, `numero integer`, `tiempo_s numeric(14,6)` | PK `(vuelta_id,numero)`; FK vuelta; número > 0 y tiempo ≥ 0. Son duraciones parciales ordenadas, no timestamps. Tres sectores en el prototipo, número extensible. |
| `segmento_vuelta` | `vuelta_id bigint`, `numero integer`, `tipo varchar(30)`, `duracion_s numeric(14,6)`, `angulo_grados numeric(12,6)`, `error_acumulado numeric(18,9)` | PK `(vuelta_id,numero)`; FK vuelta; duración/error ≥ 0; ángulo admite signo. Tipo conserva `Segmento.k` (clasificación de recta, curva y pérdida). |

`contexto_snapshot` fija `{firmware, manifiesto, perfil, controlador, parametros}` al inicio; manifiesto puede ser null en simulación. `perfil` guarda la estructura completa de PerfilReglamento; `controlador` la definición usada; `parametros` los valores confirmados al aplicar. No se almacena un secreto/token del dispositivo.

Los campos REST de Corrida `robot_id`, `controlador_id`, `parametros`, `tiempo_s`, `termino`, `error_acumulado`, `bateria_v`, `sectores_s`, `fuente_tiempo` y `j` son una proyección del snapshot y de la vuelta seleccionada según DO-03. Evita columnas redundantes que puedan contradecir a la vuelta. El contador visible de Vuelta es local a su corrida; para comparar globalmente usar corrida/numero, no solo numero.

No se obliga a que la suma de sectores coincida con el tiempo oficial de meta: pueden proceder de estimación de telemetría. Debe conservarse la procedencia. Los campos de lectura `duracion_s` y las instantáneas de piezas permiten reproducir el historial sin tomar valores actuales del catálogo.

## Eventos, mapas y optimización

| Entidad | Campos y tipos | Claves y reglas |
| --- | --- | --- |
| `evento` | Existentes: `id bigint`, `fecha timestamptz`, `sistema varchar(40)`, `nivel varchar(10)`, `mensaje text`. Extensión: `codigo varchar(40)?`, `datos jsonb = {}`, `robot_id varchar(40)?`, `corrida_id bigint?`, `vuelta_id bigint?` | PK id; FKs opcionales para eventos globales o contextualizados. Nivel info/aviso/error; mensaje de REST ≤ 500. Las tres referencias, si están informadas, deben pertenecer a la misma cadena robot/corrida/vuelta (servicio). La extensión no cambia el DTO de `/api/eventos` existente. |
| `mapa_analisis` | `id bigint`, `vuelta_id bigint?`, `fuente varchar(20)`, `puntos_crudos jsonb`, `puntos_corregidos jsonb`, `longitud_m numeric?`, `error_cierre_m numeric?`, `error_rumbo_rad numeric?`, `foto_config jsonb?`, `creado_en timestamptz` | PK id, FK vuelta opcional. fuente vuelta/ejemplo/foto. Puntos `{x,y,h}` en m/m/rad. Longitud/error de cierre ≥ 0; error de rumbo con signo. Si fuente=vuelta exige vuelta_id. Puede conservar análisis incompleto sin trazo extraído. |
| `estudio_optimizacion` | `id bigint`, `version_id bigint`, `controlador_id varchar(40)`, `perfil_id varchar(40)`, `metodo varchar(15)`, `fuente varchar(10)`, `estado varchar(20)`, `configuracion jsonb`, `estado_algoritmo jsonb` | PK id, FK version/controlador/perfil; método twiddle/bayes; fuente sim/robot; estado activo/pausado/finalizado. Congela rangos, parámetros optimizables y reglas en configuración. No mezcla versiones o fuentes. |
| `ensayo_optimizacion` | `estudio_id bigint`, `numero integer`, `setup_id bigint`, `corrida_id bigint?`, `estado varchar(20)`, `j numeric(18,9)?` | PK `(estudio_id,numero)`; FK estudio/setup/corrida. Número > 0. Estado propuesto/aplicado/evaluado/descartado. Evaluado exige corrida y J; el servicio verifica que versión, controlador, perfil, fuente y parámetros coinciden con el estudio y setup. UNIQUE corrida_id cuando no sea null, para no evaluar dos veces la misma corrida. |

`foto_config` contiene referencia relativa al archivo local administrado (no una URL temporal `blob:`), ancho_m, largo_m, umbral 20–220, cuatro esquinas en píxeles en orden superior izquierda/derecha, inferior derecha/izquierda y color de línea. Se conservan dimensiones en píxeles de la imagen usada al marcar. La imagen se guarda fuera de PostgreSQL; su referencia y parámetros permiten reabrir el análisis. HU-32/33 siguen fuera del curso según la pantalla: el modelo reserva sus datos, no implementa extracción ni control anticipado.

`estado_algoritmo` conserva, cuando se implemente reanudación: `dp`, `i`, `phase`, `best`, `base`, `prop` del Ingeniero; los mensajes de pantalla y flechas se derivan. Los ensayos conservan las propuestas aplicadas y sus resultados. La exportación CSV se obtiene de las corridas; no necesita una tabla propia.

## Restricciones e índices de implementación

- FKs del historial con `ON DELETE RESTRICT`. El archivado mantiene todas las referencias. Sector/segmento admiten cascada solo en una operación administrativa explícita de eliminación de vuelta; no se expone tal operación en EN-01.
- Índices en cada FK de consulta: componente(tipo_id), version(robot_id,ordinal), version_componente(componente_id), setup(version_id,creado_en), corrida(version_id,fecha), vuelta(corrida_id,numero), evento(fecha,id) y sus FKs de contexto.
- `jsonb_typeof` comprueba objetos/arreglos; el servicio valida estructura y reglas cruzadas contra los esquemas versionados del contrato. JSONB no implica aceptación de campos arbitrarios.
- Se verifican en pruebas de integración: pertenencia de versiones y setups, dos guardados simultáneos, revisión de stock obsoleta, conservación de snapshots tras editar catálogo, consultas de archivados y reenvío de una vuelta ya guardada.
- Cada cambio posterior del contrato requiere migración explícita, prueba de compatibilidad y actualización conjunta del diccionario, esquema REST y adaptador del frontend.

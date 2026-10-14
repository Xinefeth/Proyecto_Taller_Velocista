# Campos REST en inglés

Las solicitudes y respuestas de catálogo, inventario, robots, versiones, setups,
controladores, perfiles, corridas, vueltas, eventos y salud usan campos en inglés.
Las rutas conservan sus nombres actuales. Swagger y `openapi.json` publican el contrato nuevo.
No requiere migraciones ni volver a cargar semillas: el ORM y los datos almacenados siguen iguales.

## Compatibilidad

- Los cuerpos antiguos en español siguen admitidos. Las respuestas salen en inglés.
- No envíes ambos nombres del mismo campo: se rechazan para evitar ambigüedad.
- Las consultas usan `limit`, `type_id`, `controller_id` y `source`; `offset`, `q`, `robot_id` y `version_id` no cambian.
- Los identificadores (`linea`, `rueda`, `c05`), estados (`Actual`, `Concepto`) y textos visibles permanecen iguales.
- Las especificaciones y reglas también traducen sus claves; sus valores se conservan.
- El protocolo EN-02, los WebSockets, el manifiesto y los comandos de dispositivos mantienen el contrato del firmware.
- Los errores REST de negocio tienen la forma `{"detail":{"reason":"revision_obsoleta","message":"..."}}`.

## Consola

`consola/src/types/rest.ts` contiene DTOs generados desde FastAPI.
`consola/src/services/api.ts` ofrece métodos tipados para los recursos CRUD.
`consola/src/services/adaptadores.ts` convierte componentes, robots y versiones al modelo
actual de las pantallas, por ejemplo `name → nm` y `specifications.channels → s.canales`.
La adaptación de versiones conserva el DTO con sus IDs e instantáneas en `.api`.
Los formularios pueden seguir usando sus modelos actuales. Conectar los stores/pantallas
que todavía usan datos simulados es una tarea posterior; este cambio prepara el contrato y el cliente.

Ejemplo de lectura:

```typescript
const page = await api.componentes({ type_id: "enc", limit: 50 });
const components = page.items.map(componenteDesdeApi);
```

Los métodos devuelven páginas; recorre `offset` hasta cubrir `total` si necesitas todos los datos.
Para crear una versión posterior, envía el ID real en `base_version_id`.

## Regenerar contratos

Desde la raíz del repositorio:

```powershell
.\api\.venv\Scripts\python.exe docs/api/generar_contrato.py
.\api\.venv\Scripts\python.exe docs/api/generar_tipos_consola.py
```

El archivo generado TypeScript se entrega con formato Prettier:

```powershell
cd consola
npx prettier --write src/types/rest.ts
```

## Campos de objetos REST

| Anterior | Público |
| --- | --- |
| `agregacion` | `aggregation` |
| `angulo_grados` | `angle_degrees` |
| `archivado` | `archived` |
| `base_de_datos` | `database` |
| `bateria_v` | `battery_v` |
| `campo` | `field` |
| `campos` | `fields` |
| `cantidad` | `quantity` |
| `cantidad_editable` | `editable_quantity` |
| `capacidades` | `capabilities` |
| `categoria` | `category` |
| `clave` | `key` |
| `codigo_corto` | `short_code` |
| `compensa_bateria` | `battery_compensation` |
| `competencia` | `competition` |
| `componente_id` | `component_id` |
| `componente_snapshot` | `component_snapshot` |
| `consumo_a` | `current_a` |
| `controlador_id` | `controller_id` |
| `corrida_id` | `run_id` |
| `creado_en` | `created_at` |
| `decimales` | `decimals` |
| `depende_reglamento` | `depends_on_rules` |
| `descripcion` | `description` |
| `detalle` | `message` |
| `disponible` | `available` |
| `dispositivos` | `devices` |
| `duracion_s` | `duration_s` |
| `en_robots` | `allocated` |
| `entorno` | `environment` |
| `error_acumulado` | `accumulated_error` |
| `especificaciones` | `specifications` |
| `estado` | `status` |
| `etiqueta` | `label` |
| `faltante` | `shortage` |
| `fecha` | `date` |
| `fuente` | `source` |
| `fuente_tiempo` | `time_source` |
| `limite` | `limit` |
| `linea` | `line` |
| `lineas_perdidas` | `lost_lines` |
| `masa_g` | `mass_g` |
| `mensaje` | `message` |
| `modo` | `mode` |
| `motivo` | `reason` |
| `nivel` | `level` |
| `nombre` | `name` |
| `nombre_corto` | `short_name` |
| `nota` | `note` |
| `numero` | `number` |
| `obligatoria` | `required` |
| `obligatorio` | `required` |
| `operacion` | `operation` |
| `parametros` | `parameters` |
| `paso` | `step` |
| `perfil_id` | `profile_id` |
| `piezas` | `parts` |
| `potencia_turbina_pct` | `turbine_power_pct` |
| `precio` | `price` |
| `reglas` | `rules` |
| `sectores_s` | `sectors_s` |
| `segmentos` | `segments` |
| `sistema` | `system` |
| `termino` | `finished` |
| `tiempo_interno_ms` | `internal_time_ms` |
| `tiempo_s` | `time_s` |
| `tienda` | `store` |
| `tipo` | `type` |
| `tipo_id` | `type_id` |
| `unidad` | `unit` |
| `version_actual_id` | `current_version_id` |
| `version_base_id` | `base_version_id` |

## Especificaciones

| Anterior | Público |
| --- | --- |
| `logica` | `logic` |
| `bornes` | `terminals` |
| `comercial` | `commercial` |
| `canales` | `channels` |
| `salida` | `output` |
| `paso` | `pitch` |
| `tipo` | `type` |
| `familia` | `family` |
| `celdas` | `cells` |
| `ancho` | `width` |
| `largo` | `length` |
| `ejes` | `axes` |

## Reglas

| Anterior | Público |
| --- | --- |
| `dim` | `dimensions` |
| `sensMax` | `max_sensors` |
| `motores` | `motors` |
| `motorFam` | `motor_families` |
| `ruedas` | `wheels` |
| `turbina` | `turbine` |
| `pcbComercial` | `commercial_pcb` |
| `montaje` | `assembly` |
| `chasis` | `chassis` |
| `chasisMat` | `chassis_materials` |
| `arranque` | `start` |
| `inal` | `wireless` |
| `mapaVel` | `speed_map` |

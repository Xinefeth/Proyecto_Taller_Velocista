# EN-01 · Contrato de la API REST

Versión 1.0.0 · 6 de octubre de 2026 · Contrato para revisión.

Define las operaciones que necesitan la consola, el Catálogo y el Armador, alineadas con [DO-03](../datos/README.md). El documento usa [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0.html), con esquemas, parámetros, respuestas de error y ejemplos de petición/respuesta en cada operación.

## Archivos

- [openapi.json](openapi.json): contrato importable en herramientas compatibles con OpenAPI.
- [ejemplos.http](ejemplos.http): una petición y respuesta ilustrativa por operación; GET/DELETE sin cuerpo y 204 sin contenido.
- [generar_contrato.py](generar_contrato.py): fuente editable del contrato, esquemas y ejemplos; genera también los tipos/capacidades de DO-03.
- [validar_contrato.py](validar_contrato.py): comprueba OpenAPI, referencias, todos los ejemplos, cobertura de campos de tipos del prototipo y sincronización de archivos generados.

`x-estado: implementado` identifica las 32 operaciones del contrato, disponibles en el backend. La guía [pruebas-crud.md](pruebas-crud.md) reúne la preparación y una secuencia de pruebas manuales. **Este archivo no sustituye el `/openapi.json` servido por FastAPI**: `/docs` solo muestra lo implementado. Los ejemplos usan IDs ilustrativos; no son un script de carga ni una secuencia que deba ejecutarse sobre una base vacía.

## Operaciones

Todos los paths incluyen `/api`. Los IDs de robot/componente son cadenas; versión/setup/corrida son enteros positivos.

| Recurso | Método y ruta | Uso en consola | Estado |
| --- | --- | --- | --- |
| Tipos | GET `/api/tipos-componentes` | Formulario dinámico y capacidades | Implementado |
| Ranuras | GET `/api/ranuras` | Filas, tipos y cantidades del Armador | Implementado |
| Componentes | GET `/api/componentes` | Buscar y listar | Implementado |
| Registro | POST `/api/componentes` | Registrar componente | Implementado |
| Ficha | GET `/api/componentes/{componente_id}` | Ficha y stock, incluidos archivados | Implementado |
| Edición | PATCH `/api/componentes/{componente_id}` | Edición parcial de ficha | Implementado |
| Archivado | DELETE `/api/componentes/{componente_id}` | Baja lógica, conserva ficha y stock | Implementado |
| Inventario | GET `/api/inventario` | Stock, revisión y demanda de la última versión de robots activos | Implementado |
| Existencias | PUT `/api/inventario/{componente_id}` | Ajustar stock total con revisión | Implementado |
| Robots | GET `/api/robots` | Selector paginado de robots activos | Implementado |
| Registro de robot | POST `/api/robots` | Registro sin versiones | Implementado |
| Ficha de robot | GET `/api/robots/{robot_id}` | Identificación, incluidos archivados | Implementado |
| Robot | PATCH, DELETE `/api/robots/{robot_id}` | Edición y archivado | Implementado |
| Versiones | GET `/api/robots/{robot_id}/versiones` | Historial y piezas con snapshots | Implementado |
| Nuevo armado | POST `/api/robots/{robot_id}/versiones` | Crear versión | Implementado |
| Versión | GET `/api/robots/{robot_id}/versiones/{version_id}` | Ver armado histórico y sus snapshots | Implementado |
| Controladores | GET `/api/controladores` | Rangos, presets y parámetros optimizables | Implementado |
| Reglamento | GET `/api/perfiles` | Categoría y restricciones | Implementado |
| Setups | GET, POST `/api/robots/{robot_id}/setups` | Listar y guardar en PostgreSQL | Implementado |
| Setup | GET, DELETE `/api/setups/{setup_id}` | Recuperar o archivar | Implementado |
| Corridas | GET `/api/corridas` | Historial, comparación y exportación | Implementado |
| Corrida | GET, PATCH `/api/corridas/{corrida_id}` | Detalle y nota | Implementado |
| Vueltas | GET `/api/corridas/{corrida_id}/vueltas` | Sectores y segmentos | Implementado |
| Salud | GET `/api/salud` | Franja de estado y Sistema | Implementado |
| Eventos | GET, POST `/api/eventos` | Registro del sistema | Implementado |
| Manifiesto | GET `/api/dispositivos/velocista/manifiesto` | Capacidades del robot conectado | Implementado |
| Comandos | POST `/api/dispositivos/{dispositivo}/comandos` | Calibrar, arrancar, detener, setup, modo, línea y rearmar meta | Implementado |

Los mensajes de telemetría y ack permanecen en `/ws/consola` según EN-02. La persistencia automática de corridas y vueltas físicas desde esos mensajes queda pendiente de la integración de adquisición; los endpoints históricos consultan PostgreSQL y `python -m app.demo` permite probarlos con datos explícitamente simulados; no se define un POST manual que pueda suplantar un tiempo del cronómetro. La importación por enlace, autenticación, persistencia de mapas y ejecución de optimizadores requieren sus historias; sus datos están cubiertos por DO-03 sin inventar rutas ya operativas.

## Convenciones

- JSON en UTF-8; prefijo `/api` y contrato versionado por `info.version`. Base local `http://localhost:8000`, pista `http://192.168.50.10:8000`.
- Las nuevas rutas de listado paginado responden `{items,total,limite,offset}`, con limite 50 por defecto, máximo 200; offset desde 0. Páginas vacías devuelven items=[] manteniendo total. Tipos, ranuras, controladores y perfiles son catálogos pequeños y devuelven arreglos completos. Eventos conserva el arreglo existente, limite 50 y máximo 500.
- Componentes ordenados por nombre/id y búsqueda `q` sin distinguir tildes ni mayúsculas. Robots por codigo_corto/id; inventario por componente_id; versiones por ordinal ascendente; setups por creado_en/id descendente; vueltas por numero ascendente; corridas y eventos por fecha/id descendente. Los filtros de corridas se combinan con AND.
- POST de recurso devuelve 201 con el objeto creado. PATCH omite campos sin cambios y rechaza cuerpo vacío. `null` solo se admite donde el esquema lo declara. PATCH especificaciones reemplaza el objeto completo y se valida contra el tipo del componente guardado. DELETE archiva y devuelve 204 sin JSON; repetir un archivado conocido sigue devolviendo 204, un ID inexistente 404.
- `tienda` omitida al crear componente se guarda como cadena vacía; `consumo_a` como null. `firmware` omitido en robot se guarda como null. Las respuestas contienen esos campos de forma explícita. Especificaciones omitidas dentro de su objeto son desconocidas, no cero.
- Precio en PEN por unidad, masa en g, corriente en A; fechas con zona. El servicio rechaza cifras no finitas y fuera del rango físico declarado en DO-03. Parámetros de control usan los rangos/pasos del controlador.
- Escrituras de catálogo, versiones e inventario son transaccionales. El cliente nunca asigna `en_robots`, totales, número de versión, fecha, snapshot o J.
- La creación de versión comprueba `version_base_id`; PUT inventario compara `revision`. Los PATCH de metadatos y notas usan último guardado válido; no se garantiza fusión automática de ediciones simultáneas. Estos endpoints POST no prometen idempotencia: tras perder una respuesta, consultar antes de repetir.
- La versión y el setup deben pertenecer al robot del path; si no pertenecen se devuelve 404. Los archivados se pueden consultar por ID para el historial, pero no seleccionarse en nuevas versiones/setups. Crear sobre un robot archivado devuelve 409.
- Los listados de corridas son resultados cerrados. Una corrida aún activa no tiene resumen final y su consulta por ID devuelve 409 `corrida_en_curso`; el progreso se muestra por WebSocket.
- No se declara autenticación REST inexistente: `security: []` refleja el entorno local actual. Los tokens de dispositivos pertenecen al WebSocket EN-02. Autenticación de usuarios se diseñará con la historia de auth; no se inventa un JWT que la API no verifica.

## Errores

| Código | Significado | Ejemplo de motivo |
| --- | --- | --- |
| 404 | Recurso ausente o fuera del robot indicado | `no_encontrado`, `sin_manifiesto` |
| 409 | Conflicto de revisión, recurso activo/archivado o estado del robot | `revision_obsoleta`, `version_obsoleta`, `corrida_en_curso`, `desconectado`, `no_calibrado`, `bloqueado_competencia` |
| 422 | Forma, rango o regla de dominio inválida | `validacion`, `fuera_de_rango`, `parametro_desconocido` |
| 503 | Base de datos no disponible en una operación que la necesita | `base_no_disponible` |
| 500 | Error interno, sin detalles técnicos al cliente | `error_interno` |

Se conserva el formato real de `app/core/errores.py`:

```json
{"detail":{"motivo":"revision_obsoleta","detalle":"Vuelve a consultar el inventario antes de guardar"}}
```

La validación de forma de FastAPI devuelve `detail` como arreglo de `{loc,msg,type,...}`. OpenAPI declara ambas formas para 422. El endpoint salud responde 200 con `base_de_datos: "sin conexión"` cuando falla PostgreSQL; no debe confundirse con las respuestas 503 de operaciones de datos.

## Guardar y aplicar un setup

1. GET controladores y GET manifiesto para conocer parámetros y capacidades disponibles.
2. POST `/api/robots/v001/setups` con `{version_id,nombre,controlador_id,parametros}` guarda una nueva configuración y devuelve su ID.
3. Para aplicarla, POST `/api/dispositivos/velocista/comandos` con tipo `setup`, datos `{controlador,parametros,id_setup}` y la identidad del robot conectado comprobada desde el manifiesto.
4. 202 solo indica envío. La consola actualiza el setup aplicado cuando llega el ack con ok=true; muestra rechazo si ok=false. Persistencia en flash no se deduce de un registro en PostgreSQL.

## Validación y mantenimiento

Desde la raíz, usando Python 3.12 o superior:

```powershell
python -m pip install -r docs/api/requirements-validation.txt
python docs/api/generar_contrato.py
python docs/api/validar_contrato.py
```

La generación solo utiliza la biblioteca estándar. La validación usa `openapi-spec-validator` y JSON Schema; no necesita PostgreSQL, FastAPI, Node ni hardware. El job `contratos` del CI ejecuta la misma comprobación. Los archivos generados se versionan para que el contrato sea legible sin ejecutar herramientas. Editar la fuente y regenerar; no corregir a mano solo el JSON.

La validación de ejemplos y de esquemas comprueba el **contrato de diseño**, no demuestra que los endpoints propuestos estén implementados. Las pruebas HTTP, de persistencia y de concurrencia están en `api/tests/integration/`, con esquemas temporales que no modifican los datos de trabajo.

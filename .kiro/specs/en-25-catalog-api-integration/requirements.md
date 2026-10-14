# Requirements Document

## Introduction

EN-25 conecta el Catálogo, el Inventario y el Armador de la consola web con la API REST del sistema Velocista. Actualmente, la consola carga el catálogo de componentes desde datos locales (`catalogo.ts`) y calcula el inventario en el cliente. Esta funcionalidad reemplaza ese mecanismo de semillas locales con llamadas reales a `GET /api/components` y `GET /api/inventory` en el momento del montaje, aplicando el mismo patrón de carga (estado de carga, estado de error, reintento manual) que ya usa la carga de robots. Además, la consola puede registrar y archivar componentes en la API (Requirement 8), para probar el Catálogo, el Inventario y el Armador con datos reales.

## Glossary

- **Consola**: Aplicación web React del club Velocista ubicada en `consola/src`.
- **API**: Servidor FastAPI del sistema, accedido a través del helper `pedir<T>()` en `consola/src/services/api.ts`.
- **ComponenteApi**: Tipo TypeScript que modela la respuesta de un ítem de `GET /api/components` (campos: `id`, `tipo_id`, `nombre`, `masa_g`, `consumo_a`, `especificaciones`, `stock`, `precio`, `tienda`, `archivado`).
- **PaginaComponentes**: Tipo TypeScript que modela la respuesta paginada de `GET /api/components` (campos: `items`, `total`, `limite`, `offset`).
- **InventarioApi**: Tipo TypeScript que modela un ítem de `GET /api/inventory` (campos: `componente_id`, `stock`, `en_robots`, `disponible`, `faltante`, `revision`).
- **PaginaInventario**: Tipo TypeScript que modela la respuesta paginada de `GET /api/inventory` (campos: `items`, `total`, `limite`, `offset`).
- **Componente**: Tipo TypeScript del dominio interno de la consola (campos: `id`, `t`, `nm`, `precio`, `masa`, `tienda`, `stock`, `i?`, `s`).
- **FunciónMapeadora**: Función pura `mapComponenteApi(c: ComponenteApi): Componente` que traduce los campos de la API al tipo de dominio (`tipo_id→t`, `nombre→nm`, `masa_g→masa`, `consumo_a→i`, `especificaciones→s`).
- **ProveedorConsola**: Componente React `ProveedorConsola` en `consola/src/stores/ConsolaContext.tsx` que gestiona el estado global de la consola.
- **catalogLoading**: Estado booleano en el `ProveedorConsola` que indica que la carga del catálogo está en curso.
- **catalogError**: Estado string-o-null en el `ProveedorConsola` que almacena el mensaje de error de la carga del catálogo.
- **catalogRequest**: Contador numérico en el `ProveedorConsola` cuyo incremento dispara un nuevo intento de carga del catálogo.
- **restablecerDatos**: Acción del contexto `Consola` que en el prototipo limpiaba el localStorage y restauraba la semilla local.

## Requirements

### Requirement 1: Tipos de API para catálogo e inventario

**User Story:** As a desarrollador de la consola, I want tipos TypeScript que reflejen exactamente los contratos de `GET /api/components` y `GET /api/inventory`, so that el compilador detecte inconsistencias entre el cliente y la API.

#### Acceptance Criteria

1. THE Consola SHALL exportar la interfaz `ComponenteApi` desde `consola/src/types/api.ts` con los campos `id: string`, `tipo_id: string`, `nombre: string`, `precio: number`, `masa_g: number`, `tienda: string`, `consumo_a: number | null`, `especificaciones: Record<string, string | number>`, `stock: number`, y `archivado: boolean`.
2. THE Consola SHALL exportar la interfaz `PaginaComponentes` desde `consola/src/types/api.ts` con los campos `items: ComponenteApi[]`, `total: number`, `limite: number`, y `offset: number`.
3. THE Consola SHALL exportar la interfaz `InventarioApi` desde `consola/src/types/api.ts` con los campos `componente_id: string`, `stock: number`, `en_robots: number`, `disponible: number`, `faltante: number`, y `revision: number`.
4. THE Consola SHALL exportar la interfaz `PaginaInventario` desde `consola/src/types/api.ts` con los campos `items: InventarioApi[]`, `total: number`, `limite: number`, y `offset: number`.

### Requirement 2: Función mapeadora de API a dominio

**User Story:** As a desarrollador de la consola, I want una función pura que traduzca un `ComponenteApi` al tipo de dominio `Componente`, so that el resto del código de la consola siga usando el tipo de dominio interno sin acoplarse a los nombres de campo de la API.

#### Acceptance Criteria

1. THE Consola SHALL implementar una función `mapComponenteApi(c: ComponenteApi): Componente` que asigne `c.tipo_id` a `t`, `c.nombre` a `nm`, `c.masa_g` a `masa`, `c.consumo_a ?? undefined` a `i`, y `c.especificaciones` a `s`, copiando `id`, `precio`, `tienda`, y `stock` sin transformación.
2. WHEN `c.consumo_a` es `null`, THE FunciónMapeadora SHALL producir un `Componente` cuyo campo `i` es `undefined`.
3. THE FunciónMapeadora SHALL ser una función pura sin efectos secundarios ni dependencias de módulos externos.

### Requirement 3: Endpoints de componentes e inventario en el cliente de API

**User Story:** As a desarrollador de la consola, I want funciones de acceso en `api.ts` para los nuevos endpoints, so that todas las llamadas HTTP pasen por la capa de servicio centralizada y sigan el mismo patrón que los robots y las corridas.

#### Acceptance Criteria

1. THE Consola SHALL exponer `api.catalogo.listarComponentes(query?: string): Promise<PaginaComponentes>` que invoque `pedir<PaginaComponentes>` sobre `/components${query}`.
2. THE Consola SHALL exponer `api.catalogo.listarInventario(query?: string): Promise<PaginaInventario>` que invoque `pedir<PaginaInventario>` sobre `/inventory${query}`.
3. THE Consola SHALL exponer `api.catalogo.cargarTodo(): Promise<Componente[]>` que realice las solicitudes paginadas necesarias (máximo 200 ítems por página) hasta recuperar la lista completa de componentes activos y devuelva el arreglo mapeado al tipo de dominio `Componente`.
4. WHEN la API responde con `items` vacíos y `total` mayor a cero, THE Consola SHALL continuar paginando hasta agotar los resultados.

### Requirement 4: Estado de carga del catálogo en el ProveedorConsola

**User Story:** As a desarrollador de la consola, I want que el `ProveedorConsola` gestione la carga del catálogo con los mismos estados de carga, error y reintento que ya usa para los robots, so that el comportamiento sea consistente y predecible en toda la aplicación.

#### Acceptance Criteria

1. THE ProveedorConsola SHALL inicializar `catalogLoading` en `true` al montar, antes de que la petición a la API se resuelva.
2. THE ProveedorConsola SHALL inicializar `catalogError` en `null` al montar.
3. WHEN la llamada a `api.catalogo.cargarTodo()` se resuelve con éxito, THE ProveedorConsola SHALL actualizar `catalog` con los componentes devueltos y establecer `catalogLoading` en `false`.
4. WHEN la llamada a `api.catalogo.cargarTodo()` falla, THE ProveedorConsola SHALL establecer `catalogError` con un mensaje descriptivo y establecer `catalogLoading` en `false`.
5. WHEN `catalogRequest` se incrementa, THE ProveedorConsola SHALL limpiar `catalogError`, establecer `catalogLoading` en `true`, y relanzar la llamada a `api.catalogo.cargarTodo()`.
6. THE ProveedorConsola SHALL ignorar respuestas de peticiones canceladas (efecto desmontado) usando un flag de actividad `vivo`.
7. THE ProveedorConsola SHALL NO persistir el catálogo en `localStorage` ni leer componentes de `catalogo.ts` como semilla en tiempo de ejecución; `catalogo.ts` solo sirve como referencia de tipos de dominio y ranuras del armador.

### Requirement 5: Bloque con spinner hasta que el catálogo cargue

**User Story:** As a usuario de la consola, I want ver un indicador de carga mientras el catálogo se obtiene de la API, so that no vea listas vacías ni contenido parcial.

#### Acceptance Criteria

1. WHILE `catalogLoading` es `true`, THE ProveedorConsola SHALL renderizar únicamente un elemento con `role="status"` y texto "Cargando catálogo…" en lugar de los componentes hijos que dependen del catálogo.
2. WHILE `catalogError` no es `null` y `catalogLoading` es `false`, THE ProveedorConsola SHALL renderizar un elemento con `role="alert"` que muestre el mensaje de error y un botón de tipo `button` con texto "Reintentar" que al pulsarse incremente `catalogRequest`.
3. WHEN ambos `catalogLoading` y `catalogError` son `false` / `null` y `catalog` tiene al menos un elemento, THE ProveedorConsola SHALL renderizar los componentes hijos normalmente.

### Requirement 6: Stock calculado desde la API en lugar del cliente

**User Story:** As a usuario de la consola, I want que el stock disponible en el Inventario refleje el valor `en_robots` calculado por el servidor, so that los datos de disponibilidad sean coherentes con la base de datos.

#### Acceptance Criteria

1. THE ProveedorConsola SHALL cargar `GET /api/inventory` junto con `GET /api/components` al montar, dentro del mismo efecto de carga.
2. WHEN el inventario de la API se carga con éxito, THE ProveedorConsola SHALL actualizar el campo `stock` de cada `Componente` en `catalog` con el valor `stock` del registro de inventario cuyo `componente_id` coincide con el `id` del componente.
3. WHEN un componente de `catalog` no tiene entrada en el inventario de la API, THE ProveedorConsola SHALL conservar el campo `stock` devuelto directamente por `GET /api/components` para ese componente.
4. THE Consola SHALL NO calcular `en_robots` en el cliente; THE Consola SHALL usar exclusivamente el valor `en_robots` de `InventarioApi` para mostrar cuántas unidades están asignadas a robots.

### Requirement 7: Eliminación del botón "Restablecer datos de ejemplo"

**User Story:** As a usuario de la consola, I want que el botón "Restablecer datos de ejemplo" no esté visible en modo API, so that no exista una acción que no tiene efecto significativo cuando el catálogo viene del servidor.

#### Acceptance Criteria

1. THE Consola SHALL ocultar o eliminar del árbol DOM el botón que invoca `restablecerDatos()` en relación al catálogo de componentes cuando la consola opera en modo API.
2. THE ProveedorConsola SHALL mantener la función `restablecerDatos()` en la interfaz del contexto para no romper las llamadas existentes, pero THE ProveedorConsola SHALL limitar su comportamiento a recargar los robots (incrementando `robotsRequest`) sin limpiar ni resetear el catálogo desde `catalogo.ts`.

### Requirement 8: Registrar y archivar componentes desde la consola

**User Story:** Como integrante, quiero registrar y archivar componentes desde la consola, para probar el Catálogo, el Inventario y el Armador con datos reales.

#### Acceptance Criteria

1. CUANDO el usuario guarda el formulario "Registrar componente", LA Consola DEBE enviar el componente a `POST /api/components` (con su stock inicial) y volver a pedir el catálogo y el inventario.
2. SI la API rechaza el registro, ENTONCES LA Consola DEBE mostrar el motivo, mantener el formulario abierto y no agregar el componente.
3. CUANDO el usuario pulsa "Archivar" en un componente y confirma, LA Consola DEBE llamar a `DELETE /api/components/{id}` y volver a pedir el catálogo y el inventario.
4. LOS componentes archivados NO DEBEN aparecer en el Catálogo, el Inventario ni el Armador.
5. LOS nuevos nombres de funciones y variables DEBEN estar en inglés (`addComponent`, `archiveComponent`).

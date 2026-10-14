# Implementation Plan: EN-25 Conectar Catálogo, Inventario y Armador con la API

## Overview

Reemplaza la semilla local `catalogo.ts` con llamadas reales a `GET /api/components` y `GET /api/inventory`. La implementación sigue cuatro pasos: (1) añadir tipos de API, (2) añadir la función mapeadora y el sub-objeto `api.catalogo` en `services/api.ts`, (3) extender `ConsolaContext.tsx` con los nuevos estados y el efecto de carga paralelo, y (4) ajustar la UI (render gating, botón "Restablecer"). Cada paso es compilable de forma incremental y no rompe código existente.

## Tasks

- [ ] 1. Añadir interfaces de API a `types/api.ts`
  - Abrir `consola/src/types/api.ts` y exportar las cuatro nuevas interfaces: `ComponenteApi`, `PaginaComponentes`, `InventarioApi` y `PaginaInventario` tal como las define el diseño.
  - Asegurarse de que no se eliminan ni modifican las interfaces ya existentes en el archivo.
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 1.1 Verificar que TypeScript compila sin errores tras añadir los tipos
    - Ejecutar `tsc --noEmit` en `consola/` para confirmar cero errores de tipos.
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 2. Implementar `mapComponenteApi` y `api.catalogo` en `services/api.ts`
  - [ ] 2.1 Implementar la función pura `mapComponenteApi(c: ComponenteApi): Componente`
    - Añadirla en `consola/src/services/api.ts`, co-ubicada con el resto del cliente.
    - Aplicar la tabla de transformación del diseño: `tipo_id→t`, `nombre→nm`, `masa_g→masa`, `consumo_a→i` (null → undefined), `especificaciones→s`; copiar `id`, `precio`, `tienda`, `stock` sin cambio.
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.2 Escribir test de propiedad para `mapComponenteApi` — mapeo fiel de campos
    - **Property 1: Mapeo fiel de campos API a dominio**
    - Usar Vitest + fast-check; generar `ComponenteApi` arbitrarios con `consumo_a` no nulo y verificar que todos los campos del resultado son correctos.
    - **Validates: Requirements 2.1**

  - [ ]* 2.3 Escribir test de propiedad para `mapComponenteApi` — `consumo_a` nulo
    - **Property 2: `consumo_a` nulo produce `i` indefinido**
    - Generar objetos con `consumo_a === null` y verificar que `result.i === undefined`.
    - **Validates: Requirements 2.2**

  - [ ]* 2.4 Escribir test de propiedad para `mapComponenteApi` — función pura
    - **Property 3: Mapeo es una función pura (idempotencia e inmutabilidad del input)**
    - Verificar que dos llamadas con el mismo input producen resultados estrictamente iguales y que el objeto de entrada no es mutado.
    - **Validates: Requirements 2.3**

  - [ ] 2.5 Implementar el sub-objeto `api.catalogo` con `listarComponentes`, `listarInventario` y `cargarTodo`
    - Añadir `api.catalogo` como sub-objeto simétrico a `api.robots` en `consola/src/services/api.ts`.
    - `listarComponentes(query = "")` invoca `pedir<PaginaComponentes>` sobre `/components${query}`.
    - `listarInventario(query = "")` invoca `pedir<PaginaInventario>` sobre `/inventory${query}`.
    - `cargarTodo()` acumula todas las páginas (límite 200, `archivado=false`) en un bucle `do…while` y devuelve el arreglo mapeado con `mapComponenteApi`.
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 2.6 Escribir test de propiedad para `api.catalogo.cargarTodo` — paginación completa
    - **Property 4: Paginación completa acumula todos los componentes**
    - Mockear `fetch` para simular N páginas de tamaño variable (≤ 200) y verificar que el resultado contiene exactamente N ítems mapeados.
    - **Validates: Requirements 3.3, 3.4**

- [ ] 3. Checkpoint — compilación limpia de la capa de servicios
  - Asegurarse de que `tsc --noEmit` en `consola/` sigue sin errores después de los cambios en `services/api.ts` y `types/api.ts`. Confirmar con el usuario si surge alguna duda.

- [ ] 4. Extender `ConsolaContext.tsx` con estado de carga del catálogo
  - [ ] 4.1 Añadir los tres nuevos estados al `ProveedorConsola`
    - Declarar `catalogLoading` (inicial `true`), `catalogError` (inicial `null`) y `catalogRequest` (inicial `0`) con `useState`.
    - _Requirements: 4.1, 4.2_

  - [ ] 4.2 Añadir el efecto de carga paralelo disparado por `catalogRequest`
    - Implementar el `useEffect` que invoca `Promise.all([api.catalogo.cargarTodo(), api.catalogo.listarInventario("?limite=200")])`.
    - Aplicar la fusión de inventario: construir un `Map` por `componente_id` y sobrescribir `stock` en cada `Componente` que tenga coincidencia.
    - Manejar el flag `vivo` para descartar respuestas de efectos desmontados.
    - Actualizar `catalogLoading`, `catalogError` y `catalog` según el resultado.
    - _Requirements: 4.3, 4.4, 4.5, 4.6, 4.7, 6.1, 6.2, 6.3_

  - [ ]* 4.3 Escribir test de propiedad para la fusión de inventario
    - **Property 5: Fusión de inventario actualiza stock cuando existe coincidencia**
    - Usar Vitest + fast-check; generar listas arbitrarias de `Componente` y `InventarioApi` y verificar que el `stock` final coincide con el del inventario cuando hay match.
    - **Validates: Requirements 6.2, 6.3**

  - [ ]* 4.4 Escribir test de propiedad para la transición de estado en carga exitosa
    - **Property 6: Carga exitosa produce catálogo completo y limpia el estado de carga**
    - Mockear `api.catalogo.cargarTodo` para devolver N componentes y verificar que `catalog.length === N`, `catalogLoading === false` y `catalogError === null`.
    - **Validates: Requirements 4.3**

  - [ ]* 4.5 Escribir test de propiedad para el reintento
    - **Property 7: Reintento restablece el estado de carga e inicia nueva petición**
    - Desde un estado de error previo, simular el incremento de `catalogRequest` y verificar que `catalogError === null` y `catalogLoading === true` antes de que la nueva petición se resuelva.
    - **Validates: Requirements 4.5**

- [ ] 5. Añadir render gating en el `ProveedorConsola`
  - [ ] 5.1 Implementar los retornos tempranos para `catalogLoading` y `catalogError`
    - Mientras `robotsLoading || catalogLoading` sea `true`, devolver `<p role="status">Cargando catálogo…</p>`.
    - Mientras `catalogError` no sea `null`, devolver un `<div role="alert">` con el mensaje de error y un `<button type="button">` con texto "Reintentar" que llame a `setCatalogRequest((v) => v + 1)`.
    - Mantener el render gating existente para `robotsError` sin modificarlo.
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ]* 5.2 Escribir tests de ejemplo para el render gating
    - Verificar con React Testing Library que el spinner (`role="status"`) aparece durante la carga.
    - Verificar que el alert (`role="alert"`) y el botón "Reintentar" aparecen cuando `catalogError` no es null.
    - Verificar que los hijos se renderizan tras una carga exitosa.
    - _Requirements: 5.1, 5.2, 5.3_

- [ ] 6. Actualizar `restablecerDatos` y eliminar el botón "Restablecer datos de ejemplo"
  - [ ] 6.1 Modificar `restablecerDatos` para que no toque el catálogo
    - En `ConsolaContext.tsx`, actualizar la implementación de `restablecerDatos` para que solo incremente `robotsRequest` (sin acceder a `catalogo.ts` ni limpiar `catalog`), conservando la firma en la interfaz `Consola`.
    - _Requirements: 7.2_

  - [ ] 6.2 Eliminar del árbol DOM el botón que invoca `restablecerDatos()` en relación al catálogo
    - Localizar el lugar de la UI donde se renderiza ese botón y eliminarlo del árbol DOM (no usar `visibility: hidden` ni `aria-hidden`).
    - _Requirements: 7.1_

  - [ ]* 6.3 Escribir tests de ejemplo para las restricciones del botón y de `restablecerDatos`
    - Verificar que el botón "Restablecer datos de ejemplo" no está presente en el DOM en modo API.
    - Verificar que llamar a `restablecerDatos()` no resetea `catalog` al contenido de `catalogo.ts`.
    - _Requirements: 7.1, 7.2_

- [ ] 7. Checkpoint final — Asegurarse de que todos los tests pasan
  - Ejecutar `vitest --run` en `consola/` y confirmar que todos los tests pasan sin errores. Preguntar al usuario si surge alguna duda.

- [x] 8. Registrar y archivar componentes desde la consola
  - Añadir `api.catalog.create` (POST) y `api.catalog.archive` (DELETE) en `services/api.ts`.
  - Añadir `addComponent` y `archiveComponent` al `ProveedorConsola`, y el botón "Archivar" en el Catálogo.
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

## Notes

- Las sub-tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido.
- `catalogo.ts` permanece en el repositorio; solo se elimina su uso como semilla en tiempo de ejecución.
- El patrón de carga (loading / error / retry) es deliberadamente idéntico al que ya usa `robotsRequest` para mantener coherencia.
- Cada tarea referencia los requisitos específicos que cubre para trazabilidad.
- El campo `en_robots` nunca se calcula en el cliente; se usa el valor que devuelve `InventarioApi`.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.5"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.6", "4.1"] },
    { "id": 3, "tasks": ["4.2"] },
    { "id": 4, "tasks": ["4.3", "4.4", "4.5", "5.1"] },
    { "id": 5, "tasks": ["5.2", "6.1"] },
    { "id": 6, "tasks": ["6.2"] },
    { "id": 7, "tasks": ["6.3"] }
  ]
}
```

# Design Document

## Overview

EN-25 reemplaza la semilla local de componentes (`catalogo.ts` como fuente de datos en tiempo de ejecución) con llamadas reales a `GET /api/components` y `GET /api/inventory`. El diseño aplica exactamente el mismo patrón de carga que ya usa el `ProveedorConsola` para los robots: estado de carga booleano, estado de error string-o-null, y un contador de reintentos cuyo incremento vuelve a lanzar el efecto. La carga es de lectura; además, `addComponent` y `archiveComponent` (Requirement 8) guardan y archivan componentes con `POST` y `DELETE` y luego recargan el catálogo.

## Architecture

La funcionalidad se distribuye en cuatro capas ya existentes, sin introducir nuevos módulos:

```
consola/src/
├── types/
│   └── api.ts              ← Nuevas interfaces: ComponenteApi, PaginaComponentes,
│                             InventarioApi, PaginaInventario
├── services/
│   └── api.ts              ← Nuevas funciones: api.catalogo.listarComponentes,
│                             api.catalogo.listarInventario, api.catalogo.cargarTodo
│                             + función pura mapComponenteApi (co-ubicada aquí)
└── stores/
    └── ConsolaContext.tsx  ← Nuevos estados: catalogLoading, catalogError, catalogRequest
                              + efecto de carga paralelo a robotsRequest
```

La función mapeadora `mapComponenteApi` se ubica junto al cliente API (`services/api.ts`) porque su único propósito es traducir la respuesta de red al tipo de dominio antes de que el estado del contexto la reciba.

## Components and Interfaces

### 1. Tipos de API (`types/api.ts`)

Se añaden cuatro interfaces que reflejan exactamente los contratos REST:

```typescript
export interface ComponenteApi {
  id: string;
  tipo_id: string;
  nombre: string;
  precio: number;
  masa_g: number;
  tienda: string;
  consumo_a: number | null;
  especificaciones: Record<string, string | number>;
  stock: number;
  archivado: boolean;
}

export interface PaginaComponentes {
  items: ComponenteApi[];
  total: number;
  limite: number;
  offset: number;
}

export interface InventarioApi {
  componente_id: string;
  stock: number;
  en_robots: number;
  disponible: number;
  faltante: number;
  revision: number;
}

export interface PaginaInventario {
  items: InventarioApi[];
  total: number;
  limite: number;
  offset: number;
}
```

### 2. Función mapeadora y cliente API (`services/api.ts`)

#### `mapComponenteApi(c: ComponenteApi): Componente`

Función pura que traduce los nombres de campo de la API al tipo de dominio interno:

| Campo API         | Campo dominio | Transformación                   |
|-------------------|---------------|----------------------------------|
| `c.id`            | `id`          | sin cambio                       |
| `c.tipo_id`       | `t`           | sin cambio                       |
| `c.nombre`        | `nm`          | sin cambio                       |
| `c.precio`        | `precio`      | sin cambio                       |
| `c.masa_g`        | `masa`        | sin cambio                       |
| `c.tienda`        | `tienda`      | sin cambio                       |
| `c.stock`         | `stock`       | sin cambio (puede sobreescribirse con inventario) |
| `c.consumo_a`     | `i`           | `null` → `undefined`             |
| `c.especificaciones` | `s`        | sin cambio                       |

```typescript
export function mapComponenteApi(c: ComponenteApi): Componente {
  return {
    id: c.id,
    t: c.tipo_id,
    nm: c.nombre,
    precio: c.precio,
    masa: c.masa_g,
    tienda: c.tienda,
    stock: c.stock,
    ...(c.consumo_a != null ? { i: c.consumo_a } : {}),
    s: c.especificaciones,
  };
}
```

#### `api.catalogo`

Nuevo sub-objeto en `api`, simétrico a `api.robots` y `api.corridas`:

```typescript
catalogo: {
  listarComponentes(query = ""): Promise<PaginaComponentes>,
  listarInventario(query = ""): Promise<PaginaInventario>,
  async cargarTodo(): Promise<Componente[]>,
}
```

`cargarTodo()` recupera todas las páginas de componentes no archivados (máximo 200 por página) y aplica `mapComponenteApi` a cada ítem. El bucle de paginación sigue el mismo patrón que `api.robots.selection()`:

```typescript
async cargarTodo(): Promise<Componente[]> {
  const records: ComponenteApi[] = [];
  let page: PaginaComponentes;
  do {
    page = await api.catalogo.listarComponentes(
      `?limite=200&offset=${records.length}&archivado=false`
    );
    records.push(...page.items);
  } while (page.items.length > 0 && records.length < page.total);
  return records.map(mapComponenteApi);
}
```

### 3. Estado de carga del catálogo (`stores/ConsolaContext.tsx`)

#### Nuevos estados

```typescript
const [catalogLoading, setCatalogLoading] = useState(true);
const [catalogError, setCatalogError] = useState<string | null>(null);
const [catalogRequest, setCatalogRequest] = useState(0);
```

#### Efecto de carga

Se añade un efecto espejo al efecto de carga de robots, disparado por `catalogRequest`:

```typescript
useEffect(() => {
  let vivo = true;
  setCatalogLoading(true);
  setCatalogError(null);
  Promise.all([
    api.catalogo.cargarTodo(),
    api.catalogo.listarInventario("?limite=200"),
  ])
    .then(([componentes, paginaInv]) => {
      if (!vivo) return;
      const invMap = new Map(
        paginaInv.items.map((inv) => [inv.componente_id, inv])
      );
      const conStock = componentes.map((comp) => {
        const inv = invMap.get(comp.id);
        return inv ? { ...comp, stock: inv.stock } : comp;
      });
      setCatalogState(conStock);
    })
    .catch((e) => {
      if (!vivo)
        setCatalogError(
          `No se pudo cargar el catálogo: ${
            e instanceof ErrorApi ? e.message : "sin conexión con la API"
          }`
        );
    })
    .finally(() => {
      if (vivo) setCatalogLoading(false);
    });
  return () => {
    vivo = false;
  };
}, [catalogRequest]);
```

#### Render gating

El proveedor devuelve estados de UI exclusivos mientras el catálogo no está listo, idénticos al patrón de robots:

```typescript
if (robotsLoading || catalogLoading)
  return <p role="status">Cargando catálogo…</p>;
if (robotsError)
  return (
    <div role="alert">
      {robotsError}
      <button type="button" onClick={() => setRobotsRequest((v) => v + 1)}>
        Reintentar
      </button>
    </div>
  );
if (catalogError)
  return (
    <div role="alert">
      {catalogError}
      <button type="button" onClick={() => setCatalogRequest((v) => v + 1)}>
        Reintentar
      </button>
    </div>
  );
```

#### `restablecerDatos()` modificado

La función mantiene su firma en la interfaz `Consola` para no romper los sitios de llamada existentes, pero ya no toca el catálogo:

```typescript
const restablecerDatos = useCallback(() => {
  // EN-25: en modo API el catálogo no se restablece desde catalogo.ts.
  // Solo se recarga la lista de robots incrementando el contador de reintentos.
  if (!initialRobots) setRobotsRequest((value) => value + 1);
  setRobotId(robots[0]?.id ?? "");
  setFichaId(null);
  mostrarToast("Datos restablecidos.");
}, [mostrarToast, initialRobots, robots]);
```

## Data Models

### Flujo de datos en el montaje

```
GET /api/components ──► ComponenteApi[] ──► mapComponenteApi ──► Componente[]
                                                                        │
GET /api/inventory ──► InventarioApi[] ──────────────────────────► merge por id
                                                                        │
                                                              catalog: Componente[]
                                                           (stock actualizado desde inventario)
```

### Fusión de inventario

El campo `stock` del dominio se sobreescribe con el valor `stock` del registro de inventario cuando existe una coincidencia por `componente_id` = `id`. Si no hay coincidencia, se conserva el `stock` que ya devolvió `GET /api/components`. El campo `en_robots` se consume directamente de `InventarioApi` en los componentes de vista que lo necesiten; no se calcula en el cliente.

### Inicialización del estado

| Estado          | Valor inicial | Fuente                             |
|-----------------|---------------|------------------------------------|
| `catalog`       | `[]`          | API (no localStorage, no CAT)      |
| `catalogLoading`| `true`        | antes de que el efecto se resuelva |
| `catalogError`  | `null`        | limpio al montar y al reintentar   |
| `catalogRequest`| `0`           | primer montaje dispara la carga    |

### Datos locales que se mantienen (no se eliminan)

`catalogo.ts` permanece en el repositorio como referencia de tipos de ranura del armador (`RANURAS`) y como fuente de datos para pruebas unitarias. Solo se elimina su uso como semilla en tiempo de ejecución dentro de `ProveedorConsola`.

## Error Handling

| Situación                              | Comportamiento                                                        |
|----------------------------------------|-----------------------------------------------------------------------|
| Red no disponible al montar            | `catalogError` se establece, spinner desaparece, se muestra "Reintentar" |
| API responde 4xx/5xx                   | `aErrorApi` convierte la respuesta a `ErrorApi`; mensaje descriptivo en `catalogError` |
| Componente desmontado antes de resolver | flag `vivo = false` descarta la actualización de estado              |
| Retry manual                          | incrementar `catalogRequest` limpia `catalogError`, reactiva spinner y relanza fetch |
| Inventario vacío (sin registros)       | cada componente conserva su `stock` devuelto por `GET /api/components` |
| Componente sin entrada en inventario   | se conserva `stock` de `ComponenteApi`; sin error                    |

## Accessibility

- El spinner usa `role="status"` para que los lectores de pantalla anuncien el estado de carga.
- El bloque de error usa `role="alert"` para que los lectores de pantalla anuncien el error inmediatamente.
- El botón "Reintentar" es un `<button type="button">` nativo, accesible por teclado por defecto.
- La ocultación del botón "Restablecer datos de ejemplo" se logra eliminándolo del árbol DOM (no con `visibility: hidden` ni `aria-hidden`), por lo que desaparece también del árbol de accesibilidad.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Mapeo fiel de campos API a dominio

*Para cualquier* objeto `ComponenteApi` válido con `consumo_a` no nulo, `mapComponenteApi(c)` produce un `Componente` tal que `result.t === c.tipo_id`, `result.nm === c.nombre`, `result.masa === c.masa_g`, `result.i === c.consumo_a`, `result.s === c.especificaciones`, y los campos `id`, `precio`, `tienda`, `stock` son idénticos a los del input.

**Validates: Requirements 2.1**

### Property 2: `consumo_a` nulo produce `i` indefinido

*Para cualquier* objeto `ComponenteApi` con `consumo_a === null`, `mapComponenteApi(c)` produce un `Componente` cuyo campo `i` es `undefined`.

**Validates: Requirements 2.2**

### Property 3: Mapeo es una función pura (idempotencia e inmutabilidad del input)

*Para cualquier* objeto `ComponenteApi`, llamar a `mapComponenteApi` dos veces con el mismo objeto produce resultados estrictamente iguales, y el objeto de entrada no es mutado.

**Validates: Requirements 2.3**

### Property 4: Paginación completa acumula todos los componentes

*Para cualquier* configuración de páginas (total N, páginas de tamaño ≤ 200), `api.catalogo.cargarTodo()` devuelve exactamente N componentes mapeados, independientemente de cuántas páginas requiera la paginación.

**Validates: Requirements 3.3, 3.4**

### Property 5: Fusión de inventario actualiza stock cuando existe coincidencia

*Para cualquier* lista de componentes y lista de registros de inventario, después de la carga el campo `stock` de cada componente que tiene un registro coincidente por `id` es igual al valor `stock` de ese registro de inventario.

**Validates: Requirements 6.2, 6.3**

### Property 6: Carga exitosa produce catálogo completo y limpia el estado de carga

*Para cualquier* respuesta exitosa de `api.catalogo.cargarTodo()` que devuelva N componentes, el estado `catalog` del proveedor contendrá exactamente N elementos y `catalogLoading` será `false` y `catalogError` será `null`.

**Validates: Requirements 4.3**

### Property 7: Reintento restablece el estado de carga e inicia nueva petición

*Para cualquier* estado de error previo del catálogo, incrementar `catalogRequest` produce `catalogError === null` y `catalogLoading === true` antes de que la nueva petición se resuelva.

**Validates: Requirements 4.5**

## Testing Strategy

### Unit / Property Tests (puras, sin red)

| Objetivo | Tipo | Herramienta sugerida |
|---|---|---|
| `mapComponenteApi` — mapeo correcto de todos los campos | Property (Properties 1, 2, 3) | Vitest + fast-check |
| `api.catalogo.cargarTodo()` — paginación completa | Property (Property 4) | Vitest + fetch mock |
| Fusión de inventario sobre `catalog` | Property (Property 5) | Vitest + fast-check |
| Transición de estado en carga exitosa | Property (Property 6) | Vitest + React Testing Library |
| Reintento limpia error y reactiva spinner | Property (Property 7) | Vitest + React Testing Library |
| Estado inicial `catalogLoading = true` | Example | Vitest + React Testing Library |
| Estado inicial `catalogError = null` | Example | Vitest + React Testing Library |
| Error de red establece `catalogError` | Example | Vitest + fetch mock |
| Spinner `role="status"` presente durante carga | Example | Vitest + React Testing Library |
| Alert `role="alert"` + botón "Reintentar" en error | Example | Vitest + React Testing Library |
| Hijos renderizados tras carga exitosa | Example | Vitest + React Testing Library |
| Desmontaje descarta respuesta pendiente | Example | Vitest + React Testing Library |
| Botón "Restablecer datos de ejemplo" ausente del DOM | Example | Vitest + React Testing Library |
| `restablecerDatos()` no resetea catálogo a CAT | Example | Vitest + React Testing Library |

### Integration Tests (requieren servidor levantado)

| Objetivo | Tipo |
|---|---|
| `GET /api/components` y `GET /api/inventory` son llamados al montar | Integration (1-2 ejemplos) |
| Ambos endpoints llamados juntos en el mismo efecto | Integration |

### Estrategia de cobertura

- Las propiedades cubren el núcleo de la lógica: mapeo, paginación y fusión de inventario.
- Los tests de ejemplo cubren los estados de UI y los efectos secundarios del contexto React.
- Los tests de integración verifican el cableado real con la API; se ejecutan solo en CI con servidor disponible.
- `catalogo.ts` sigue siendo válido como fixture en tests unitarios; no se elimina.

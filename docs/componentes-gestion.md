# Componentes comunes de gestión (EN-06)

| Campo | Detalle |
| --- | --- |
| Ítem | EN-06 · Habilitador · Must · tarea T-17 |
| Responsable | ALG |
| Depende de | EN-16 (prototipo del Catálogo y el Armador) y EN-19 (migración del prototipo) |
| Lo usan | HU-01, HU-02, HU-03, HU-04, HU-06, HU-07 y HU-09 |
| Carpeta | `consola/src/components/gestion/` |

## 1. Qué resuelve

El backlog pide tablas, formularios y filtros reutilizables con el estilo del prototipo. Tras la migración del prototipo (EN-19) las pantallas ya existían, pero cada una dibujaba su propia tabla, su buscador y sus campos. EN-06 saca esas piezas a componentes comunes para que Catálogo, Armador y las historias siguientes las reutilicen.

**No agrega CSS.** Los componentes usan las clases que ya están en `styles/prototipo.css` (`.tabs`, `.search`, `.chips`, `.table`, `.ct`, `.fld`, `.lbl`, `.inp`, `.g2`, `.g3`, `.hint`). Las tarjetas (`Card`), los avisos (`Toast`), la ficha (`Drawer`) y el modal del registro ya existen desde EN-19 y no se duplican.

## 2. Qué hay

**Archivo:** `consola/src/components/gestion/`

| Pieza | Para qué sirve | Clase del prototipo |
| --- | --- | --- |
| `TablaDatos` | Tabla con encabezado, filas clicables (ratón, Enter y Espacio) y estado vacío | `.table` · `table.ct` |
| `Buscador` | Campo de búsqueda con lupa | `.search` |
| `ChipsFiltro` | Filtro de una opción con conteos | `.chips` |
| `Pestanas` | Pestañas con flechas, Inicio y Fin | `.tabs` |
| `CampoEntrada`, `CampoSelector` | Campo con etiqueta, error enlazado y teclado decimal en cifras | `.fld` · `.lbl` · `.inp` |
| `FormularioDinamico` | Dibuja campos a partir de su descripción | `.g2` · `.g3` |
| `useFiltroLista` | Búsqueda por texto (sin distinguir tildes) y filtro por categoría | — |
| `validarCampos`, `parsearNumero` | Obligatorios, números (coma o punto), rangos y enteros | — |

## 3. Cómo se usan

**Archivo:** `consola/src/pages/Catalogo.tsx`

```tsx
// Funciones estables, fuera del componente
const textoBuscable = (x: Componente) => `${x.nm} ${TIPOS[x.t].nm} ${TIPOS[x.t].sum(x.s)} ${x.tienda}`;
const categoriaDe = (x: Componente) => x.t;

const filtro = useFiltroLista(ordenado, { texto: textoBuscable, categoria: categoriaDe });

<Buscador valor={filtro.consulta} alCambiar={filtro.setConsulta} etiqueta="Buscar componentes" />
<ChipsFiltro etiqueta="Filtrar por tipo" valor={filtro.categoria} alCambiar={filtro.setCategoria} opciones={...} />
<TablaDatos etiqueta="Componentes del catálogo" columnas={columnas} filas={filtro.filtradas}
            clave={(x) => x.id} alHacerClic={(x) => c.abrirFicha(x.id)} />
```

Cada columna se describe con `{ id, encabezado, celda, derecha?, clase? }`. `clase` admite las del prototipo (`nm`, `sp`, `m`).

## 4. Registro manual de un componente (HU-02)

**Archivo:** `consola/src/components/RegistroModal.tsx`

En el Sprint 1 los datos entran a mano: el piloto o el integrante abre **Registrar componente**, elige el tipo y llena los campos. Los campos de especificaciones cambian según el tipo (sensor de línea: canales, salida, paso; encoder: pulsos por vuelta; turbina: diámetro, voltaje, corriente…) y salen de `datos/tipos.ts`.

Validaciones, con el mensaje junto al campo:

| Campo | Regla |
| --- | --- |
| Nombre | Obligatorio |
| Precio (S/) | Obligatorio y mayor que 0 |
| Masa (g) | Obligatoria y mayor o igual a 0 |
| En el club | Entero mayor o igual a 0 |
| Especificaciones | Opcionales; si son cifras deben ser números válidos |

Los obligatorios son los mismos del prototipo. Se agrega la validación de las cifras de especificaciones. El registro sigue guardando en el estado de la consola; conectarlo a la API es de HU-01 y HU-02 (tareas T-21, T-22, T-28 y T-29).

## 5. Pruebas

`npm test` dentro de `consola/`. Se agregan 18 pruebas, sin dependencias nuevas:

| Archivo | Qué cubre |
| --- | --- |
| `TablaDatos.test.tsx` | encabezados, clases, estado vacío, clic y teclado |
| `filtros.test.tsx` | búsqueda sin tildes, filtro por categoría, chips, buscador y pestañas con teclado |
| `formularios.test.tsx` | validación (obligatorios, coma decimal, rangos, enteros) y campos enlazados |
| `RegistroManual.test.tsx` | el Catálogo completo: buscar, filtrar, validar, cambiar de tipo y registrar |

## 6. Compatibilidad con lo que ya existía

La pantalla del Catálogo y el modal de registro se ven igual que antes (comparados píxel por píxel). Cambios de comportamiento, todos menores:

- La búsqueda encuentra "batería" al escribir "bateria".
- Las filas del inventario ahora se pueden recorrer con el teclado.
- El mensaje de error del registro aparece junto a cada campo y no solo al final.

## 7. Lo que no incluye

- La tabla de piezas del Armador (cantidad y subtotal) es de HU-06 y se construye sobre `TablaDatos` si encaja.
- Ordenar por columna y paginar: el catálogo del club cabe en una lista. Se agregan si una historia lo pide.
- La aprobación del Product Owner del estilo (criterio del backlog): pendiente.

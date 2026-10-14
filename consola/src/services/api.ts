// Única capa que hace llamadas HTTP a la API (DO-02, sección 6).
import type {
  ApiComponent,
  ApiComponentCreate,
  CorridaApi,
  ErrorNegocio,
  ApiInventory,
  ApiComponentPage,
  PaginaCorridas,
  ApiInventoryPage,
  PaginaRobots,
  Salud,
  RobotVersionApi,
} from "../types/api";
import { TIPOS } from "../datos/tipos";
import type { Componente, RobotDef } from "../types/dominio";

export class ErrorApi extends Error {
  constructor(
    readonly status: number,
    readonly motivo: string,
    detalle: string,
  ) {
    super(detalle);
  }
}

/** Convierte cualquier respuesta de error al formato estándar { motivo, detalle }. */
export function aErrorApi(status: number, cuerpo: unknown): ErrorApi {
  const detail = (cuerpo as { detail?: unknown } | null)?.detail;
  if (detail && typeof detail === "object" && !Array.isArray(detail) && "motivo" in detail) {
    const d = detail as ErrorNegocio;
    return new ErrorApi(status, d.motivo, d.detalle);
  }
  if (Array.isArray(detail))
    return new ErrorApi(status, "validacion", "Hay datos inválidos en la solicitud");
  return new ErrorApi(status, "error_http", `La API respondió ${status}`);
}

export async function pedir<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const respuesta = await fetch(`/api${ruta}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...opciones.headers },
    ...opciones,
  });
  const cuerpo = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw aErrorApi(respuesta.status, cuerpo);
  return cuerpo as T;
}

/** Traduce un componente de la API al tipo de la consola (EN-25). Es el único lugar donde se renombran los campos. */
export function mapApiComponent(c: ApiComponent): Componente {
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

/** Traduce un componente nuevo de la consola al cuerpo de POST /api/components. */
export function toApiComponentCreate(c: Omit<Componente, "id">): ApiComponentCreate {
  const consumo = Number(c.s.i);
  return {
    tipo_id: c.t,
    nombre: c.nm,
    precio: c.precio,
    masa_g: c.masa,
    tienda: c.tienda,
    consumo_a: c.s.i !== undefined && c.s.i !== "" && Number.isFinite(consumo) ? consumo : null,
    especificaciones: c.s,
    stock: c.stock,
  };
}

/** Páginas de 200 (el máximo de la API) hasta cubrir `total`; se detiene si llega una página vacía. */
async function fetchAllPages<T>(
  pedirPagina: (query: string) => Promise<{ items: T[]; total: number }>,
): Promise<T[]> {
  const registros: T[] = [];
  let pagina: { items: T[]; total: number };
  do {
    pagina = await pedirPagina(`?limit=200&offset=${registros.length}`);
    registros.push(...pagina.items);
  } while (pagina.items.length > 0 && registros.length < pagina.total);
  return registros;
}

export const api = {
  salud: () => pedir<Salud>("/health"),
  robots: {
    /** Lista los robots del armador (HU-13). `query` es la cadena ?a=b opcional. */
    listar: (query = "") => pedir<PaginaRobots>(`/robots${query}`),
    version: (robotId: string, versionId: number) =>
      pedir<RobotVersionApi>(`/robots/${encodeURIComponent(robotId)}/versions/${versionId}`),
    /** Lista completa y versión actual, sin sustituir datos del servidor por prototipos. */
    async selection(): Promise<RobotDef[]> {
      const records: PaginaRobots["items"] = [];
      let page: PaginaRobots;
      do {
        page = await api.robots.listar(`?limite=200&offset=${records.length}`);
        records.push(...page.items);
      } while (page.items.length > 0 && records.length < page.total);
      return Promise.all(
        records.map(async (record) => {
          const version =
            record.version_actual_id === null
              ? null
              : await api.robots.version(record.id, record.version_actual_id);
          return {
            id: record.id,
            nm: record.nombre,
            short: record.codigo_corto,
            tipo: record.tipo,
            fw: record.firmware,
            ver: [
              {
                v: version?.etiqueta ?? "Sin versión",
                fecha: version?.fecha ?? "—",
                nota: version?.nota ?? "Sin versión registrada",
                estado: version?.estado ?? "Borrador",
                parts: Object.fromEntries(
                  Object.entries(version?.piezas ?? {}).map(([slot, part]) => [
                    slot,
                    { id: part.componente_id, q: part.cantidad },
                  ]),
                ),
              },
            ],
          };
        }),
      );
    },
  },
  catalog: {
    /** Una página de componentes. `query` es la cadena ?a=b opcional (limit, offset, q, type_id). */
    listComponents: (query = "") => pedir<ApiComponentPage>(`/components${query}`),
    /** Una página del inventario. `query` es la cadena ?a=b opcional (limit, offset). */
    listInventory: (query = "") => pedir<ApiInventoryPage>(`/inventory${query}`),
    /** Todos los componentes activos, ya traducidos al tipo de la consola. Omite tipos desconocidos. */
    async loadAll(): Promise<Componente[]> {
      const registros = await fetchAllPages((query) => api.catalog.listComponents(query));
      return registros
        .filter((c) => {
          if (Object.hasOwn(TIPOS, c.tipo_id)) return true;
          console.warn(`Componente ${c.id} omitido: tipo desconocido "${c.tipo_id}"`);
          return false;
        })
        .map(mapApiComponent);
    },
    /** Guarda un componente nuevo (y su stock inicial) en la base de datos. */
    create: (c: Omit<Componente, "id">) =>
      pedir<ApiComponent>("/components", {
        method: "POST",
        body: JSON.stringify(toApiComponentCreate(c)),
      }),
    /** Archiva un componente (DELETE): deja de aparecer en el catálogo. */
    archive: (id: string) =>
      pedir<null>(`/components/${encodeURIComponent(id)}`, { method: "DELETE" }),
    /** Todas las existencias del inventario, indexadas por componente. */
    async loadInventory(): Promise<Record<string, ApiInventory>> {
      const registros = await fetchAllPages((query) => api.catalog.listInventory(query));
      return Object.fromEntries(registros.map((r) => [r.componente_id, r]));
    },
  },
  corridas: {
    /** Crea y persiste una corrida simulada (la consola la invoca al ARRANCAR). */
    crearSimulada: () => pedir<CorridaApi>("/runs/simulated", { method: "POST" }),
    /** Historial de corridas desde la base de datos. `query` es la cadena ?a=b opcional. */
    listar: (query = "") => pedir<PaginaCorridas>(`/runs${query}`),
  },
};

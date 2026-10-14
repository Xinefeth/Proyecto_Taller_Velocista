// Única capa que hace llamadas HTTP a la API (DO-02, sección 6).
import type {
  CorridaApi,
  ErrorNegocio,
  PaginaCorridas,
  ComponenteApi,
  PaginaComponentes,
  PaginaRobots,
  Salud,
  RobotApi,
  RobotVersionApi,
} from "../types/api";
import type { Componente, RobotDef } from "../types/dominio";

/** Mapea un componente de la API al modelo de la consola. */
function aComponente(r: ComponenteApi): Componente {
  return {
    id: r.id,
    t: r.tipo_id,
    nm: r.nombre,
    precio: r.precio,
    masa: r.masa_g,
    tienda: r.tienda,
    stock: r.stock,
    s: r.especificaciones,
    ...(r.consumo_a != null ? { i: r.consumo_a } : {}),
  };
}

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

export const api = {
  salud: () => pedir<Salud>("/health"),
  robots: {
    /** Lista los robots del armador (HU-13). `query` es la cadena ?a=b opcional. */
    listar: (query = "") => pedir<PaginaRobots>(`/robots${query}`),
    version: (robotId: string, versionId: number) =>
      pedir<RobotVersionApi>(`/robots/${encodeURIComponent(robotId)}/versions/${versionId}`),
    /** Registra un robot en la base de datos (POST /robots, HU-06). Sin versiones. */
    crear: (datos: {
      nombre: string;
      codigo_corto: string;
      tipo: "velocista" | "minisumo";
      firmware?: string | null;
    }) => pedir<RobotApi>("/robots", { method: "POST", body: JSON.stringify(datos) }),
    /** Guarda una nueva versión del robot con su lista de piezas (POST, HU-06). */
    crearVersion: (
      robotId: string,
      datos: {
        version_base_id: number | null;
        nota: string;
        estado: "Actual" | "Concepto" | "Borrador";
        piezas: Record<string, { componente_id: string; cantidad: number }>;
      },
    ) =>
      pedir<RobotVersionApi>(`/robots/${encodeURIComponent(robotId)}/versions`, {
        method: "POST",
        body: JSON.stringify(datos),
      }),
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
            verActualId: record.version_actual_id,
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
  catalogo: {
    /** Lista todos los componentes del catálogo desde la base de datos (HU-01). */
    async listar(): Promise<Componente[]> {
      const records: ComponenteApi[] = [];
      let page: PaginaComponentes;
      do {
        page = await pedir<PaginaComponentes>(
          `/components?limite=200&offset=${records.length}`,
        );
        records.push(...page.items);
      } while (page.items.length > 0 && records.length < page.total);
      return records.map(aComponente);
    },
    /** Registra un componente en la base de datos (POST /components, HU-02). */
    async crear(datos: {
      tipo_id: string;
      nombre: string;
      precio: number;
      masa_g: number;
      tienda: string;
      consumo_a?: number | null;
      especificaciones: Record<string, string | number>;
      stock: number;
    }): Promise<Componente> {
      return aComponente(
        await pedir<ComponenteApi>("/components", {
          method: "POST",
          body: JSON.stringify(datos),
        }),
      );
    },
  },
  corridas: {
    /** Crea y persiste una corrida simulada del robot indicado (al ARRANCAR en Simulado). */
    crearSimulada: (robotId: string) =>
      pedir<CorridaApi>(`/runs/simulated?robot_id=${encodeURIComponent(robotId)}`, {
        method: "POST",
      }),
    /** Historial de corridas desde la base de datos. `query` es la cadena ?a=b opcional. */
    listar: (query = "") => pedir<PaginaCorridas>(`/runs${query}`),
  },
};

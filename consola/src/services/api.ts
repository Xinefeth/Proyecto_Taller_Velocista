// Única capa que hace llamadas HTTP a la API (DO-02, sección 6).
import type {
  CorridaApi,
  ErrorNegocio,
  PaginaCorridas,
  PaginaRobots,
  Salud,
  RobotVersionApi,
} from "../types/api";
import type { RobotDef } from "../types/dominio";

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
  corridas: {
    /** Crea y persiste una corrida simulada (la consola la invoca al ARRANCAR). */
    crearSimulada: () => pedir<CorridaApi>("/runs/simulated", { method: "POST" }),
    /** Historial de corridas desde la base de datos. `query` es la cadena ?a=b opcional. */
    listar: (query = "") => pedir<PaginaCorridas>(`/runs${query}`),
  },
};

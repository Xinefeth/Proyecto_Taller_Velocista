// Única capa que hace llamadas HTTP a la API (DO-02, sección 6).
import type { ErrorNegocio, Salud } from "../types/api";

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
  salud: () => pedir<Salud>("/salud"),
};

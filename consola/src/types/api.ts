// Tipos de las respuestas REST usadas por la base de la consola. El contrato completo es EN-01 (OpenAPI).

export interface Salud {
  api: string;
  base_de_datos: string;
  entorno: string;
  dispositivos: Record<"velocista" | "cronometro", boolean>;
}

/** Formato estándar de errores de negocio (DO-02, sección 8.4). */
export interface ErrorNegocio {
  motivo: string;
  detalle: string;
}

export type EstadoConexion = "revisando" | "ok" | "falla";

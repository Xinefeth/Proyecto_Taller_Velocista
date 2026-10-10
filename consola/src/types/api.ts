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

/** Resumen de una corrida devuelto por la API (EN-01 · CorridaSalida). */
export interface CorridaApi {
  id: number;
  numero: number;
  robot_id: string;
  version_id: number;
  setup_id: number;
  perfil_id: string;
  controlador_id: string;
  parametros: Record<string, number>;
  fecha: string;
  fuente: "sim" | "robot";
  modo: "prueba" | "competencia";
  linea: "negra" | "blanca";
  compensa_bateria: boolean;
  potencia_turbina_pct: number;
  tiempo_s: number | null;
  termino: boolean;
  error_acumulado: number;
  bateria_v: number;
  sectores_s: number[];
  fuente_tiempo: "meta" | "telemetria";
  nota: string;
  j: number;
}

export interface PaginaCorridas {
  items: CorridaApi[];
  total: number;
  limite: number;
  offset: number;
}

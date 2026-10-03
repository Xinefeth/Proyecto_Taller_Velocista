// Tipos del contrato de mensajes v1.0 (EN-02).
// Fuente única de verdad: api/app/contrato/ · Documento: docs/contrato/

export type ValorCanal = number | boolean | number[];

export interface Canal {
  nombre: string;
  descripcion: string;
  tipo: "float" | "int" | "bool" | "float[]" | "int[]";
  longitud?: number;
  unidad: string;
  min?: number;
  max?: number;
  grupo: "estado" | "senales";
}

export interface Parametro {
  nombre: string;
  etiqueta: string;
  tipo: "float" | "int";
  min: number;
  max: number;
  paso?: number;
  valor: number;
  unidad: string;
  optimizable: boolean;
}

export interface Controlador {
  nombre: string;
  descripcion: string;
  parametros: Parametro[];
}

export interface Manifiesto {
  contrato: string;
  id: string;
  tipo_robot: string;
  firmware: string;
  sensores: {
    nombre: string;
    modelo: string;
    canales: string[];
    detalles: Record<string, unknown>;
  }[];
  actuadores: { nombre: string; tipo: string; modelo: string; canales: string[] }[];
  canales: Canal[];
  controladores: Controlador[];
  controlador_activo: string;
  comandos: string[];
  frecuencias: { lazo_hz: number; estado_hz: number; senales_hz: number };
  arranque: "comando" | "modulo_arranque";
  compensa_bateria: boolean;
}

export interface EstadoRobot {
  estado: "listo" | "calibrando" | "corriendo" | "detenido" | "error";
  calibrado: boolean;
  modo: "prueba" | "competencia";
  linea: "negra" | "blanca";
  controlador: string;
  lazo_hz: number;
  rssi_dbm: number;
  canales: Record<string, ValorCanal>;
}

export interface Senales {
  t_ms: number;
  canales: Record<string, ValorCanal>;
}

export interface Ack {
  ok: boolean;
  motivo?: string;
  detalle?: string;
}

/** Mensaje que la API reenvía a la consola por /ws/consola. */
export interface MensajeConsola<T = Record<string, unknown>> {
  origen: "velocista" | "cronometro" | "api";
  tipo: string;
  seq: number;
  ts: number;
  datos: T;
  recibido_ms: number;
}

/** Canales de un grupo según el manifiesto: la consola arma sus paneles con esto. */
export function canalesDe(m: Manifiesto, grupo: Canal["grupo"]): Canal[] {
  return m.canales.filter((c) => c.grupo === grupo);
}

// Tipos del dominio de la consola, portados del prototipo (Protoripo.html, maqueta v2).
// Modelan el catálogo, los robots con versiones, los perfiles de reglamento y los
// controladores enchufables (DO-03, HU-06, HU-10, HU-17).

/** Especificaciones de un componente: cada tipo declara sus campos (numéricos o de texto). */
export type Specs = Record<string, number | string>;

export type Severidad = "ok" | "warn" | "bad";

/** Resultado de una revisión (compatibilidad o reglamento): severidad, título y detalle. */
export type Chequeo = [Severidad, string, string];

/** Un tipo de componente y lo que aporta a la consola (DO-03: capacidades). */
export interface TipoComponente {
  nm: string;
  /** Color identificador del tipo. */
  c: string;
  /** Campos del tipo: [clave, etiqueta, "n" numérico | "t" texto]. */
  f: [clave: string, etiqueta: string, tipo: "n" | "t"][];
  /** Resumen legible de las specs. */
  sum: (s: Specs) => string;
  /** Qué aporta al manifiesto/consola; ausente si el tipo no agrega paneles. */
  cap?: (s: Specs) => string;
}

export interface Componente {
  id: string;
  /** Clave del tipo en TIPOS. */
  t: string;
  nm: string;
  precio: number;
  masa: number;
  tienda: string;
  stock: number;
  /** Consumo estimado en amperios. */
  i?: number;
  s: Specs;
}

/** Ranura del armador: un hueco que se llena con un componente de un tipo. */
export interface Ranura {
  k: string;
  t: string;
  nm: string;
  /** 1 si es obligatoria. */
  req?: number;
  /** 1 si admite cantidad editable. */
  q?: number;
  /** 1 si es opcional y depende del reglamento. */
  opt?: number;
}

export interface PiezaRef {
  id: string;
  q: number;
}

/** Piezas de una versión: por clave de ranura, la pieza elegida. */
export type Piezas = Record<string, PiezaRef | undefined>;

export interface Version {
  v: string;
  fecha: string;
  nota: string;
  estado: string;
  parts: Piezas;
}

export interface RobotDef {
  id: string;
  nm: string;
  short: string;
  tipo: "velocista" | "minisumo";
  fw: string | null;
  ver: Version[];
}

/** Reglas de una categoría, guardadas como datos (HU-10). `null` = libre. */
export interface ReglasPerfil {
  dim: [number, number] | null;
  sensMax: number | null;
  motores: number | null;
  motorFam: string[] | null;
  ruedas: number | null;
  drivers: number | null;
  mcu: string[] | null;
  turbina: boolean;
  pcbComercial: boolean;
  montaje: string;
  chasis: string;
  chasisMat?: string[];
  arranque: string;
  inal: boolean;
  enc: boolean;
  imu: boolean;
  mapaVel: boolean;
  mr4: boolean;
}

export interface Perfil {
  id: string;
  comp: string;
  tag: string;
  cat: string;
  r: ReglasPerfil;
}

/** Definición de un parámetro de control (rango, paso y decimales). */
export interface DefParam {
  nm: string;
  t: string;
  min: number;
  max: number;
  step: number;
  dec: number;
}

/** Un controlador enchufable (PID, adaptativo, difuso) con sus parámetros y presets. */
export interface Controlador {
  nm: string;
  short: string;
  /** Parámetros que expone, en orden. */
  keys: string[];
  /** Parámetros que optimiza el ingeniero de pista (Twiddle). */
  tw: string[];
  desc: string;
  pre: Record<string, Record<string, number>>;
}

/** Setup activo: controlador elegido y valores de sus parámetros (HU-17). */
export interface Setup {
  ctrl: string;
  p: Record<string, number>;
}

/** Datos derivados de las piezas de una versión (facts del prototipo). */
export interface Hechos {
  cost: number;
  mass: number;
  cur: number;
  line?: Componente;
  sensores: number;
  sensMods: number;
  motor?: Componente;
  motores: number;
  mcu?: Componente;
  driver?: Componente;
  drivers: number;
  bat?: Componente;
  reg?: Componente;
  mux?: Componente;
  exp?: Componente;
  rueda?: Componente;
  chasis?: Componente;
  ancho: number;
  largo: number;
  enc?: Componente;
  imu?: Componente;
  turb?: Componente;
  radio: string;
}

// Tipos de componente con sus capacidades (DO-03), portados del prototipo (Protoripo.html).
// Cada tipo declara qué campos tiene y qué aporta a la consola/manifiesto (`cap`).
import type { Specs, TipoComponente } from "../types/dominio";

export const TIPOS: Record<string, TipoComponente> = {
  mcu: {
    nm: "Microcontrolador",
    c: "#FF5A78",
    f: [
      ["mhz", "Frecuencia (MHz)", "n"],
      ["radio", "Radio", "t"],
      ["logica", "Lógica (V)", "n"],
      ["adc", "Entradas analógicas usables", "n"],
    ],
    sum: (s) => `${s.mhz} MHz · ${s.radio} · ${s.logica} V`,
    cap: (s) =>
      s.radio && s.radio !== "Ninguna"
        ? `Conexión y arranque inalámbrico por ${s.radio}`
        : "Ejecuta el firmware (sin radio)",
  },
  exp: {
    nm: "Placa de expansión",
    c: "#A2A7B8",
    f: [
      ["bornes", "Bornes", "n"],
      ["comercial", "PCB comercial", "t"],
    ],
    sum: (s) => `${s.bornes} bornes · ${s.comercial === "Sí" ? "PCB comercial" : "diseño propio"}`,
  },
  linea: {
    nm: "Sensor de línea",
    c: "#3DDC97",
    f: [
      ["canales", "Canales", "n"],
      ["salida", "Salida", "t"],
      ["paso", "Paso (mm)", "n"],
      ["i", "Consumo (A)", "n"],
    ],
    sum: (s) => `${s.canales} canales · ${s.salida} · paso ${s.paso} mm`,
    cap: (s) => `${s.canales} canales de línea en la regleta`,
  },
  mux: {
    nm: "Multiplexor",
    c: "#6CB6FF",
    f: [
      ["canales", "Canales", "n"],
      ["tipo", "Tipo", "t"],
    ],
    sum: (s) => `${s.canales} canales · ${s.tipo}`,
  },
  motor: {
    nm: "Motor",
    c: "#B48CFF",
    f: [
      ["v", "Voltaje nominal (V)", "n"],
      ["rpm", "RPM sin carga", "n"],
      ["inom", "Corriente nominal (A)", "n"],
      ["ipico", "Corriente de arranque (A)", "n"],
      ["red", "Reducción", "t"],
      ["familia", "Familia", "t"],
    ],
    sum: (s) => `${s.v} V · ${s.rpm} rpm · ${s.ipico} A arranque`,
    cap: () => "Actuador: PWM de −100 a 100 %",
  },
  driver: {
    nm: "Driver",
    c: "#FFCB57",
    f: [
      ["canales", "Canales", "n"],
      ["icont", "Corriente continua (A)", "n"],
      ["ipico", "Corriente pico (A)", "n"],
      ["vmin", "V mín.", "n"],
      ["vmax", "V máx.", "n"],
    ],
    sum: (s) => `${s.canales} ch · ${s.icont} A cont. · ${s.vmin}–${s.vmax} V`,
  },
  bat: {
    nm: "Batería",
    c: "#3DDC97",
    f: [
      ["celdas", "Celdas (S)", "n"],
      ["mah", "Capacidad (mAh)", "n"],
      ["c", "Descarga (C)", "n"],
      ["vmax", "V a carga completa", "n"],
    ],
    sum: (s) => `${s.celdas}S · ${s.mah} mAh · ${s.c}C`,
    cap: () => "Voltaje de batería en la telemetría",
  },
  reg: {
    nm: "Regulador",
    c: "#A2A7B8",
    f: [
      ["vout", "Salida (V)", "n"],
      ["imax", "Corriente máx. (A)", "n"],
      ["tipo", "Tipo", "t"],
    ],
    sum: (s) => `${s.vout} V · ${s.imax} A · ${s.tipo}`,
  },
  rueda: {
    nm: "Rueda",
    c: "#A2A7B8",
    f: [
      ["diam", "Diámetro (mm)", "n"],
      ["material", "Material", "t"],
    ],
    sum: (s) => `Ø ${s.diam} mm · ${s.material}`,
  },
  chasis: {
    nm: "Chasis",
    c: "#A2A7B8",
    f: [
      ["ancho", "Ancho (mm)", "n"],
      ["largo", "Largo (mm)", "n"],
      ["material", "Material", "t"],
    ],
    sum: (s) => `${s.ancho} × ${s.largo} mm · ${s.material}`,
  },
  sw: {
    nm: "Interruptor",
    c: "#5E6374",
    f: [["tipo", "Tipo", "t"]],
    sum: (s) => String(s.tipo),
  },
  enc: {
    nm: "Encoder",
    c: "#6CB6FF",
    f: [
      ["cpr", "Pulsos por vuelta (CPR)", "n"],
      ["tipo", "Tipo", "t"],
    ],
    sum: (s) => `${s.cpr} CPR · ${s.tipo}`,
    cap: () => "Velocidad de cada rueda (rpm)",
  },
  imu: {
    nm: "IMU",
    c: "#6CB6FF",
    f: [
      ["ejes", "Ejes", "n"],
      ["bus", "Bus", "t"],
    ],
    sum: (s) => `${s.ejes} ejes · ${s.bus}`,
    cap: () => "Giro y aceleración",
  },
  turb: {
    nm: "Turbina",
    c: "#FF2D55",
    f: [
      ["diam", "Diámetro (mm)", "n"],
      ["v", "Voltaje (V)", "n"],
      ["imax", "Corriente (A)", "n"],
    ],
    sum: (s) => `Ø ${s.diam} mm · ${s.v} V · ${s.imax} A`,
    cap: () => "Actuador: succión de 0 a 100 %",
  },
};

/** Orden canónico de los tipos (para chips del catálogo y ordenación). */
export const ORDEN_TIPOS: string[] = Object.keys(TIPOS);

/** Color de un tipo, con respaldo gris. */
export const colorTipo = (t: string): string => TIPOS[t]?.c ?? "#A2A7B8";

/** Resumen de specs de un componente de tipo `t`. */
export const resumenSpecs = (t: string, s: Specs): string => TIPOS[t].sum(s);

// Robots del armador con sus versiones y piezas, portados del prototipo (Protoripo.html).
// Datos semilla (HU-06). Las versiones nuevas se agregan en memoria desde el armador.
import type { RobotDef } from "../types/dominio";

export const ROBOTS: RobotDef[] = [
  {
    id: "v001",
    nm: "Velocista 001",
    short: "001",
    tipo: "velocista",
    fw: "0.3.1",
    ver: [
      {
        v: "v0",
        fecha: "20 set 2026",
        nota: "Prueba de concepto: 1 QTR-8A directo al ESP32",
        estado: "Descartada",
        parts: {
          mcu: { id: "c01", q: 1 },
          linea: { id: "c05", q: 1 },
          motor: { id: "c09", q: 2 },
          driver: { id: "c12", q: 1 },
          bat: { id: "c15", q: 1 },
          reg: { id: "c17", q: 1 },
          rueda: { id: "c18", q: 1 },
          chasis: { id: "c20", q: 1 },
        },
      },
      {
        v: "v1",
        fecha: "29 set 2026",
        nota: "Primer armado: 2 QTR-8A con multiplexor de 16 canales",
        estado: "Actual",
        parts: {
          mcu: { id: "c01", q: 1 },
          exp: { id: "c04", q: 1 },
          linea: { id: "c05", q: 2 },
          mux: { id: "c08", q: 1 },
          motor: { id: "c09", q: 2 },
          driver: { id: "c12", q: 1 },
          bat: { id: "c14", q: 1 },
          reg: { id: "c16", q: 1 },
          rueda: { id: "c18", q: 1 },
          chasis: { id: "c19", q: 1 },
          sw: { id: "c21", q: 1 },
        },
      },
    ],
  },
  {
    id: "v002",
    nm: "Velocista 002",
    short: "002",
    tipo: "velocista",
    fw: null,
    ver: [
      {
        v: "v1",
        fecha: "—",
        nota: "Concepto para Master: encoders y turbina",
        estado: "Concepto",
        parts: {
          mcu: { id: "c01", q: 1 },
          exp: { id: "c04", q: 1 },
          linea: { id: "c05", q: 2 },
          mux: { id: "c08", q: 1 },
          motor: { id: "c10", q: 2 },
          driver: { id: "c12", q: 1 },
          bat: { id: "c14", q: 1 },
          reg: { id: "c16", q: 1 },
          rueda: { id: "c18", q: 1 },
          chasis: { id: "c25", q: 1 },
          sw: { id: "c21", q: 1 },
          enc: { id: "c22", q: 1 },
          turb: { id: "c24", q: 1 },
        },
      },
    ],
  },
  {
    id: "ms01",
    nm: "MiniSumo RC",
    short: "MS1",
    tipo: "minisumo",
    fw: null,
    ver: [
      {
        v: "v0",
        fecha: "12 set 2026",
        nota: "Chasis MDF con motores TT",
        estado: "Actual",
        parts: {
          mcu: { id: "c02", q: 1 },
          motor: { id: "c11", q: 2 },
          driver: { id: "c13", q: 1 },
          bat: { id: "c15", q: 1 },
          reg: { id: "c17", q: 1 },
          chasis: { id: "c20", q: 1 },
          sw: { id: "c21", q: 1 },
        },
      },
    ],
  },
];

/** Nombre legible de cada tipo de robot. */
export const TIPO: Record<string, string> = {
  velocista: "Seguidor velocista",
  minisumo: "MiniSumo RC",
};

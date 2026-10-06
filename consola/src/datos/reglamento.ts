// Perfiles de reglamento como datos (HU-10, SP-01) y reglas generales, del prototipo (Protoripo.html).
import type { Perfil, ReglasPerfil } from "../types/dominio";

export const PERFILES: Perfil[] = [
  {
    id: "mr4a",
    comp: "Muchik Rumble 4",
    tag: "MR4",
    cat: "Amateur",
    r: {
      dim: [200, 250],
      sensMax: 8,
      motores: 2,
      motorFam: ["TT amarillo"],
      ruedas: 2,
      drivers: 1,
      mcu: ["Arduino UNO", "Arduino Nano", "Raspberry Pi Pico", "ESP32"],
      turbina: false,
      pcbComercial: false,
      montaje: "Protoboard, cableado directo, shield genérico o PCB propia",
      chasis: "Obligatorio: impresión 3D o MDF",
      chasisMat: ["3D", "MDF"],
      arranque: "Interruptor, pulsador, IR o Bluetooth",
      inal: false,
      enc: false,
      imu: false,
      mapaVel: false,
      mr4: true,
    },
  },
  {
    id: "mr4s",
    comp: "Muchik Rumble 4",
    tag: "MR4",
    cat: "Senior",
    r: {
      dim: [200, 250],
      sensMax: null,
      motores: 2,
      motorFam: null,
      ruedas: 2,
      drivers: null,
      mcu: null,
      turbina: false,
      pcbComercial: true,
      montaje: "Libre",
      chasis: "Libre",
      arranque: "Inalámbrico",
      inal: true,
      enc: false,
      imu: false,
      mapaVel: false,
      mr4: true,
    },
  },
  {
    id: "mr4m",
    comp: "Muchik Rumble 4",
    tag: "MR4",
    cat: "Master",
    r: {
      dim: [300, 300],
      sensMax: null,
      motores: null,
      motorFam: null,
      ruedas: null,
      drivers: null,
      mcu: null,
      turbina: true,
      pcbComercial: true,
      montaje: "Libre (se admiten robots comerciales)",
      chasis: "Libre",
      arranque: "Inalámbrico",
      inal: true,
      enc: false,
      imu: false,
      mapaVel: false,
      mr4: true,
    },
  },
  {
    id: "club",
    comp: "Pruebas del club",
    tag: "Club",
    cat: "Libre",
    r: {
      dim: null,
      sensMax: null,
      motores: null,
      motorFam: null,
      ruedas: null,
      drivers: null,
      mcu: null,
      turbina: true,
      pcbComercial: true,
      montaje: "Libre",
      chasis: "Libre",
      arranque: "Libre",
      inal: false,
      enc: true,
      imu: true,
      mapaVel: true,
      mr4: false,
    },
  },
];

/** Reglas generales de la competencia, para la tabla informativa del reglamento. */
export const GENERALES: [string, string][] = [
  [
    "El robot se mueve solo por el sensado de la línea",
    "Sin movimientos pre-programados, control remoto, otros sensores ni encoders.",
  ],
  ["Una vuelta por intento, en 3 rondas", "Vale el menor tiempo de las tres rondas."],
  ["Máximo 120 s por intento", "Si no llega a la meta es ronda nula. En la consola: J = 120."],
  ["1 minuto para estar listo", "Incluye colocar el robot y calibrar los sensores."],
  [
    "Recuperación autónoma en 10 s",
    "Si sale de la pista, debe volver solo sin saltarse un sector.",
  ],
  [
    "Pista",
    "Línea de 19 mm negra sobre blanco o viceversa; curvas de Ø ≥ 30 cm; ángulos ≥ 90°; rampas ≤ 30°; puede haber túneles.",
  ],
  ["Sensores de tiempo a ≥ 30 cm de la línea", "Aplica a los postes del cronómetro de meta."],
  [
    "Amateur y Senior: robot de fabricación propia",
    "Senior: una PCB con agujero para turbina pasa a Master.",
  ],
];

/** Filas de la tabla comparativa de reglas por categoría (HU-10). */
export const REGLAS: [string, (r: ReglasPerfil) => string][] = [
  ["Dimensiones máx.", (r) => (r.dim ? `${r.dim[0] / 10} × ${r.dim[1] / 10} cm` : "Libre")],
  [
    "Sensores",
    (r) => (r.sensMax ? `Máx. ${r.sensMax}, solo en módulo (QTR-8A, QTR-8RC, TCRT5000…)` : "Libre"),
  ],
  [
    "Motores",
    (r) =>
      r.motorFam
        ? `Solo ${r.motores} motorreductores amarillos o celestes, sin modificar`
        : r.motores
          ? `Solo ${r.motores}`
          : "Libre",
  ],
  ["Ruedas", (r) => (r.ruedas ? `Solo ${r.ruedas}` : "Libre")],
  ["Driver", (r) => (r.drivers ? `Libre (solo ${r.drivers})` : "Libre")],
  ["Microcontrolador", (r) => (r.mcu ? r.mcu.join(", ") : "Libre")],
  ["Turbina", (r) => (r.turbina ? "Libre" : "No permitida")],
  ["Montaje", (r) => r.montaje],
  ["Chasis", (r) => r.chasis],
  ["Arranque", (r) => r.arranque],
  ["Encoders e IMU", (r) => (r.enc ? "Permitidos" : "Prohibidos")],
  ["Mapa para la velocidad", (r) => (r.mapaVel ? "Permitido" : "Prohibido")],
];

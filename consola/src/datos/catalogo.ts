// Catálogo de componentes del club y ranuras del armador, portados del prototipo (Protoripo.html).
// Datos semilla del catálogo (EN-04, HU-01). En modo robot vendrán de la API.
import type { Componente, Ranura } from "../types/dominio";

export const CAT: Componente[] = [
  { id: "c01", t: "mcu", nm: "ESP32-S3 DevKitC-1 N16R8", precio: 48, masa: 9, tienda: "Proveedor local (Trujillo)", stock: 2, i: 0.24, s: { mhz: 240, radio: "WiFi + BLE", logica: 3.3, adc: 10 } },
  { id: "c02", t: "mcu", nm: "Arduino Nano (ATmega328P)", precio: 28, masa: 7, tienda: "Proveedor local (Trujillo)", stock: 4, i: 0.03, s: { mhz: 16, radio: "Ninguna", logica: 5, adc: 8 } },
  { id: "c03", t: "mcu", nm: "Raspberry Pi Pico", precio: 30, masa: 3, tienda: "Proveedor Lima", stock: 1, i: 0.03, s: { mhz: 133, radio: "Ninguna", logica: 3.3, adc: 3 } },
  { id: "c04", t: "exp", nm: "Placa de expansión ESP32-S3", precio: 22, masa: 14, tienda: "Proveedor local (Trujillo)", stock: 2, s: { bornes: 44, comercial: "Sí" } },
  { id: "c05", t: "linea", nm: "Pololu QTR-8A", precio: 62, masa: 3, tienda: "Importación", stock: 3, i: 0.1, s: { canales: 8, salida: "Analógica", paso: 9.525, i: 0.1 } },
  { id: "c06", t: "linea", nm: "Pololu QTR-8RC", precio: 62, masa: 3, tienda: "Importación", stock: 1, i: 0.1, s: { canales: 8, salida: "RC digital", paso: 9.525, i: 0.1 } },
  { id: "c07", t: "linea", nm: "Módulo TCRT5000 × 5", precio: 18, masa: 6, tienda: "Proveedor local (Trujillo)", stock: 2, i: 0.08, s: { canales: 5, salida: "Analógica", paso: 12, i: 0.08 } },
  { id: "c08", t: "mux", nm: "CD74HC4067 · 16 canales", precio: 12, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 3, s: { canales: 16, tipo: "Analógico" } },
  { id: "c09", t: "motor", nm: "Micromotor N20 10:1 · 6 V", precio: 38, masa: 10, tienda: "Proveedor Lima", stock: 4, i: 0.35, s: { v: 6, rpm: 3000, inom: 0.35, ipico: 1.6, red: "10:1", familia: "N20" } },
  { id: "c10", t: "motor", nm: "Pololu 10:1 Micro Metal HPCB · 6 V", precio: 95, masa: 10, tienda: "Importación", stock: 2, i: 0.4, s: { v: 6, rpm: 3200, inom: 0.4, ipico: 1.6, red: "10:1", familia: "Micro Metal" } },
  { id: "c11", t: "motor", nm: "Motorreductor amarillo TT 1:48", precio: 8, masa: 30, tienda: "Proveedor local (Trujillo)", stock: 10, i: 0.2, s: { v: 6, rpm: 200, inom: 0.2, ipico: 1.5, red: "1:48", familia: "TT amarillo" } },
  { id: "c12", t: "driver", nm: "TB6612FNG", precio: 16, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 3, s: { canales: 2, icont: 1.2, ipico: 3.2, vmin: 2.5, vmax: 13.5 } },
  { id: "c13", t: "driver", nm: "DRV8833", precio: 14, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 2, s: { canales: 2, icont: 1.5, ipico: 2, vmin: 2.7, vmax: 10.8 } },
  { id: "c14", t: "bat", nm: "LiPo 2S 450 mAh 30C", precio: 55, masa: 26, tienda: "Proveedor Lima", stock: 2, s: { celdas: 2, mah: 450, c: 30, vmax: 8.4 } },
  { id: "c15", t: "bat", nm: "LiPo 2S 300 mAh 25C", precio: 45, masa: 18, tienda: "Proveedor Lima", stock: 1, s: { celdas: 2, mah: 300, c: 25, vmax: 8.4 } },
  { id: "c16", t: "reg", nm: "Mini buck MP1584 · 5 V", precio: 7, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 5, s: { vout: 5, imax: 3, tipo: "Conmutado" } },
  { id: "c17", t: "reg", nm: "LM7805", precio: 3, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 6, s: { vout: 5, imax: 1, tipo: "Lineal" } },
  { id: "c18", t: "rueda", nm: "Ruedas de silicona 22 mm (par)", precio: 24, masa: 6, tienda: "Proveedor Lima", stock: 2, s: { diam: 22, material: "Silicona" } },
  { id: "c19", t: "chasis", nm: "Chasis PETG impreso 3D", precio: 20, masa: 22, tienda: "Impresión del club", stock: 1, s: { ancho: 180, largo: 215, material: "PETG impreso 3D" } },
  { id: "c20", t: "chasis", nm: "Chasis MDF 3 mm", precio: 10, masa: 30, tienda: "Proveedor local (Trujillo)", stock: 2, s: { ancho: 170, largo: 200, material: "MDF" } },
  { id: "c25", t: "chasis", nm: "Chasis PETG largo con toma de turbina", precio: 26, masa: 28, tienda: "Impresión del club", stock: 0, s: { ancho: 190, largo: 240, material: "PETG impreso 3D" } },
  { id: "c21", t: "sw", nm: "Interruptor deslizante mini", precio: 1.5, masa: 1, tienda: "Proveedor local (Trujillo)", stock: 10, s: { tipo: "Deslizante" } },
  { id: "c22", t: "enc", nm: "Encoders magnéticos N20 (par)", precio: 32, masa: 2, tienda: "Importación", stock: 1, s: { cpr: 12, tipo: "Magnético" } },
  { id: "c23", t: "imu", nm: "MPU-6050", precio: 14, masa: 2, tienda: "Proveedor local (Trujillo)", stock: 2, i: 0.004, s: { ejes: 6, bus: "I²C" } },
  { id: "c24", t: "turb", nm: "EDF 30 mm · 7.4 V", precio: 85, masa: 14, tienda: "Importación", stock: 0, i: 3.5, s: { diam: 30, v: 7.4, imax: 3.5 } },
];

/** Ranuras del armador: tipo, obligatoriedad y si admiten cantidad (HU-06). */
export const RANURAS: Ranura[] = [
  { k: "mcu", t: "mcu", nm: "Microcontrolador", req: 1 },
  { k: "exp", t: "exp", nm: "Placa de expansión" },
  { k: "linea", t: "linea", nm: "Sensores de línea", req: 1, q: 1 },
  { k: "mux", t: "mux", nm: "Multiplexor" },
  { k: "motor", t: "motor", nm: "Motores", req: 1, q: 1 },
  { k: "driver", t: "driver", nm: "Driver", req: 1 },
  { k: "bat", t: "bat", nm: "Batería", req: 1 },
  { k: "reg", t: "reg", nm: "Regulador", req: 1 },
  { k: "rueda", t: "rueda", nm: "Ruedas (par)" },
  { k: "chasis", t: "chasis", nm: "Chasis", req: 1 },
  { k: "sw", t: "sw", nm: "Interruptor" },
  { k: "enc", t: "enc", nm: "Encoders", opt: 1 },
  { k: "imu", t: "imu", nm: "IMU", opt: 1 },
  { k: "turb", t: "turb", nm: "Turbina", opt: 1 },
];

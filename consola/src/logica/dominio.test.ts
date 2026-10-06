// Pruebas de la lógica de dominio: resumen del robot (HU-07), piezas y versiones (HU-06),
// compatibilidad (HU-08), reglamento (HU-10) y manifiesto (EN-02).
import { describe, expect, it } from "vitest";
import { CAT } from "../datos/catalogo";
import { PERFILES } from "../datos/reglamento";
import { ROBOTS } from "../datos/robots";
import type { Componente, Piezas, RobotDef, Specs } from "../types/dominio";
import {
  checks,
  compat,
  complies,
  curVer,
  facts,
  guardarPiezas,
  manifest,
  profById,
  robotById,
  siguienteIdComponente,
  usedIn,
  usedQty,
} from "./dominio";

// Catálogo pequeño con números fáciles de comprobar a mano.
const comp = (
  id: string,
  t: string,
  precio: number,
  masa: number,
  s: Specs,
  i?: number,
): Componente => ({
  id,
  t,
  nm: id,
  precio,
  masa,
  tienda: "Prueba",
  stock: 1,
  s,
  ...(i === undefined ? {} : { i }),
});
const mcu = comp(
  "mcu1",
  "mcu",
  50,
  9,
  { mhz: 240, radio: "WiFi + BLE", logica: 3.3, adc: 10 },
  0.24,
);
const linea = comp(
  "lin1",
  "linea",
  60,
  3,
  { canales: 8, salida: "Analógica", paso: 9.5, i: 0.1 },
  0.1,
);
const mux = comp("mux1", "mux", 12, 2, { canales: 16, tipo: "Analógico" });
const motor = comp(
  "mot1",
  "motor",
  38,
  10,
  { v: 6, rpm: 3000, inom: 0.35, ipico: 1.6, red: "10:1", familia: "N20" },
  0.35,
);
const driver = comp("drv1", "driver", 16, 2, {
  canales: 2,
  icont: 1.2,
  ipico: 3.2,
  vmin: 2.5,
  vmax: 13.5,
});
const bat = comp("bat1", "bat", 55, 26, { celdas: 2, mah: 450, c: 30, vmax: 8.4 });
const CATALOGO = [mcu, linea, mux, motor, driver, bat];

const piezas = (o: Record<string, [string, number]>): Piezas =>
  Object.fromEntries(Object.entries(o).map(([k, [id, q]]) => [k, { id, q }]));

describe("facts: costo, masa y consumo (HU-07)", () => {
  it("suma precio, masa y consumo de las piezas por su cantidad", () => {
    const f = facts(piezas({ mcu: ["mcu1", 1], linea: ["lin1", 2] }), CATALOGO);
    expect(f.cost).toBe(50 + 60 * 2);
    expect(f.mass).toBe(9 + 3 * 2 + 8); // 8 g de cableado y soldadura
    expect(f.cur).toBeCloseTo(0.24 + 0.1 * 2, 10);
    expect(f.sensores).toBe(16); // 8 canales por módulo × 2 módulos
    expect(f.sensMods).toBe(2);
  });

  it("se actualiza al cambiar una pieza", () => {
    const antes = facts(piezas({ mcu: ["mcu1", 1], linea: ["lin1", 2] }), CATALOGO);
    const unaMenos = facts(piezas({ mcu: ["mcu1", 1], linea: ["lin1", 1] }), CATALOGO);
    expect(antes.cost - unaMenos.cost).toBe(60);
    expect(antes.mass - unaMenos.mass).toBe(3);
    expect(antes.cur - unaMenos.cur).toBeCloseTo(0.1, 10);
    const sinMux = facts(piezas({ mcu: ["mcu1", 1] }), CATALOGO);
    const conMux = facts(piezas({ mcu: ["mcu1", 1], mux: ["mux1", 1] }), CATALOGO);
    expect(conMux.cost - sinMux.cost).toBe(12);
  });

  it("un robot sin piezas vale 0 y no suma el cableado", () => {
    const f = facts({}, CATALOGO);
    expect([f.cost, f.mass, f.cur, f.sensores]).toEqual([0, 0, 0, 0]);
  });

  it("ignora una pieza que ya no está en el catálogo", () => {
    const f = facts(piezas({ mcu: ["mcu1", 1], linea: ["no-existe", 1] }), CATALOGO);
    expect(f.cost).toBe(50);
    expect(f.line).toBeUndefined();
  });

  it("con los datos de ejemplo, el Velocista 001 vale lo que dice el catálogo", () => {
    const f = facts(curVer(ROBOTS[0]).parts, CAT);
    expect(f.cost).toBeCloseTo(405.5, 5);
    expect(Math.round(f.mass)).toBe(118);
    expect(f.cur).toBeCloseTo(1.14, 5);
    expect(f.sensores).toBe(16);
    expect(f.motores).toBe(2);
  });
});

describe("compat: compatibilidad de las piezas (HU-08)", () => {
  const revisar = (o: Record<string, [string, number]>, cat = CATALOGO) =>
    compat(facts(piezas(o), cat));
  const titulos = (l: ReturnType<typeof compat>, s: string) =>
    l.filter((x) => x[0] === s).map((x) => x[1]);

  it("avisa cuando falta el microcontrolador", () => {
    expect(titulos(revisar({ linea: ["lin1", 1] }), "bad")).toContain("Falta el microcontrolador");
  });

  it("revisa que el multiplexor alcance para los canales", () => {
    const bien = revisar({ mcu: ["mcu1", 1], linea: ["lin1", 2], mux: ["mux1", 1] });
    expect(titulos(bien, "ok")).toContain("16 canales por el multiplexor");
    const mal = revisar({ mcu: ["mcu1", 1], linea: ["lin1", 3], mux: ["mux1", 1] });
    expect(titulos(mal, "bad")).toContain("El multiplexor no alcanza");
  });

  it("sin multiplexor, revisa las entradas analógicas del microcontrolador", () => {
    expect(titulos(revisar({ mcu: ["mcu1", 1], linea: ["lin1", 1] }), "ok")).toContain(
      "Entradas analógicas suficientes",
    );
    const mal = revisar({ mcu: ["mcu1", 1], linea: ["lin1", 2] });
    expect(titulos(mal, "bad")).toContain("Faltan entradas analógicas");
    expect(mal.find((x) => x[1] === "Faltan entradas analógicas")![2]).toContain("ADC2");
  });

  it("compara la corriente del motor con la del driver", () => {
    expect(titulos(revisar({ motor: ["mot1", 2], driver: ["drv1", 1] }), "ok")).toContain(
      "El driver soporta los motores",
    );
    const flojo = comp("drv2", "driver", 8, 2, {
      canales: 2,
      icont: 0.5,
      ipico: 1,
      vmin: 2.5,
      vmax: 10,
    });
    expect(
      titulos(revisar({ motor: ["mot1", 2], driver: ["drv2", 1] }, [...CATALOGO, flojo]), "bad"),
    ).toContain("El driver no soporta los motores");
  });

  it("revisa el voltaje de la batería frente al driver y a los motores", () => {
    expect(titulos(revisar({ bat: ["bat1", 1], driver: ["drv1", 1] }), "ok")).toContain(
      "Batería dentro del rango del driver",
    );
    const bajo = comp("drv3", "driver", 8, 2, {
      canales: 2,
      icont: 1.2,
      ipico: 3.2,
      vmin: 9,
      vmax: 12,
    });
    expect(
      titulos(revisar({ bat: ["bat1", 1], driver: ["drv3", 1] }, [...CATALOGO, bajo]), "bad"),
    ).toContain("Batería fuera del rango del driver");
    // Motores de 6 V con batería de 8,4 V: aviso con el PWM máximo (6 × 1,2 / 8,4 = 86 %).
    const aviso = revisar({ bat: ["bat1", 1], motor: ["mot1", 2] }).find((x) => x[0] === "warn")!;
    expect(aviso[2]).toContain("86 %");
  });

  it("los robots de ejemplo no tienen errores de compatibilidad", () => {
    for (const r of ROBOTS) {
      const errores = compat(facts(curVer(r).parts, CAT)).filter((x) => x[0] === "bad");
      expect(errores, r.nm).toEqual([]);
    }
  });
});

describe("checks: reglamento por categoría (HU-10)", () => {
  const perfil = (id: string) => profById(PERFILES, id)!;
  const robot = (id: string) => robotById(ROBOTS, id)!;
  const malos = (r: RobotDef, id: string) =>
    checks(facts(curVer(r).parts, CAT), perfil(id))
      .filter((x) => x[0] === "bad")
      .map((x) => x[1]);

  it("el Velocista 001 cumple Senior, Master y el perfil libre", () => {
    for (const id of ["mr4s", "mr4m", "club"])
      expect(complies(robot("v001"), perfil(id), CAT), id).toBe(true);
  });

  it("el Velocista 001 no cumple Amateur: sensores, motor y PCB comercial", () => {
    expect(malos(robot("v001"), "mr4a")).toEqual(["Sensores", "Tipo de motor", "PCB comercial"]);
  });

  it("encoders y turbina no se aceptan en el reglamento, pero el perfil libre sí los permite", () => {
    expect(malos(robot("v002"), "mr4s")).toEqual(["Turbina", "Encoders"]);
    expect(complies(robot("v002"), perfil("club"), CAT)).toBe(true);
  });

  it("exige arranque inalámbrico en Senior", () => {
    expect(malos(robot("ms01"), "mr4s")).toContain("Arranque");
  });
});

describe("manifest: sensores y actuadores salen de las piezas (HU-06, EN-02)", () => {
  const m = (id: string) => manifest(robotById(ROBOTS, id)!, CAT, "pid", true);

  it("el Velocista 001 expone regleta, batería y dos motores, y arranca por radio", () => {
    expect(m("v001").sensores.map((x) => x.id)).toEqual(["regleta", "bateria"]);
    expect(m("v001").actuadores.map((x) => x.id)).toEqual(["motor_izq", "motor_der"]);
    expect(m("v001").arranque).toBe("inalambrico");
    expect(m("v001").sensores[0]).toMatchObject({ canales: 16, modulos: 2, via: "multiplexor" });
  });

  it("acepta encoders y turbina: aparecen como sensor y actuador", () => {
    expect(m("v002").sensores.map((x) => x.id)).toContain("encoders");
    expect(m("v002").actuadores.map((x) => x.id)).toContain("turbina");
  });

  it("un robot sin radio arranca con interruptor", () => {
    expect(m("ms01").arranque).toBe("interruptor");
    expect(m("ms01").sensores.map((x) => x.id)).toEqual(["bateria"]);
  });
});

describe("inventario: robots que usan cada pieza (HU-03, HU-04)", () => {
  it("cuenta las piezas en la versión actual de cada robot", () => {
    const u = usedIn(ROBOTS, "c05"); // Pololu QTR-8A
    expect(u.map((x) => x.r.id)).toEqual(["v001", "v002"]);
    expect(usedQty(ROBOTS, "c05")).toBe(4); // 2 en cada robot
    expect(usedQty(ROBOTS, "c03")).toBe(0); // la Raspberry Pi Pico no se usa
  });
});

describe("siguienteIdComponente", () => {
  it("toma el mayor número usado más uno", () => {
    expect(siguienteIdComponente(CAT)).toBe("c26");
    expect(siguienteIdComponente([])).toBe("c01");
    expect(
      siguienteIdComponente([comp("c09", "mcu", 1, 1, {}), comp("raro", "mcu", 1, 1, {})]),
    ).toBe("c10");
  });
});

describe("guardarPiezas: versiones del robot (HU-06)", () => {
  const nuevo: RobotDef = {
    id: "v003",
    nm: "Velocista 003",
    short: "003",
    tipo: "velocista",
    fw: null,
    ver: [{ v: "v1", fecha: "hoy", nota: "Borrador", estado: "Borrador", parts: {} }],
  };

  it("un robot nuevo queda con su versión 1 y la lista de piezas, sin crear una v2 vacía", () => {
    const { robot, version } = guardarPiezas(
      nuevo,
      piezas({ mcu: ["c01", 1], linea: ["c05", 1] }),
      "Primer armado",
    );
    expect(robot.ver).toHaveLength(1);
    expect(version.v).toBe("v1");
    expect(robot.ver[0].parts).toEqual({ mcu: { id: "c01", q: 1 }, linea: { id: "c05", q: 1 } });
    expect(robot.ver[0].nota).toBe("Primer armado");
  });

  it("si el robot ya tiene piezas, crea la versión siguiente y deja la actual como anterior", () => {
    const v001 = robotById(ROBOTS, "v001")!;
    const cambio = { ...curVer(v001).parts, chasis: { id: "c20", q: 1 } };
    const { robot, version } = guardarPiezas(v001, cambio, "Chasis: MDF");
    expect(robot.ver).toHaveLength(v001.ver.length + 1);
    expect(version.v).toBe("v2");
    expect(robot.ver.at(-2)?.estado).toBe("Anterior");
    expect(robot.ver.at(-1)?.estado).toBe("Actual");
    expect(v001.ver.at(-1)?.estado).toBe("Actual"); // no modifica el robot original
  });

  it("acepta cualquier tipo de pieza, incluidos encoders, IMU y turbina", () => {
    const todas = piezas({ mcu: ["c01", 1], enc: ["c22", 1], imu: ["c23", 1], turb: ["c24", 1] });
    const { robot } = guardarPiezas(nuevo, todas, "Con extras");
    const f = facts(curVer(robot).parts, CAT);
    expect([f.enc?.id, f.imu?.id, f.turb?.id]).toEqual(["c22", "c23", "c24"]);
  });
});

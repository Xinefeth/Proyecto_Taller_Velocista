import { beforeEach, describe, expect, it } from "vitest";
import { CAT } from "../datos/catalogo";
import { ROBOTS } from "../datos/robots";
import type { Componente } from "../types/dominio";
import {
  CLAVE_COMPONENTES,
  CLAVE_ROBOTS,
  borrarRegistrados,
  cargarComponentes,
  cargarRobots,
  esComponente,
  esRobot,
  guardarComponentes,
  guardarRobots,
  type Almacen,
} from "./persistencia";

// Almacén en memoria con la misma interfaz que localStorage.
function crearAlmacen(): Almacen & { datos: Map<string, string> } {
  const datos = new Map<string, string>();
  return {
    datos,
    getItem: (k) => datos.get(k) ?? null,
    setItem: (k, v) => void datos.set(k, v),
    removeItem: (k) => void datos.delete(k),
  };
}

const nuevo: Componente = {
  id: "c26",
  t: "enc",
  nm: "Encoder óptico",
  precio: 30.5,
  masa: 4,
  tienda: "Local",
  stock: 2,
  s: { cpr: 20, tipo: "Óptico" },
};

let almacen: ReturnType<typeof crearAlmacen>;
beforeEach(() => {
  almacen = crearAlmacen();
});

describe("componentes registrados a mano", () => {
  it("sin nada guardado devuelve solo el catálogo de ejemplo", () => {
    expect(cargarComponentes(CAT, almacen)).toEqual(CAT);
  });

  it("guarda solo los registrados y los devuelve después del catálogo de ejemplo", () => {
    guardarComponentes([...CAT, nuevo], CAT, almacen);
    const guardado = JSON.parse(almacen.datos.get(CLAVE_COMPONENTES)!);
    expect(guardado.items).toEqual([nuevo]);
    const cargado = cargarComponentes(CAT, almacen);
    expect(cargado).toHaveLength(CAT.length + 1);
    expect(cargado.at(-1)).toEqual(nuevo);
  });

  it("si ya no hay registrados, borra la clave", () => {
    guardarComponentes([...CAT, nuevo], CAT, almacen);
    guardarComponentes(CAT, CAT, almacen);
    expect(almacen.datos.has(CLAVE_COMPONENTES)).toBe(false);
  });

  it("descarta lo dañado o inválido en vez de romper la consola", () => {
    almacen.setItem(CLAVE_COMPONENTES, "{esto no es json");
    expect(cargarComponentes(CAT, almacen)).toEqual(CAT);
    almacen.setItem(
      CLAVE_COMPONENTES,
      JSON.stringify({
        version: 1,
        items: [nuevo, { id: "c27", t: "inexistente" }, { ...nuevo, id: "c28", precio: "x" }],
      }),
    );
    expect(cargarComponentes(CAT, almacen).map((c) => c.id)).toEqual([
      ...CAT.map((c) => c.id),
      "c26",
    ]);
  });

  it("ignora una versión de formato desconocida y un id que ya existe en el catálogo de ejemplo", () => {
    almacen.setItem(CLAVE_COMPONENTES, JSON.stringify({ version: 99, items: [nuevo] }));
    expect(cargarComponentes(CAT, almacen)).toEqual(CAT);
    almacen.setItem(
      CLAVE_COMPONENTES,
      JSON.stringify({ version: 1, items: [{ ...nuevo, id: "c01" }] }),
    );
    expect(cargarComponentes(CAT, almacen)).toEqual(CAT);
  });

  it("sigue funcionando sin almacenamiento disponible", () => {
    expect(cargarComponentes(CAT, null)).toEqual(CAT);
    expect(() => guardarComponentes([...CAT, nuevo], CAT, null)).not.toThrow();
  });

  it("no rompe si el almacén lanza errores (lleno o bloqueado)", () => {
    const roto: Almacen = {
      getItem: () => {
        throw new Error("bloqueado");
      },
      setItem: () => {
        throw new Error("lleno");
      },
      removeItem: () => {
        throw new Error("bloqueado");
      },
    };
    expect(cargarComponentes(CAT, roto)).toEqual(CAT);
    expect(() => guardarComponentes([...CAT, nuevo], CAT, roto)).not.toThrow();
    expect(() => borrarRegistrados(roto)).not.toThrow();
  });
});

describe("robots", () => {
  it("sin cambios no guarda nada y carga los de ejemplo", () => {
    guardarRobots(ROBOTS, ROBOTS, almacen);
    expect(almacen.datos.has(CLAVE_ROBOTS)).toBe(false);
    expect(cargarRobots(ROBOTS, almacen)).toEqual(ROBOTS);
  });

  it("conserva un robot nuevo y las versiones agregadas", () => {
    const creado = { ...ROBOTS[0], id: "v003", nm: "Velocista 003", short: "003" };
    guardarRobots([...ROBOTS, creado], ROBOTS, almacen);
    expect(cargarRobots(ROBOTS, almacen).map((r) => r.id)).toEqual([
      "v001",
      "v002",
      "ms01",
      "v003",
    ]);
  });

  it("si lo guardado no es válido, vuelve a los robots de ejemplo", () => {
    almacen.setItem(CLAVE_ROBOTS, JSON.stringify({ version: 1, items: [{ id: 5 }] }));
    expect(cargarRobots(ROBOTS, almacen)).toEqual(ROBOTS);
    almacen.setItem(CLAVE_ROBOTS, "null");
    expect(cargarRobots(ROBOTS, almacen)).toEqual(ROBOTS);
  });

  it("cargarRobots devuelve una copia: modificarla no cambia los datos de ejemplo", () => {
    const copia = cargarRobots(ROBOTS, almacen);
    copia[0].nm = "Cambiado";
    expect(ROBOTS[0].nm).toBe("Velocista 001");
  });
});

describe("restablecer", () => {
  it("borrarRegistrados quita componentes y robots", () => {
    guardarComponentes([...CAT, nuevo], CAT, almacen);
    guardarRobots([...ROBOTS, { ...ROBOTS[0], id: "v003" }], ROBOTS, almacen);
    borrarRegistrados(almacen);
    expect(almacen.datos.size).toBe(0);
  });
});

describe("validadores", () => {
  it("esComponente rechaza tipos, números y especificaciones inválidos", () => {
    expect(esComponente(nuevo)).toBe(true);
    expect(esComponente({ ...nuevo, t: "constructor" })).toBe(false);
    expect(esComponente({ ...nuevo, precio: -1 })).toBe(false);
    expect(esComponente({ ...nuevo, masa: Infinity })).toBe(false);
    expect(esComponente({ ...nuevo, nm: "  " })).toBe(false);
    expect(esComponente({ ...nuevo, s: { cpr: {} } })).toBe(false);
    expect(esComponente(null)).toBe(false);
  });

  it("esRobot revisa versiones y piezas", () => {
    expect(ROBOTS.every(esRobot)).toBe(true);
    expect(esRobot({ ...ROBOTS[0], ver: [] })).toBe(false);
    expect(esRobot({ ...ROBOTS[0], tipo: "otro" })).toBe(false);
    expect(
      esRobot({
        ...ROBOTS[0],
        ver: [{ v: "v1", fecha: "", nota: "", estado: "", parts: { mcu: { id: 1, q: 1 } } }],
      }),
    ).toBe(false);
  });
});

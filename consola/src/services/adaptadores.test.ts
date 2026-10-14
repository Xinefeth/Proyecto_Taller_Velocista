import { describe, expect, it } from "vitest";
import { componenteDesdeApi, componenteParaApi, robotDesdeApi } from "./adaptadores";

describe("REST adapters", () => {
  it("round-trips specifications without changing screen models", () => {
    const dto = {
      id: "c05",
      type_id: "linea" as const,
      name: "QTR",
      price: 62,
      mass_g: 3,
      store: "Importación",
      stock: 2,
      current_a: null,
      archived: false,
      specifications: { channels: 8, pitch: 9.525, output: "Analógica" },
    };
    const model = componenteDesdeApi(dto);
    expect(model.s).toEqual({ canales: 8, paso: 9.525, salida: "Analógica" });
    expect(model.nm).toBe("QTR");
    expect(model.i).toBeUndefined();
    const expected = {
      type_id: dto.type_id,
      name: dto.name,
      price: dto.price,
      mass_g: dto.mass_g,
      store: dto.store,
      stock: dto.stock,
      current_a: dto.current_a,
      specifications: dto.specifications,
    };
    expect(componenteParaApi({ ...model, t: "linea" })).toEqual(expected);
  });
  it("preserves version IDs and immutable snapshots for later saves", () => {
    const robot = {
      id: "r1",
      name: "Robot",
      short_code: "R1",
      type: "velocista" as const,
      firmware: null,
      current_version_id: 7,
      archived: false,
    };
    const version = {
      id: 7,
      robot_id: "r1",
      label: "v0",
      date: "2026-10-13T00:00:00Z",
      note: "Concepto",
      status: "Concepto" as const,
      parts: {},
    };
    const model = robotDesdeApi(robot, [version]);
    expect(model.ver[0].v).toBe("v0");
    expect(model.api.current_version_id).toBe(7);
  });
});

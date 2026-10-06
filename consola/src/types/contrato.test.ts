import { describe, expect, it } from "vitest";
import manifiestoEjemplo from "../../../docs/contrato/ejemplos/velocista.manifiesto.json";
import { canalesDe, type Manifiesto } from "./contrato";

describe("canalesDe", () => {
  it("separa los canales del manifiesto de ejemplo por grupo", () => {
    const m = manifiestoEjemplo.datos as unknown as Manifiesto;
    expect(canalesDe(m, "estado").map((c) => c.nombre)).toEqual(["bateria_v"]);
    expect(canalesDe(m, "senales").map((c) => c.nombre)).toContain("error");
  });
});

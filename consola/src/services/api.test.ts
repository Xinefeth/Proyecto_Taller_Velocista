import { describe, expect, it } from "vitest";
import { aErrorApi } from "./api";

describe("aErrorApi", () => {
  it("lee el formato estándar de errores de negocio", () => {
    const e = aErrorApi(409, {
      detail: { motivo: "no_calibrado", detalle: "Calibra antes de arrancar" },
    });
    expect([e.status, e.motivo, e.message]).toEqual([
      409,
      "no_calibrado",
      "Calibra antes de arrancar",
    ]);
  });
  it("traduce los errores de validación de FastAPI", () => {
    expect(aErrorApi(422, { detail: [{ loc: ["body"], msg: "x" }] }).motivo).toBe("validacion");
  });
  it("tolera respuestas sin cuerpo", () => {
    expect(aErrorApi(500, null).motivo).toBe("error_http");
  });
});

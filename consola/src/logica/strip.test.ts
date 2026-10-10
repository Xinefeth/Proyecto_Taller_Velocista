import { describe, expect, it } from "vitest";
import { stripFromMessages, stripFromSignals } from "./strip";
import type { Senales } from "../types/contrato";
import type { MensajeConsola } from "../types/mensajes";

const signalsWith = (readings: unknown): Senales =>
  ({ t_ms: 0, canales: { regleta: readings, error: 0.99 } }) as Senales;

describe("HU-15 · cálculo desde los 16 canales", () => {
  it.each([0, 15])("calcula posición y error en el extremo %i", (index) => {
    const readings = Array<number>(16).fill(0);
    readings[index] = 1000;
    const view = stripFromSignals(signalsWith(readings));
    expect(view?.positionMm).toBe(index === 0 ? -72 : 72);
    expect(view?.error).toBe(index === 0 ? -1 : 1);
    expect(view?.centered).toBe(false);
    expect(view?.active).toBe(1);
  });

  it("calcula el centro y detecta la línea perdida", () => {
    const readings = Array<number>(16).fill(0);
    readings[7] = readings[8] = 1000;
    expect(stripFromSignals(signalsWith(readings))).toMatchObject({
      positionMm: 0,
      error: 0,
      centered: true,
      lost: false,
    });
    expect(stripFromSignals(signalsWith(Array(16).fill(0)))).toMatchObject({
      centered: false,
      lost: true,
    });
  });

  it.each([
    undefined,
    [],
    Array(15).fill(0),
    Array(17).fill(0),
    Array(16).fill(NaN),
    Array(16).fill(Infinity),
    Array(16).fill("1000"),
  ])("rechaza muestras inválidas para permitir el respaldo (%j)", (readings) => {
    expect(stripFromSignals(signalsWith(readings))).toBeNull();
  });

  it("usa la muestra más reciente del velocista e ignora otros emisores", () => {
    const message = (origin: string, index: number): MensajeConsola => {
      const readings = Array<number>(16).fill(0);
      readings[index] = 1000;
      return {
        origen: origin,
        tipo: "senales",
        datos: signalsWith(readings),
        recibido_ms: 0,
      } as unknown as MensajeConsola;
    };
    expect(
      stripFromMessages([
        message("cronometro", 0),
        message("velocista", 15),
        message("velocista", 0),
      ])?.positionMm,
    ).toBe(72);
    expect(stripFromMessages([])).toBeNull();
  });
});

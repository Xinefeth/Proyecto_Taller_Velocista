// HU-15 · Vista de la regleta: 16 barras con su valor, posición (mm), error y "centrada".
// Monta solo la tarjeta Regleta y le inyecta un `senales` real por /ws/consola (mock de
// escucharConsola). Comprueba que la vista se alimenta de los canales reales, no de la
// simulación de respaldo.
import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Regleta } from "./Control";
import { ProveedorConsola } from "../stores/ConsolaContext";
import { ProveedorConexion } from "../stores/ConexionContext";
import { api } from "../services/api";
import * as ws from "../services/ws";
import type { MensajeConsola } from "../types/mensajes";
import { ROBOTS as TEST_ROBOTS } from "../datos/robots";

// Igual que api/herramientas/robot_falso.py: pico en `center`, caída hacia los lados.
function rawReadings(center: number): number[] {
  return Array.from({ length: 16 }, (_, i) =>
    Math.max(0, Math.round(1000 - 350 * Math.abs(i - center) ** 1.5)),
  );
}

function signalsMessage(readings: number[], error = 0): MensajeConsola {
  return {
    origen: "velocista",
    tipo: "senales",
    datos: { t_ms: 0, canales: { error, regleta: readings, pwm_izq: 160, pwm_der: 160 } },
    recibido_ms: 0,
  };
}

// Hace que /ws/consola entregue este mensaje `senales` en cuanto la consola se suscribe.
function deliver(message: MensajeConsola) {
  vi.spyOn(ws, "escucharConsola").mockImplementation((onMessage, onConnectionChange) => {
    onConnectionChange(true);
    onMessage(message);
    return { cerrar: () => {} };
  });
}

beforeEach(() => {
  // Neutraliza los efectos de red y el bucle de simulación del store.
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.spyOn(api, "salud").mockReturnValue(new Promise(() => {}));
  vi.spyOn(api.robots, "listar").mockReturnValue(new Promise(() => {}));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

const mountStrip = () =>
  render(
    <ProveedorConexion>
      <ProveedorConsola initialRobots={TEST_ROBOTS}>
        <Regleta />
      </ProveedorConsola>
    </ProveedorConexion>,
  );

describe("HU-15 · Vista de la regleta con datos reales", () => {
  it("dibuja las 16 lecturas como barras con su valor", () => {
    deliver(signalsMessage(rawReadings(7.5)));
    const { container } = mountStrip();
    const bars = container.querySelectorAll(".bars .bar");
    expect(bars).toHaveLength(16);
    // Cada barra muestra su valor (dígito 0..9) y una altura proporcional.
    bars.forEach((b) => {
      const n = b.querySelector(".n")?.textContent ?? "";
      expect(n).toMatch(/^[0-9]$/);
      expect((b.querySelector(".tb i") as HTMLElement).style.height).toMatch(/%$/);
    });
    // Con la línea al center, los canales centrales saturan: algún dígito alto (≥ 7).
    const digits = Array.from(bars, (b) => Number(b.querySelector(".n")?.textContent));
    expect(Math.max(...digits)).toBeGreaterThanOrEqual(7);
  });

  it("con la línea al centro muestra 0.0 mm y 'Centrada'", () => {
    deliver(signalsMessage(rawReadings(7.5)));
    const { container } = mountStrip();
    expect(container.textContent).toContain("Centrada");
    const position = container.querySelector(".sread .v")?.textContent ?? "";
    expect(position).toBe("0.0 mm");
  });

  it("con la línea a la derecha muestra posición positiva y 'Hacia la derecha'", () => {
    deliver(signalsMessage(rawReadings(12)));
    const { container } = mountStrip();
    expect(container.textContent).toContain("Hacia la derecha");
    const position = container.querySelector(".sread .v")?.textContent ?? "";
    expect(position).toMatch(/^\+\d+\.\d mm$/);
  });

  it("deriva el error de las lecturas aunque el canal error sea diferente", () => {
    deliver(signalsMessage(rawReadings(7.5), 0.33));
    const { container } = mountStrip();
    const values = Array.from(container.querySelectorAll(".sread .v"), (v) => v.textContent);
    // [posición, error, sobre la línea]
    expect(values[1]).toBe("0.00");
    expect(values[2]).toMatch(/^\d+ \/ 16$/);
  });

  it("mantiene la simulación como respaldo sin mensajes reales", () => {
    vi.spyOn(ws, "escucharConsola").mockReturnValue({ cerrar: () => {} });
    const { container } = mountStrip();
    expect(container.querySelectorAll(".bars .bar")).toHaveLength(16);
    expect(container.querySelector(".sread .v")?.textContent).toMatch(/mm$/);
    expect(container.textContent).toContain("Centrada");
  });

  it("sin línea detectada (todos los canales en 0) marca 'Línea perdida' y 'Perdida'", () => {
    deliver(signalsMessage(new Array(16).fill(0)));
    const { container } = mountStrip();
    expect(container.textContent).toContain("Línea perdida");
    const position = container.querySelector(".sread .v")?.textContent ?? "";
    expect(position).toBe("Perdida");
  });
});

// Armador de robots: registrar un robot y sus piezas (HU-06) y ver su resumen (HU-07).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { ProveedorConsola } from "../stores/ConsolaContext";

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("scrollTo", () => {});
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const abrirArmador = () => {
  const vista = render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Armador de robots" }));
  return vista;
};

const tarjetaResumen = () => screen.getByRole("heading", { name: "Resumen" }).closest("article")!;

/** Valor de una cifra del resumen, por ejemplo "Costo total". */
const resumen = (etiqueta: string) =>
  within(tarjetaResumen()).getByText(etiqueta).nextElementSibling!.textContent;
const elegir = (pieza: string, id: string) =>
  fireEvent.change(screen.getByLabelText(pieza), { target: { value: id } });

describe("HU-07 · resumen del robot", () => {
  it("calcula costo, masa y consumo a partir de las piezas", () => {
    abrirArmador();
    expect(resumen("Costo total")).toBe("S/ 405.50");
    expect(resumen("Masa")).toBe("118 g");
    expect(resumen("Consumo estimado")).toBe("1.14 A");
    expect(resumen("Sensores de línea")).toBe("16");
  });

  it("se actualiza al cambiar una pieza", () => {
    abrirArmador();
    elegir("Chasis", "c20"); // MDF (S/ 10, 30 g) en vez de PETG (S/ 20, 22 g)
    expect(resumen("Costo total")).toBe("S/ 395.50");
    expect(resumen("Masa")).toBe("126 g");
    expect(screen.getByText("Tienes cambios sin guardar en las piezas.")).toBeTruthy();
  });

  it("al descartar los cambios vuelve a los valores guardados", () => {
    abrirArmador();
    elegir("Chasis", "c20");
    fireEvent.click(screen.getByRole("button", { name: "Descartar" }));
    expect(resumen("Costo total")).toBe("S/ 405.50");
  });
});

describe("HU-06 · registrar un robot y sus piezas", () => {
  it("crea el robot con su versión 1 y la lista de piezas", () => {
    abrirArmador();
    fireEvent.click(screen.getByRole("button", { name: /Nuevo robot/ }));
    expect(screen.getByRole("heading", { name: "Velocista 003" })).toBeTruthy();
    expect(resumen("Costo total")).toBe("S/ 0.00");

    elegir("Microcontrolador", "c01"); // ESP32-S3: S/ 48
    elegir("Sensores de línea", "c05"); // QTR-8A: S/ 62
    expect(resumen("Costo total")).toBe("S/ 110.00");
    fireEvent.click(screen.getByRole("button", { name: "Guardar como nueva versión" }));

    // Queda una sola versión (v1) con sus piezas; no se crea una v2 y deja la v1 vacía.
    expect(screen.getByRole("button", { name: "v1 · actual" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^v2/ })).toBeNull();
    expect(resumen("Costo total")).toBe("S/ 110.00");
    expect(screen.queryByText("Tienes cambios sin guardar en las piezas.")).toBeNull();
  });

  it("acepta encoders, IMU y turbina", () => {
    abrirArmador();
    fireEvent.click(screen.getByRole("button", { name: /Nuevo robot/ }));
    elegir("Encoders", "c22");
    elegir("IMU", "c23");
    elegir("Turbina", "c24");
    expect(resumen("Costo total")).toBe("S/ 131.00"); // 32 + 14 + 85
    // Lo que expone a la consola sale de las piezas elegidas.
    const expone = within(tarjetaResumen());
    expect(expone.getByText("Encoders")).toBeTruthy();
    expect(expone.getByText("IMU")).toBeTruthy();
    expect(expone.getByText("Turbina")).toBeTruthy();
  });

  it("conserva el robot nuevo aunque se recargue la consola", () => {
    const primera = abrirArmador();
    fireEvent.click(screen.getByRole("button", { name: /Nuevo robot/ }));
    elegir("Microcontrolador", "c01");
    fireEvent.click(screen.getByRole("button", { name: "Guardar como nueva versión" }));
    primera.unmount();
    abrirArmador();
    expect(screen.getByRole("button", { name: /Velocista 003/ })).toBeTruthy();
  });
});

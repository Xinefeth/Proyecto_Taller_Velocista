import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { ProveedorConsola } from "./stores/ConsolaContext";

beforeEach(() => {
  // El store arranca un bucle con requestAnimationFrame; en pruebas lo dejamos inerte.
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("scrollTo", () => {});
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const montar = () =>
  render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );

describe("App", () => {
  it("muestra el selector de robot y las secciones del riel", () => {
    montar();
    expect(screen.getByText("Velocista 001")).toBeTruthy();
    // Nombres únicos del riel (la nav móvil usa nombres cortos).
    for (const nombre of ["Catálogo de componentes", "Armador de robots", "Perfiles de reglamento"]) {
      expect(screen.getByRole("button", { name: nombre })).toBeTruthy();
    }
  });

  it("navega a la gestión de catálogo", () => {
    montar();
    fireEvent.click(screen.getByRole("button", { name: "Catálogo de componentes" }));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Catálogo de componentes");
    expect(screen.getByPlaceholderText("Buscar por nombre, tipo o especificación")).toBeTruthy();
  });

  it("navega al reglamento", () => {
    montar();
    fireEvent.click(screen.getByRole("button", { name: "Perfiles de reglamento" }));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Perfiles de reglamento");
  });
});

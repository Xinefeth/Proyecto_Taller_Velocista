import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { ProveedorConexion } from "./stores/ConexionContext";

class WebSocketFalso {
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  close() {}
}

beforeEach(() => {
  vi.stubGlobal("WebSocket", WebSocketFalso);
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => null }),
  );
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const montar = () =>
  render(
    <ProveedorConexion>
      <App />
    </ProveedorConexion>,
  );

describe("App", () => {
  it("muestra las siete secciones del prototipo y el estado del sistema", () => {
    montar();
    for (const nombre of [
      "Control",
      "Telemetría",
      "Corridas y optimización",
      "Mapa de pista",
      "Catálogo de componentes",
      "Armador de robots",
      "Perfiles de reglamento",
    ]) {
      expect(screen.getByRole("button", { name: nombre })).toBeTruthy();
    }
    expect(screen.getByLabelText("Estado del sistema", { selector: "div" })).toBeTruthy();
  });

  it("navega entre secciones", () => {
    montar();
    fireEvent.click(screen.getByRole("button", { name: "Catálogo de componentes" }));
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Catálogo de componentes");
    expect(screen.getByText("HU-01")).toBeTruthy();
  });
});

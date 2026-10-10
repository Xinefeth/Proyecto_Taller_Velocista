// Modal del manifiesto (HU-13): muestra un panel por dispositivo declarado y oculta los demás.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { ROBOTS as TEST_ROBOTS } from "../datos/robots";
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

const abrirManifiestoDesdeArmador = () => {
  render(
    <ProveedorConsola initialRobots={TEST_ROBOTS}>
      <App />
    </ProveedorConsola>,
  );
  // El Armador abre con el Velocista 001 (regleta, batería y motores; sin encoder/IMU/turbina).
  fireEvent.click(screen.getByRole("button", { name: "Armador de robots" }));
  fireEvent.click(screen.getByRole("button", { name: "Ver manifiesto esperado" }));
  return screen.getByRole("dialog", { name: "Manifiesto del robot" });
};

describe("ManifiestoModal · paneles por manifiesto (HU-13)", () => {
  it("actualiza los paneles al cambiar de robot", () => {
    const dialog = abrirManifiestoDesdeArmador();
    expect(within(dialog).queryByText("Encoders")).toBeNull();
    fireEvent.click(within(dialog).getByRole("button", { name: "Listo" }));
    fireEvent.click(screen.getByRole("button", { name: /Velocista 002/ }));
    fireEvent.click(screen.getByRole("button", { name: "Ver manifiesto esperado" }));
    const panels = within(
      screen.getByRole("dialog", { name: "Manifiesto del robot" }),
    ).getByLabelText("Paneles del robot");
    expect(within(panels).getByText("Encoders")).toBeTruthy();
    expect(within(panels).getByText("Turbina")).toBeTruthy();
  });
  it("muestra los paneles de los dispositivos declarados", () => {
    const paneles = within(abrirManifiestoDesdeArmador()).getByLabelText("Paneles del robot");
    expect(within(paneles).getByText("Regleta de línea")).toBeTruthy();
    expect(within(paneles).getByText("Batería")).toBeTruthy();
    expect(within(paneles).getByText("Motor izquierdo")).toBeTruthy();
    expect(within(paneles).getByText("Motor derecho")).toBeTruthy();
  });

  it("sin encoder (ni IMU ni turbina) no aparece ese panel", () => {
    const paneles = within(abrirManifiestoDesdeArmador()).getByLabelText("Paneles del robot");
    expect(within(paneles).queryByText("Encoders")).toBeNull();
    expect(within(paneles).queryByText("IMU")).toBeNull();
    expect(within(paneles).queryByText("Turbina")).toBeNull();
  });
});

import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ProveedorConsola, useConsola } from "./ConsolaContext";
import { api, ErrorApi } from "../services/api";

beforeEach(() => {
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function Selection() {
  const { robot } = useConsola();
  return (
    <p>
      {robot.nm} · {robot.tipo} · {robot.ver[0].v} · {robot.fw}
    </p>
  );
}

it("muestra carga y selecciona un robot exclusivo del backend", async () => {
  vi.spyOn(api.robots, "selection").mockResolvedValue([
    {
      id: "server",
      nm: "Robot del servidor",
      short: "S",
      tipo: "velocista",
      fw: "9.1",
      ver: [{ v: "v8", fecha: "—", nota: "", estado: "Actual", parts: {} }],
    },
  ]);
  render(
    <ProveedorConsola>
      <Selection />
    </ProveedorConsola>,
  );
  expect(screen.getByRole("status").textContent).toContain("Cargando robots");
  expect(await screen.findByText("Robot del servidor · velocista · v8 · 9.1")).toBeTruthy();
});

it("una respuesta vacía muestra el estado vacío", async () => {
  vi.spyOn(api.robots, "selection").mockResolvedValue([]);
  render(
    <ProveedorConsola>
      <Selection />
    </ProveedorConsola>,
  );
  expect(await screen.findByText("No hay robots registrados en el armador.")).toBeTruthy();
});

it("el 503 muestra error y ofrece reintentar sin robots locales", async () => {
  vi.spyOn(api.robots, "selection").mockRejectedValue(
    new ErrorApi(503, "base_no_disponible", "La base de datos no está disponible"),
  );
  render(
    <ProveedorConsola>
      <Selection />
    </ProveedorConsola>,
  );
  expect((await screen.findByRole("alert")).textContent).toContain(
    "La base de datos no está disponible",
  );
  expect(screen.getByRole("button", { name: "Reintentar" })).toBeTruthy();
  expect(screen.queryByText(/Velocista 001/)).toBeNull();
});

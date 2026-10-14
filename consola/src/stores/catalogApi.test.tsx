// EN-25 · El catálogo y el inventario de la consola salen de la API (solo lectura).
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import App from "../App";
import { CAT } from "../datos/catalogo";
import { ROBOTS as TEST_ROBOTS } from "../datos/robots";
import { api, ErrorApi } from "../services/api";
import type { ApiInventory } from "../types/api";
import { ProveedorConsola, useConsola } from "./ConsolaContext";

beforeEach(() => {
  localStorage.clear();
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("scrollTo", () => {});
  vi.spyOn(api.robots, "selection").mockResolvedValue(TEST_ROBOTS);
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

const sensor = { ...CAT.find((c) => c.id === "c05")!, nm: "Sensor del servidor", stock: 6 };
const existencia = (extra: Partial<ApiInventory> = {}): ApiInventory => ({
  componente_id: sensor.id,
  stock: 9,
  en_robots: 3,
  disponible: 6,
  faltante: 0,
  revision: 2,
  ...extra,
});

function Resumen() {
  const { catalog, apiMode, inventory } = useConsola();
  return (
    <p>
      {apiMode ? "api" : "ejemplo"} · {catalog.map((c) => `${c.nm}:${c.stock}`).join(",")} ·{" "}
      {Object.keys(inventory).length} existencias
    </p>
  );
}

it("muestra la carga y luego solo los componentes de la API, sin el catálogo local", async () => {
  vi.spyOn(api.catalog, "loadAll").mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({ [sensor.id]: existencia() });
  render(
    <ProveedorConsola>
      <Resumen />
    </ProveedorConsola>,
  );
  expect(screen.getByRole("status").textContent).toContain("Cargando");
  // El stock del inventario manda sobre el de la lista de componentes.
  expect(await screen.findByText("api · Sensor del servidor:9 · 1 existencias")).toBeTruthy();
  expect(screen.queryByText(/ESP32-S3/)).toBeNull();
});

it("si el catálogo falla muestra el error, ofrece reintentar y no usa datos de ejemplo", async () => {
  const cargar = vi
    .spyOn(api.catalog, "loadAll")
    .mockRejectedValueOnce(
      new ErrorApi(503, "base_no_disponible", "La base de datos no está disponible"),
    )
    .mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  render(
    <ProveedorConsola>
      <Resumen />
    </ProveedorConsola>,
  );
  const alerta = await screen.findByRole("alert");
  expect(alerta.textContent).toContain("No se pudo cargar el catálogo");
  expect(alerta.textContent).toContain("La base de datos no está disponible");
  expect(screen.queryByText(/Sensor del servidor/)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
  expect(screen.getByRole("status").textContent).toContain("Cargando catálogo");
  expect(await screen.findByText(/Sensor del servidor:6/)).toBeTruthy();
  expect(cargar).toHaveBeenCalledTimes(2);
});

it("sin conexión con la API muestra un mensaje claro", async () => {
  vi.spyOn(api.catalog, "loadAll").mockRejectedValue(new TypeError("fetch failed"));
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  render(
    <ProveedorConsola>
      <Resumen />
    </ProveedorConsola>,
  );
  expect((await screen.findByRole("alert")).textContent).toContain("sin conexión con la API");
});

it("una respuesta vacía del inventario conserva el stock de cada componente", async () => {
  vi.spyOn(api.catalog, "loadAll").mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  render(
    <ProveedorConsola>
      <Resumen />
    </ProveedorConsola>,
  );
  expect(await screen.findByText("api · Sensor del servidor:6 · 0 existencias")).toBeTruthy();
});

it("no guarda en el navegador el catálogo que viene de la API", async () => {
  vi.spyOn(api.catalog, "loadAll").mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  const guardar = vi.spyOn(Storage.prototype, "setItem");
  render(
    <ProveedorConsola>
      <Resumen />
    </ProveedorConsola>,
  );
  await screen.findByText(/Sensor del servidor/);
  expect(guardar.mock.calls.some(([clave]) => String(clave).includes("componentes"))).toBe(false);
});

it("el Catálogo no ofrece restablecer datos de ejemplo y el inventario usa los números del servidor", async () => {
  vi.spyOn(api.catalog, "loadAll").mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({
    [sensor.id]: existencia({ stock: 6, en_robots: 8, disponible: -2, faltante: 2 }),
  });
  render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );
  fireEvent.click(await screen.findByRole("button", { name: "Catálogo de componentes" }));
  expect(screen.queryByRole("button", { name: "Restablecer datos de ejemplo" })).toBeNull();
  const inventario = screen.getByRole("table", { name: "Inventario del club", hidden: true });
  const fila = within(inventario).getByText("Sensor del servidor").closest("tr")!;
  expect(within(fila).getByText("Faltan 2")).toBeTruthy();
  expect(within(fila).getByText("8")).toBeTruthy();
  expect(within(fila).getByText("-2")).toBeTruthy();
});

it("el Armador no falla si una pieza de la versión ya no está en el catálogo (por ejemplo, archivada)", async () => {
  const robot = structuredClone(TEST_ROBOTS[0]!);
  const version = robot.ver[robot.ver.length - 1]!;
  version.parts.linea = { id: "archivada-1", q: 2 };
  vi.spyOn(api.robots, "selection").mockResolvedValue([robot]);
  vi.spyOn(api.catalog, "loadAll").mockResolvedValue(CAT.filter((c) => c.t !== "linea"));
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );
  fireEvent.click(await screen.findByRole("button", { name: "Armador de robots" }));
  expect(screen.getByRole("heading", { name: "Resumen" })).toBeTruthy();
});

function Actions() {
  const { addComponent, archiveComponent, catalog } = useConsola();
  return (
    <>
      <p>{catalog.map((c) => c.nm).join(",") || "vacío"}</p>
      <button
        type="button"
        onClick={() =>
          void addComponent({
            t: "linea",
            nm: "Nuevo",
            precio: 10,
            masa: 5,
            tienda: "X",
            stock: 2,
            s: { i: 0.1 },
          })
        }
      >
        guardar
      </button>
      <button type="button" onClick={() => void archiveComponent(sensor.id)}>
        archivar
      </button>
    </>
  );
}

it("guardar un componente lo envía a la API y vuelve a pedir el catálogo", async () => {
  const loadAll = vi
    .spyOn(api.catalog, "loadAll")
    .mockResolvedValueOnce([])
    .mockResolvedValue([sensor]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  const create = vi.spyOn(api.catalog, "create").mockResolvedValue({} as never);
  render(
    <ProveedorConsola>
      <Actions />
    </ProveedorConsola>,
  );
  await screen.findByText("vacío");
  fireEvent.click(screen.getByText("guardar"));
  expect(await screen.findByText("Sensor del servidor")).toBeTruthy();
  expect(create).toHaveBeenCalledTimes(1);
  expect(loadAll).toHaveBeenCalledTimes(2);
});

it("archivar un componente llama a la API y lo quita de la lista", async () => {
  vi.spyOn(api.catalog, "loadAll").mockResolvedValueOnce([sensor]).mockResolvedValue([]);
  vi.spyOn(api.catalog, "loadInventory").mockResolvedValue({});
  const archive = vi.spyOn(api.catalog, "archive").mockResolvedValue(null);
  render(
    <ProveedorConsola>
      <Actions />
    </ProveedorConsola>,
  );
  await screen.findByText("Sensor del servidor");
  fireEvent.click(screen.getByText("archivar"));
  expect(await screen.findByText("vacío")).toBeTruthy();
  expect(archive).toHaveBeenCalledWith(sensor.id);
});

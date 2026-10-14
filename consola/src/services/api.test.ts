import { afterEach, describe, expect, it, vi } from "vitest";
import { aErrorApi, api, mapApiComponent, toApiComponentCreate } from "./api";
import type { ApiComponent, ApiInventory } from "../types/api";

afterEach(() => vi.unstubAllGlobals());

const apiComponent = (id: string, extra: Partial<ApiComponent> = {}): ApiComponent => ({
  id,
  tipo_id: "linea",
  nombre: `Pieza ${id}`,
  precio: 62,
  masa_g: 3,
  tienda: "Importación",
  consumo_a: 0.1,
  especificaciones: { canales: 8, salida: "Analógica" },
  stock: 4,
  archivado: false,
  ...extra,
});
const apiInventory = (id: string, extra: Partial<ApiInventory> = {}): ApiInventory => ({
  componente_id: id,
  stock: 4,
  en_robots: 2,
  disponible: 2,
  faltante: 0,
  revision: 1,
  ...extra,
});
const respuesta = (body: unknown, status = 200) => ({
  ok: status < 400,
  status,
  json: async () => body,
});

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

describe("EN-25 · catálogo desde la API", () => {
  it("traduce los campos de la API al tipo de la consola", () => {
    expect(mapApiComponent(apiComponent("c05"))).toEqual({
      id: "c05",
      t: "linea",
      nm: "Pieza c05",
      precio: 62,
      masa: 3,
      tienda: "Importación",
      stock: 4,
      i: 0.1,
      s: { canales: 8, salida: "Analógica" },
    });
  });

  it("deja el consumo sin definir cuando la API manda null", () => {
    const c = mapApiComponent(apiComponent("c19", { consumo_a: null }));
    expect(c.i).toBeUndefined();
    expect("i" in c).toBe(false);
  });

  it("no modifica el objeto de la API y devuelve lo mismo al repetir", () => {
    const entrada = apiComponent("c01");
    const copia = structuredClone(entrada);
    expect(mapApiComponent(entrada)).toEqual(mapApiComponent(entrada));
    expect(entrada).toEqual(copia);
  });

  it("pide páginas de 200 hasta cubrir el total", async () => {
    const todos = Array.from({ length: 201 }, (_, n) => apiComponent(`c${n}`));
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(
        respuesta({ items: todos.slice(0, 200), total: 201, limite: 200, offset: 0 }),
      )
      .mockResolvedValueOnce(
        respuesta({ items: todos.slice(200), total: 201, limite: 200, offset: 200 }),
      );
    vi.stubGlobal("fetch", fetch);
    const catalogo = await api.catalog.loadAll();
    expect(catalogo).toHaveLength(201);
    expect(fetch.mock.calls.map((llamada) => llamada[0])).toEqual([
      "/api/components?limit=200&offset=0",
      "/api/components?limit=200&offset=200",
    ]);
  });

  it("omite los componentes de un tipo que la consola no conoce", async () => {
    const aviso = vi.spyOn(console, "warn").mockImplementation(() => {});
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        respuesta({
          items: [apiComponent("c01"), apiComponent("x99", { tipo_id: "raro" })],
          total: 2,
          limite: 200,
          offset: 0,
        }),
      ),
    );
    const catalogo = await api.catalog.loadAll();
    expect(catalogo.map((c) => c.id)).toEqual(["c01"]);
    expect(aviso).toHaveBeenCalled();
    aviso.mockRestore();
  });

  it("indexa el inventario por componente y recorre todas sus páginas", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(
        respuesta({
          items: Array.from({ length: 200 }, (_, n) => apiInventory(`c${n}`)),
          total: 201,
          limite: 200,
          offset: 0,
        }),
      )
      .mockResolvedValueOnce(
        respuesta({
          items: [apiInventory("c200", { en_robots: 5 })],
          total: 201,
          limite: 200,
          offset: 200,
        }),
      );
    vi.stubGlobal("fetch", fetch);
    const inventario = await api.catalog.loadInventory();
    expect(Object.keys(inventario)).toHaveLength(201);
    expect(inventario.c200?.en_robots).toBe(5);
    expect(fetch.mock.calls[1]?.[0]).toBe("/api/inventory?limit=200&offset=200");
  });

  it("propaga el error estándar de la API", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          respuesta({ detail: { motivo: "base_no_disponible", detalle: "Sin base" } }, 503),
        ),
    );
    await expect(api.catalog.loadAll()).rejects.toMatchObject({
      status: 503,
      motivo: "base_no_disponible",
    });
  });
});

describe("EN-25 · guardar y archivar componentes", () => {
  afterEach(() => vi.restoreAllMocks());

  it("traduce un componente nuevo al cuerpo de la API", () => {
    expect(
      toApiComponentCreate({
        t: "linea",
        nm: "QTR",
        precio: 10,
        masa: 3,
        tienda: "T",
        stock: 2,
        s: { i: 0.1 },
      }),
    ).toEqual({
      tipo_id: "linea",
      nombre: "QTR",
      precio: 10,
      masa_g: 3,
      tienda: "T",
      consumo_a: 0.1,
      especificaciones: { i: 0.1 },
      stock: 2,
    });
    expect(
      toApiComponentCreate({
        t: "chasis",
        nm: "C",
        precio: 1,
        masa: 1,
        tienda: "",
        stock: 0,
        s: {},
      }).consumo_a,
    ).toBeNull();
  });

  it("create usa POST /components y archive usa DELETE", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(respuesta({}))
      .mockResolvedValueOnce({ ok: true, status: 204, json: async () => null });
    vi.stubGlobal("fetch", fetchMock);
    await api.catalog.create({
      t: "chasis",
      nm: "C",
      precio: 1,
      masa: 1,
      tienda: "",
      stock: 0,
      s: {},
    });
    await api.catalog.archive("c_1");
    expect(fetchMock.mock.calls[0][0]).toBe("/api/components");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(fetchMock.mock.calls[1][0]).toBe("/api/components/c_1");
    expect(fetchMock.mock.calls[1][1].method).toBe("DELETE");
    vi.unstubAllGlobals();
  });
});

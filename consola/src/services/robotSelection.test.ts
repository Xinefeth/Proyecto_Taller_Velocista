import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(() => vi.unstubAllGlobals());

const robot = (id: string, version: number | null = 7) => ({
  id,
  nombre: `Robot ${id}`,
  codigo_corto: id,
  tipo: "velocista",
  firmware: "2.0.1",
  version_actual_id: version,
  archivado: false,
});
const respond = (body: unknown, status = 200) => ({
  ok: status < 400,
  status,
  json: async () => body,
});

describe("HU-13 · selección desde la API", () => {
  it("incluye robots exclusivos de la API con la etiqueta y piezas de su versión actual", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(respond({ items: [robot("nuevo")], total: 1 }))
      .mockResolvedValueOnce(
        respond({
          etiqueta: "v3",
          fecha: "2026-10-10",
          nota: "Real",
          estado: "Actual",
          piezas: { enc: { componente_id: "c22", cantidad: 2 } },
        }),
      );
    vi.stubGlobal("fetch", fetch);
    const [record] = await api.robots.selection();
    expect(record).toMatchObject({
      id: "nuevo",
      nm: "Robot nuevo",
      tipo: "velocista",
      fw: "2.0.1",
    });
    expect(record.ver[0]).toMatchObject({ v: "v3", parts: { enc: { id: "c22", q: 2 } } });
    expect(fetch.mock.calls[1][0]).toBe("/api/robots/nuevo/versions/7");
  });

  it("carga las páginas restantes y no inventa versiones cuando el puntero es null", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(respond({ items: [robot("uno", null)], total: 2 }))
      .mockResolvedValueOnce(respond({ items: [robot("dos", null)], total: 2 }));
    vi.stubGlobal("fetch", fetch);
    const records = await api.robots.selection();
    expect(records.map((record) => record.id)).toEqual(["uno", "dos"]);
    expect(records[0].ver[0]).toMatchObject({ v: "Sin versión", parts: {} });
    expect(fetch.mock.calls[1][0]).toBe("/api/robots?limite=200&offset=1");
  });

  it("una lista vacía no se sustituye por robots locales", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(respond({ items: [], total: 0 })));
    expect(await api.robots.selection()).toEqual([]);
  });

  it("propaga el 503 con el mensaje en español", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        respond(
          {
            detail: {
              motivo: "base_no_disponible",
              detalle: "La base de datos no está disponible",
            },
          },
          503,
        ),
      ),
    );
    await expect(api.robots.selection()).rejects.toThrow("La base de datos no está disponible");
  });
});

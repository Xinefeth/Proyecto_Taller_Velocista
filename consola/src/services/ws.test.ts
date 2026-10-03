import { describe, expect, it } from "vitest";
import { urlConsola } from "./ws";

describe("urlConsola", () => {
  it("usa ws en http y wss en https, en el mismo origen", () => {
    expect(urlConsola({ protocol: "http:", host: "192.168.50.10:8000" })).toBe(
      "ws://192.168.50.10:8000/ws/consola",
    );
    expect(urlConsola({ protocol: "https:", host: "lab.local" })).toBe(
      "wss://lab.local/ws/consola",
    );
  });
});

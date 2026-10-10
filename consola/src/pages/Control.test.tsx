// HU-16 · "Detener siempre está disponible": el botón ARRANCAR/DETENER nunca queda
// deshabilitado, en ningún estado del robot (sin calibrar, calibrando, calibrado,
// corriendo y corriendo sin enlace).
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../App";
import { ROBOTS as TEST_ROBOTS } from "../datos/robots";
import { ProveedorConsola } from "../stores/ConsolaContext";
import { api } from "../services/api";

// Cola de requestAnimationFrame bajo nuestro control: el bucle del store se reagenda solo,
// así que no podemos dejar rAF síncrono y recursivo (desbordaría la pila). Guardamos las
// callbacks y las disparamos a mano con un timestamp elegido.
let rafQueue: FrameRequestCallback[] = [];
beforeEach(() => {
  rafQueue = [];
  vi.stubGlobal("requestAnimationFrame", (cb: FrameRequestCallback) => rafQueue.push(cb));
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("scrollTo", () => {});
  // Arrancar en modo simulado crea la corrida por la API; aquí la dejamos pendiente para
  // no tocar la red ni provocar setState tardíos tras terminar la prueba.
  vi.spyOn(api.corridas, "crearSimulada").mockReturnValue(new Promise(() => {}));
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

// Avanza un frame de animación; envuelto en act por los setState que dispara.
const frame = (t: number) =>
  act(() => {
    const batch = rafQueue;
    rafQueue = [];
    batch.forEach((cb) => cb(t));
  });

const montar = () =>
  render(
    <ProveedorConsola initialRobots={TEST_ROBOTS}>
      <App />
    </ProveedorConsola>,
  );

const boton = (name: string | RegExp) => screen.getByRole("button", { name });
// Botón principal de la tarjeta Salida, sea ARRANCAR o DETENER.
const botonAccion = () => boton(/^(ARRANCAR|DETENER)$/);

// Calibra (la calibración dura 1.8 s; un frame muy posterior la completa de una vez) y arranca.
const ponerEnMarcha = () => {
  fireEvent.click(boton("Calibrar"));
  frame(performance.now() + 5000);
  fireEvent.click(boton("ARRANCAR"));
};

describe("HU-16 · Detener siempre está disponible", () => {
  it("calibrado: el botón de acción sigue habilitado antes de arrancar", () => {
    montar();
    fireEvent.click(boton("Calibrar"));
    frame(performance.now() + 5000);
    expect(boton("Recalibrar")).toBeTruthy();
    expect((botonAccion() as HTMLButtonElement).disabled).toBe(false);
  });

  it("sin enlace y sin correr: el botón de acción sigue habilitado", () => {
    montar();
    fireEvent.click(screen.getByTitle("Toca para simular una caída del enlace"));
    expect(botonAccion().textContent).toContain("ARRANCAR");
    expect((botonAccion() as HTMLButtonElement).disabled).toBe(false);
  });

  it("el botón de acción nunca está deshabilitado: sin calibrar y calibrando", () => {
    montar();
    // Sin calibrar: muestra ARRANCAR y está habilitado.
    expect(botonAccion().textContent).toContain("ARRANCAR");
    expect((botonAccion() as HTMLButtonElement).disabled).toBe(false);
    // Calibrando: sigue habilitado.
    fireEvent.click(boton("Calibrar"));
    expect((botonAccion() as HTMLButtonElement).disabled).toBe(false);
  });

  it("corriendo: el botón pasa a DETENER, queda habilitado y detiene al pulsarlo", () => {
    montar();
    ponerEnMarcha();
    const detener = boton("DETENER");
    expect((detener as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(detener);
    // Tras detener vuelve a ARRANCAR (el robot ya no corre).
    expect(botonAccion().textContent).toContain("ARRANCAR");
  });

  it("corriendo sin enlace (competencia): DETENER sigue disponible y detiene", () => {
    montar();
    fireEvent.click(boton("Competencia"));
    ponerEnMarcha();
    // Se cae el enlace; en competencia el robot sigue corriendo por su cuenta.
    fireEvent.click(screen.getByTitle("Toca para simular una caída del enlace"));
    const detener = boton("DETENER");
    expect((detener as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(detener);
    expect(botonAccion().textContent).toContain("ARRANCAR");
  });
});

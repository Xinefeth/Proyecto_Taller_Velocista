// Catálogo e inventario (HU-01 a HU-04), con los datos de ejemplo de la consola.
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
  vi.restoreAllMocks();
});

const montar = () =>
  render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );

const abrirCatalogo = () => {
  const vista = montar();
  fireEvent.click(screen.getByRole("button", { name: "Catálogo de componentes" }));
  return vista;
};

// La fila de la tabla de componentes (la del inventario está oculta y repite los nombres).
const fila = (nombre: string) =>
  within(screen.getByRole("table", { name: "Componentes del catálogo" }))
    .getByText(nombre)
    .closest("tr")!;

function registrar(nombre: string) {
  fireEvent.click(screen.getByRole("button", { name: "Registrar componente" }));
  const modal = within(screen.getByRole("dialog", { name: "Registrar componente" }));
  fireEvent.change(modal.getByLabelText("Nombre"), { target: { value: nombre } });
  fireEvent.change(modal.getByLabelText("Precio (S/)"), { target: { value: "18,50" } });
  fireEvent.change(modal.getByLabelText("Masa (g)"), { target: { value: "2" } });
  fireEvent.click(modal.getByRole("button", { name: "Guardar en el catálogo" }));
}

describe("HU-01 · listar, buscar y filtrar", () => {
  it("cada fila muestra las especificaciones clave y el precio", () => {
    abrirCatalogo();
    const f = within(fila("Pololu QTR-8A"));
    expect(f.getByText("8 canales · Analógica · paso 9.525 mm")).toBeTruthy();
    expect(f.getByText("S/ 62.00")).toBeTruthy();
    expect(f.getByText("3 g")).toBeTruthy();
  });

  it("busca por nombre y filtra por tipo", () => {
    abrirCatalogo();
    fireEvent.change(screen.getByLabelText("Buscar componentes"), { target: { value: "qtr" } });
    expect(screen.getByText(/2 de 25 componentes/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Buscar componentes"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /^Motor/ }));
    expect(screen.getByText(/3 de 25 componentes/)).toBeTruthy();
  });
});

describe("HU-03 · ficha del componente", () => {
  it("muestra specs, precio, tienda y en qué robots se usa", () => {
    abrirCatalogo();
    fireEvent.click(fila("Pololu QTR-8A"));
    const ficha = within(screen.getByLabelText("Ficha del componente"));
    expect(ficha.getByText("Pololu QTR-8A")).toBeTruthy();
    expect(ficha.getByText("S/ 62.00")).toBeTruthy();
    expect(ficha.getByText("Importación")).toBeTruthy();
    expect(ficha.getByText("Canales")).toBeTruthy();
    expect(ficha.getByText("Velocista 001")).toBeTruthy();
    expect(ficha.getByText("Velocista 002")).toBeTruthy();
    expect(ficha.getAllByText("×2")).toHaveLength(2);
  });

  it("dice cuando ningún robot usa el componente", () => {
    abrirCatalogo();
    fireEvent.click(fila("Raspberry Pi Pico"));
    expect(
      within(screen.getByLabelText("Ficha del componente")).getByText(
        "Ningún robot lo usa todavía.",
      ),
    ).toBeTruthy();
  });
});

describe("HU-04 · inventario del club", () => {
  it("muestra cantidades disponibles y usadas por robot, y avisa lo que falta", () => {
    abrirCatalogo();
    fireEvent.click(screen.getByRole("tab", { name: "Inventario del club" }));
    const tabla = within(screen.getByRole("table", { name: "Inventario del club" }));
    // La QTR-8A: 3 en el club y 4 en robots (2 + 2).
    const qtr = within(tabla.getByText("Pololu QTR-8A").closest("tr")!);
    expect(qtr.getByText("Faltan 1")).toBeTruthy();
    expect(qtr.getByText("Velocista 001 ×2, Velocista 002 ×2")).toBeTruthy();
    // La Raspberry Pi Pico: 1 en el club y ninguna en robots.
    expect(
      within(tabla.getByText("Raspberry Pi Pico").closest("tr")!).getByText("Disponible"),
    ).toBeTruthy();
  });
});

describe("HU-02 · registro manual", () => {
  it("no deja registrar dos veces el mismo componente", () => {
    abrirCatalogo();
    registrar("Sensor QTR-3A");
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
    registrar("sensor qtr-3a"); // mismo nombre, otra escritura, mismo tipo
    const modal = within(screen.getByRole("dialog", { name: "Registrar componente" }));
    expect(modal.getAllByRole("alert").map((a) => a.textContent)).toContain(
      "Ya existe un componente con ese nombre en este tipo.",
    );
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
  });

  it("asigna un id nuevo que no se repite", () => {
    abrirCatalogo();
    registrar("Sensor A");
    registrar("Sensor B");
    expect(within(fila("Sensor A")).getByText("C26")).toBeTruthy();
    expect(within(fila("Sensor B")).getByText("C27")).toBeTruthy();
  });

  it("conserva lo registrado aunque se recargue la consola", () => {
    const primera = abrirCatalogo();
    registrar("Sensor guardado");
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
    primera.unmount();
    abrirCatalogo(); // como recargar la página
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
    expect(fila("Sensor guardado")).toBeTruthy();
  });

  it("restablece los datos de ejemplo si se confirma, y no hace nada si se cancela", () => {
    abrirCatalogo();
    registrar("Sensor temporal");
    const confirmar = vi.spyOn(window, "confirm").mockReturnValue(false);
    fireEvent.click(screen.getByRole("button", { name: "Restablecer datos de ejemplo" }));
    expect(confirmar).toHaveBeenCalled();
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
    confirmar.mockReturnValue(true);
    fireEvent.click(screen.getByRole("button", { name: "Restablecer datos de ejemplo" }));
    expect(screen.getByText(/25 de 25 componentes/)).toBeTruthy();
    expect(screen.queryAllByText("Sensor temporal")).toHaveLength(0);
  });
});

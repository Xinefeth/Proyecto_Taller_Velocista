// Registro manual de un componente (HU-02) y búsqueda en el catálogo (HU-01), de punta a punta.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "../../App";
import { ProveedorConsola } from "../../stores/ConsolaContext";

beforeEach(() => {
  vi.stubGlobal("requestAnimationFrame", () => 0);
  vi.stubGlobal("cancelAnimationFrame", () => {});
  vi.stubGlobal("scrollTo", () => {});
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const abrirCatalogo = () => {
  render(
    <ProveedorConsola>
      <App />
    </ProveedorConsola>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Catálogo de componentes" }));
};

describe("Catálogo", () => {
  it("busca sin distinguir tildes y filtra por tipo", () => {
    abrirCatalogo();
    expect(screen.getByText(/25 de 25 componentes/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Buscar componentes"), { target: { value: "bateria" } });
    expect(screen.getByText(/2 de 25 componentes/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Buscar componentes"), { target: { value: "zzzz" } });
    expect(screen.getByText("Nada coincide con “zzzz”.")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Buscar componentes"), { target: { value: "" } });
    fireEvent.click(screen.getByRole("button", { name: /^Driver/ }));
    expect(screen.getByText(/2 de 25 componentes/)).toBeTruthy();
  });

  it("muestra el inventario con la misma tabla", () => {
    abrirCatalogo();
    fireEvent.click(screen.getByRole("tab", { name: "Inventario del club" }));
    expect(screen.getByRole("table", { name: "Inventario del club" })).toBeTruthy();
  });
});

describe("Registrar componente a mano (HU-02)", () => {
  it("valida lo obligatorio, cambia los campos según el tipo y guarda", () => {
    abrirCatalogo();
    fireEvent.click(screen.getByRole("button", { name: "Registrar componente" }));
    const dialogo = screen.getByRole("dialog", { name: "Registrar componente" });
    const modal = within(dialogo);

    // Sensor de línea (tipo inicial): campos de especificaciones propios.
    expect(modal.getByLabelText("Canales")).toBeTruthy();

    // Sin datos: avisa lo que falta, igual que el prototipo.
    fireEvent.click(modal.getByRole("button", { name: "Guardar en el catálogo" }));
    const alertas = modal.getAllByRole("alert").map((a) => a.textContent);
    expect(alertas).toContain("Escribe el nombre del componente.");
    expect(alertas).toContain("El precio debe ser mayor que 0.");
    expect(alertas).toContain("Escribe la masa en gramos.");
    expect(modal.getByRole("status").textContent).toContain("Revisa los campos marcados");

    // Cambiar a Encoder: aparecen sus campos y desaparecen los del sensor.
    fireEvent.change(modal.getByRole("combobox"), { target: { value: "enc" } });
    expect(modal.getByLabelText("Pulsos por vuelta (CPR)")).toBeTruthy();
    expect(modal.queryByLabelText("Canales")).toBeNull();

    // Una cifra de especificación con letras no se acepta.
    fireEvent.change(modal.getByLabelText("Nombre"), {
      target: { value: "Encoder óptico de prueba" },
    });
    fireEvent.change(modal.getByLabelText("Precio (S/)"), { target: { value: "30,5" } });
    fireEvent.change(modal.getByLabelText("Masa (g)"), { target: { value: "4" } });
    fireEvent.change(modal.getByLabelText("Pulsos por vuelta (CPR)"), {
      target: { value: "veinte" },
    });
    fireEvent.click(modal.getByRole("button", { name: "Guardar en el catálogo" }));
    expect(modal.getAllByRole("alert").map((a) => a.textContent)).toContain(
      "Escribe un número válido.",
    );

    // Corregida la cifra, se guarda y el componente aparece en el catálogo.
    fireEvent.change(modal.getByLabelText("Pulsos por vuelta (CPR)"), { target: { value: "20" } });
    fireEvent.click(modal.getByRole("button", { name: "Guardar en el catálogo" }));
    // Cerrado, el modal queda oculto (aria-hidden) y ya no se encuentra por rol.
    expect(screen.queryByRole("dialog", { name: "Registrar componente" })).toBeNull();
    expect(screen.getByText(/26 de 26 componentes/)).toBeTruthy();
    expect(screen.getAllByText("Encoder óptico de prueba").length).toBeGreaterThan(0);
    expect(screen.getByText("S/ 30.50")).toBeTruthy();
  });
});

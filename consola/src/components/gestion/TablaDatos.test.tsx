import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { TablaDatos, type Columna } from "./TablaDatos";

interface Fila {
  id: string;
  nombre: string;
  precio: number;
}
const columnas: Columna<Fila>[] = [
  { id: "nombre", encabezado: "Componente", clase: "nm", celda: (f) => f.nombre },
  { id: "precio", encabezado: "Precio", clase: "m", derecha: true, celda: (f) => `S/ ${f.precio}` },
];
const filas: Fila[] = [
  { id: "a", nombre: "QTR-8A", precio: 62 },
  { id: "b", nombre: "TB6612FNG", precio: 16 },
];

afterEach(cleanup);

describe("TablaDatos", () => {
  it("dibuja encabezados, filas y las clases del prototipo", () => {
    render(
      <TablaDatos etiqueta="Componentes" columnas={columnas} filas={filas} clave={(f) => f.id} />,
    );
    expect(screen.getByRole("table", { name: "Componentes" }).className).toBe("ct");
    expect(screen.getByRole("columnheader", { name: "Precio" }).className).toBe("r");
    expect(screen.getByText("QTR-8A").className).toBe("nm");
    expect(screen.getByText("S/ 16").className).toBe("m r");
    expect(screen.getAllByRole("row")).toHaveLength(3);
  });

  it("muestra el mensaje cuando no hay filas", () => {
    render(
      <TablaDatos
        etiqueta="Vacía"
        columnas={columnas}
        filas={[]}
        clave={(f: Fila) => f.id}
        vacio="Sin resultados"
      />,
    );
    const celda = screen.getByText("Sin resultados");
    expect(celda.getAttribute("colspan")).toBe("2");
    expect(celda.className).toBe("empty");
  });

  it("las filas clicables responden al clic, a Enter y a Espacio", () => {
    const alHacerClic = vi.fn();
    render(
      <TablaDatos
        etiqueta="Clicable"
        columnas={columnas}
        filas={filas}
        clave={(f) => f.id}
        alHacerClic={alHacerClic}
      />,
    );
    const fila = screen.getByText("QTR-8A").closest("tr")!;
    expect(fila.getAttribute("tabindex")).toBe("0");
    fireEvent.click(fila);
    fireEvent.keyDown(fila, { key: "Enter" });
    fireEvent.keyDown(fila, { key: " " });
    fireEvent.keyDown(fila, { key: "a" });
    expect(alHacerClic).toHaveBeenCalledTimes(3);
    expect(alHacerClic).toHaveBeenLastCalledWith(filas[0]);
  });

  it("sin alHacerClic las filas no son enfocables", () => {
    render(<TablaDatos etiqueta="Fija" columnas={columnas} filas={filas} clave={(f) => f.id} />);
    expect(screen.getByText("QTR-8A").closest("tr")!.hasAttribute("tabindex")).toBe(false);
  });
});

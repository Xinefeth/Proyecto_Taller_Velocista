import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Buscador } from "./Buscador";
import { ChipsFiltro } from "./ChipsFiltro";
import { Pestanas } from "./Pestanas";
import { normalizar, useFiltroLista } from "./useFiltroLista";

interface Pieza {
  nombre: string;
  tipo: string;
}
const piezas: Pieza[] = [
  { nombre: "Batería LiPo 2S", tipo: "bat" },
  { nombre: "Pololu QTR-8A", tipo: "linea" },
  { nombre: "Pololu QTR-8RC", tipo: "linea" },
  { nombre: "Módulo TCRT5000", tipo: "linea" },
];
const texto = (p: Pieza) => p.nombre;
const categoria = (p: Pieza) => p.tipo;

afterEach(cleanup);

describe("useFiltroLista", () => {
  it("normaliza tildes y mayúsculas", () => {
    expect(normalizar("  Batería ")).toBe("bateria");
  });

  it("busca sin distinguir tildes ni mayúsculas", () => {
    const { result } = renderHook(() => useFiltroLista(piezas, { texto, categoria }));
    act(() => result.current.setConsulta("BATERIA"));
    expect(result.current.filtradas.map((p) => p.nombre)).toEqual(["Batería LiPo 2S"]);
  });

  it("filtra por categoría y los conteos salen de la lista completa", () => {
    const { result } = renderHook(() => useFiltroLista(piezas, { texto, categoria }));
    expect(result.current.conteos).toEqual({ bat: 1, linea: 3 });
    act(() => result.current.setCategoria("linea"));
    expect(result.current.filtradas).toHaveLength(3);
    act(() => result.current.setConsulta("rc"));
    expect(result.current.filtradas.map((p) => p.nombre)).toEqual(["Pololu QTR-8RC"]);
    expect(result.current.conteos).toEqual({ bat: 1, linea: 3 });
    act(() => result.current.setCategoria(null));
    expect(result.current.filtradas).toHaveLength(1);
  });
});

describe("ChipsFiltro", () => {
  const opciones = [
    { valor: "bat", etiqueta: "Batería", cantidad: 1 },
    { valor: "linea", etiqueta: "Sensor de línea", cantidad: 3 },
  ];

  it("marca Todos cuando no hay filtro y muestra las cantidades", () => {
    render(
      <ChipsFiltro
        etiqueta="Tipo"
        opciones={opciones}
        valor={null}
        alCambiar={() => undefined}
        cantidadTodos={4}
      />,
    );
    expect(screen.getByRole("button", { name: /Todos/ }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByRole("button", { name: /Sensor de línea/ }).textContent).toContain("3");
  });

  it("elige una opción y Todos vuelve a mostrar todo", () => {
    const alCambiar = vi.fn();
    render(<ChipsFiltro etiqueta="Tipo" opciones={opciones} valor="bat" alCambiar={alCambiar} />);
    expect(screen.getByRole("button", { name: /Batería/ }).getAttribute("aria-pressed")).toBe(
      "true",
    );
    fireEvent.click(screen.getByRole("button", { name: /Sensor de línea/ }));
    expect(alCambiar).toHaveBeenLastCalledWith("linea");
    fireEvent.click(screen.getByRole("button", { name: /Todos/ }));
    expect(alCambiar).toHaveBeenLastCalledWith(null);
  });
});

describe("Buscador", () => {
  it("avisa cada cambio del texto", () => {
    const alCambiar = vi.fn();
    render(<Buscador valor="" alCambiar={alCambiar} etiqueta="Buscar piezas" marcador="Buscar…" />);
    fireEvent.change(screen.getByLabelText("Buscar piezas"), { target: { value: "qtr" } });
    expect(alCambiar).toHaveBeenCalledWith("qtr");
  });
});

describe("Pestanas", () => {
  const pestanas = [
    { id: "a", etiqueta: "Componentes" },
    { id: "b", etiqueta: "Inventario" },
  ];

  it("marca la activa y cambia con las flechas del teclado", () => {
    const alCambiar = vi.fn();
    render(<Pestanas etiqueta="Secciones" pestanas={pestanas} activa="a" alCambiar={alCambiar} />);
    const primera = screen.getByRole("tab", { name: "Componentes" });
    expect(primera.getAttribute("aria-selected")).toBe("true");
    expect(screen.getByRole("tab", { name: "Inventario" }).getAttribute("tabindex")).toBe("-1");
    fireEvent.keyDown(primera, { key: "ArrowRight" });
    expect(alCambiar).toHaveBeenLastCalledWith("b");
    fireEvent.keyDown(primera, { key: "End" });
    expect(alCambiar).toHaveBeenLastCalledWith("b");
  });
});

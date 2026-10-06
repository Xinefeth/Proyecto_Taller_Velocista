import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { FormularioDinamico } from "./FormularioDinamico";
import { parsearNumero, validarCampos, type DefCampo, type Valores } from "./validacion";

const campos: DefCampo[] = [
  { nombre: "nombre", etiqueta: "Nombre", tipo: "texto", requerido: true },
  {
    nombre: "precio",
    etiqueta: "Precio (S/)",
    tipo: "numero",
    requerido: true,
    minExclusivo: 0,
    mensajes: { minimo: "El precio debe ser mayor que 0." },
  },
  { nombre: "club", etiqueta: "En el club", tipo: "numero", entero: true, min: 0, max: 100 },
  {
    nombre: "tipo",
    etiqueta: "Tipo",
    tipo: "seleccion",
    opciones: [{ valor: "a", etiqueta: "A" }],
  },
];

afterEach(cleanup);

describe("validarCampos", () => {
  it("exige los campos obligatorios", () => {
    expect(validarCampos(campos, {})).toEqual({
      nombre: "Este campo es obligatorio.",
      precio: "Este campo es obligatorio.",
    });
  });

  it("acepta coma o punto decimal y revisa rangos y enteros", () => {
    expect(parsearNumero("0,35")).toBe(0.35);
    expect(parsearNumero("abc")).toBeNull();
    const e = validarCampos(campos, { nombre: "x", precio: "0", club: "2,5" });
    expect(e.precio).toBe("El precio debe ser mayor que 0.");
    expect(e.club).toBe("Debe ser un número entero.");
    expect(validarCampos(campos, { nombre: "x", precio: "12,5", club: "101" }).club).toBe(
      "Debe ser menor o igual a 100.",
    );
    expect(validarCampos(campos, { nombre: "x", precio: "doce" }).precio).toBe(
      "Escribe un número válido.",
    );
    expect(validarCampos(campos, { nombre: "x", precio: "1", club: "-1" }).club).toBe(
      "Debe ser mayor o igual a 0.",
    );
  });

  it("deja pasar un campo opcional vacío y rechaza una opción que no está en la lista", () => {
    expect(validarCampos(campos, { nombre: "x", precio: "1", club: "" })).toEqual({});
    expect(validarCampos(campos, { nombre: "x", precio: "1", tipo: "zzz" }).tipo).toBe(
      "Elige una opción de la lista.",
    );
  });
});

describe("FormularioDinamico", () => {
  function Prueba() {
    const [valores, setValores] = useState<Valores>({});
    return (
      <FormularioDinamico
        campos={campos}
        valores={valores}
        errores={validarCampos(campos, valores)}
        alCambiar={(n, v) => setValores((x) => ({ ...x, [n]: v }))}
      />
    );
  }

  it("enlaza etiqueta, error y campo, y usa teclado decimal en las cifras", () => {
    render(<Prueba />);
    const precio = screen.getByLabelText("Precio (S/)");
    expect(precio.getAttribute("inputmode")).toBe("decimal");
    expect(precio.className).toBe("inp m");
    fireEvent.change(precio, { target: { value: "abc" } });
    expect(precio.getAttribute("aria-invalid")).toBe("true");
    const alertas = screen.getAllByRole("alert").map((a) => a.textContent);
    expect(alertas).toContain("Escribe un número válido.");
    expect(precio.getAttribute("aria-describedby")).toBeTruthy();
    fireEvent.change(precio, { target: { value: "12,5" } });
    expect(precio.hasAttribute("aria-invalid")).toBe(false);
  });
});

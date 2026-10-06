// Dibuja campos a partir de su descripción (DefCampo). Sirve para el registro de componentes (HU-02),
// donde los campos cambian según el tipo. No guarda estado: quien lo usa controla valores y errores.
import { Fragment } from "react";
import { CampoEntrada, CampoSelector } from "./Campo";
import type { DefCampo, Errores, Valores } from "./validacion";

export interface FormularioDinamicoProps {
  campos: readonly DefCampo[];
  valores: Valores;
  errores?: Errores;
  alCambiar: (nombre: string, valor: string) => void;
  /** Con 2 o 3 columnas usa las grillas .g2 y .g3 del prototipo; con 1 no agrega contenedor. */
  columnas?: 1 | 2 | 3;
}

export function FormularioDinamico({
  campos,
  valores,
  errores = {},
  alCambiar,
  columnas = 2,
}: FormularioDinamicoProps) {
  const Contenedor = columnas === 1 ? Fragment : "div";
  const props = columnas === 1 ? {} : { className: `g${columnas}` };
  return (
    <Contenedor {...props}>
      {campos.map((c) =>
        c.tipo === "seleccion" ? (
          <CampoSelector
            key={c.nombre}
            etiqueta={c.etiqueta}
            opciones={c.opciones ?? []}
            value={valores[c.nombre] ?? ""}
            error={errores[c.nombre]}
            onChange={(e) => alCambiar(c.nombre, e.target.value)}
          />
        ) : (
          <CampoEntrada
            key={c.nombre}
            etiqueta={c.etiqueta}
            numerico={c.tipo === "numero"}
            placeholder={c.marcador}
            value={valores[c.nombre] ?? ""}
            error={errores[c.nombre]}
            onChange={(e) => alCambiar(c.nombre, e.target.value)}
          />
        ),
      )}
    </Contenedor>
  );
}

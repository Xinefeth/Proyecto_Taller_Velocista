// Campo de búsqueda con lupa (.search del prototipo).
import { Buscar } from "../IconosUI";

export interface BuscadorProps {
  valor: string;
  alCambiar: (valor: string) => void;
  marcador?: string;
  /** Nombre accesible del campo. */
  etiqueta: string;
}

export function Buscador({ valor, alCambiar, marcador = "Buscar…", etiqueta }: BuscadorProps) {
  return (
    <label className="search">
      <Buscar />
      <input
        className="inp"
        placeholder={marcador}
        aria-label={etiqueta}
        value={valor}
        onChange={(e) => alCambiar(e.target.value)}
      />
    </label>
  );
}

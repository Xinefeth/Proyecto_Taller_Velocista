// Barra lateral de navegación, igual a la del prototipo.
import { SECCIONES, type IdSeccion } from "../secciones";
import { iconos, Marca } from "./Iconos";

interface Props {
  actual: IdSeccion;
  alElegir: (id: IdSeccion) => void;
}

export function Rail({ actual, alElegir }: Props) {
  const grupo = (g: "Robot" | "Gestión") =>
    SECCIONES.filter((s) => s.grupo === g).map((s) => (
      <button
        key={s.id}
        type="button"
        className="nb"
        aria-label={s.titulo}
        aria-current={actual === s.id ? "page" : undefined}
        onClick={() => alElegir(s.id)}
      >
        {iconos[s.id]}
        <span className="tip">{s.titulo}</span>
      </button>
    ));

  return (
    <nav className="rail" aria-label="Secciones">
      <div className="mark">
        <Marca />
      </div>
      <span className="gl">Robot</span>
      {grupo("Robot")}
      <span className="sep" />
      <span className="gl">Gestión</span>
      {grupo("Gestión")}
      <div className="grow" />
      <button
        type="button"
        className="sysbtn"
        aria-label="Estado del sistema"
        aria-current={actual === "sistema" ? "page" : undefined}
        onClick={() => alElegir("sistema")}
      >
        SIS
        <br />
        TEMA
      </button>
    </nav>
  );
}

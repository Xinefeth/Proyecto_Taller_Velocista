// Barra lateral de navegación, igual a la del prototipo (Protoripo.html): grupos Robot y Gestión,
// más el botón de la capa del backlog.
import { useConsola, type Tab } from "../stores/ConsolaContext";
import { iconos, Marca } from "./Iconos";

const ROBOT: [Tab, string][] = [
  ["control", "Control"],
  ["telemetria", "Telemetría"],
  ["tiempos", "Corridas y optimización"],
  ["mapa", "Mapa de pista"],
];
const GESTION: [Tab, string][] = [
  ["catalogo", "Catálogo de componentes"],
  ["armador", "Armador de robots"],
  ["reglamento", "Perfiles de reglamento"],
];

export function Rail() {
  const { tab, goTab, blOpen, setBlOpen } = useConsola();
  const boton = ([id, titulo]: [Tab, string]) => (
    <button
      key={id}
      type="button"
      className="nb"
      aria-label={titulo}
      aria-current={tab === id ? "page" : undefined}
      onClick={() => goTab(id)}
    >
      {iconos[id]}
      <span className="tip">{titulo}</span>
    </button>
  );
  return (
    <nav className="rail" aria-label="Secciones">
      <div className="mark" aria-hidden="true">
        <Marca />
      </div>
      <span className="gl">Robot</span>
      {ROBOT.map(boton)}
      <span className="sep" />
      <span className="gl">Gestión</span>
      {GESTION.map(boton)}
      <div className="grow" />
      <button
        type="button"
        className="blbtn"
        aria-pressed={blOpen}
        title="Capa del backlog: IDs y alcance por sprint"
        onClick={() => setBlOpen(!blOpen)}
      >
        BACK
        <br />
        LOG
      </button>
    </nav>
  );
}

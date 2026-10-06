// Navegación inferior para pantallas angostas (Protoripo.html).
import { useConsola, type Tab } from "../stores/ConsolaContext";
import { iconos } from "./Iconos";

const SECCIONES: [Tab, string][] = [
  ["control", "Control"],
  ["telemetria", "Telemetría"],
  ["tiempos", "Corridas"],
  ["mapa", "Mapa"],
  ["catalogo", "Catálogo"],
  ["armador", "Armador"],
  ["reglamento", "Reglamento"],
];

export function BottomNav() {
  const { tab, goTab, blOpen, setBlOpen } = useConsola();
  return (
    <nav className="bottom-nav" aria-label="Secciones">
      {SECCIONES.map(([id, titulo]) => (
        <button
          key={id}
          type="button"
          aria-current={tab === id ? "page" : undefined}
          onClick={() => goTab(id)}
        >
          {iconos[id]}
          {titulo}
        </button>
      ))}
      <button type="button" onClick={() => setBlOpen(!blOpen)}>
        <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}>
          <path d="M4 6h16M4 12h10M4 18h13" />
        </svg>
        Backlog
      </button>
    </nav>
  );
}

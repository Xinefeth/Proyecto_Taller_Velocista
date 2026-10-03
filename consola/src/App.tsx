// Estructura de la consola: barra lateral, franja superior y la página activa.
import { useState, type ReactElement } from "react";
import { Rail } from "./components/Rail";
import { Strip } from "./components/Strip";
import { Armador } from "./pages/Armador";
import { Catalogo } from "./pages/Catalogo";
import { Control } from "./pages/Control";
import { Corridas } from "./pages/Corridas";
import { Mapa } from "./pages/Mapa";
import { Reglamento } from "./pages/Reglamento";
import { Sistema } from "./pages/Sistema";
import { Telemetria } from "./pages/Telemetria";
import { SECCIONES, type IdSeccion } from "./secciones";

const PAGINAS: Record<IdSeccion, () => ReactElement> = {
  control: Control,
  telemetria: Telemetria,
  tiempos: Corridas,
  mapa: Mapa,
  catalogo: Catalogo,
  armador: Armador,
  reglamento: Reglamento,
  sistema: Sistema,
};

export default function App() {
  const [actual, setActual] = useState<IdSeccion>("control");
  const Pagina = PAGINAS[actual];
  const titulo = SECCIONES.find((s) => s.id === actual)!.titulo;
  return (
    <div className="shell">
      <Rail actual={actual} alElegir={setActual} />
      <div className="main">
        <Strip titulo={titulo} />
        <section className="view on" aria-label={titulo}>
          <Pagina />
        </section>
      </div>
    </div>
  );
}

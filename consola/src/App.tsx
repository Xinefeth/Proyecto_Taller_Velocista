// Estructura de la consola (Protoripo.html): riel, franja superior, la vista activa, navegación
// móvil, capa del backlog, modales y avisos. La navegación la lleva el store (ConsolaContext).
import type { ReactElement } from "react";
import { Rail } from "./components/Rail";
import { Strip } from "./components/Strip";
import { BottomNav } from "./components/BottomNav";
import { BacklogLayer } from "./components/BacklogLayer";
import { Capas } from "./components/Capas";
import { Toast } from "./components/Toast";
import { useConsola, type Tab } from "./stores/ConsolaContext";
import { Control } from "./pages/Control";
import { Telemetria } from "./pages/Telemetria";
import { Corridas } from "./pages/Corridas";
import { Mapa } from "./pages/Mapa";
import { Catalogo } from "./pages/Catalogo";
import { Armador } from "./pages/Armador";
import { Reglamento } from "./pages/Reglamento";

const PAGINAS: Record<Tab, () => ReactElement> = {
  control: Control,
  telemetria: Telemetria,
  tiempos: Corridas,
  mapa: Mapa,
  catalogo: Catalogo,
  armador: Armador,
  reglamento: Reglamento,
};

export default function App() {
  const { tab } = useConsola();
  const Pagina = PAGINAS[tab];
  return (
    <>
      <div className="shell">
        <Rail />
        <div className="main">
          <Strip />
          <p className="simline only-v note" style={{ margin: "-6px 4px 10px" }}>
            Maqueta con datos simulados. Toca el enlace WiFi para simular una caída, la batería para cambiarla o el
            cronómetro de meta para desconectarlo.
          </p>
          <Pagina />
        </div>
      </div>
      <BottomNav />
      <BacklogLayer />
      <Capas />
      <Toast />
    </>
  );
}

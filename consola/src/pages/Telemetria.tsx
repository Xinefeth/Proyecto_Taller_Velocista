import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "telemetria")!;

export function Telemetria() {
  return <Pendiente seccion={seccion} />;
}

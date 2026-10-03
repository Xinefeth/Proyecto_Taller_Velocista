import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "mapa")!;

export function Mapa() {
  return <Pendiente seccion={seccion} />;
}

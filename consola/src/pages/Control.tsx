import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "control")!;

export function Control() {
  return <Pendiente seccion={seccion} />;
}

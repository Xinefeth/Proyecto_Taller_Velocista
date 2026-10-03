import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "reglamento")!;

export function Reglamento() {
  return <Pendiente seccion={seccion} />;
}

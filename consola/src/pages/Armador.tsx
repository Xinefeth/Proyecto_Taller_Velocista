import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "armador")!;

export function Armador() {
  return <Pendiente seccion={seccion} />;
}

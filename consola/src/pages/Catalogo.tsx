import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "catalogo")!;

export function Catalogo() {
  return <Pendiente seccion={seccion} />;
}

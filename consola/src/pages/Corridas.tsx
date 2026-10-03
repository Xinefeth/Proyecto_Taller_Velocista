import { Pendiente } from "../components/Pendiente";
import { SECCIONES } from "../secciones";

const seccion = SECCIONES.find((s) => s.id === "tiempos")!;

export function Corridas() {
  return <Pendiente seccion={seccion} />;
}

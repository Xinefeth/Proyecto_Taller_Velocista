// Franja superior: robot, enlace en vivo y estado del sistema (API, base de datos, tiempo real).
import { useConexion } from "../stores/ConexionContext";
import type { EstadoConexion } from "../types/api";
import { Indicador } from "./Indicador";

const enLinea = (v: boolean | undefined): EstadoConexion =>
  v === undefined ? "revisando" : v ? "ok" : "falla";

export function Strip({ titulo }: { titulo: string }) {
  const { salud, api, baseDeDatos, tiempoReal } = useConexion();
  const robot = salud?.dispositivos.velocista;
  return (
    <header className="strip">
      <div className="rsel">
        <div className="rbtn">
          <b>Velocista 001</b>
          <span className="live">
            <i />
            <span>{robot ? "EN LÍNEA" : "SIN ENLACE"}</span>
          </span>
        </div>
      </div>
      <div className="ptitle">
        <h1>{titulo}</h1>
      </div>
      <div className="stats" aria-label="Estado del sistema">
        <Indicador etiqueta="API" estado={api} />
        <Indicador etiqueta="Base de datos" estado={baseDeDatos} />
        <Indicador etiqueta="Tiempo real" estado={tiempoReal} />
        <div className="divv" />
        <Indicador etiqueta="Robot" estado={enLinea(salud?.dispositivos.velocista)} />
        <Indicador etiqueta="Cronómetro" estado={enLinea(salud?.dispositivos.cronometro)} />
      </div>
    </header>
  );
}

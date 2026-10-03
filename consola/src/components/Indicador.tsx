import type { EstadoConexion } from "../types/api";

const TEXTO: Record<EstadoConexion, string> = { revisando: "…", ok: "OK", falla: "Sin conexión" };

export function Indicador({ etiqueta, estado }: { etiqueta: string; estado: EstadoConexion }) {
  return (
    <div className="st">
      <span className="lbl">{etiqueta}</span>
      <span className="v">
        <span className={`dot ${estado}`} aria-hidden="true" />
        {TEXTO[estado]}
      </span>
    </div>
  );
}

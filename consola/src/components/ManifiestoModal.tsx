// Modal del manifiesto del robot (EN-02): lo que el robot envía al conectarse. Del prototipo.
import { useConsola } from "../stores/ConsolaContext";
import { Cerrar } from "./IconosUI";
import { manifest, robotById } from "../logica/dominio";

export function ManifiestoModal() {
  const c = useConsola();
  const r = c.manifiestoId ? robotById(c.robots, c.manifiestoId) : null;
  const abierto = !!r;
  const json = r ? JSON.stringify(manifest(r, c.catalog, c.applied.ctrl, c.comp), null, 2) : "";
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(json);
      c.mostrarToast("JSON copiado.");
    } catch {
      c.mostrarToast("No se pudo copiar.");
    }
  };
  return (
    <div className={`modal ${abierto ? "on" : ""}`} role="dialog" aria-modal={abierto} aria-label="Manifiesto del robot" aria-hidden={!abierto}>
      {r && (
        <>
          <div className="dh">
            <div>
              <span className="lbl">Contrato de mensajes · EN-02</span>
              <h3>Manifiesto · {r.nm}</h3>
            </div>
            <button type="button" className="x" aria-label="Cerrar" onClick={c.cerrarManifiesto}>
              <Cerrar />
            </button>
          </div>
          <div className="mb">
            <p className="note" style={{ margin: 0 }}>
              El robot lo envía al conectarse. La consola arma sus paneles y el panel Setup a partir de este mensaje.
            </p>
            <pre className="json">{json}</pre>
          </div>
          <div className="mf">
            <button type="button" className="sb" onClick={copiar}>
              Copiar JSON
            </button>
            <button type="button" className="sb red" onClick={c.cerrarManifiesto}>
              Listo
            </button>
          </div>
        </>
      )}
    </div>
  );
}

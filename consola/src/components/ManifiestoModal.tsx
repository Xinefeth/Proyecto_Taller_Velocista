// Modal del manifiesto del robot (EN-02): lo que el robot envía al conectarse. Del prototipo.
import { useConsola } from "../stores/ConsolaContext";
import { Cerrar } from "./IconosUI";
import { manifest, panelesManifiesto, robotById } from "../logica/dominio";

export function ManifiestoModal() {
  const c = useConsola();
  const r = c.manifiestoId ? robotById(c.robots, c.manifiestoId) : null;
  const abierto = !!r;
  const m = r ? manifest(r, c.catalog, c.applied.ctrl, c.comp) : null;
  const panels = m ? panelesManifiesto(m) : [];
  const json = m ? JSON.stringify(m, null, 2) : "";
  const copiar = async () => {
    try {
      await navigator.clipboard.writeText(json);
      c.mostrarToast("JSON copiado.");
    } catch {
      c.mostrarToast("No se pudo copiar.");
    }
  };
  return (
    <div
      className={`modal ${abierto ? "on" : ""}`}
      role="dialog"
      aria-modal={abierto}
      aria-label="Manifiesto del robot"
      aria-hidden={!abierto}
    >
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
              El robot lo envía al conectarse. La consola arma sus paneles y el panel Setup a partir
              de este mensaje.
            </p>
            <p className="sub" style={{ margin: "12px 0 6px" }}>
              Paneles del robot
            </p>
            <div
              aria-label="Paneles del robot"
              style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
            >
              {panels.map((panel) => (
                <span key={panel.id} className="tag">
                  {panel.nombre}
                </span>
              ))}
              {panels.length === 0 && <span>Sin dispositivos declarados.</span>}
            </div>
            <pre className="json" style={{ marginTop: 12 }}>
              {json}
            </pre>
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

// Capa del backlog: muestra los IDs del Product Backlog v5 y atenúa por alcance (Protoripo.html).
import { useConsola, type Alcance } from "../stores/ConsolaContext";
import { Cerrar } from "./IconosUI";

const ALCANCES: [Alcance, string][] = [
  ["s1", "Sprint 1"],
  ["s2", "Fin del curso"],
  ["all", "Todo"],
];

export function BacklogLayer() {
  const { blOpen, setBlOpen, showPbi, setShowPbi, scope, setScope } = useConsola();
  return (
    <aside className={`blp ${blOpen ? "on" : ""}`} aria-label="Capa del backlog">
      <h4>
        Capa del backlog
        <button type="button" className="x" aria-label="Cerrar" onClick={() => setBlOpen(false)}>
          <Cerrar />
        </button>
      </h4>
      <div className="row">
        <span style={{ fontSize: 12.5 }}>Mostrar IDs en cada panel</span>
        <button
          type="button"
          className="sw"
          role="switch"
          aria-checked={showPbi}
          onClick={() => setShowPbi(!showPbi)}
        >
          <i />
        </button>
      </div>
      <div>
        <span className="lbl">Alcance</span>
        <div className="seg wide" style={{ marginTop: 6 }}>
          {ALCANCES.map(([v, t]) => (
            <button key={v} type="button" aria-pressed={scope === v} onClick={() => setScope(v)}>
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="leg">
        <i style={{ background: "var(--green-soft)", color: "var(--green)" }}>S1</i>
        <i style={{ background: "var(--red-soft)", color: "var(--red-hi)" }}>S2</i>
        <i style={{ background: "var(--yellow-soft)", color: "var(--yellow)" }}>Could</i>
        <i style={{ background: "var(--panel4)", color: "var(--dim)" }}>Won&apos;t</i>
      </div>
      <p>
        IDs del Product Backlog v5. “Sprint 1” atenúa lo que llega después; “Fin del curso” atenúa
        solo lo que queda fuera (Won&apos;t).
      </p>
    </aside>
  );
}

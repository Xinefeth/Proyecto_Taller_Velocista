// Vista Mapa de pista (Protoripo.html): reconstrucción desde la vuelta 1 (HU-30, solo análisis).
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { fmt } from "../logica/formato";
import { drawRec } from "../logica/lienzos";
import { useCanvas } from "../hooks/useCanvas";

function DesdeVuelta() {
  const c = useConsola();
  const m = c.mapRef.current;
  const ref = useCanvas((cv) => drawRec(cv, m.raw, m.corr, m.recording));
  let estado: [string, string], pasos: [string, string, string];
  if (m.recording) {
    estado = ["Mapeando", "tag red"];
    pasos = ["done", "cur", "todo"];
  } else if (m.corr && !m.pending) {
    estado = ["Listo", "tag good"];
    pasos = ["done", "done", "done"];
  } else if (m.pending && m.corr) {
    estado = ["Se rehará", "tag warn"];
    pasos = ["cur", "todo", "todo"];
  } else {
    estado = ["Esperando vuelta", "tag"];
    pasos = ["cur", "todo", "todo"];
  }
  const textos = [
    "Arranca el robot desde la meta y deja que complete una vuelta.",
    "Se estima el recorrido con el modelo PWM → movimiento.",
    "Se corrige la deriva obligando a que la vuelta cierre en la meta.",
  ];
  return (
    <Card className="s12" pbi="HU-30 · SP-03" sprint="C">
      <div className="hd">
        <h2>Desde la primera vuelta</h2>
        <span className={estado[1]}>{estado[0]}</span>
      </div>
      <ol className="steps">
        {textos.map((t, i) => (
          <li key={i} className={pasos[i]}>
            <span>{i + 1}</span>
            {t}
          </li>
        ))}
      </ol>
      <div className="recbox">
        <canvas ref={ref} role="img" aria-label="Recorrido estimado y corregido" />
      </div>
      <div className="st3">
        <div>
          <div className="lbl">Longitud</div>
          <div className="v">{m.stats ? `${fmt(m.stats.len, 2)} m` : "—"}</div>
        </div>
        <div>
          <div className="lbl">Error de cierre</div>
          <div className="v">{m.stats ? `${Math.round(m.stats.closeErr * 100)} cm` : "—"}</div>
        </div>
        <div>
          <div className="lbl">Giro sobrante</div>
          <div className="v">{m.stats ? `${fmt(m.stats.errH, 1)}°` : "—"}</div>
        </div>
      </div>
      <div className="acts" style={{ marginTop: 10 }}>
        <button type="button" className="sb" onClick={c.rehacerMapa}>
          Rehacer en la próxima vuelta
        </button>
        <button type="button" className="sb red" onClick={() => c.goTab("control")}>
          Ir al tablero
        </button>
      </div>
    </Card>
  );
}

export function Mapa() {
  return (
    <section className="view on dv" aria-label="Mapa de pista">
      <DesdeVuelta />
    </section>
  );
}

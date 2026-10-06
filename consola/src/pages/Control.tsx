// Vista Control (Protoripo.html): tablero del velocista en vivo.
// EN-19, HU-13 a HU-18, HU-21 a HU-24, HU-30, HU-11.
import { useState } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { ICO, Gate, Play, Stop } from "../components/IconosUI";
import { CTRL, PDEF, differs } from "../datos/controladores";
import { curVer, facts } from "../logica/dominio";
import { clamp, fmt } from "../logica/formato";
import { drawChart, drawHealth, drawMap, type DatosMapa } from "../logica/lienzos";
import { useCanvas } from "../hooks/useCanvas";

// Alcance de cada controlador: en Sprint 1 solo PID; adaptativo (EN-21) es S2 y difuso (HU-31) es Could.
const CTRL_SPRINT: Record<string, "2" | "C" | undefined> = { pid: undefined, adapt: "2", fuzzy: "C" };

function Salida() {
  const c = useConsola();
  const calTag = c.calibrating
    ? ["Calibrando", "tag"]
    : c.calibrated
      ? ["Calibrado", "tag good"]
      : ["Sin calibrar", "tag warn"];
  let hint: [string, string];
  if (c.running) hint = [c.mode === "competencia" ? "Intento en curso: una vuelta." : "En pista, modo prueba.", "hint"];
  else if (!c.calibrated) hint = ["Calibra los sensores antes de arrancar.", "hint warn"];
  else if (differs(c.draft, c.applied)) hint = ["Saldrá con el setup enviado, no con los cambios pendientes.", "hint warn"];
  else hint = ["Listo para salir.", "hint"];
  const modeNote =
    c.mode === "prueba"
      ? "Prueba: vueltas continuas; se detiene si se pierde el enlace."
      : c.perfil.r.mr4
        ? "Competencia: una vuelta y se detiene, como un intento de MR4 (máx. 120 s)."
        : "Competencia: una vuelta y se detiene.";
  return (
    <Card className="a-go" pbi="HU-16 · HU-18" sprint="1">
      <div className="hd">
        <h2>Salida</h2>
        <span className={calTag[1]}>{calTag[0]}</span>
      </div>
      <button type="button" className="go" data-running={c.running} onClick={c.arrancarDetener}>
        {c.running ? <Stop /> : <Play />}
        <span>{c.running ? "DETENER" : "ARRANCAR"}</span>
      </button>
      <div className="gosub">
        <span>Arranque inalámbrico</span>
        <span>{c.perfil.r.inal ? `Requerido · ${c.perfil.cat}` : "Opcional en este perfil"}</span>
      </div>
      <p className={hint[1]}>{hint[0]}</p>
      <div className={`calp ${c.calibrating ? "on" : ""}`}>
        <i style={{ width: `${c.calProgress * 100}%` }} />
      </div>
      <div className="rows">
        <div className="row">
          <span className="lbl">Sensores</span>
          <button type="button" className="sb" disabled={c.running || c.calibrating} onClick={c.calibrar}>
            {c.calibrating ? "Desliza…" : c.calibrated ? "Recalibrar" : "Calibrar"}
          </button>
        </div>
        <div className="row">
          <span className="lbl">Modo</span>
          <div className="seg" role="group" aria-label="Modo">
            <button type="button" aria-pressed={c.mode === "prueba"} disabled={c.running} onClick={() => c.setMode("prueba")}>
              Prueba
            </button>
            <button
              type="button"
              aria-pressed={c.mode === "competencia"}
              disabled={c.running}
              onClick={() => c.setMode("competencia")}
            >
              Competencia
            </button>
          </div>
        </div>
        <div className="row">
          <span className="lbl">Línea</span>
          <div className="seg" role="group" aria-label="Color de la línea">
            <button type="button" aria-pressed={c.line === "negra"} disabled={c.running} onClick={() => c.setLine("negra")}>
              Negra
            </button>
            <button type="button" aria-pressed={c.line === "blanca"} disabled={c.running} onClick={() => c.setLine("blanca")}>
              Blanca
            </button>
          </div>
        </div>
      </div>
      <p className="note">{modeNote}</p>
      <div className="lock" role="status">
        Modo competencia: mientras corre solo responde a Detener y el setup queda bloqueado. El juez verifica que no haya
        control durante el recorrido.
      </div>
    </Card>
  );
}

function Parametro({ id }: { id: string }) {
  const c = useConsola();
  const d = PDEF[id];
  const same = c.draft.ctrl === c.applied.ctrl;
  const ch = !same || Math.abs(c.draft.p[id] - c.applied.p[id]) > 1e-9;
  return (
    <div className="prm">
      <label className="nm" htmlFor={`n-${id}`} title={d.t}>
        {d.nm}
      </label>
      <input
        type="range"
        id={`r-${id}`}
        min={d.min}
        max={d.max}
        step={d.step}
        value={c.draft.p[id]}
        aria-label={d.t}
        onChange={(e) => c.setParam(id, +e.target.value)}
      />
      <div className="ctl">
        <button type="button" aria-label={`Bajar ${d.nm}`} onClick={() => c.setParam(id, c.draft.p[id] - d.step)}>
          −
        </button>
        <input
          id={`n-${id}`}
          inputMode="decimal"
          className={ch ? "changed" : ""}
          value={fmt(c.draft.p[id], d.dec)}
          onChange={(e) => {
            const v = parseFloat(e.target.value.replace(",", "."));
            if (!isNaN(v)) c.setParam(id, v);
          }}
        />
        <button type="button" aria-label={`Subir ${d.nm}`} onClick={() => c.setParam(id, c.draft.p[id] + d.step)}>
          +
        </button>
      </div>
      <div className="was">{ch && same ? `en robot ${fmt(c.applied.p[id], d.dec)}` : ""}</div>
    </div>
  );
}

function Setup() {
  const c = useConsola();
  const ctrl = CTRL[c.draft.ctrl];
  const same = c.draft.ctrl === c.applied.ctrl;
  const pend = differs(c.draft, c.applied);
  let tag: [string, string];
  if (pend) tag = [same ? "Sin enviar" : `Cambia a ${ctrl.short}`, "tag red"];
  else if (differs(c.applied, c.saved)) tag = ["Sin guardar", "tag warn"];
  else tag = ["Guardado", "tag good"];
  const why = c.perfil.r.mapaVel
    ? "Permitido por este perfil, pero la función queda fuera de este curso (HU-33)."
    : `Bloqueado por ${c.perfil.comp} · ${c.perfil.cat}: el robot solo puede guiarse por la línea, sin movimientos pre-programados.`;
  const eng = c.ingeniero.vista(c.applied.ctrl);
  return (
    <Card className="a-setup" pbi="HU-17" sprint="1">
      <div className="hd">
        <h2>
          Setup <small>{ctrl.nm}</small>
        </h2>
        <span className={tag[1]}>{tag[0]}</span>
      </div>
      <div className="ctrlsel">
        <span className="lbl">Controlador</span>
        <div className="seg" role="group" aria-label="Controlador" style={{ marginTop: 6 }}>
          {Object.entries(CTRL).map(([k, v]) => (
            <button
              key={k}
              type="button"
              aria-pressed={c.draft.ctrl === k}
              disabled={c.locked}
              data-sprint={CTRL_SPRINT[k]}
              onClick={() => c.setCtrl(k)}
            >
              {v.nm}
            </button>
          ))}
        </div>
        <p className="ctrldesc">{ctrl.desc}</p>
      </div>
      <div className="presets" role="group" aria-label="Ajustes rápidos">
        {Object.keys(ctrl.pre).map((k) => (
          <button key={k} type="button" aria-pressed={c.preset === k} disabled={c.locked} onClick={() => c.setPreset(k)}>
            {k}
          </button>
        ))}
      </div>
      <div>
        {ctrl.keys.map((id) => (
          <Parametro key={id} id={id} />
        ))}
      </div>
      <div className="acts">
        <button type="button" className="sb red" disabled={!pend || c.locked} onClick={c.enviarSetup}>
          Enviar
        </button>
        <button type="button" className="sb ghost" disabled={c.locked} onClick={c.guardarSetup}>
          Guardar en robot
        </button>
      </div>
      <p className="note">
        {pend
          ? same
            ? "Los valores en rojo aún no están en el robot."
            : `El robot sigue con ${CTRL[c.applied.ctrl].nm} hasta que envíes.`
          : ""}
      </p>
      <div className="opts">
        <div className="row">
          <span className="l">Compensar batería</span>
          <button type="button" className="sw" role="switch" aria-checked={c.comp} onClick={c.toggleComp}>
            <i />
          </button>
        </div>
        <div className="row" data-sprint="W">
          <span className="l">Velocidad por mapa</span>
          <button type="button" className="sw" role="switch" aria-checked={false} disabled>
            <i />
          </button>
        </div>
        <div className="lockrow">
          {ICO.lock}
          <span>{why}</span>
        </div>
      </div>
      <div className="eng" data-sprint="2">
        <p dangerouslySetInnerHTML={{ __html: eng.mini }} />
        <button type="button" className="sb" disabled={!eng.hasProp || c.locked} onClick={c.cargarPropuesta}>
          Cargar
        </button>
      </div>
    </Card>
  );
}

function PistaEnVivo() {
  const c = useConsola();
  const sim = c.simRef.current;
  const m = c.mapRef.current;
  const datos: DatosMapa = {
    recording: m.recording,
    raw: m.raw,
    corr: m.corr,
    path: m.path,
    mapMode: c.mapMode,
    lastBins: c.lastBinsRef.current,
    lastColsSector: c.lastLap && c.lastLap.col.length === 3 ? c.lastLap.col : null,
    trail: c.trailRef.current,
    running: c.running,
    simS: sim.s,
    simE: sim.e,
    short: c.robot.short,
  };
  const ref = useCanvas((cv) => drawMap(cv, datos));
  const lostNow = Math.abs(sim.es) > 1.1;
  const tMean = c.running && sim.lapT > 0.2
    ? fmt(sim.iae / sim.lapT, 2)
    : c.lastLap
      ? fmt(c.lastLap.iae / Math.max(0.01, c.lastLap.t), 2)
      : "—";
  return (
    <Card className="a-map" aria-label="Pista en vivo" pbi="HU-22 · HU-24" sprint="2">
      <div className="hd">
        <h2>
          Pista en vivo <small>{m.recording ? "mapeando vuelta 1" : m.source || "sin mapa"}</small>
        </h2>
        <div className="seg" role="group" aria-label="Qué mostrar en el mapa">
          <button type="button" aria-pressed={c.mapMode === "error"} onClick={() => c.setMapMode("error")}>
            Error
          </button>
          <button type="button" aria-pressed={c.mapMode === "sectores"} onClick={() => c.setMapMode("sectores")}>
            Sectores
          </button>
        </div>
      </div>
      <div className="mapbox">
        <canvas ref={ref} role="img" aria-label="Mapa de pista con la posición del robot" />
        {!(m.path || m.recording) && (
          <div className="mapmsg">
            <div>
              <p>
                El mapa se construye durante la primera vuelta y sirve solo para analizar: el robot se guía únicamente por la
                línea.
              </p>
              <div className="b">
                <button type="button" className="sb" onClick={() => c.goTab("mapa")}>
                  Ver mapa
                </button>
                <button type="button" className="sb ghost" onClick={c.usarEjemplo}>
                  Usar pista de pruebas
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="telem">
        <div>
          <div className="lbl">Sector</div>
          <div className="v">{c.running ? `S${sim.sec + 1}` : "—"}</div>
        </div>
        <div>
          <div className="lbl">Error</div>
          <div className={`v ${Math.abs(sim.p) > 0.6 ? "bad" : ""}`}>{fmt(sim.p, 2)}</div>
        </div>
        <div>
          <div className="lbl">PWM izq / der</div>
          <div className="v">{`${Math.round(sim.pl)} / ${Math.round(sim.pr)}`}</div>
        </div>
        <div>
          <div className="lbl">Error medio</div>
          <div className="v">{tMean}</div>
        </div>
        <div>
          <div className="lbl">Líneas perdidas</div>
          <div className={`v ${lostNow ? "bad" : ""}`}>{c.running ? sim.lost : c.lastLap ? c.lastLap.lost : 0}</div>
        </div>
      </div>
      <div className="offline" role="status">
        Sin enlace: la telemetría está en pausa. Si el robot sigue corriendo, las vueltas se graban en su memoria y se
        sincronizan al reconectar.
      </div>
    </Card>
  );
}

function Cronometraje() {
  const c = useConsola();
  const sim = c.simRef.current;
  const fins = c.laps.filter((l) => l.fin);
  const best = fins.length ? Math.min(...fins.map((l) => l.t)) : null;
  let gap = "—",
    gapPurple = false;
  if (best != null && c.lastLap?.fin) {
    const g = c.lastLap.t - best;
    gap = g <= 1e-9 ? "Mejor" : `+${fmt(g, 3)}`;
    gapPurple = g <= 1e-9;
  }
  const last16 = c.laps.slice(-16);
  const lf = last16.filter((l) => l.fin);
  const tmax = Math.max(...lf.map((l) => l.t), 1);
  const tmin = Math.min(...lf.map((l) => l.t), tmax);
  const [nota, setNota] = useState("");
  const sec = (i: number): [string, string] => {
    if (c.running && i === sim.sec) return ["live", fmt(sim.lapT - sim.secStart, 2)];
    if (c.running && i < sim.sec) {
      const x = sim.secT[i];
      return [x < c.bestSec[i] ? "purple" : "green", fmt(x, 3)];
    }
    if (c.lastLap?.fin) return [c.lastLap.col[i], fmt(c.lastLap.sec[i], 3)];
    return ["", "—"];
  };
  return (
    <Card className="a-time" aria-label="Cronometraje" pbi="HU-19 · EN-15" sprint="2">
      <div className="hd">
        <h2>Cronometraje</h2>
        <span className="tag">{c.laps.length ? `${c.laps.length} vuelta${c.laps.length === 1 ? "" : "s"}` : "Sin vueltas"}</span>
      </div>
      <button type="button" className={`gate ${c.gate ? "" : "off"}`} title="Cronómetro de meta: toca para simular una desconexión" onClick={c.toggleGate}>
        <span className="l">
          <Gate />
          <span>{c.gate ? "Meta · barrera OK" : "Meta desconectada"}</span>
        </span>
        <span className={`tag ${c.gate ? "good" : "warn"}`}>
          <span className="dot" />
          {c.gate ? "± 5 ms" : "Telemetría"}
        </span>
      </button>
      <div className="lapbig">
        <div>
          <div className="lbl">Vuelta</div>
          <div className="n">
            {c.lapCount ? (
              <>
                {c.lapCount}
                {c.mode === "competencia" && <small> / 1</small>}
              </>
            ) : (
              "—"
            )}
          </div>
        </div>
        <div>
          <div className="lbl" style={{ textAlign: "right" }}>
            Dif. a la mejor
          </div>
          <div className="gap" style={{ color: gapPurple ? "var(--purple)" : "" }}>
            {gap}
          </div>
        </div>
      </div>
      <div className="now">
        {fmt(sim.lapT, 3)}
        <small>s</small>
      </div>
      <div className="pair">
        <div>
          <div className="lbl">Última</div>
          <div className="v">{c.lastLap ? (c.lastLap.fin ? fmt(c.lastLap.t, 3) : "No terminó") : "—"}</div>
        </div>
        <div>
          <div className="lbl">Mejor</div>
          <div className="v purple">{best != null ? fmt(best, 3) : "—"}</div>
        </div>
      </div>
      <div className="secs">
        {[0, 1, 2].map((i) => {
          const [cls, val] = sec(i);
          return (
            <div key={i} data-c={cls}>
              <div className="lbl">S{i + 1}</div>
              <div className="v">{val}</div>
            </div>
          );
        })}
      </div>
      <div className="hist" aria-label="Historial de vueltas">
        {last16.map((l, i) => {
          if (!l.fin) return <i key={i} className="dnf" style={{ height: "100%" }} title={`V${l.n}: no terminó`} />;
          const h = 30 + (1 - (l.t - tmin) / Math.max(0.01, tmax - tmin)) * 70;
          return <i key={i} className={l.t === best ? "best" : ""} style={{ height: `${h}%` }} title={`V${l.n}: ${fmt(l.t, 3)} s`} />;
        })}
      </div>
      <div className="quick">
        <input
          className="inp"
          placeholder="Nota para la última corrida"
          aria-label="Nota para la última corrida"
          value={nota}
          onChange={(e) => setNota(e.target.value)}
        />
        <button
          type="button"
          className="sb"
          onClick={() => {
            if (c.guardarNota(nota)) setNota("");
          }}
        >
          Guardar nota
        </button>
      </div>
      <p className="note">Cada vuelta se registra sola como corrida.</p>
    </Card>
  );
}

function Regleta() {
  const c = useConsola();
  const sim = c.simRef.current;
  const pos = -sim.es;
  const vis = Math.abs(sim.es) <= 1.1;
  let act = 0;
  const bars = Array.from({ length: 16 }, (_, i) => {
    const x = -1 + i * (2 / 15);
    let v = vis ? Math.exp(-((x - pos) ** 2) / (2 * 0.018)) : 0;
    v = clamp(v + Math.random() * 0.04, 0, 1);
    const hot = v > 0.5;
    if (hot) act++;
    return { h: 8 + v * 92, hot, n: Math.round(v * 9) };
  });
  const posTag: [string, string] = !vis
    ? ["Línea perdida", "tag red"]
    : Math.abs(pos) < 0.25
      ? ["Centrada", "tag good"]
      : [pos > 0 ? "Hacia la derecha" : "Hacia la izquierda", "tag"];
  return (
    <Card className="a-sens" pbi="HU-15" sprint="1">
      <div className="hd">
        <h2>
          Regleta <small>16 canales · 2 × QTR-8A</small>
        </h2>
        <span className={posTag[1]}>{posTag[0]}</span>
      </div>
      <div className="bars">
        {bars.map((b, i) => (
          <div className="bar" key={i}>
            <div className="tb">
              <i className={b.hot ? "hot" : ""} style={{ height: `${b.h}%` }} />
            </div>
            <div className="n">{b.n}</div>
          </div>
        ))}
      </div>
      <div className="modl">
        <span>QTR-8A · izquierda</span>
        <span>QTR-8A · derecha</span>
      </div>
      <div className="sread">
        <div>
          <div className="lbl">Posición</div>
          <div className={`v ${vis ? "" : "bad"}`}>{vis ? `${pos > 0 ? "+" : ""}${fmt(pos * 72, 1)} mm` : "Perdida"}</div>
        </div>
        <div>
          <div className="lbl">Error</div>
          <div className="v">{fmt(sim.p, 2)}</div>
        </div>
        <div>
          <div className="lbl">Sobre la línea</div>
          <div className="v">{act} / 16</div>
        </div>
      </div>
    </Card>
  );
}

function Senales() {
  const c = useConsola();
  const ref = useCanvas((cv) => drawChart(cv, c.histRef.current, c.show));
  const keys: [keyof typeof c.show, string, string][] = [
    ["err", "var(--red)", "Error"],
    ["pl", "var(--ink)", "Izq"],
    ["pr", "var(--dim)", "Der"],
  ];
  return (
    <Card className="a-sig" pbi="HU-21" sprint="2">
      <div className="hd">
        <h2>
          Señales <small>6 s · 20 Hz</small>
        </h2>
        <div className="keys">
          {keys.map(([k, col, t]) => (
            <button key={k} type="button" aria-pressed={c.show[k]} onClick={() => c.toggleSenal(k)}>
              <i style={{ background: col }} />
              {t}
            </button>
          ))}
        </div>
      </div>
      <div className="cbox">
        <canvas ref={ref} role="img" aria-label="Error y PWM de cada motor" />
      </div>
    </Card>
  );
}

function Registro() {
  const c = useConsola();
  return (
    <Card className="flat a-log" pbi="HU-23" sprint="2">
      <div className="hd">
        <h2>Registro de eventos</h2>
        <span className="tag">{c.log.length}</span>
      </div>
      <div className="logs">
        <table>
          <thead>
            <tr>
              <th>Hora</th>
              <th>Sistema</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {c.log.map((e, i) => (
              <tr key={i} className={e.lv}>
                <td>{e.t}</td>
                <td>{e.sys}</td>
                <td>{e.msg}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function ErrorPista() {
  const c = useConsola();
  const sim = c.simRef.current;
  const ref = useCanvas((cv) => drawHealth(cv, c.running, sim.s, c.curBinsRef.current, c.curCntRef.current, c.lastBinsRef.current));
  return (
    <Card className="a-health" pbi="HU-30" sprint="C">
      <div className="hd">
        <h2>
          Error a lo largo de la pista <small>vuelta actual sobre la anterior</small>
        </h2>
        <div className="hscale lbl">
          <span>Estable</span>
          <i style={{ background: "#2A2E3A" }} />
          <i style={{ background: "#7A2338" }} />
          <i style={{ background: "var(--red)" }} />
          <span>Inestable</span>
        </div>
      </div>
      <div className="hbox">
        <canvas ref={ref} role="img" aria-label="Error del robot a lo largo de la distancia de la pista" />
      </div>
    </Card>
  );
}

function PanelesManifiesto() {
  const c = useConsola();
  const sim = c.simRef.current;
  const f = facts(curVer(c.robot).parts, c.catalog);
  const encL = Math.round((Math.max(0, sim.wl) / 100) * 3200);
  const encR = Math.round((Math.max(0, sim.wr) / 100) * 3200);
  return (
    <div className="a-ext">
      {f.enc && (
        <Card pbi="HU-13 · HU-11" sprint="1">
          <div className="hd">
            <h2>
              Encoders <small>{f.enc.s.cpr} CPR · del manifiesto</small>
            </h2>
            <span className="tag">2 ruedas</span>
          </div>
          <div className="gauge">
            <div>
              <div className="lbl">Rueda izquierda</div>
              <div className="v">{encL} rpm</div>
            </div>
            <div>
              <div className="lbl">Rueda derecha</div>
              <div className="v">{encR} rpm</div>
            </div>
          </div>
          {!c.perfil.r.enc && (
            <div className="lockov">
              <div>
                {ICO.lock}
                <p>
                  Encoders no permitidos en{" "}
                  <b>
                    {c.perfil.comp} · {c.perfil.cat}
                  </b>
                  : el robot solo puede guiarse por la línea.
                </p>
              </div>
            </div>
          )}
        </Card>
      )}
      {f.turb && (
        <Card pbi="HU-13 · HU-11" sprint="1">
          <div className="hd">
            <h2>
              Turbina <small>{f.turb.nm}</small>
            </h2>
            <span className={`tag ${c.turb ? "red" : ""}`}>{c.turb ? "Encendida" : "Apagada"}</span>
          </div>
          <div className="prm" style={{ gridTemplateColumns: "60px 1fr auto", border: 0 }}>
            <span className="nm">Succión</span>
            <input
              type="range"
              min={0}
              max={100}
              step={5}
              value={c.turb}
              aria-label="Potencia de la turbina"
              onChange={(e) => c.setTurb(+e.target.value)}
            />
            <span className="m">{c.turb} %</span>
          </div>
          <div className="gauge">
            <div>
              <div className="lbl">Corriente</div>
              <div className="v">{fmt((c.turb / 100) * 3.5, 1)} A</div>
            </div>
            <div>
              <div className="lbl">Encendido</div>
              <div className="v" style={{ fontSize: 13, marginTop: 6 }}>
                Al energizar, según el reglamento
              </div>
            </div>
          </div>
          {!c.perfil.r.turbina && (
            <div className="lockov">
              <div>
                {ICO.lock}
                <p>
                  Turbina no permitida en{" "}
                  <b>
                    {c.perfil.comp} · {c.perfil.cat}
                  </b>
                  . Solo en Master.
                </p>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

export function Control() {
  return (
    <section className="view on mc" aria-label="Control">
      <Salida />
      <Setup />
      <PistaEnVivo />
      <Cronometraje />
      <Regleta />
      <Senales />
      <Registro />
      <ErrorPista />
      <PanelesManifiesto />
    </section>
  );
}

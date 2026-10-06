// Franja superior de la consola (Protoripo.html): selector de robot con manifiesto, batería y
// enlace simulados, tiempos de vuelta, fuente de datos (EN-05) y chip del perfil de reglamento.
import { useEffect, useRef, useState } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { complies, curVer, facts } from "../logica/dominio";
import { clamp, fmt } from "../logica/formato";
import { colores } from "../logica/lienzos";
import { Chevron, Shield } from "./IconosUI";
import { PbiChip } from "./Card";

const TITULOS: Record<string, [string, string]> = {
  catalogo: ["Catálogo de componentes", "Specs reales, precios e inventario del club"],
  armador: ["Armador de robots", "Arma un robot desde el catálogo: costo, masa, compatibilidad y reglamento"],
  reglamento: ["Perfiles de reglamento", "Reglas como datos: qué permite cada competencia y categoría"],
};

export function Strip() {
  const c = useConsola();
  const [menu, setMenu] = useState(false);
  const rsel = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menu) return;
    const fuera = (e: MouseEvent) => {
      if (!rsel.current?.contains(e.target as Node)) setMenu(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setMenu(false);
    document.addEventListener("click", fuera);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("click", fuera);
      document.removeEventListener("keydown", esc);
    };
  }, [menu]);

  const col = colores();
  const fins = c.laps.filter((l) => l.fin);
  const best = fins.length ? Math.min(...fins.map((l) => l.t)) : null;
  let gap = "—";
  if (best != null && c.lastLap?.fin) {
    const g = c.lastLap.t - best;
    gap = g <= 1e-9 ? "Mejor" : `+${fmt(g, 3)}`;
  }
  const rec = c.mapRef.current.recording;
  const liveTxt = !c.connected
    ? "SIN ENLACE"
    : c.running
      ? rec
        ? "MAPEANDO · EN VIVO"
        : "EN PISTA · EN VIVO"
      : c.source === "sim"
        ? "EN REPOSO · SIMULADO"
        : "EN REPOSO";

  const pct = clamp((c.vbat - 6.8) / (8.4 - 6.8), 0, 1);
  const batColor = pct < 0.3 ? col["--red"] : pct < 0.55 ? col["--yellow"] : col["--green"];
  const ok = complies(c.robot, c.perfil, c.catalog);
  const titulo = TITULOS[c.tab];

  return (
    <header className="strip">
      <div className="rsel only-v" ref={rsel} data-pbi="HU-13" data-sprint="1">
        <PbiChip pbi="HU-13" sprint="1" inl />
        <button type="button" className="rbtn" aria-haspopup="menu" aria-expanded={menu} onClick={() => setMenu((m) => !m)}>
          <b>
            <span>{c.robot.nm}</span>
            <Chevron />
          </b>
          <span className={`live ${!c.running || !c.connected ? "off" : ""}`}>
            <i />
            <span>{liveTxt}</span>
          </span>
        </button>
        {menu && (
          <div className="menu" role="menu">
            {c.robots.map((r) => {
              const v = curVer(r),
                f = facts(v.parts, c.catalog),
                esVelo = r.tipo === "velocista",
                cumple = complies(r, c.perfil, c.catalog);
              return (
                <button
                  key={r.id}
                  type="button"
                  className="mi"
                  role="menuitemradio"
                  aria-checked={r.id === c.robotId}
                  disabled={!esVelo}
                  onClick={() => {
                    setMenu(false);
                    c.selectRobot(r.id);
                  }}
                >
                  <b>
                    {r.nm} <span className="dimt m" style={{ fontSize: 11, fontWeight: 400 }}>{v.v}</span>
                  </b>
                  <span className={`tag ${cumple ? "good" : "red"}`} style={{ fontSize: 9 }}>
                    {cumple ? "Cumple" : "No cumple"}
                  </span>
                  <small>
                    {esVelo
                      ? `${f.mcu ? f.mcu.nm.split(" ")[0] : "—"} · ${f.sensores} sensores${f.enc ? " · encoders" : ""}${
                          f.turb ? " · turbina" : ""
                        } · ${r.fw ? "firmware " + r.fw : "sin firmware: solo simulado"}`
                      : "Sin consola para MiniSumo todavía"}
                  </small>
                </button>
              );
            })}
            <hr />
            <button type="button" className="mi" onClick={() => { setMenu(false); c.abrirManifiesto(c.robotId); }}>
              <b>Ver manifiesto</b>
              <small>Lo que el robot envía al conectarse (EN-02)</small>
            </button>
            <button type="button" className="mi" onClick={() => { setMenu(false); c.abrirEnArmador(c.robotId); }}>
              <b>Abrir en el armador</b>
              <small>Piezas, costo y versiones</small>
            </button>
          </div>
        )}
      </div>

      <div className="ptitle only-g">
        <h1>{titulo ? titulo[0] : "Gestión"}</h1>
        <p>{titulo ? titulo[1] : ""}</p>
      </div>

      <div className="stats only-v" data-pbi="HU-14" data-sprint="1">
        <PbiChip pbi="HU-14" sprint="1" inl />
        <button type="button" className="st" title="Toca para simular un cambio de batería" onClick={c.cambiarBateria}>
          <span className="lbl">Batería</span>
          <span className="v">
            <span className="batbar">
              <i style={{ width: `${pct * 100}%`, background: batColor }} />
            </span>
            <span>{fmt(c.vbat, 2)} V</span>
          </span>
        </button>
        <button type="button" className="st" title="Toca para simular una caída del enlace" onClick={c.toggleConnected}>
          <span className="lbl">Enlace WiFi</span>
          <span className="v" style={{ color: c.connected ? "" : col["--red-hi"] }}>
            {c.connected ? (
              <>
                −{c.link.dbm} dBm <small>{c.link.ms} ms</small>
              </>
            ) : (
              "Sin enlace"
            )}
          </span>
        </button>
        <div className="st hide-m">
          <span className="lbl">Lazo</span>
          <span className="v">1000 Hz</span>
        </div>
        <div className="divv" />
        <div className="st" data-sprint="2">
          <span className="lbl">Vuelta</span>
          <span className="v">{c.lapCount || "—"}</span>
        </div>
        <div className="st" data-sprint="2">
          <span className="lbl">Última</span>
          <span className="v">{c.lastLap?.fin ? fmt(c.lastLap.t, 3) : "—"}</span>
        </div>
        <div className="st" data-sprint="2">
          <span className="lbl">Mejor</span>
          <span className="v purple">{best != null ? fmt(best, 3) : "—"}</span>
        </div>
        <div className="st hide-m" data-sprint="2">
          <span className="lbl">Dif. a la mejor</span>
          <span className="v" style={{ color: gap === "Mejor" ? col["--purple"] : "" }}>
            {gap}
          </span>
        </div>
      </div>

      <div className="spacer" />
      <div className="stripR">
        <div className="seg only-v" role="group" aria-label="Fuente de datos" data-pbi="EN-05" data-sprint="1">
          <button type="button" aria-pressed={c.source === "sim"} onClick={() => c.setSource("sim")}>
            Simulado
          </button>
          <button type="button" aria-pressed={c.source === "robot"} onClick={() => c.setSource("robot")}>
            Robot
          </button>
        </div>
        <button
          type="button"
          className={`regchip ${ok ? "ok" : "bad"}`}
          title={`${c.perfil.comp} · ${c.perfil.cat}: ${c.robot.nm} ${ok ? "cumple" : "no cumple"} el reglamento`}
          onClick={() => c.goTab("reglamento")}
        >
          <Shield />
          <span>
            <b>{c.perfil.tag}</b> · {c.perfil.cat}
          </span>
        </button>
      </div>
    </header>
  );
}

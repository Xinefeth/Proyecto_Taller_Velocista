// Vista Perfiles de reglamento (Protoripo.html): reglas como datos, cumplimiento del robot y
// qué bloquea la consola. HU-10, HU-11, SP-01.
import { useState, type ReactElement } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { ICO } from "../components/IconosUI";
import { GENERALES, REGLAS } from "../datos/reglamento";
import { checks, curVer, facts } from "../logica/dominio";

export function Reglamento() {
  const c = useConsola();
  const velos = c.robots.filter((x) => x.tipo === "velocista");
  const [rgRobot, setRgRobot] = useState(velos.find((x) => x.id === c.robotId) ? c.robotId : velos[0]?.id);
  const rb = c.robots.find((x) => x.id === rgRobot) ?? velos[0];
  const pr = c.perfil;
  const ck = checks(facts(curVer(rb).parts, c.catalog), pr);
  const bad = ck.some((x) => x[0] === "bad");
  const r = pr.r;

  const locks: [string, ReactElement, string, string][] = [
    [r.mapaVel ? "ok" : "bad", r.mapaVel ? ICO.ok : ICO.lock, "Velocidad por mapa", r.mapaVel ? "Permitida por el perfil (función fuera de este curso)." : "Bloqueada: movimientos pre-programados."],
    [r.enc ? "ok" : "bad", r.enc ? ICO.ok : ICO.lock, "Panel de encoders", r.enc ? "Visible si el robot los tiene." : "Bloqueado aunque el robot los tenga."],
    [r.turbina ? "ok" : "bad", r.turbina ? ICO.ok : ICO.lock, "Panel de turbina", r.turbina ? "Visible si el robot la tiene." : `No permitida en ${pr.cat}.`],
    [r.inal ? "warn" : "ok", r.inal ? ICO.warn : ICO.ok, "Arranque", r.inal ? "Inalámbrico obligatorio: ARRANCAR desde la consola." : "Libre."],
    ["warn", ICO.warn, "Modo competencia", "Solo Arrancar y Detener; el setup se bloquea durante el recorrido."],
  ];
  if (r.mr4) locks.push(["warn", ICO.warn, "Intento", "Una vuelta y se detiene; pasados 120 s cuenta como no terminada."]);

  return (
    <section className="view on rg" aria-label="Reglamento">
      <div className="stack">
        <Card pbi="HU-10" sprint="2">
          <div className="hd">
            <h2>Perfiles</h2>
          </div>
          <div className="plist">
            {c.perfiles.map((p) => (
              <button key={p.id} type="button" className="pli" aria-current={p.id === c.perfil.id} onClick={() => c.setProfile(p.id)}>
                <b>
                  {p.comp} · {p.cat}
                </b>
                <small>{p.r.mr4 ? "Seguidor de línea velocista" : "Sin restricciones, para experimentar"}</small>
              </button>
            ))}
          </div>
          <button type="button" className="sb ghost" disabled style={{ width: "100%", marginTop: 10 }} title="Fuera del backlog actual">
            Nuevo perfil
          </button>
          <p className="note">Las reglas se guardan como datos: agregar una competencia no requiere programar.</p>
        </Card>
      </div>

      <div className="stack">
        <Card pbi="HU-10 · SP-01" sprint="2">
          <div className="hd">
            <h2>
              Reglas por categoría <small>Muchik Rumble 4 · Seguidor de línea velocista</small>
            </h2>
          </div>
          <div className="table">
            <table className="rt">
              <thead>
                <tr>
                  <th />
                  {c.perfiles.map((p) => (
                    <th key={p.id} className={p.id === c.perfil.id ? "on" : ""}>
                      {p.r.mr4 ? p.cat : "Club"}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {REGLAS.map(([l, fn]) => (
                  <tr key={l}>
                    <th scope="row">{l}</th>
                    {c.perfiles.map((p) => {
                      const val = fn(p.r);
                      const no = /^(No permitida|Prohibid)/.test(val);
                      return (
                        <td key={p.id} className={`${p.id === c.perfil.id ? "on" : ""} ${no ? "no" : ""}`.trim()}>
                          {val}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
        <Card>
          <div className="hd">
            <h2>Reglas generales de la competencia</h2>
          </div>
          <ul className="gen">
            {GENERALES.map(([t, d], i) => (
              <li key={i}>
                {ICO.info}
                <span>
                  <b>{t}.</b> {d}
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <div className="stack">
        <Card pbi="HU-10" sprint="2">
          <div className="hd">
            <h2>Cumplimiento</h2>
            <span className={`tag ${bad ? "red" : "good"}`}>{bad ? "No cumple" : "Cumple"}</span>
          </div>
          <div className="seg wide" style={{ marginBottom: 10 }}>
            {velos.map((x) => (
              <button key={x.id} type="button" aria-pressed={x.id === rgRobot} onClick={() => setRgRobot(x.id)}>
                {x.nm}
              </button>
            ))}
          </div>
          <ul className="checks">
            {ck.map(([s, t, d], i) => (
              <li key={i} className={s}>
                {ICO[s]}
                <span>
                  <b>{t}</b>
                  <small>{d}</small>
                </span>
              </li>
            ))}
          </ul>
        </Card>
        <Card pbi="HU-11" sprint="2">
          <div className="hd">
            <h2>Qué bloquea en la consola</h2>
          </div>
          <ul className="checks">
            {locks.map(([s, ic, t, d], i) => (
              <li key={i} className={s}>
                {ic}
                <span>
                  <b>{t}</b>
                  <small>{d}</small>
                </span>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </section>
  );
}

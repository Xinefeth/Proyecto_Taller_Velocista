// Vista Armador de robots (Protoripo.html): registra robots y versiones desde el catálogo,
// con costo/masa/consumo, compatibilidad y cumplimiento del reglamento.
// HU-06, HU-07, HU-08, HU-09, HU-10.
import { useEffect, useState } from "react";
import { useConsola, RANURAS } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { ICO, Chispa, Mas } from "../components/IconosUI";
import { TIPO } from "../datos/robots";
import { byId, checks, compat, curVer, facts } from "../logica/dominio";
import { clamp, clone, fmt, money } from "../logica/formato";
import type { Piezas, RobotDef } from "../types/dominio";

export function Armador() {
  const c = useConsola();
  const [abRobot, setAbRobot] = useState(c.armadorInicial ?? "v001");
  const [abView, setAbView] = useState<number | null>(null);
  const [abDraft, setAbDraft] = useState<Piezas | null>(null);

  useEffect(() => {
    if (c.armadorInicial) {
      setAbRobot(c.armadorInicial);
      setAbView(null);
      setAbDraft(null);
    }
  }, [c.armadorInicial]);

  const r = c.robots.find((x) => x.id === abRobot) ?? c.robots[0];
  const vi = abView == null ? r.ver.length - 1 : abView;
  const v = r.ver[vi];
  const isCur = vi === r.ver.length - 1;
  const parts = abDraft && isCur ? abDraft : v.parts;
  const f = facts(parts, c.catalog);
  const orig = v.parts;
  const dirty = !!abDraft && isCur && JSON.stringify(abDraft) !== JSON.stringify(v.parts);

  const edit = (fn: (d: Piezas) => void) => {
    const d: Piezas = abDraft ? { ...abDraft } : clone(v.parts);
    fn(d);
    setAbDraft(d);
  };

  const guardar = () => {
    if (!abDraft) return;
    const d = abDraft;
    const diff = RANURAS.filter((sl) => JSON.stringify(v.parts[sl.k] || null) !== JSON.stringify(d[sl.k] || null)).map((sl) => {
      const a = v.parts[sl.k] && byId(c.catalog, v.parts[sl.k]!.id);
      const b = d[sl.k] && byId(c.catalog, d[sl.k]!.id);
      return a && b && a.id === b.id ? `${sl.nm} ×${d[sl.k]!.q}` : `${sl.nm}: ${b ? b.nm : "sin pieza"}`;
    });
    const nvNum = parseInt(v.v.slice(1), 10) + 1;
    const estado = r.fw ? "Actual" : v.estado === "Borrador" ? "Borrador" : "Concepto";
    const nv = { v: "v" + nvNum, fecha: "hoy", nota: diff.join("; ") || "Cambio de piezas", estado, parts: d };
    c.setRobots((list) =>
      list.map((x) => {
        if (x.id !== r.id) return x;
        const ver = x.ver.map((vv, i) => (i === x.ver.length - 1 && vv.estado === "Actual" ? { ...vv, estado: "Anterior" } : vv));
        return { ...x, ver: [...ver, nv] };
      }),
    );
    setAbDraft(null);
    setAbView(null);
    c.registrar("Armador", `${r.nm} ${nv.v}: ${nv.nota}`, "good");
    c.mostrarToast(`${r.nm} ${nv.v} guardado. Las corridas nuevas se asignan a esta versión.`);
  };

  const nuevoRobot = () => {
    const n = c.robots.filter((x) => x.tipo === "velocista").length + 1;
    const id = "v" + String(n).padStart(3, "0");
    const nuevo: RobotDef = {
      id,
      nm: `Velocista ${String(n).padStart(3, "0")}`,
      short: String(n).padStart(3, "0"),
      tipo: "velocista",
      fw: null,
      ver: [{ v: "v1", fecha: "hoy", nota: "Borrador", estado: "Borrador", parts: {} }],
    };
    c.setRobots((list) => [...list, nuevo]);
    setAbRobot(id);
    setAbView(null);
    setAbDraft(null);
    c.mostrarToast("Robot creado: elige sus piezas del catálogo.");
  };

  const aut = f.bat && f.cur ? (Number(f.bat.s.mah) / (f.cur * 1000)) * 60 * 0.8 : null;
  const cp = compat(f);
  const nb = cp.filter((x) => x[0] === "bad").length;
  const nw = cp.filter((x) => x[0] === "warn").length;
  const ck = checks(f, c.perfil);
  const expo: string[] = [];
  if (f.sensores) expo.push(`Regleta de ${f.sensores} canales`);
  if (f.motores) expo.push(`${f.motores} motores (PWM)`);
  if (f.bat) expo.push("Voltaje de batería");
  if (f.enc) expo.push("Encoders");
  if (f.imu) expo.push("IMU");
  if (f.turb) expo.push("Turbina");
  if (f.radio !== "Ninguna") expo.push(`Arranque inalámbrico (${f.radio.split(" ")[0]})`);

  return (
    <section className="view on ab" aria-label="Armador">
      <div className="stack">
        <Card pbi="HU-06" sprint="1">
          <div className="hd">
            <h2>Robots</h2>
            <span className="tag">{c.robots.length}</span>
          </div>
          <div className="rlist">
            {c.robots.map((x) => (
              <button
                key={x.id}
                type="button"
                className="rli"
                aria-current={x.id === abRobot}
                onClick={() => {
                  setAbDraft(null);
                  setAbRobot(x.id);
                  setAbView(null);
                }}
              >
                <span className="ic">{x.tipo === "velocista" ? ICO.velo : ICO.sumo}</span>
                <b>{x.nm}</b>
                <small>
                  {TIPO[x.tipo]} · {curVer(x).v} · {curVer(x).estado}
                </small>
              </button>
            ))}
          </div>
          <button type="button" className="sb ghost" style={{ width: "100%", marginTop: 10 }} onClick={nuevoRobot}>
            <Mas />
            Nuevo robot
          </button>
        </Card>
      </div>

      <div className="stack">
        <Card pbi="HU-06" sprint="1">
          <div className="hd">
            <h2>{r.nm}</h2>
            <div className="vchips">
              {r.ver.map((x, i) => (
                <button
                  key={i}
                  type="button"
                  className={`tag ${i === vi ? "red" : ""}`}
                  onClick={() => {
                    if (i !== r.ver.length - 1) setAbDraft(null);
                    setAbView(i);
                  }}
                >
                  {x.v}
                  {i === r.ver.length - 1 ? " · actual" : ""}
                </button>
              ))}
            </div>
          </div>
          <p className="note" style={{ margin: "-4px 0 12px" }}>
            {TIPO[r.tipo]} · {v.nota} · {v.fecha !== "—" ? v.fecha + " · " : ""}
            {r.fw ? "firmware " + r.fw : "sin firmware"}
            {isCur ? "" : " · versión anterior: solo lectura"}
          </p>
          <div className="slothead">
            <span>Pieza</span>
            <span>Componente del catálogo</span>
            <span className="r">Cantidad</span>
            <span className="r">Subtotal</span>
            <span className="r">Masa</span>
          </div>
          <div className="slots">
            {RANURAS.map((sl) => {
              const p = parts[sl.k];
              const comp = p && byId(c.catalog, p.id);
              const chg = !!abDraft && isCur && JSON.stringify(orig[sl.k] || null) !== JSON.stringify(p || null);
              return (
                <div key={sl.k} className={`slot ${sl.opt ? "opt" : ""} ${chg ? "chg" : ""}`}>
                  <div className="sl">
                    {sl.nm}
                    <small>{sl.req ? "obligatorio" : sl.opt ? "opcional · según reglamento" : "opcional"}</small>
                  </div>
                  <select
                    className="inp"
                    disabled={!isCur}
                    aria-label={sl.nm}
                    value={p?.id ?? ""}
                    onChange={(e) =>
                      edit((d) => {
                        if (!e.target.value) delete d[sl.k];
                        else d[sl.k] = { id: e.target.value, q: d[sl.k] ? d[sl.k]!.q : sl.k === "motor" ? 2 : 1 };
                      })
                    }
                  >
                    <option value="">— Ninguno —</option>
                    {c.catalog
                      .filter((x) => x.t === sl.t)
                      .map((x) => (
                        <option key={x.id} value={x.id}>
                          {x.nm} · {money(x.precio)}
                        </option>
                      ))}
                  </select>
                  <div className="q">
                    {sl.q && p ? (
                      <>
                        <button type="button" disabled={!isCur} aria-label="Menos" onClick={() => edit((d) => (d[sl.k]!.q = clamp(d[sl.k]!.q - 1, 1, 4)))}>
                          −
                        </button>
                        <span>{p.q}</span>
                        <button type="button" disabled={!isCur} aria-label="Más" onClick={() => edit((d) => (d[sl.k]!.q = clamp(d[sl.k]!.q + 1, 1, 4)))}>
                          +
                        </button>
                      </>
                    ) : (
                      <span className="dimt">{p ? "×" + p.q : ""}</span>
                    )}
                  </div>
                  <div className="pr">{comp ? money(comp.precio * p!.q) : "—"}</div>
                  <div className="ms">{comp ? comp.masa * p!.q + " g" : "—"}</div>
                </div>
              );
            })}
          </div>
          {dirty && (
            <div className="unsaved">
              <span>Tienes cambios sin guardar en las piezas.</span>
              <span style={{ display: "flex", gap: 6 }}>
                <button type="button" className="sb ghost" onClick={() => setAbDraft(null)}>
                  Descartar
                </button>
                <button type="button" className="sb red" onClick={guardar}>
                  Guardar como nueva versión
                </button>
              </span>
            </div>
          )}
          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }} data-sprint="W">
            <button type="button" className="sb ghost" disabled title="Fuera de este curso (HU-12)">
              <Chispa />
              Sugerir piezas por objetivo
            </button>
          </div>
        </Card>

        <Card pbi="HU-09" sprint="2">
          <div className="hd">
            <h2>
              Versiones <small>comparación</small>
            </h2>
          </div>
          <div className="table">
            <table className="ct" style={{ minWidth: 640 }}>
              <thead>
                <tr>
                  <th>Versión</th>
                  <th>Cambio</th>
                  <th className="r">Costo</th>
                  <th className="r">Masa</th>
                  <th className="r">Corridas</th>
                  <th className="r">Mejor vuelta</th>
                  <th className="r">J medio</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {r.ver.map((x, i) => {
                  const fx = facts(x.parts, c.catalog);
                  const rr = c.runs.filter((z) => z.robot === r.id && z.ver === x.v);
                  const ft = rr.filter((z) => z.fin);
                  const bst = ft.length ? Math.min(...ft.map((z) => z.t!)) : null;
                  const jm = rr.length ? rr.reduce((a, z) => a + z.J, 0) / rr.length : null;
                  return (
                    <tr key={i} style={i === vi ? { background: "rgba(255,45,85,.05)" } : undefined}>
                      <td className="m">{x.v}</td>
                      <td className="sp">{x.nota}</td>
                      <td className="m r">{money(fx.cost)}</td>
                      <td className="m r">{Math.round(fx.mass)} g</td>
                      <td className="m r">{rr.length}</td>
                      <td className="m r">{bst != null ? fmt(bst, 3) : "—"}</td>
                      <td className="m r">{jm != null ? fmt(jm, 2) : "—"}</td>
                      <td>
                        <span className={`badge ${x.estado === "Actual" ? "good" : x.estado === "Descartada" || x.estado === "Anterior" ? "" : "warn"}`}>
                          {x.estado}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      <div className="stack">
        <Card pbi="HU-07" sprint="1">
          <div className="hd">
            <h2>Resumen</h2>
            <span className={`tag ${v.estado === "Actual" ? "good" : v.estado === "Concepto" || v.estado === "Borrador" ? "warn" : ""}`}>
              {v.estado}
            </span>
          </div>
          <div className="bigsum">
            <div>
              <div className="lbl">Costo total</div>
              <div className="v">{money(f.cost)}</div>
            </div>
            <div>
              <div className="lbl">Masa</div>
              <div className="v">
                {Math.round(f.mass)}
                <small> g</small>
              </div>
            </div>
            <div>
              <div className="lbl">Consumo estimado</div>
              <div className="v">
                {fmt(f.cur, 2)}
                <small> A</small>
              </div>
            </div>
            <div>
              <div className="lbl">Autonomía</div>
              <div className="v">
                {aut ? Math.round(aut) : "—"}
                <small> min</small>
              </div>
            </div>
            <div>
              <div className="lbl">Dimensiones</div>
              <div className="v" style={{ fontSize: 17 }}>
                {f.ancho ? `${f.ancho} × ${f.largo}` : "—"}
                <small> mm</small>
              </div>
            </div>
            <div>
              <div className="lbl">Sensores de línea</div>
              <div className="v">{f.sensores || "—"}</div>
            </div>
          </div>
          <div className="sub" style={{ marginTop: 12 }}>
            Lo que expone a la consola
          </div>
          <div className="expo">
            {expo.length ? (
              expo.map((x, i) => (
                <span key={i}>
                  <i />
                  {x}
                </span>
              ))
            ) : (
              <span className="dimt">Agrega piezas para ver qué expone.</span>
            )}
          </div>
          <button
            type="button"
            className="sb ghost"
            style={{ width: "100%", marginTop: 10 }}
            disabled={r.tipo !== "velocista"}
            onClick={() => c.abrirManifiesto(r.id)}
          >
            Ver manifiesto esperado
          </button>
        </Card>

        <Card pbi="HU-08" sprint="2">
          <div className="hd">
            <h2>Compatibilidad</h2>
            <span className={`tag ${nb ? "red" : nw ? "warn" : "good"}`}>
              {nb ? `${nb} error${nb > 1 ? "es" : ""}` : nw ? `${nw} aviso${nw > 1 ? "s" : ""}` : "Todo OK"}
            </span>
          </div>
          <ul className="checks">
            {cp.length ? (
              cp.map(([s, t, d], i) => (
                <li key={i} className={s}>
                  {ICO[s]}
                  <span>
                    <b>{t}</b>
                    <small>{d}</small>
                  </span>
                </li>
              ))
            ) : (
              <li className="ok">
                {ICO.ok}
                <span>
                  <b>Sin piezas que revisar</b>
                </span>
              </li>
            )}
          </ul>
        </Card>

        <Card pbi="HU-10" sprint="2">
          <div className="hd">
            <h2>Reglamento</h2>
            <button type="button" className={`tag ${ck.some((x) => x[0] === "bad") ? "red" : "good"}`} onClick={() => c.goTab("reglamento")}>
              {c.perfil.tag} · {c.perfil.cat}
            </button>
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
      </div>
    </section>
  );
}

// Ficha lateral de un componente (Protoripo.html, HU-03).
import { useConsola } from "../stores/ConsolaContext";
import { ICO, Cerrar } from "./IconosUI";
import { TIPOS } from "../datos/tipos";
import { byId, curVer } from "../logica/dominio";
import { money } from "../logica/formato";
import type { RobotDef } from "../types/dominio";

export function Drawer() {
  const c = useConsola();
  const comp = c.fichaId ? byId(c.catalog, c.fichaId) : null;
  const abierto = !!comp;
  const T = comp ? TIPOS[comp.t] : null;
  const usadoEn: { r: RobotDef; q: number }[] = comp
    ? c.robots
        .map((r) => {
          const p = Object.values(curVer(r).parts).find((x) => x && x.id === comp.id);
          return p ? { r, q: p.q } : null;
        })
        .filter((x): x is { r: RobotDef; q: number } => x != null)
    : [];
  const usadoQty = usadoEn.reduce((a, x) => a + x.q, 0);
  return (
    <aside className={`drawer ${abierto ? "on" : ""}`} aria-label="Ficha del componente" aria-hidden={!abierto}>
      {comp && T && (
        <>
          <div className="dh">
            <div>
              <span className="lbl">
                {T.nm} · {comp.id.toUpperCase()}
              </span>
              <h3>{comp.nm}</h3>
            </div>
            <button type="button" className="x" aria-label="Cerrar" onClick={c.cerrarFicha}>
              <Cerrar />
            </button>
          </div>
          <div className="db">
            <div className="kv">
              <div>
                <div className="lbl">Precio</div>
                <div className="v">{money(comp.precio)}</div>
              </div>
              <div>
                <div className="lbl">Masa</div>
                <div className="v">{comp.masa} g</div>
              </div>
              <div>
                <div className="lbl">En el club</div>
                <div className="v">
                  {comp.stock} <span className="dimt" style={{ fontSize: 12 }}>· {usadoQty} en robots</span>
                </div>
              </div>
              <div>
                <div className="lbl">Tienda</div>
                <div className="v" style={{ fontFamily: "var(--sans)", fontSize: 13 }}>
                  {comp.tienda}
                </div>
              </div>
            </div>
            <div>
              <div className="sub" style={{ border: 0, padding: 0, marginBottom: 6 }}>
                Especificaciones
              </div>
              <dl className="specs">
                {T.f.map(([k, l]) => (
                  <div key={k} style={{ display: "contents" }}>
                    <dt>{l}</dt>
                    <dd>{comp.s[k] ?? "—"}</dd>
                  </div>
                ))}
                {comp.i ? (
                  <div style={{ display: "contents" }}>
                    <dt>Consumo estimado</dt>
                    <dd>{comp.i} A</dd>
                  </div>
                ) : null}
              </dl>
            </div>
            {T.cap && (
              <div className="cap">
                {ICO.cap}
                <span>
                  Aporta a la consola: <b>{T.cap(comp.s)}</b>
                </span>
              </div>
            )}
            <div>
              <div className="sub" style={{ border: 0, padding: 0, marginBottom: 6 }}>
                Usado en
              </div>
              {usadoEn.length ? (
                usadoEn.map((x) => (
                  <div key={x.r.id} className="row" style={{ padding: "7px 0", borderBottom: "1px solid var(--line)" }}>
                    <span>
                      {x.r.nm} <span className="dimt m" style={{ fontSize: 11 }}>{curVer(x.r).v}</span>
                    </span>
                    <span className="m">×{x.q}</span>
                  </div>
                ))
              ) : (
                <p className="empty" style={{ margin: 0 }}>
                  Ningún robot lo usa todavía.
                </p>
              )}
            </div>
            <div className="card flat" data-pbi="HU-05" data-sprint="2" style={{ padding: "12px 14px" }}>
              <div className="hd" style={{ marginBottom: 6 }}>
                <h2 style={{ fontSize: 13 }}>Historial de precios</h2>
                <span className="tag">Desde enlace</span>
              </div>
              <p className="note" style={{ margin: 0 }}>
                Se llena al registrar o actualizar el componente desde el enlace de la tienda.
              </p>
            </div>
          </div>
        </>
      )}
    </aside>
  );
}

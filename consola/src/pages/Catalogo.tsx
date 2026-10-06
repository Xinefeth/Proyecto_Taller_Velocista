// Vista Catálogo (Protoripo.html): componentes con specs, precios e inventario del club.
// HU-01 a HU-05, EN-17.
import { useState, type CSSProperties } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { Buscar, Mas } from "../components/IconosUI";
import { TIPOS, ORDEN_TIPOS } from "../datos/tipos";
import { curVer } from "../logica/dominio";
import { money } from "../logica/formato";
import type { Componente, RobotDef } from "../types/dominio";

const tchip = (t: string) => (
  <span className="tchip" style={{ "--tc": TIPOS[t].c } as CSSProperties}>
    <i />
    {TIPOS[t].nm}
  </span>
);

export function Catalogo() {
  const c = useConsola();
  const [tabCat, setTabCat] = useState<"comp" | "inv">("comp");
  const [catType, setCatType] = useState("all");
  const [q, setQ] = useState("");

  const usedIn = (id: string): { r: RobotDef; q: number }[] =>
    c.robots
      .map((r) => {
        const p = Object.values(curVer(r).parts).find((x) => x && x.id === id);
        return p ? { r, q: p.q } : null;
      })
      .filter((x): x is { r: RobotDef; q: number } => x != null);
  const usedQty = (id: string) => usedIn(id).reduce((a, x) => a + x.q, 0);

  const counts: Record<string, number> = {};
  c.catalog.forEach((x) => (counts[x.t] = (counts[x.t] || 0) + 1));
  const ql = q.toLowerCase();
  const lista: Componente[] = c.catalog
    .filter(
      (x) =>
        (catType === "all" || x.t === catType) &&
        (!ql ||
          `${x.nm} ${TIPOS[x.t].nm} ${TIPOS[x.t].sum(x.s)} ${x.tienda}`.toLowerCase().includes(ql)),
    )
    .sort(
      (a, b) => ORDEN_TIPOS.indexOf(a.t) - ORDEN_TIPOS.indexOf(b.t) || a.nm.localeCompare(b.nm),
    );

  let miss = 0;
  c.catalog.forEach((x) => {
    if (x.stock - usedQty(x.id) < 0) miss++;
  });

  return (
    <section className="view on dv" aria-label="Catálogo">
      <div className="s12">
        <div className="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={tabCat === "comp"}
            onClick={() => setTabCat("comp")}
          >
            Componentes
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={tabCat === "inv"}
            onClick={() => setTabCat("inv")}
          >
            Inventario del club
          </button>
        </div>
      </div>

      <Card
        className="s12"
        pbi="HU-01 · HU-03"
        sprint="1"
        {...(tabCat !== "comp" ? { hidden: true } : {})}
      >
        <div className="bar2">
          <label className="search">
            <Buscar />
            <input
              className="inp"
              placeholder="Buscar por nombre, tipo o especificación"
              aria-label="Buscar componentes"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </label>
          <div className="spacer" />
          <button type="button" className="sb red" onClick={c.abrirRegistro}>
            <Mas />
            Registrar componente
          </button>
        </div>
        <div className="chips" style={{ marginBottom: 12 }}>
          <button type="button" aria-pressed={catType === "all"} onClick={() => setCatType("all")}>
            Todos <small>{c.catalog.length}</small>
          </button>
          {ORDEN_TIPOS.filter((t) => counts[t]).map((t) => (
            <button
              key={t}
              type="button"
              aria-pressed={catType === t}
              onClick={() => setCatType(t)}
            >
              {TIPOS[t].nm} <small>{counts[t]}</small>
            </button>
          ))}
        </div>
        <div className="table">
          <table className="ct">
            <thead>
              <tr>
                <th>Componente</th>
                <th>Tipo</th>
                <th>Especificaciones clave</th>
                <th className="r">Precio</th>
                <th className="r">Masa</th>
                <th>Tienda</th>
                <th className="r">Club</th>
                <th>En uso</th>
              </tr>
            </thead>
            <tbody>
              {!lista.length ? (
                <tr>
                  <td colSpan={8} className="empty" style={{ padding: "18px 10px" }}>
                    Nada coincide con “{q}”.
                  </td>
                </tr>
              ) : (
                lista.map((x) => {
                  const u = usedIn(x.id);
                  const st = x.stock === 0 ? "zero" : x.stock <= 1 ? "low" : "";
                  return (
                    <tr
                      key={x.id}
                      tabIndex={0}
                      onClick={() => c.abrirFicha(x.id)}
                      onKeyDown={(e) => e.key === "Enter" && c.abrirFicha(x.id)}
                    >
                      <td className="nm">
                        <b>{x.nm}</b>
                        <small>{x.id.toUpperCase()}</small>
                      </td>
                      <td>{tchip(x.t)}</td>
                      <td className="sp">{TIPOS[x.t].sum(x.s)}</td>
                      <td className="m r">{money(x.precio)}</td>
                      <td className="m r">{x.masa} g</td>
                      <td className="sp">{x.tienda}</td>
                      <td className="r">
                        <span className={`stock ${st}`}>{x.stock}</span>
                      </td>
                      <td className="sp">
                        {u.length ? (
                          u.map((z) => z.r.nm).join(", ")
                        ) : (
                          <span className="dimt">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <p className="note">{`${lista.length} de ${c.catalog.length} componentes · precios en soles, por unidad`}</p>
      </Card>

      <Card
        className="s12"
        pbi="HU-04 · EN-17"
        sprint="1"
        {...(tabCat !== "inv" ? { hidden: true } : {})}
      >
        <div className="hd">
          <h2>Inventario del club</h2>
          <span className={`tag ${miss ? "warn" : "good"}`}>
            {miss ? `${miss} por comprar` : "Completo"}
          </span>
        </div>
        <div className="table">
          <table className="ct">
            <thead>
              <tr>
                <th>Componente</th>
                <th>Tipo</th>
                <th className="r">En el club</th>
                <th className="r">En robots</th>
                <th className="r">Disponible</th>
                <th>Estado</th>
                <th>Usado en</th>
              </tr>
            </thead>
            <tbody>
              {c.catalog.map((x) => {
                const u = usedQty(x.id);
                const d = x.stock - u;
                const est =
                  d < 0 ? (
                    <span className="badge bad">Faltan {-d}</span>
                  ) : d === 0 && u ? (
                    <span className="badge warn">Todo en uso</span>
                  ) : (
                    <span className="badge good">Disponible</span>
                  );
                return (
                  <tr key={x.id} onClick={() => c.abrirFicha(x.id)} style={{ cursor: "pointer" }}>
                    <td className="nm">
                      <b>{x.nm}</b>
                    </td>
                    <td>{tchip(x.t)}</td>
                    <td className="m r">{x.stock}</td>
                    <td className="m r">{u}</td>
                    <td className="m r" style={{ color: d < 0 ? "var(--red-hi)" : "" }}>
                      {d}
                    </td>
                    <td>{est}</td>
                    <td className="sp">
                      {usedIn(x.id)
                        .map((z) => `${z.r.nm} ×${z.q}`)
                        .join(", ") || <span className="dimt">—</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="note">
          Las cantidades “en robots” salen de la versión actual de cada robot del armador.
        </p>
      </Card>
    </section>
  );
}

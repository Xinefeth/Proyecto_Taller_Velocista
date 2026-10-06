// Modal para registrar un componente, manual (HU-02) o desde enlace (HU-05). Del prototipo.
import { useEffect, useState } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Cerrar, ICO } from "./IconosUI";
import { TIPOS } from "../datos/tipos";
import type { Specs } from "../types/dominio";
import { PbiChip } from "./Card";

export function RegistroModal() {
  const c = useConsola();
  const [rt, setRt] = useState<"manual" | "link">("manual");
  const [tipo, setTipo] = useState("linea");
  const [nombre, setNombre] = useState("");
  const [precio, setPrecio] = useState("");
  const [masa, setMasa] = useState("");
  const [stock, setStock] = useState("0");
  const [tienda, setTienda] = useState("");
  const [link, setLink] = useState("");
  const [specs, setSpecs] = useState<Record<string, string>>({});
  const [err, setErr] = useState("");
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (c.regOpen) {
      setRt("manual");
      setTipo("linea");
      setNombre("");
      setPrecio("");
      setMasa("");
      setStock("0");
      setTienda("");
      setLink("");
      setSpecs({});
      setErr("");
    }
  }, [c.regOpen]);

  const T = TIPOS[tipo];
  const specVals = (): Specs => {
    const o: Specs = {};
    T.f.forEach(([k, , ty]) => {
      const raw = specs[k] ?? "";
      o[k] = ty === "n" && raw !== "" && !isNaN(+raw.replace(",", ".")) ? +raw.replace(",", ".") : raw;
    });
    return o;
  };
  const cap = T.cap ? (
    <>
      {ICO.cap}
      <span>
        Aporta a la consola: <b>{T.cap(specVals())}</b>
      </span>
    </>
  ) : (
    <>
      {ICO.info}
      <span>Este tipo no agrega paneles a la consola.</span>
    </>
  );

  const extraer = () => {
    setFetching(true);
    setLink((l) => l || "https://tienda.ejemplo/producto/qtr-hd-15a");
    setTimeout(() => {
      setFetching(false);
      setTipo("linea");
      setNombre("Pololu QTR-HD-15A");
      setPrecio("71.50");
      setMasa("2");
      setTienda("Importación");
      setSpecs({ canales: "15", salida: "Analógica", paso: "4", i: "0.1" });
      c.mostrarToast("Datos extraídos: revísalos antes de guardar.");
    }, 900);
  };

  const guardar = () => {
    const nm = nombre.trim();
    const pr = parseFloat(precio.replace(",", "."));
    const ms = parseFloat(masa.replace(",", "."));
    const st = parseInt(stock, 10) || 0;
    if (!nm) return setErr("Escribe el nombre del componente.");
    if (!(pr > 0)) return setErr("El precio debe ser mayor que 0.");
    if (!(ms >= 0)) return setErr("Escribe la masa en gramos.");
    const s = specVals();
    const id = "c" + String(c.catalog.length + 2).padStart(2, "0");
    c.setCatalog((list) => [...list, { id, t: tipo, nm, precio: pr, masa: ms, tienda: tienda.trim() || "—", stock: st, s, i: Number(s.i) || 0 }]);
    c.cerrarRegistro();
    c.registrar("Catálogo", `Registrado: ${nm}`, "good");
    c.mostrarToast(`${nm} quedó en el catálogo.`);
  };

  if (!c.regOpen) return <div className="modal" role="dialog" aria-hidden="true" aria-label="Registrar componente" />;

  return (
    <div className="modal on" role="dialog" aria-modal="true" aria-label="Registrar componente">
      <div className="dh">
        <div>
          <span className="lbl">Catálogo</span>
          <h3>Registrar componente</h3>
        </div>
        <button type="button" className="x" aria-label="Cerrar" onClick={c.cerrarRegistro}>
          <Cerrar />
        </button>
      </div>
      <div className="mb">
        <div className="tabs" role="tablist" style={{ margin: 0 }}>
          <button type="button" role="tab" aria-selected={rt === "manual"} onClick={() => setRt("manual")}>
            Manual <PbiChip pbi="HU-02" sprint="1" inl />
          </button>
          <button type="button" role="tab" aria-selected={rt === "link"} onClick={() => setRt("link")} data-sprint="2">
            Desde enlace <PbiChip pbi="HU-05" sprint="2" inl />
          </button>
        </div>
        {rt === "link" && (
          <div>
            <div className="fld">
              <span className="lbl">Enlace de la tienda</span>
              <div style={{ display: "flex", gap: 6 }}>
                <input className="inp" placeholder="https://…/producto/qtr-8a" value={link} onChange={(e) => setLink(e.target.value)} />
                <button type="button" className="sb" onClick={extraer}>
                  {fetching ? "Extrayendo…" : "Extraer datos"}
                </button>
              </div>
            </div>
            <p className="note">Se extraen nombre, precio y especificaciones; revisa los datos antes de guardar.</p>
          </div>
        )}
        <div className="g2">
          <label className="fld">
            <span className="lbl">Tipo</span>
            <select className="inp" value={tipo} onChange={(e) => { setTipo(e.target.value); setSpecs({}); }}>
              {Object.entries(TIPOS).map(([k, v]) => (
                <option key={k} value={k}>
                  {v.nm}
                </option>
              ))}
            </select>
          </label>
          <label className="fld">
            <span className="lbl">Nombre</span>
            <input className="inp" placeholder="Ej. Pololu QTR-8A" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </label>
        </div>
        <div className="g3">
          <label className="fld">
            <span className="lbl">Precio (S/)</span>
            <input className="inp m" inputMode="decimal" placeholder="0.00" value={precio} onChange={(e) => setPrecio(e.target.value)} />
          </label>
          <label className="fld">
            <span className="lbl">Masa (g)</span>
            <input className="inp m" inputMode="decimal" placeholder="0" value={masa} onChange={(e) => setMasa(e.target.value)} />
          </label>
          <label className="fld">
            <span className="lbl">En el club</span>
            <input className="inp m" inputMode="numeric" value={stock} onChange={(e) => setStock(e.target.value)} />
          </label>
        </div>
        <label className="fld">
          <span className="lbl">Tienda</span>
          <input className="inp" placeholder="Proveedor local (Trujillo)" value={tienda} onChange={(e) => setTienda(e.target.value)} />
        </label>
        <div className="sub">Especificaciones del tipo</div>
        <div className="g2">
          {T.f.map(([k, l, ty]) => (
            <label className="fld" key={k}>
              <span className="lbl">{l}</span>
              <input
                className={`inp${ty === "n" ? " m" : ""}`}
                inputMode={ty === "n" ? "decimal" : undefined}
                value={specs[k] ?? ""}
                onChange={(e) => setSpecs((o) => ({ ...o, [k]: e.target.value }))}
              />
            </label>
          ))}
        </div>
        <div className="cap">{cap}</div>
        <p className="hint warn">{err}</p>
      </div>
      <div className="mf">
        <button type="button" className="sb ghost" onClick={c.cerrarRegistro}>
          Cancelar
        </button>
        <button type="button" className="sb red" onClick={guardar}>
          Guardar en el catálogo
        </button>
      </div>
    </div>
  );
}

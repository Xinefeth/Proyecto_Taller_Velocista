// Vista Catálogo (Protoripo.html): componentes con specs, precios e inventario del club.
// HU-01 a HU-05, EN-17. Usa los componentes comunes de gestión (EN-06).
import { useMemo, useState, type CSSProperties } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { Mas } from "../components/IconosUI";
import {
  Buscador,
  ChipsFiltro,
  Pestanas,
  TablaDatos,
  useFiltroLista,
  type Columna,
} from "../components/gestion";
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

const PESTANAS = [
  { id: "comp", etiqueta: "Componentes" },
  { id: "inv", etiqueta: "Inventario del club" },
];

// Funciones estables (fuera del componente) para que el filtro no se recalcule en cada render.
const textoBuscable = (x: Componente) =>
  `${x.nm} ${TIPOS[x.t].nm} ${TIPOS[x.t].sum(x.s)} ${x.tienda}`;
const categoriaDe = (x: Componente) => x.t;
const porTipoYNombre = (a: Componente, b: Componente) =>
  ORDEN_TIPOS.indexOf(a.t) - ORDEN_TIPOS.indexOf(b.t) || a.nm.localeCompare(b.nm);

export function Catalogo() {
  const c = useConsola();
  const [tabCat, setTabCat] = useState("comp");

  const ordenado = useMemo(() => [...c.catalog].sort(porTipoYNombre), [c.catalog]);
  const filtro = useFiltroLista(ordenado, { texto: textoBuscable, categoria: categoriaDe });
  const lista = filtro.filtradas;

  const usedIn = (id: string): { r: RobotDef; q: number }[] =>
    c.robots
      .map((r) => {
        const p = Object.values(curVer(r).parts).find((x) => x && x.id === id);
        return p ? { r, q: p.q } : null;
      })
      .filter((x): x is { r: RobotDef; q: number } => x != null);
  const usedQty = (id: string) => usedIn(id).reduce((a, x) => a + x.q, 0);
  const sinUso = <span className="dimt">—</span>;

  let miss = 0;
  c.catalog.forEach((x) => {
    if (x.stock - usedQty(x.id) < 0) miss++;
  });

  const columnasLista: Columna<Componente>[] = [
    {
      id: "nombre",
      encabezado: "Componente",
      clase: "nm",
      celda: (x) => (
        <>
          <b>{x.nm}</b>
          <small>{x.id.toUpperCase()}</small>
        </>
      ),
    },
    { id: "tipo", encabezado: "Tipo", celda: (x) => tchip(x.t) },
    {
      id: "specs",
      encabezado: "Especificaciones clave",
      clase: "sp",
      celda: (x) => TIPOS[x.t].sum(x.s),
    },
    {
      id: "precio",
      encabezado: "Precio",
      clase: "m",
      derecha: true,
      celda: (x) => money(x.precio),
    },
    { id: "masa", encabezado: "Masa", clase: "m", derecha: true, celda: (x) => `${x.masa} g` },
    { id: "tienda", encabezado: "Tienda", clase: "sp", celda: (x) => x.tienda },
    {
      id: "club",
      encabezado: "Club",
      derecha: true,
      celda: (x) => (
        <span className={`stock ${x.stock === 0 ? "zero" : x.stock <= 1 ? "low" : ""}`}>
          {x.stock}
        </span>
      ),
    },
    {
      id: "enUso",
      encabezado: "En uso",
      clase: "sp",
      celda: (x) => {
        const u = usedIn(x.id);
        return u.length ? u.map((z) => z.r.nm).join(", ") : sinUso;
      },
    },
  ];

  const columnasInventario: Columna<Componente>[] = [
    {
      id: "nombre",
      encabezado: "Componente",
      clase: "nm",
      celda: (x) => <b>{x.nm}</b>,
    },
    { id: "tipo", encabezado: "Tipo", celda: (x) => tchip(x.t) },
    { id: "club", encabezado: "En el club", clase: "m", derecha: true, celda: (x) => x.stock },
    {
      id: "enRobots",
      encabezado: "En robots",
      clase: "m",
      derecha: true,
      celda: (x) => usedQty(x.id),
    },
    {
      id: "disponible",
      encabezado: "Disponible",
      clase: "m",
      derecha: true,
      celda: (x) => {
        const d = x.stock - usedQty(x.id);
        return <span style={{ color: d < 0 ? "var(--red-hi)" : "" }}>{d}</span>;
      },
    },
    {
      id: "estado",
      encabezado: "Estado",
      celda: (x) => {
        const u = usedQty(x.id);
        const d = x.stock - u;
        return d < 0 ? (
          <span className="badge bad">Faltan {-d}</span>
        ) : d === 0 && u ? (
          <span className="badge warn">Todo en uso</span>
        ) : (
          <span className="badge good">Disponible</span>
        );
      },
    },
    {
      id: "usadoEn",
      encabezado: "Usado en",
      clase: "sp",
      celda: (x) =>
        usedIn(x.id)
          .map((z) => `${z.r.nm} ×${z.q}`)
          .join(", ") || sinUso,
    },
  ];

  return (
    <section className="view on dv" aria-label="Catálogo">
      <div className="s12">
        <Pestanas
          pestanas={PESTANAS}
          activa={tabCat}
          alCambiar={setTabCat}
          etiqueta="Secciones del catálogo"
        />
      </div>

      <Card
        className="s12"
        pbi="HU-01 · HU-03"
        sprint="1"
        {...(tabCat !== "comp" ? { hidden: true } : {})}
      >
        <div className="bar2">
          <Buscador
            valor={filtro.consulta}
            alCambiar={filtro.setConsulta}
            marcador="Buscar por nombre, tipo o especificación"
            etiqueta="Buscar componentes"
          />
          <div className="spacer" />
          <button type="button" className="sb red" onClick={c.abrirRegistro}>
            <Mas />
            Registrar componente
          </button>
        </div>
        <ChipsFiltro
          etiqueta="Filtrar por tipo"
          valor={filtro.categoria}
          alCambiar={filtro.setCategoria}
          cantidadTodos={c.catalog.length}
          opciones={ORDEN_TIPOS.filter((t) => filtro.conteos[t]).map((t) => ({
            valor: t,
            etiqueta: TIPOS[t].nm,
            cantidad: filtro.conteos[t],
          }))}
          style={{ marginBottom: 12 }}
        />
        <TablaDatos
          etiqueta="Componentes del catálogo"
          columnas={columnasLista}
          filas={lista}
          clave={(x) => x.id}
          alHacerClic={(x) => c.abrirFicha(x.id)}
          vacio={`Nada coincide con “${filtro.consulta}”.`}
        />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 10,
          }}
        >
          <p className="note">{`${lista.length} de ${c.catalog.length} componentes · precios en soles, por unidad`}</p>
          <button
            type="button"
            className="sb ghost"
            title="Borra lo que registraste a mano y vuelve a los datos de ejemplo"
            onClick={() => {
              if (
                window.confirm(
                  "Se borrarán los componentes y robots que registraste y se volverá a los datos de ejemplo. ¿Continuar?",
                )
              )
                c.restablecerDatos();
            }}
          >
            Restablecer datos de ejemplo
          </button>
        </div>
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
        <TablaDatos
          etiqueta="Inventario del club"
          columnas={columnasInventario}
          filas={c.catalog}
          clave={(x) => x.id}
          alHacerClic={(x) => c.abrirFicha(x.id)}
        />
        <p className="note">
          Las cantidades “en robots” salen de la versión actual de cada robot del armador.
        </p>
      </Card>
    </section>
  );
}

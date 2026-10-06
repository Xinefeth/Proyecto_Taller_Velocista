// Modal para registrar un componente, manual (HU-02) o desde enlace (HU-05). Del prototipo.
// Los campos se dibujan con los componentes comunes de gestión (EN-06) y se validan con validarCampos.
import { useEffect, useMemo, useState } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Cerrar, ICO } from "./IconosUI";
import { TIPOS } from "../datos/tipos";
import type { Specs } from "../types/dominio";
import { PbiChip } from "./Card";
import { siguienteIdComponente } from "../logica/dominio";
import {
  FormularioDinamico,
  Pestanas,
  normalizar,
  parsearNumero,
  validarCampos,
  type DefCampo,
  type Valores,
} from "./gestion";

const CAMPOS_BASICOS: DefCampo[] = [
  {
    nombre: "tipo",
    etiqueta: "Tipo",
    tipo: "seleccion",
    opciones: Object.entries(TIPOS).map(([k, v]) => ({ valor: k, etiqueta: v.nm })),
  },
  {
    nombre: "nombre",
    etiqueta: "Nombre",
    tipo: "texto",
    requerido: true,
    marcador: "Ej. Pololu QTR-8A",
    mensajes: { obligatorio: "Escribe el nombre del componente." },
  },
];

const CAMPOS_NUMEROS: DefCampo[] = [
  {
    nombre: "precio",
    etiqueta: "Precio (S/)",
    tipo: "numero",
    requerido: true,
    minExclusivo: 0,
    marcador: "0.00",
    mensajes: {
      obligatorio: "El precio debe ser mayor que 0.",
      minimo: "El precio debe ser mayor que 0.",
    },
  },
  {
    nombre: "masa",
    etiqueta: "Masa (g)",
    tipo: "numero",
    requerido: true,
    min: 0,
    marcador: "0",
    mensajes: { obligatorio: "Escribe la masa en gramos." },
  },
  { nombre: "stock", etiqueta: "En el club", tipo: "numero", entero: true, min: 0 },
];

const CAMPO_TIENDA: DefCampo[] = [
  { nombre: "tienda", etiqueta: "Tienda", tipo: "texto", marcador: "Proveedor local (Trujillo)" },
];

const INICIAL: Valores = {
  tipo: "linea",
  nombre: "",
  precio: "",
  masa: "",
  stock: "0",
  tienda: "",
};

const PESTANAS_REGISTRO = [
  {
    id: "manual",
    etiqueta: (
      <>
        Manual <PbiChip pbi="HU-02" sprint="1" inl />
      </>
    ),
  },
  {
    id: "link",
    sprint: "2",
    etiqueta: (
      <>
        Desde enlace <PbiChip pbi="HU-05" sprint="2" inl />
      </>
    ),
  },
];

export function RegistroModal() {
  const c = useConsola();
  const [rt, setRt] = useState("manual");
  const [valores, setValores] = useState<Valores>(INICIAL);
  const [link, setLink] = useState("");
  const [errores, setErrores] = useState<Record<string, string>>({});
  const [aviso, setAviso] = useState("");
  const [fetching, setFetching] = useState(false);

  useEffect(() => {
    if (c.regOpen) {
      setRt("manual");
      setValores(INICIAL);
      setLink("");
      setErrores({});
      setAviso("");
    }
  }, [c.regOpen]);

  const T = TIPOS[valores.tipo];
  // Los campos de especificaciones cambian según el tipo (HU-02). Son opcionales; si se llenan
  // las cifras, deben ser números válidos (unidades en la etiqueta).
  const camposSpecs = useMemo<DefCampo[]>(
    () =>
      T.f.map(([k, etiqueta, ty]) => ({
        nombre: `spec_${k}`,
        etiqueta,
        tipo: ty === "n" ? "numero" : "texto",
        min: ty === "n" ? 0 : undefined,
      })),
    [T],
  );

  const cambiar = (nombre: string, valor: string) => {
    if (nombre === "tipo") {
      // Al cambiar de tipo se limpian las especificaciones del tipo anterior.
      setValores((v) => {
        const resto = Object.fromEntries(Object.entries(v).filter(([k]) => !k.startsWith("spec_")));
        return { ...resto, tipo: valor };
      });
      setErrores((e) =>
        Object.fromEntries(Object.entries(e).filter(([k]) => !k.startsWith("spec_"))),
      );
      return;
    }
    setValores((v) => ({ ...v, [nombre]: valor }));
    setErrores((e) => {
      if (!e[nombre]) return e;
      return Object.fromEntries(Object.entries(e).filter(([k]) => k !== nombre));
    });
  };

  const specVals = (): Specs => {
    const o: Specs = {};
    T.f.forEach(([k, , ty]) => {
      const raw = valores[`spec_${k}`] ?? "";
      const n = ty === "n" ? parsearNumero(raw) : null;
      o[k] = n !== null ? n : raw;
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
      setValores({
        tipo: "linea",
        nombre: "Pololu QTR-HD-15A",
        precio: "71.50",
        masa: "2",
        stock: "0",
        tienda: "Importación",
        spec_canales: "15",
        spec_salida: "Analógica",
        spec_paso: "4",
        spec_i: "0.1",
      });
      setErrores({});
      c.mostrarToast("Datos extraídos: revísalos antes de guardar.");
    }, 900);
  };

  const guardar = () => {
    const nuevos = validarCampos(
      [...CAMPOS_BASICOS, ...CAMPOS_NUMEROS, ...CAMPO_TIENDA, ...camposSpecs],
      valores,
    );
    setErrores(nuevos);
    if (Object.keys(nuevos).length > 0) {
      setAviso("Revisa los campos marcados antes de guardar.");
      return;
    }
    const nm = valores.nombre.trim();
    // Un mismo componente no se registra dos veces: evita duplicar el catálogo y el inventario.
    if (c.catalog.some((x) => x.t === valores.tipo && normalizar(x.nm) === normalizar(nm))) {
      setErrores({ nombre: "Ya existe un componente con ese nombre en este tipo." });
      setAviso("Revisa los campos marcados antes de guardar.");
      return;
    }
    const s = specVals();
    const id = siguienteIdComponente(c.catalog);
    c.setCatalog((list) => [
      ...list,
      {
        id,
        t: valores.tipo,
        nm,
        precio: parsearNumero(valores.precio) ?? 0,
        masa: parsearNumero(valores.masa) ?? 0,
        tienda: valores.tienda.trim() || "—",
        stock: parsearNumero(valores.stock) ?? 0,
        s,
        i: Number(s.i) || 0,
      },
    ]);
    c.cerrarRegistro();
    c.registrar("Catálogo", `Registrado: ${nm}`, "good");
    c.mostrarToast(`${nm} quedó en el catálogo.`);
  };

  if (!c.regOpen)
    return (
      <div className="modal" role="dialog" aria-hidden="true" aria-label="Registrar componente" />
    );

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
        <Pestanas
          pestanas={PESTANAS_REGISTRO}
          activa={rt}
          alCambiar={setRt}
          etiqueta="Forma de registro"
          style={{ margin: 0 }}
        />
        {rt === "link" && (
          <div>
            <div className="fld">
              <span className="lbl">Enlace de la tienda</span>
              <div style={{ display: "flex", gap: 6 }}>
                <input
                  className="inp"
                  placeholder="https://…/producto/qtr-8a"
                  aria-label="Enlace de la tienda"
                  value={link}
                  onChange={(e) => setLink(e.target.value)}
                />
                <button type="button" className="sb" onClick={extraer}>
                  {fetching ? "Extrayendo…" : "Extraer datos"}
                </button>
              </div>
            </div>
            <p className="note">
              Se extraen nombre, precio y especificaciones; revisa los datos antes de guardar.
            </p>
          </div>
        )}
        <FormularioDinamico
          campos={CAMPOS_BASICOS}
          valores={valores}
          errores={errores}
          alCambiar={cambiar}
          columnas={2}
        />
        <FormularioDinamico
          campos={CAMPOS_NUMEROS}
          valores={valores}
          errores={errores}
          alCambiar={cambiar}
          columnas={3}
        />
        <FormularioDinamico
          campos={CAMPO_TIENDA}
          valores={valores}
          errores={errores}
          alCambiar={cambiar}
          columnas={1}
        />
        <div className="sub">Especificaciones del tipo</div>
        <FormularioDinamico
          campos={camposSpecs}
          valores={valores}
          errores={errores}
          alCambiar={cambiar}
          columnas={2}
        />
        <div className="cap">{cap}</div>
        <p className="hint warn" role="status">
          {aviso}
        </p>
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

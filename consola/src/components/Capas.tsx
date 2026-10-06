// Capa de fondo (scrim) y modales de la consola: ficha, registro y manifiesto. Del prototipo.
import { useEffect } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Drawer } from "./Drawer";
import { RegistroModal } from "./RegistroModal";
import { ManifiestoModal } from "./ManifiestoModal";

export function Capas() {
  const c = useConsola();
  const alguna = !!c.fichaId || c.regOpen || !!c.manifiestoId;
  const cerrar = () => {
    c.cerrarFicha();
    c.cerrarRegistro();
    c.cerrarManifiesto();
  };
  useEffect(() => {
    if (!alguna) return;
    const esc = (e: KeyboardEvent) => e.key === "Escape" && cerrar();
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alguna]);
  return (
    <>
      <div className={`scrim ${alguna ? "on" : ""}`} onClick={cerrar} />
      <Drawer />
      <RegistroModal />
      <ManifiestoModal />
    </>
  );
}

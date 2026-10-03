// Estado compartido de la conexión: salud de la API y tiempo real.
import { createContext, useContext, type ReactNode } from "react";
import { useSalud } from "../hooks/useSalud";
import { useTiempoReal } from "../hooks/useTiempoReal";
import type { EstadoConexion, Salud } from "../types/api";
import type { MensajeConsola } from "../types/mensajes";

interface Conexion {
  salud: Salud | null;
  api: EstadoConexion;
  baseDeDatos: EstadoConexion;
  tiempoReal: EstadoConexion;
  mensajes: MensajeConsola[];
}

const Contexto = createContext<Conexion | null>(null);

export function ProveedorConexion({ children }: { children: ReactNode }) {
  const { salud, estado } = useSalud();
  const { conectado, mensajes } = useTiempoReal();
  const baseDeDatos: EstadoConexion =
    estado === "revisando" ? "revisando" : salud?.base_de_datos === "ok" ? "ok" : "falla";
  const valor: Conexion = {
    salud,
    api: estado,
    baseDeDatos,
    tiempoReal: conectado === null ? "revisando" : conectado ? "ok" : "falla",
    mensajes,
  };
  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useConexion(): Conexion {
  const c = useContext(Contexto);
  if (!c) throw new Error("useConexion debe usarse dentro de ProveedorConexion");
  return c;
}

import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { EstadoConexion, Salud } from "../types/api";

export const INTERVALO_SALUD_MS = 5000;

/** Consulta /api/salud al montar y cada INTERVALO_SALUD_MS. */
export function useSalud(): { salud: Salud | null; estado: EstadoConexion } {
  const [salud, setSalud] = useState<Salud | null>(null);
  const [estado, setEstado] = useState<EstadoConexion>("revisando");

  useEffect(() => {
    let vivo = true;
    const consultar = () =>
      api
        .salud()
        .then((s) => vivo && (setSalud(s), setEstado("ok")))
        .catch(() => vivo && (setSalud(null), setEstado("falla")));
    consultar();
    const id = setInterval(consultar, INTERVALO_SALUD_MS);
    return () => {
      vivo = false;
      clearInterval(id);
    };
  }, []);

  return { salud, estado };
}

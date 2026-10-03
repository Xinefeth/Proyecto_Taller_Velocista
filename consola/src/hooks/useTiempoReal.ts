import { useEffect, useState } from "react";
import { escucharConsola } from "../services/ws";
import type { MensajeConsola } from "../types/mensajes";

export const MAX_MENSAJES = 50;

/** Mantiene la conexión con /ws/consola y los últimos mensajes recibidos. */
export function useTiempoReal(): { conectado: boolean | null; mensajes: MensajeConsola[] } {
  const [conectado, setConectado] = useState<boolean | null>(null);
  const [mensajes, setMensajes] = useState<MensajeConsola[]>([]);

  useEffect(() => {
    const s = escucharConsola(
      (m) => setMensajes((prev) => [m, ...prev].slice(0, MAX_MENSAJES)),
      setConectado,
    );
    return () => s.cerrar();
  }, []);

  return { conectado, mensajes };
}

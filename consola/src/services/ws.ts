// Única capa que abre conexiones WebSocket (DO-02, sección 6). La consola solo escucha.
import type { MensajeConsola } from "../types/mensajes";

export const REINTENTO_MS = 3000;

export function urlConsola(loc: Pick<Location, "protocol" | "host">): string {
  return `${loc.protocol === "https:" ? "wss:" : "ws:"}//${loc.host}/ws/consola`;
}

export interface Suscripcion {
  cerrar: () => void;
}

/** Se conecta a /ws/consola y se reconecta sola cada REINTENTO_MS mientras no se cierre. */
export function escucharConsola(
  alMensaje: (m: MensajeConsola) => void,
  alCambiarEstado: (conectado: boolean) => void,
): Suscripcion {
  let cerrado = false;
  let socket: WebSocket | null = null;
  let reintento: ReturnType<typeof setTimeout> | undefined;

  const conectar = () => {
    socket = new WebSocket(urlConsola(window.location));
    socket.onopen = () => alCambiarEstado(true);
    socket.onclose = () => {
      alCambiarEstado(false);
      if (!cerrado) reintento = setTimeout(conectar, REINTENTO_MS);
    };
    socket.onmessage = (e) => {
      try {
        alMensaje(JSON.parse(e.data as string) as MensajeConsola);
      } catch {
        /* se ignoran mensajes no JSON */
      }
    };
  };
  conectar();
  return {
    cerrar: () => {
      cerrado = true;
      clearTimeout(reintento);
      socket?.close();
    },
  };
}

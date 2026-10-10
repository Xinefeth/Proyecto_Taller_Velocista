// Deriva el estado en vivo del robot (HU-14) a partir de los mensajes de /ws/consola.
// Fuente: mensajes `estado` (EstadoRobot) y `enlace`/`hola` que la API reenvía.
import type { EstadoRobot } from "../types/contrato";
import type { MensajeConsola } from "../types/mensajes";

export interface RobotStatus {
  /** ¿El velocista está enlazado? */
  connected: boolean;
  /** Estado del robot, o null si aún no llegó un `estado`. */
  state: EstadoRobot["estado"] | null;
  /** Batería en voltios (canal `bateria_v`), o null. */
  battery: number | null;
  /** RSSI del enlace en dBm (`rssi_dbm`), o null. */
  rssiDbm: number | null;
  /** Frecuencia del lazo de control en Hz (`lazo_hz`), o null. */
  loopHz: number | null;
}

export const EMPTY_STATUS: RobotStatus = {
  connected: false,
  state: null,
  battery: null,
  rssiDbm: null,
  loopHz: null,
};

/**
 * Recorre los mensajes (más nuevo primero, como los entrega useTiempoReal) y arma el
 * último estado conocido del velocista. Si llegó un `estado` reciente, se considera
 * enlazado aunque no haya llegado el mensaje `enlace`.
 */
export function robotStatusFromMessages(messages: MensajeConsola[]): RobotStatus {
  let state: RobotStatus["state"] = null;
  let battery: number | null = null;
  let rssiDbm: number | null = null;
  let loopHz: number | null = null;
  let connected: boolean | null = null;

  for (const m of messages) {
    if (state === null && m.origen === "velocista" && m.tipo === "estado") {
      const d = m.datos as unknown as EstadoRobot;
      state = d.estado ?? null;
      loopHz = typeof d.lazo_hz === "number" ? d.lazo_hz : null;
      rssiDbm = typeof d.rssi_dbm === "number" ? d.rssi_dbm : null;
      const bv = d.canales?.bateria_v;
      battery = typeof bv === "number" ? bv : null;
    }
    if (connected === null && m.origen === "api" && m.tipo === "enlace") {
      const d = m.datos as { dispositivo?: string; conectado?: boolean };
      if (d.dispositivo === "velocista") connected = Boolean(d.conectado);
    }
    if (connected === null && m.origen === "api" && m.tipo === "hola") {
      const d = m.datos as { dispositivos?: Record<string, boolean> };
      if (d.dispositivos && "velocista" in d.dispositivos) {
        connected = Boolean(d.dispositivos.velocista);
      }
    }
    if (state !== null && connected !== null) break;
  }

  if (connected === null) connected = state !== null;
  return { connected, state, battery, rssiDbm, loopHz };
}

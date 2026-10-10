import { describe, expect, it } from "vitest";
import { robotStatusFromMessages } from "./robotStatus";
import type { MensajeConsola } from "../types/mensajes";

function estado(datos: Record<string, unknown>, recibido = 0): MensajeConsola {
  return { origen: "velocista", tipo: "estado", datos, recibido_ms: recibido };
}
function enlace(conectado: boolean): MensajeConsola {
  return {
    origen: "api",
    tipo: "enlace",
    datos: { dispositivo: "velocista", conectado },
    recibido_ms: 0,
  };
}

const ESTADO_OK = {
  estado: "running",
  calibrado: true,
  modo: "prueba",
  linea: "negra",
  controlador: "pid",
  lazo_hz: 1000,
  rssi_dbm: -58,
  canales: { bateria_v: 7.9 },
};

describe("robotStatusFromMessages", () => {
  it("sin mensajes devuelve estado vacío y desconectado", () => {
    const s = robotStatusFromMessages([]);
    expect(s).toEqual({
      connected: false,
      state: null,
      battery: null,
      rssiDbm: null,
      loopHz: null,
    });
  });

  it("lee batería, rssi, lazo y estado de un mensaje `estado`", () => {
    const s = robotStatusFromMessages([estado(ESTADO_OK)]);
    expect(s.state).toBe("running");
    expect(s.battery).toBe(7.9);
    expect(s.rssiDbm).toBe(-58);
    expect(s.loopHz).toBe(1000);
    // Con un `estado` reciente se considera enlazado aunque no haya `enlace`.
    expect(s.connected).toBe(true);
  });

  it("toma el `estado` más nuevo (los mensajes vienen con el más nuevo primero)", () => {
    const nuevo = estado({ ...ESTADO_OK, estado: "stopped", canales: { bateria_v: 7.2 } }, 2);
    const viejo = estado({ ...ESTADO_OK, estado: "running", canales: { bateria_v: 7.9 } }, 1);
    const s = robotStatusFromMessages([nuevo, viejo]);
    expect(s.state).toBe("stopped");
    expect(s.battery).toBe(7.2);
  });

  it("`enlace` conectado=false sin `estado` deja desconectado y sin estado", () => {
    const s = robotStatusFromMessages([enlace(false)]);
    expect(s.connected).toBe(false);
    expect(s.state).toBeNull();
  });

  it("canales sin bateria_v deja battery en null", () => {
    const s = robotStatusFromMessages([estado({ ...ESTADO_OK, canales: {} })]);
    expect(s.battery).toBeNull();
    expect(s.state).toBe("running");
  });
});

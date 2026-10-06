// Lógica de dominio pura: hechos de un robot, compatibilidad (HU-08), cumplimiento del
// reglamento (HU-10) y manifiesto (EN-02). Portada del prototipo (Protoripo.html).
// Las funciones reciben el catálogo/robots para no depender de estado global (testeable).
import type {
  Chequeo,
  Componente,
  Hechos,
  Perfil,
  Piezas,
  RobotDef,
  Severidad,
  Version,
} from "../types/dominio";
import { CTRL, PDEF } from "../datos/controladores";
import { fmt, num } from "./formato";

export const byId = (cat: Componente[], id: string): Componente | undefined =>
  cat.find((c) => c.id === id);

export const robotById = (robots: RobotDef[], id: string): RobotDef | undefined =>
  robots.find((r) => r.id === id);

/** Versión actual de un robot (la última). */
export const curVer = (r: RobotDef): Version => r.ver[r.ver.length - 1];

export const profById = (perfiles: Perfil[], id: string): Perfil | undefined =>
  perfiles.find((p) => p.id === id);

/** Robots que usan un componente en su versión actual, con la pieza concreta. */
export const usedIn = (robots: RobotDef[], id: string): { r: RobotDef; q: number }[] =>
  robots
    .map((r) => {
      const p = Object.values(curVer(r).parts).find((x) => x && x.id === id);
      return p ? { r, q: p.q } : null;
    })
    .filter((x): x is { r: RobotDef; q: number } => x != null);

export const usedQty = (robots: RobotDef[], id: string): number =>
  usedIn(robots, id).reduce((a, x) => a + x.q, 0);

/** Datos derivados de las piezas de una versión. */
export function facts(parts: Piezas, cat: Componente[]): Hechos {
  const g = (k: string): Componente | undefined => {
    const p = parts[k];
    return p ? byId(cat, p.id) : undefined;
  };
  const q = (k: string): number => (parts[k] ? parts[k]!.q : 0);
  let cost = 0,
    mass = 0,
    cur = 0;
  Object.values(parts).forEach((p) => {
    if (!p) return;
    const c = byId(cat, p.id);
    if (!c) return;
    cost += c.precio * p.q;
    mass += c.masa * p.q;
    cur += (c.i || 0) * p.q;
  });
  const line = g("linea"),
    ch = g("chasis"),
    mcu = g("mcu");
  return {
    cost,
    mass: mass ? mass + 8 : 0,
    cur,
    line,
    sensores: line ? num(line.s.canales) * q("linea") : 0,
    sensMods: q("linea"),
    motor: g("motor"),
    motores: q("motor"),
    mcu,
    driver: g("driver"),
    drivers: q("driver"),
    bat: g("bat"),
    reg: g("reg"),
    mux: g("mux"),
    exp: g("exp"),
    rueda: g("rueda"),
    chasis: ch,
    ancho: ch ? num(ch.s.ancho) : 0,
    largo: ch ? num(ch.s.largo) : 0,
    enc: g("enc"),
    imu: g("imu"),
    turb: g("turb"),
    radio: mcu ? String(mcu.s.radio) : "Ninguna",
  };
}

const C = (s: Severidad, t: string, d: string): Chequeo => [s, t, d];

/** Revisión de compatibilidad de las piezas (HU-08). */
export function compat(f: Hechos): Chequeo[] {
  const L: Chequeo[] = [];
  if (!f.mcu)
    L.push(C("bad", "Falta el microcontrolador", "Sin él no hay firmware ni conexión con la consola."));
  if (f.line && f.mcu) {
    const need = f.line.s.salida === "Analógica" ? f.sensores : 0;
    if (need) {
      if (f.mux) {
        L.push(
          f.sensores <= num(f.mux.s.canales)
            ? C(
                "ok",
                `${f.sensores} canales por el multiplexor`,
                `Usa 1 entrada analógica y 4 pines de selección del ${f.mcu.nm.split(" ")[0]}.`,
              )
            : C(
                "bad",
                "El multiplexor no alcanza",
                `${f.sensores} canales > ${f.mux.s.canales} del multiplexor.`,
              ),
        );
      } else {
        L.push(
          need <= num(f.mcu.s.adc)
            ? C("ok", "Entradas analógicas suficientes", `${need} de ${f.mcu.s.adc} disponibles.`)
            : C(
                "bad",
                "Faltan entradas analógicas",
                `${need} sensores y solo ${f.mcu.s.adc} entradas usables${
                  /WiFi/.test(f.radio) ? " con WiFi activo (ADC2 no funciona con WiFi)" : ""
                }. Agrega un multiplexor.`,
              ),
        );
      }
    }
  }
  if (f.motor && f.driver) {
    const ip = num(f.motor.s.ipico),
      ic = num(f.motor.s.inom);
    L.push(
      ip <= num(f.driver.s.ipico) && ic <= num(f.driver.s.icont)
        ? C(
            "ok",
            "El driver soporta los motores",
            `Arranque ${ip} A ≤ ${f.driver.s.ipico} A pico; nominal ${ic} A ≤ ${f.driver.s.icont} A continuos.`,
          )
        : C(
            "bad",
            "El driver no soporta los motores",
            `Arranque ${ip} A frente a ${f.driver.s.ipico} A pico.`,
          ),
    );
  }
  if (f.bat && f.driver) {
    const v = num(f.bat.s.vmax);
    L.push(
      v >= num(f.driver.s.vmin) && v <= num(f.driver.s.vmax)
        ? C("ok", "Batería dentro del rango del driver", `${v} V en ${f.driver.s.vmin}–${f.driver.s.vmax} V.`)
        : C("bad", "Batería fuera del rango del driver", `${v} V fuera de ${f.driver.s.vmin}–${f.driver.s.vmax} V.`),
    );
  }
  if (f.bat && f.motor) {
    const lim = num(f.motor.s.v) * 1.2,
      pct = Math.round((lim / num(f.bat.s.vmax)) * 100);
    L.push(
      pct < 100
        ? C(
            "warn",
            `Motores de ${f.motor.s.v} V con batería de ${f.bat.s.vmax} V`,
            `Limita el PWM máximo a ${pct} % para no pasar de ${fmt(lim, 1)} V.`,
          )
        : C("ok", "Voltaje de motores compatible", ""),
    );
  }
  if (f.reg && f.mcu) {
    const logic =
      (f.mcu.i || 0) + (f.line ? num(f.line.s.i) * f.sensMods : 0) + (f.imu ? (f.imu.i || 0) : 0);
    L.push(
      logic <= num(f.reg.s.imax)
        ? C("ok", "El regulador cubre la lógica", `${fmt(logic, 2)} A de ${f.reg.s.imax} A.`)
        : C("bad", "El regulador no alcanza", `${fmt(logic, 2)} A > ${f.reg.s.imax} A.`),
    );
  }
  if (f.turb && f.bat) {
    const need = num(f.turb.s.imax) + (f.motor ? num(f.motor.s.inom) * f.motores : 0),
      can = (num(f.bat.s.mah) / 1000) * num(f.bat.s.c);
    L.push(
      need <= can
        ? C("ok", "La batería soporta turbina y motores", `${fmt(need, 1)} A de ${fmt(can, 1)} A de descarga.`)
        : C("bad", "La batería no soporta la turbina", `${fmt(need, 1)} A > ${fmt(can, 1)} A.`),
    );
  }
  if (f.enc && f.motor && f.motor.s.familia === "TT amarillo")
    L.push(C("warn", "Encoders con motores TT", "Los encoders del catálogo son para motores N20 o Micro Metal."));
  return L;
}

/** Cumplimiento del reglamento de un perfil (HU-10). */
export function checks(f: Hechos, prof: Perfil): Chequeo[] {
  const r = prof.r,
    L: Chequeo[] = [];
  if (r.dim)
    L.push(
      f.ancho <= r.dim[0] && f.largo <= r.dim[1]
        ? C("ok", "Dimensiones", `${f.ancho} × ${f.largo} mm ≤ ${r.dim[0]} × ${r.dim[1]} mm`)
        : C("bad", "Dimensiones", `${f.ancho} × ${f.largo} mm supera ${r.dim[0]} × ${r.dim[1]} mm`),
    );
  L.push(
    r.sensMax && f.sensores > r.sensMax
      ? C("bad", "Sensores", `${f.sensores} sensores; máximo ${r.sensMax} en ${prof.cat}`)
      : C("ok", "Sensores", `${f.sensores} canales${r.sensMax ? ` (máx. ${r.sensMax})` : " · libre"}`),
  );
  if (r.motores)
    L.push(
      f.motores <= r.motores
        ? C("ok", "Motores", `${f.motores} de máximo ${r.motores}`)
        : C("bad", "Motores", `${f.motores} > ${r.motores}`),
    );
  if (r.motorFam)
    L.push(
      f.motor && r.motorFam.includes(String(f.motor.s.familia))
        ? C("ok", "Tipo de motor", String(f.motor.s.familia))
        : C("bad", "Tipo de motor", "Solo motorreductores amarillos o celestes sin modificar"),
    );
  if (r.mcu)
    L.push(
      f.mcu && r.mcu.some((m) => f.mcu!.nm.includes(m.split(" ").pop() ?? m) || f.mcu!.nm.includes(m))
        ? C("ok", "Microcontrolador", f.mcu.nm)
        : C("bad", "Microcontrolador", `Permitidos: ${r.mcu.join(", ")}`),
    );
  if (r.pcbComercial === false && f.exp && f.exp.s.comercial === "Sí")
    L.push(C("bad", "PCB comercial", "No permitida en Amateur (el robot pasa a Senior)"));
  if (r.chasisMat)
    L.push(
      f.chasis && r.chasisMat.some((m) => String(f.chasis!.s.material).includes(m))
        ? C("ok", "Chasis", String(f.chasis.s.material))
        : C("bad", "Chasis", "Obligatorio de impresión 3D o MDF"),
    );
  L.push(
    f.turb && !r.turbina
      ? C("bad", "Turbina", `No permitida en ${prof.cat}`)
      : C("ok", "Turbina", f.turb ? "Permitida" : "No lleva"),
  );
  L.push(
    f.enc && !r.enc
      ? C("bad", "Encoders", "Prohibidos: el robot solo puede guiarse por la línea")
      : C("ok", "Encoders", f.enc ? "Permitidos" : "No lleva"),
  );
  if (f.imu && !r.imu) L.push(C("bad", "IMU", "Prohibida: solo sensado de línea"));
  L.push(
    r.inal && f.radio === "Ninguna"
      ? C("bad", "Arranque", "Requiere arranque inalámbrico")
      : C("ok", "Arranque", r.inal ? `Inalámbrico por ${f.radio}` : "Libre"),
  );
  return L;
}

/** True si el robot cumple el perfil (ningún chequeo en "bad"). */
export const complies = (robot: RobotDef, prof: Perfil, cat: Componente[]): boolean =>
  !checks(facts(curVer(robot).parts, cat), prof).some((x) => x[0] === "bad");

export interface Manifiesto {
  tipo: "manifiesto";
  robot: string;
  nombre: string;
  version: string;
  firmware: string | null;
  sensores: Record<string, unknown>[];
  actuadores: Record<string, unknown>[];
  controlador: {
    activo: string;
    disponibles: string[];
    parametros: Record<string, { min: number; max: number; paso: number }>;
  };
  telemetria: { estado_hz: number; senales_hz: number; lazo_hz: number };
  arranque: "inalambrico" | "interruptor";
  compensacion_bateria: boolean;
}

/** Manifiesto que el robot envía al conectarse (EN-02). */
export function manifest(
  r: RobotDef,
  cat: Componente[],
  ctrlActivo: string,
  compensacionBateria: boolean,
): Manifiesto {
  const v = curVer(r),
    f = facts(v.parts, cat);
  const m: Manifiesto = {
    tipo: "manifiesto",
    robot: r.id,
    nombre: r.nm,
    version: v.v,
    firmware: r.fw || null,
    sensores: [],
    actuadores: [],
    controlador: {
      activo: ctrlActivo,
      disponibles: Object.keys(CTRL),
      parametros: Object.fromEntries(
        CTRL[ctrlActivo].keys.map((k) => [k, { min: PDEF[k].min, max: PDEF[k].max, paso: PDEF[k].step }]),
      ),
    },
    telemetria: { estado_hz: 1, senales_hz: 20, lazo_hz: 1000 },
    arranque: f.radio !== "Ninguna" ? "inalambrico" : "interruptor",
    compensacion_bateria: compensacionBateria,
  };
  if (f.sensores)
    m.sensores.push({ id: "regleta", tipo: "linea", canales: f.sensores, modulos: f.sensMods, via: f.mux ? "multiplexor" : "directo" });
  m.sensores.push({ id: "bateria", tipo: "voltaje", unidad: "V" });
  if (f.enc) m.sensores.push({ id: "encoders", tipo: "encoder", cpr: f.enc.s.cpr, ruedas: 2 });
  if (f.imu) m.sensores.push({ id: "imu", tipo: "imu", ejes: f.imu.s.ejes });
  if (f.motores)
    ["motor_izq", "motor_der"].slice(0, f.motores).forEach((id) => m.actuadores.push({ id, tipo: "motor", pwm: [-100, 100] }));
  if (f.turb) m.actuadores.push({ id: "turbina", tipo: "turbina", pwm: [0, 100] });
  return m;
}

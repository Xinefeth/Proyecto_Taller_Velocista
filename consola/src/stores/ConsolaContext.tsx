// Estado y lógica de la consola simulada (EN-19): robot, setup, corridas, mapa y navegación.
// Portado del prototipo (Protoripo.html). Ejecuta el bucle de simulación (modo Simulado, EN-05)
// y expone estado + acciones a las vistas. El modo Robot real se cablea con services/ (EN-05).
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { Componente, Perfil, RobotDef, Setup } from "../types/dominio";
import type { Corrida, Vuelta } from "../types/corridas";
import { CAT, RANURAS } from "../datos/catalogo";
import { ROBOTS } from "../datos/robots";
import { PERFILES } from "../datos/reglamento";
import { CTRL, PDEF, psum } from "../datos/controladores";
import { curVer, facts, profById, robotById } from "../logica/dominio";
import { clamp, clone, fmt } from "../logica/formato";
import {
  borrarRegistrados,
  cargarComponentes,
  cargarRobots,
  guardarComponentes,
  guardarRobots,
} from "../logica/persistencia";
import { Ingeniero, type MetodoIngeniero } from "../logica/ingeniero";
import {
  construirMapa,
  DT,
  EXAMPLE,
  LEN,
  Simulador,
  VMAX,
  type Punto,
  type StatsMapa,
} from "../logica/simulador";
import { HIST, NB, RATE, resetEncuadre, robotOn } from "../logica/lienzos";

export type Tab =
  | "control"
  | "telemetria"
  | "tiempos"
  | "mapa"
  | "catalogo"
  | "armador"
  | "reglamento";
export type Fuente = "sim" | "robot";
export type Modo = "prueba" | "competencia";
export type ColorLinea = "negra" | "blanca";
export type Alcance = "s1" | "s2" | "all";

export interface EventoLog {
  t: string;
  sys: string;
  msg: string;
  lv: "" | "good" | "warn" | "bad" | "best";
}

interface MapaState {
  path: Punto[] | null;
  source: string | null;
  pending: boolean;
  recording: boolean;
  raw: Punto[] | null;
  corr: Punto[] | null;
  stats: StatsMapa | null;
  est: { x: number; y: number; h: number; dist: number; next: number } | null;
  bias: number;
}

const GRUPO: Record<Tab, "velocista" | "gestion"> = {
  control: "velocista",
  telemetria: "velocista",
  tiempos: "velocista",
  mapa: "velocista",
  catalogo: "gestion",
  armador: "gestion",
  reglamento: "gestion",
};

const store = {
  get<T>(k: string, d: T): T {
    try {
      const v = localStorage.getItem("apaec.v2." + k);
      return v == null ? d : (JSON.parse(v) as T);
    } catch {
      return d;
    }
  },
  set(k: string, v: unknown): void {
    try {
      localStorage.setItem("apaec.v2." + k, JSON.stringify(v));
    } catch {
      /* almacenamiento no disponible */
    }
  },
};

export interface Consola {
  tick: number;
  // navegación
  tab: Tab;
  goTab: (t: Tab) => void;
  // datos
  catalog: Componente[];
  robots: RobotDef[];
  perfiles: Perfil[];
  robot: RobotDef;
  robotId: string;
  perfil: Perfil;
  selectRobot: (id: string) => void;
  setProfile: (id: string) => void;
  // conexión / fuente
  source: Fuente;
  setSource: (v: Fuente) => void;
  connected: boolean;
  toggleConnected: () => void;
  link: { dbm: number; ms: number };
  // estado del robot
  mode: Modo;
  setMode: (v: Modo) => void;
  line: ColorLinea;
  setLine: (v: ColorLinea) => void;
  calibrated: boolean;
  calibrating: boolean;
  calProgress: number;
  calibrar: () => void;
  running: boolean;
  arrancarDetener: () => void;
  locked: boolean;
  gate: boolean;
  toggleGate: () => void;
  comp: boolean;
  toggleComp: () => void;
  turb: number;
  setTurb: (v: number) => void;
  vbat: number;
  cambiarBateria: () => void;
  // setup (HU-17)
  draft: Setup;
  applied: Setup;
  saved: Setup;
  preset: string | null;
  setCtrl: (v: string) => void;
  setParam: (id: string, val: number) => void;
  setPreset: (name: string) => void;
  enviarSetup: () => void;
  guardarSetup: () => void;
  // corridas / ingeniero
  laps: Vuelta[];
  runs: Corrida[];
  lastLap: Vuelta | null;
  lastRun: Corrida | null;
  lapCount: number;
  bestSec: number[];
  engMethod: MetodoIngeniero;
  setEngMethod: (v: MetodoIngeniero) => void;
  ingeniero: Ingeniero;
  cargarPropuesta: () => void;
  guardarNota: (txt: string) => boolean;
  // mapa
  mapMode: "error" | "sectores";
  setMapMode: (v: "error" | "sectores") => void;
  usarEjemplo: () => void;
  rehacerMapa: () => void;
  // señales
  show: { err: boolean; pl: boolean; pr: boolean };
  toggleSenal: (s: "err" | "pl" | "pr") => void;
  // catálogo / armador
  setCatalog: (f: (c: Componente[]) => Componente[]) => void;
  setRobots: (f: (r: RobotDef[]) => RobotDef[]) => void;
  // log
  log: EventoLog[];
  registrar: (sys: string, msg: string, lv?: EventoLog["lv"]) => void;
  // modales
  fichaId: string | null;
  abrirFicha: (id: string) => void;
  cerrarFicha: () => void;
  regOpen: boolean;
  abrirRegistro: () => void;
  cerrarRegistro: () => void;
  /** Borra lo registrado a mano y vuelve al catálogo y los robots de ejemplo. */
  restablecerDatos: () => void;
  manifiestoId: string | null;
  abrirManifiesto: (id: string) => void;
  cerrarManifiesto: () => void;
  armadorInicial: string | null;
  abrirEnArmador: (id: string) => void;
  // backlog
  blOpen: boolean;
  setBlOpen: (v: boolean) => void;
  showPbi: boolean;
  setShowPbi: (v: boolean) => void;
  scope: Alcance;
  setScope: (v: Alcance) => void;
  // toast
  toast: string | null;
  mostrarToast: (m: string) => void;
  // refs para lienzos
  simRef: React.MutableRefObject<Simulador>;
  mapRef: React.MutableRefObject<MapaState>;
  trailRef: React.MutableRefObject<{ x: number; y: number; err: number }[]>;
  histRef: React.MutableRefObject<{ err: number[]; pl: number[]; pr: number[] }>;
  curBinsRef: React.MutableRefObject<Float32Array>;
  curCntRef: React.MutableRefObject<Float32Array>;
  lastBinsRef: React.MutableRefObject<number[] | null>;
}

const Contexto = createContext<Consola | null>(null);

export function ProveedorConsola({ children }: { children: ReactNode }) {
  const [tick, setTick] = useState(0);
  const bump = useCallback(() => setTick((t) => (t + 1) % 1_000_000), []);

  const [tab, setTab] = useState<Tab>("control");
  // Lo registrado a mano se conserva en el navegador hasta que exista la API (HU-02, HU-06).
  const [catalog, setCatalogState] = useState<Componente[]>(() => cargarComponentes(CAT));
  const [robots, setRobotsState] = useState<RobotDef[]>(() => cargarRobots(ROBOTS));
  useEffect(() => guardarComponentes(catalog, CAT), [catalog]);
  useEffect(() => guardarRobots(robots, ROBOTS), [robots]);
  const [perfiles] = useState<Perfil[]>(() => clone(PERFILES));

  const [robotId, setRobotId] = useState("v001");
  const [profileId, setProfileId] = useState<string>(() => {
    const p = store.get("profile", "mr4s");
    return profById(PERFILES, p) ? p : "mr4s";
  });
  const [source, setSourceState] = useState<Fuente>("sim");
  const [connected, setConnected] = useState(true);
  const [mode, setModeState] = useState<Modo>("prueba");
  const [line, setLineState] = useState<ColorLinea>("negra");
  const [calibrated, setCalibrated] = useState(false);
  const [calibrating, setCalibrating] = useState(false);
  const [calProgress, setCalProgress] = useState(0);
  const [running, setRunning] = useState(false);
  const [gate, setGate] = useState(true);
  const [comp, setComp] = useState(true);
  const [turb, setTurbState] = useState(0);

  const [draft, setDraft] = useState<Setup>(() => ({ ctrl: "pid", p: { ...CTRL.pid.pre.Base } }));
  const [applied, setApplied] = useState<Setup>(() => ({
    ctrl: "pid",
    p: { ...CTRL.pid.pre.Base },
  }));
  const [saved, setSaved] = useState<Setup>(() => ({ ctrl: "pid", p: { ...CTRL.pid.pre.Base } }));
  const [preset, setPresetState] = useState<string | null>("Base");

  const [engMethod, setEngMethodState] = useState<MetodoIngeniero>("twiddle");
  const [mapMode, setMapMode] = useState<"error" | "sectores">("error");
  const [show, setShow] = useState({ err: true, pl: true, pr: true });

  const [fichaId, setFichaId] = useState<string | null>(null);
  const [regOpen, setRegOpen] = useState(false);
  const [manifiestoId, setManifiestoId] = useState<string | null>(null);
  const [armadorInicial, setArmadorInicial] = useState<string | null>(null);

  const [blOpen, setBlOpen] = useState(false);
  const [showPbi, setShowPbiState] = useState<boolean>(() => store.get("pbi", false));
  // Por defecto "Sprint 1": los paneles de Sprint 2 se ven desactivados (criterio de EN-19).
  const [scope, setScopeState] = useState<Alcance>(() => store.get<Alcance>("scope", "s1"));

  const [toast, setToast] = useState<string | null>(null);
  const toastT = useRef<ReturnType<typeof setTimeout>>();
  const mostrarToast = useCallback((m: string) => {
    setToast(m);
    clearTimeout(toastT.current);
    toastT.current = setTimeout(() => setToast(null), 2800);
  }, []);

  // --- Refs vivos (leídos por el bucle y los lienzos) ---
  const simRef = useRef(new Simulador());
  const mapRef = useRef<MapaState>({
    path: null,
    source: null,
    pending: true,
    recording: false,
    raw: null,
    corr: null,
    stats: null,
    est: null,
    bias: 1,
  });
  const trailRef = useRef<{ x: number; y: number; err: number }[]>([]);
  const histRef = useRef({ err: [] as number[], pl: [] as number[], pr: [] as number[] });
  const curBinsRef = useRef(new Float32Array(NB));
  const curCntRef = useRef(new Float32Array(NB));
  const lastBinsRef = useRef<number[] | null>(null);

  const lapsRef = useRef<Vuelta[]>([]);
  const runsRef = useRef<Corrida[]>([]);
  const pendingSyncRef = useRef<Vuelta[]>([]);
  const lastLapRef = useRef<Vuelta | null>(null);
  const lastRunRef = useRef<Corrida | null>(null);
  const lapCountRef = useRef(0);
  const bestSecRef = useRef<number[]>([Infinity, Infinity, Infinity]);
  const logRef = useRef<EventoLog[]>([]);
  const engRef = useRef(new Ingeniero());
  const vbatRef = useRef(8.2);
  const linkRef = useRef({ dbm: 58, ms: 12 });
  const [, setLinkTick] = useState(0);

  // Valores que el bucle necesita siempre frescos.
  const live = useRef({
    running,
    connected,
    mode,
    comp,
    turb,
    gate,
    robotId,
    tab,
    applied,
    engMethod,
    source,
  });
  live.current = {
    running,
    connected,
    mode,
    comp,
    turb,
    gate,
    robotId,
    tab,
    applied,
    engMethod,
    source,
  };

  const robot = useMemo(() => robotById(robots, robotId) ?? robots[0], [robots, robotId]);
  const perfil = useMemo(() => profById(perfiles, profileId) ?? perfiles[0], [perfiles, profileId]);
  const locked = running && mode === "competencia";

  const registrar = useCallback((sys: string, msg: string, lv: EventoLog["lv"] = "") => {
    const d = new Date();
    const t = [d.getHours(), d.getMinutes(), d.getSeconds()]
      .map((x) => String(x).padStart(2, "0"))
      .join(":");
    logRef.current = [{ t, sys, msg, lv }, ...logRef.current].slice(0, 80);
  }, []);

  // --- Corridas ---
  const registrarCorrida = useCallback(
    (L: Vuelta, src?: string) => {
      const rb = robotById(robots, L.robot);
      const r: Corrida = {
        n: runsRef.current.length + 1,
        robot: L.robot,
        ver: rb ? curVer(rb).v : "",
        ctrl: L.ctrl,
        p: { ...L.p },
        t: L.fin ? L.t : null,
        fin: L.fin,
        iae: L.iae,
        vbat: L.vbat,
        sec: L.fin ? L.sec : [],
        src: src || L.src,
        note: L.why || "",
        J: 0,
      };
      r.J = r.fin ? r.t! + 2 * r.iae : 120;
      runsRef.current = [...runsRef.current, r];
      lastRunRef.current = r;
      if (L.robot === live.current.robotId)
        engRef.current.feed(
          r,
          runsRef.current.filter((x) => x.robot === L.robot),
        );
      registrar("Corridas", `#${r.n} registrada · ${CTRL[r.ctrl].short} · J ${fmt(r.J, 2)}`);
    },
    [robots, registrar],
  );

  const mkLap = useCallback((fin: boolean, why?: string): Vuelta => {
    const sim = simRef.current;
    return {
      n: lapCountRef.current,
      t: sim.lapT,
      iae: sim.iae,
      ctrl: live.current.applied.ctrl,
      p: { ...live.current.applied.p },
      vbat: vbatRef.current,
      segs: sim.closeLap(),
      sec: fin ? sim.secT.slice(0, 3) : [],
      col: [],
      fin,
      lost: sim.lost,
      src: live.current.gate ? "Meta" : "Telemetría",
      why: why || "",
      robot: live.current.robotId,
    };
  }, []);

  const onLap = useCallback(() => {
    const sim = simRef.current,
      m = mapRef.current;
    if (m.recording && m.raw && m.est) {
      m.raw.push({ x: m.est.x, y: m.est.y, h: m.est.h });
      const res = construirMapa(m.raw);
      if (res) {
        m.corr = res.corr;
        m.path = res.corr;
        m.source = "desde la vuelta 1";
        m.pending = false;
        m.recording = false;
        m.stats = res.stats;
        resetEncuadre();
        registrar(
          "Mapa",
          `Construido: ${fmt(res.stats.len, 2)} m, cierre corregido ${Math.round(res.stats.closeErr * 100)} cm`,
          "good",
        );
      }
    }
    const L = mkLap(true);
    const prev = lapsRef.current.filter((l) => l.fin).slice(-1)[0];
    const bs = bestSecRef.current;
    L.col = L.sec.map((t, i) =>
      t < bs[i] ? "purple" : prev && prev.sec[i] != null && t < prev.sec[i] ? "green" : "yellow",
    );
    L.sec.forEach((t, i) => {
      if (t < bs[i]) bs[i] = t;
    });
    const fins = lapsRef.current.filter((l) => l.fin);
    const prevBest = fins.length ? Math.min(...fins.map((l) => l.t)) : Infinity;
    lastLapRef.current = L;
    lapsRef.current = [...lapsRef.current, L];
    lastBinsRef.current = Array.from(curBinsRef.current, (v, i) =>
      curCntRef.current[i] ? v / curCntRef.current[i] : 0,
    );
    curBinsRef.current.fill(0);
    curCntRef.current.fill(0);
    trailRef.current = [];
    if (L.t < prevBest)
      registrar("Vuelta", `V${lapCountRef.current} ${fmt(L.t, 3)} s, mejor vuelta`, "best");
    else
      registrar("Vuelta", `V${lapCountRef.current} ${fmt(L.t, 3)} s (+${fmt(L.t - prevBest, 3)})`);
    if (live.current.connected) registrarCorrida(L);
    else pendingSyncRef.current.push(L);
    Object.assign(sim, { lapT: 0, iae: 0, lost: 0, sec: 0, secT: [], secStart: 0 });
    lapCountRef.current++;
    if (live.current.mode === "competencia") {
      setRunning(false);
      registrar("Intento", `Terminado: 1 vuelta en ${fmt(L.t, 3)} s`, "good");
      mostrarToast(`Intento terminado: ${fmt(L.t, 3)} s.`);
    }
  }, [mkLap, registrar, registrarCorrida, mostrarToast]);

  const onDNF = useCallback(
    (why: string) => {
      const L = mkLap(false, why);
      lastLapRef.current = L;
      lapsRef.current = [...lapsRef.current, L];
      const m = mapRef.current;
      if (m.recording) {
        m.recording = false;
        m.raw = null;
      }
      setRunning(false);
      if (live.current.connected) registrarCorrida(L);
      else pendingSyncRef.current.push(L);
      registrar(
        "Robot",
        why === "Tiempo máximo"
          ? "Tiempo máximo de 120 s: ronda nula"
          : `Salió de la pista en S${simRef.current.sec + 1}`,
        "bad",
      );
      mostrarToast(
        why === "Tiempo máximo"
          ? "Pasó los 120 s: corrida no terminada (J = 120)."
          : "Salió de la pista: corrida no terminada (J = 120).",
      );
    },
    [mkLap, registrar, registrarCorrida, mostrarToast],
  );

  // --- Bucle de simulación ---
  const acc = useRef({ a1: 0, a2: 0, jit: 0, lostLogT: -9, lastTs: 0, lowLogged: false });
  useEffect(() => {
    let raf = 0;
    acc.current.lastTs = performance.now();
    const loop = (ts: number) => {
      const L = live.current;
      const a = acc.current;
      const dt = Math.min(0.05, (ts - a.lastTs) / 1000);
      a.lastTs = ts;
      const sim = simRef.current,
        m = mapRef.current;
      if (L.running) {
        const steps = Math.round(dt / DT);
        for (let i = 0; i < steps; i++) {
          const ev = sim.step(L.applied, { comp: L.comp, vbat: vbatRef.current });
          if (m.recording && m.est && m.raw) {
            const k = m.bias;
            const v = ((sim.pl + sim.pr) / 2 / 100) * VMAX * k,
              yaw =
                ((((sim.pl - sim.pr) / 100) * VMAX) / 0.13) *
                k *
                (1 + (Math.random() - 0.5) * 0.02);
            m.est.h += yaw * DT;
            const ds = Math.max(0, v) * DT;
            m.est.x += Math.cos(m.est.h) * ds;
            m.est.y += Math.sin(m.est.h) * ds;
            m.est.dist += ds;
            if (m.est.dist >= m.est.next) {
              m.est.next += 0.02;
              m.raw.push({ x: m.est.x, y: m.est.y, h: m.est.h });
            }
          }
          const bi = Math.min(NB - 1, Math.floor(((sim.s % LEN) / LEN) * NB));
          curBinsRef.current[bi] += Math.abs(sim.es);
          curCntRef.current[bi]++;
          if (ev === "lost" && sim.lapT - a.lostLogT > 0.6) {
            a.lostLogT = sim.lapT;
            registrar("Línea", `Perdida en S${sim.sec + 1}`, "warn");
          }
          if (ev === "lap") {
            onLap();
            if (!live.current.running) break;
          }
          if (ev === "crash") {
            onDNF("Salió de la pista");
            break;
          }
          if (ev === "timeout") {
            onDNF("Tiempo máximo");
            break;
          }
          a.a1 += DT;
          if (a.a1 >= 1 / RATE) {
            a.a1 -= 1 / RATE;
            const h = histRef.current;
            h.err.push(sim.p);
            h.pl.push(sim.pl);
            h.pr.push(sim.pr);
            if (h.err.length > HIST * RATE) {
              h.err.shift();
              h.pl.shift();
              h.pr.shift();
            }
          }
          a.a2 += DT;
          if (a.a2 >= 0.02 && m.path && !m.recording) {
            a.a2 = 0;
            const r = robotOn(m.path, sim.s, sim.e);
            trailRef.current.push({ x: r.x, y: r.y, err: Math.abs(sim.es) });
            if (trailRef.current.length > 90) trailRef.current.shift();
          }
        }
        vbatRef.current = Math.max(6.8, vbatRef.current - dt * (0.0035 + (L.turb / 100) * 0.004));
        if (vbatRef.current < 7.3 && !a.lowLogged) {
          a.lowLogged = true;
          registrar("Batería", `Baja: ${fmt(vbatRef.current, 2)} V, cámbiala pronto`, "warn");
        }
      }
      if (L.connected) {
        a.jit += dt;
        if (a.jit > 0.8) {
          a.jit = 0;
          linkRef.current = {
            dbm: 55 + Math.round(Math.random() * 8),
            ms: 9 + Math.round(Math.random() * 9),
          };
          setLinkTick((x) => (x + 1) % 1000);
        }
      }
      if (
        L.running ||
        (L.connected && (L.tab === "control" || L.tab === "telemetria")) ||
        (L.tab === "mapa" && m.recording)
      )
        bump();
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [onLap, onDNF, registrar, bump]);

  // --- Efectos de cuerpo (clases globales como en el prototipo) ---
  useEffect(() => {
    document.body.dataset.group = GRUPO[tab];
  }, [tab]);
  useEffect(() => {
    document.body.classList.toggle("locked", locked);
  }, [locked]);
  useEffect(() => {
    document.body.classList.toggle("is-offline", !connected);
  }, [connected]);
  useEffect(() => {
    document.body.classList.toggle("show-pbi", showPbi);
  }, [showPbi]);
  useEffect(() => {
    document.body.dataset.scope = scope;
  }, [scope]);

  // --- Acciones ---
  const goTab = useCallback((t: Tab) => {
    setTab(t);
    window.scrollTo({ top: 0 });
  }, []);

  const setSource = useCallback(
    (v: Fuente) => {
      if (v === "sim") {
        setSourceState("sim");
        registrar("Enlace", "Fuente: datos simulados");
        return;
      }
      const r = robotById(robots, live.current.robotId);
      if (!r?.fw) {
        mostrarToast(`${r?.nm ?? "El robot"} aún no tiene firmware: solo modo simulado.`);
        return;
      }
      registrar("Enlace", "Buscando ws://192.168.4.1:81 …");
      setTimeout(() => {
        setSourceState("sim");
        registrar("Enlace", "No se encontró el robot: se mantiene el modo simulado", "warn");
        mostrarToast("En esta maqueta no hay robot real: se mantiene el modo simulado.");
      }, 1400);
    },
    [robots, registrar, mostrarToast],
  );

  const toggleConnected = useCallback(() => {
    setConnected((c) => {
      const next = !c;
      if (!next) {
        if (live.current.running && live.current.mode === "prueba") {
          setRunning(false);
          registrar("Enlace", "Perdido: robot detenido (modo prueba)", "bad");
        } else
          registrar(
            "Enlace",
            live.current.running
              ? "Perdido: el robot sigue y graba las vueltas en su memoria"
              : "Perdido",
            "bad",
          );
      } else {
        const n = pendingSyncRef.current.length;
        while (pendingSyncRef.current.length)
          registrarCorrida(pendingSyncRef.current.shift()!, "Sincronizada");
        registrar(
          "Enlace",
          n
            ? `Restablecido: ${n} vuelta${n > 1 ? "s" : ""} sincronizada${n > 1 ? "s" : ""} desde la memoria del robot`
            : "Restablecido",
          "good",
        );
        if (n)
          mostrarToast(
            `${n} vuelta${n > 1 ? "s" : ""} recuperada${n > 1 ? "s" : ""} de la memoria del robot.`,
          );
      }
      return next;
    });
  }, [registrar, registrarCorrida, mostrarToast]);

  const cambiarBateria = useCallback(() => {
    vbatRef.current = 8.35;
    acc.current.lowLogged = false;
    registrar("Batería", "Cambiada: 8.35 V", "good");
    bump();
  }, [registrar, bump]);

  const toggleGate = useCallback(() => {
    setGate((g) => {
      const next = !g;
      registrar(
        "Cronómetro",
        next
          ? "Conectado: la barrera marca las vueltas"
          : "Desconectado: las vueltas se toman de la telemetría del robot",
        next ? "good" : "warn",
      );
      return next;
    });
  }, [registrar]);

  const toggleComp = useCallback(() => {
    setComp((v) => {
      const next = !v;
      registrar(
        "Firmware",
        next ? "Compensación de batería activada" : "Compensación de batería desactivada",
        next ? "good" : "warn",
      );
      mostrarToast(
        next
          ? "El PWM se escala con el voltaje: tiempos comparables entre cargas."
          : "Sin compensación: los tiempos cambian con la batería.",
      );
      return next;
    });
  }, [registrar, mostrarToast]);

  const setMode = useCallback(
    (v: Modo) => {
      setModeState(v);
      registrar(
        "Modo",
        v === "prueba"
          ? "Prueba: vueltas continuas"
          : "Competencia: una vuelta y solo responde a Detener",
      );
    },
    [registrar],
  );
  const setLine = useCallback(
    (v: ColorLinea) => {
      setLineState(v);
      registrar(
        "Sensores",
        v === "negra" ? "Línea negra sobre blanco" : "Línea blanca sobre negro",
      );
    },
    [registrar],
  );
  const setTurb = useCallback((v: number) => setTurbState(v), []);

  const calibrar = useCallback(() => {
    if (live.current.running || calibrating) return;
    if (!live.current.connected) return mostrarToast("Sin enlace: no se puede calibrar.");
    setCalibrating(true);
    setCalProgress(0);
    const t0 = performance.now(),
      dur = 1800;
    const tickCal = (now: number) => {
      const k = Math.min(1, (now - t0) / dur);
      setCalProgress(k);
      if (k < 1) {
        requestAnimationFrame(tickCal);
        return;
      }
      setCalibrating(false);
      setCalibrated(true);
      setCalProgress(0);
      const n = facts(curVer(robot).parts, catalog).sensores;
      registrar("Sensores", `Calibración completa: ${n}/${n} canales en 1.8 s`, "good");
    };
    requestAnimationFrame(tickCal);
  }, [calibrating, robot, catalog, registrar, mostrarToast]);

  const arrancarDetener = useCallback(() => {
    if (live.current.running) {
      setRunning(false);
      const m = mapRef.current;
      if (m.recording) {
        m.recording = false;
        m.raw = null;
      }
      registrar("Robot", "Detenido por el piloto");
      return;
    }
    if (!live.current.connected)
      return mostrarToast("Sin enlace: el arranque inalámbrico necesita conexión.");
    if (!calibrated) return mostrarToast("Calibra los sensores antes de arrancar.");
    simRef.current.reset();
    trailRef.current = [];
    lapCountRef.current = 1;
    curBinsRef.current.fill(0);
    curCntRef.current.fill(0);
    const m = mapRef.current;
    if (m.pending) {
      m.recording = true;
      m.est = { x: 0, y: 0, h: 0, dist: 0, next: 0 };
      m.raw = [{ x: 0, y: 0, h: 0 }];
      m.bias = 1 + (Math.random() * 0.08 - 0.04);
      registrar("Mapa", "Mapeando durante la vuelta 1");
    }
    registrar(
      "Robot",
      `Arranque inalámbrico · ${CTRL[live.current.applied.ctrl].nm} · ${psum(live.current.applied.ctrl, live.current.applied.p)}`,
      "good",
    );
    setRunning(true);
  }, [calibrated, registrar, mostrarToast]);

  // Setup
  const setCtrl = useCallback(
    (v: string) => {
      if (locked || v === draft.ctrl) return;
      setDraft({ ctrl: v, p: v === applied.ctrl ? { ...applied.p } : { ...CTRL[v].pre.Base } });
      setPresetState(v === applied.ctrl ? null : "Base");
    },
    [locked, draft.ctrl, applied],
  );
  const setParam = useCallback(
    (id: string, val: number) => {
      if (locked || !CTRL[draft.ctrl].keys.includes(id)) return;
      const d = PDEF[id];
      const p = { ...draft.p };
      p[id] = clamp(+(+val).toFixed(d.dec + 1), d.min, d.max);
      setDraft({ ctrl: draft.ctrl, p });
      setPresetState(null);
    },
    [locked, draft],
  );
  const setPreset = useCallback(
    (name: string) => {
      if (locked) return;
      setDraft({ ctrl: draft.ctrl, p: { ...CTRL[draft.ctrl].pre[name] } });
      setPresetState(name);
    },
    [locked, draft.ctrl],
  );
  const enviarSetup = useCallback(() => {
    if (!connected) return mostrarToast("Sin enlace: no se pudo enviar.");
    const chg = draft.ctrl !== applied.ctrl;
    setApplied(clone(draft));
    if (chg) registrar("Controlador", `Cambiado a ${CTRL[draft.ctrl].nm}`, "good");
    registrar("Setup", `Enviado: ${psum(draft.ctrl, draft.p)}`);
    mostrarToast(
      chg ? `Controlador ${CTRL[draft.ctrl].nm} enviado al robot.` : "Setup enviado al robot.",
    );
  }, [connected, draft, applied.ctrl, registrar, mostrarToast]);
  const guardarSetup = useCallback(() => {
    if (!connected) return mostrarToast("Sin enlace: no se pudo guardar.");
    const d = clone(draft);
    setApplied(d);
    setSaved(d);
    registrar("Setup", "Guardado en la memoria del robot", "good");
    mostrarToast("Guardado en el robot: se mantiene al reiniciar.");
  }, [connected, draft, registrar, mostrarToast]);

  // Ingeniero
  const setEngMethod = useCallback(
    (v: MetodoIngeniero) => {
      engRef.current.method = v;
      engRef.current.restart(
        runsRef.current.filter((r) => r.robot === live.current.robotId),
        live.current.applied.ctrl,
      );
      setEngMethodState(v);
      registrar("Ingeniero", v === "bayes" ? "Método: optimización bayesiana" : "Método: Twiddle");
    },
    [registrar],
  );
  const cargarPropuesta = useCallback(() => {
    const eng = engRef.current;
    if (!eng.prop || locked) return;
    setDraft({ ctrl: eng.ctrl!, p: { ...eng.prop } });
    setPresetState(null);
    if (tab !== "control") goTab("control");
    mostrarToast("Sugerencia cargada en el setup. Envíala y sal a pista.");
  }, [locked, tab, goTab, mostrarToast]);
  const guardarNota = useCallback(
    (txt: string) => {
      const v = txt.trim();
      if (!lastRunRef.current) {
        mostrarToast("Aún no hay corridas.");
        return false;
      }
      if (!v) return false;
      const r = lastRunRef.current;
      r.note = r.note ? `${r.note}. ${v}` : v;
      mostrarToast(`Nota guardada en la corrida #${r.n}.`);
      bump();
      return true;
    },
    [mostrarToast, bump],
  );

  // Mapa
  const usarEjemplo = useCallback(() => {
    const m = mapRef.current;
    m.path = EXAMPLE;
    m.source = "pista de pruebas";
    m.pending = false;
    resetEncuadre();
    registrar("Mapa", "Usando el plano de la pista de pruebas");
    bump();
  }, [registrar, bump]);
  const rehacerMapa = useCallback(() => {
    mapRef.current.pending = true;
    mostrarToast("El mapa se rehará en la próxima vuelta desde la meta.");
    bump();
  }, [mostrarToast, bump]);

  const toggleSenal = useCallback(
    (s: "err" | "pl" | "pr") => setShow((o) => ({ ...o, [s]: !o[s] })),
    [],
  );

  // Robot / perfil
  const selectRobot = useCallback(
    (id: string) => {
      if (id === live.current.robotId) return;
      if (live.current.running) return mostrarToast("Detén el robot antes de cambiar.");
      setRobotId(id);
      setCalibrated(false);
      lapsRef.current = [];
      lastLapRef.current = null;
      lapCountRef.current = 0;
      bestSecRef.current = [Infinity, Infinity, Infinity];
      lastBinsRef.current = null;
      const r = robotById(robots, id)!;
      if (!r.fw && live.current.source === "robot") setSourceState("sim");
      engRef.current.reset(live.current.applied.ctrl);
      registrar(
        "Consola",
        `Robot seleccionado: ${r.nm} ${curVer(r).v}. Paneles armados desde su manifiesto`,
        "good",
      );
      mostrarToast(`${r.nm}: la consola muestra solo lo que este robot tiene.`);
    },
    [robots, registrar, mostrarToast],
  );
  const setProfile = useCallback(
    (id: string) => {
      setProfileId((cur) => {
        if (id === cur) return cur;
        store.set("profile", id);
        const p = profById(perfiles, id)!;
        registrar("Reglamento", `Perfil activo: ${p.comp} · ${p.cat}`, "good");
        mostrarToast(`Perfil activo: ${p.comp} · ${p.cat}. La consola y el armador se ajustan.`);
        return id;
      });
    },
    [perfiles, registrar, mostrarToast],
  );

  const setCatalog = useCallback((f: (c: Componente[]) => Componente[]) => setCatalogState(f), []);
  const setRobots = useCallback((f: (r: RobotDef[]) => RobotDef[]) => setRobotsState(f), []);

  const abrirFicha = useCallback((id: string) => setFichaId(id), []);
  const cerrarFicha = useCallback(() => setFichaId(null), []);
  const abrirRegistro = useCallback(() => setRegOpen(true), []);
  const cerrarRegistro = useCallback(() => setRegOpen(false), []);
  const restablecerDatos = useCallback(() => {
    borrarRegistrados();
    setCatalogState(clone(CAT));
    setRobotsState(clone(ROBOTS));
    setRobotId("v001");
    setFichaId(null);
    mostrarToast("Datos de ejemplo restablecidos.");
  }, [mostrarToast]);
  const abrirManifiesto = useCallback((id: string) => setManifiestoId(id), []);
  const cerrarManifiesto = useCallback(() => setManifiestoId(null), []);
  const abrirEnArmador = useCallback(
    (id: string) => {
      setArmadorInicial(id);
      goTab("armador");
    },
    [goTab],
  );

  const setShowPbi = useCallback((v: boolean) => {
    setShowPbiState(v);
    store.set("pbi", v);
  }, []);
  const setScope = useCallback(
    (v: Alcance) => {
      setScopeState(v);
      store.set("scope", v);
      mostrarToast(
        v === "s1"
          ? "Alcance: Sprint 1. Lo que llega después se ve atenuado."
          : v === "s2"
            ? "Alcance: fin del curso. Solo lo que queda fuera se ve atenuado."
            : "Alcance: todo el diseño.",
      );
    },
    [mostrarToast],
  );

  const valor: Consola = {
    tick,
    tab,
    goTab,
    catalog,
    robots,
    perfiles,
    robot,
    robotId,
    perfil,
    selectRobot,
    setProfile,
    source,
    setSource,
    connected,
    toggleConnected,
    link: linkRef.current,
    mode,
    setMode,
    line,
    setLine,
    calibrated,
    calibrating,
    calProgress,
    calibrar,
    running,
    arrancarDetener,
    locked,
    gate,
    toggleGate,
    comp,
    toggleComp,
    turb,
    setTurb,
    vbat: vbatRef.current,
    cambiarBateria,
    draft,
    applied,
    saved,
    preset,
    setCtrl,
    setParam,
    setPreset,
    enviarSetup,
    guardarSetup,
    laps: lapsRef.current,
    runs: runsRef.current,
    lastLap: lastLapRef.current,
    lastRun: lastRunRef.current,
    lapCount: lapCountRef.current,
    bestSec: bestSecRef.current,
    engMethod,
    setEngMethod,
    ingeniero: engRef.current,
    cargarPropuesta,
    guardarNota,
    mapMode,
    setMapMode,
    usarEjemplo,
    rehacerMapa,
    show,
    toggleSenal,
    setCatalog,
    setRobots,
    log: logRef.current,
    registrar,
    fichaId,
    abrirFicha,
    cerrarFicha,
    regOpen,
    abrirRegistro,
    cerrarRegistro,
    restablecerDatos,
    manifiestoId,
    abrirManifiesto,
    cerrarManifiesto,
    armadorInicial,
    abrirEnArmador,
    blOpen,
    setBlOpen,
    showPbi,
    setShowPbi,
    scope,
    setScope,
    toast,
    mostrarToast,
    simRef,
    mapRef,
    trailRef,
    histRef,
    curBinsRef,
    curCntRef,
    lastBinsRef,
  };

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useConsola(): Consola {
  const c = useContext(Contexto);
  if (!c) throw new Error("useConsola debe usarse dentro de ProveedorConsola");
  return c;
}

export { RANURAS };

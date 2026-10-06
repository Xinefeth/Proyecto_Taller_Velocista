// Vista Mapa de pista (Protoripo.html): reconstrucción desde la vuelta 1 (HU-30, solo análisis),
// desde una foto (HU-32, fuera del curso) y perfil de velocidad por mapa bloqueado (HU-33).
import { useRef, useState } from "react";
import { useConsola } from "../stores/ConsolaContext";
import { Card } from "../components/Card";
import { ICO } from "../components/IconosUI";
import { fmt } from "../logica/formato";
import { colores, drawRec } from "../logica/lienzos";
import { useCanvas } from "../hooks/useCanvas";

function DesdeVuelta() {
  const c = useConsola();
  const m = c.mapRef.current;
  const ref = useCanvas((cv) => drawRec(cv, m.raw, m.corr, m.recording));
  let estado: [string, string], pasos: [string, string, string];
  if (m.recording) {
    estado = ["Mapeando", "tag red"];
    pasos = ["done", "cur", "todo"];
  } else if (m.corr && !m.pending) {
    estado = ["Listo", "tag good"];
    pasos = ["done", "done", "done"];
  } else if (m.pending && m.corr) {
    estado = ["Se rehará", "tag warn"];
    pasos = ["cur", "todo", "todo"];
  } else {
    estado = ["Esperando vuelta", "tag"];
    pasos = ["cur", "todo", "todo"];
  }
  const textos = [
    "Arranca el robot desde la meta y deja que complete una vuelta.",
    "Se estima el recorrido con el modelo PWM → movimiento.",
    "Se corrige la deriva obligando a que la vuelta cierre en la meta.",
  ];
  return (
    <Card className="s6" pbi="HU-30 · SP-03" sprint="C">
      <div className="hd">
        <h2>Desde la primera vuelta</h2>
        <span className={estado[1]}>{estado[0]}</span>
      </div>
      <ol className="steps">
        {textos.map((t, i) => (
          <li key={i} className={pasos[i]}>
            <span>{i + 1}</span>
            {t}
          </li>
        ))}
      </ol>
      <div className="recbox">
        <canvas ref={ref} role="img" aria-label="Recorrido estimado y corregido" />
      </div>
      <div className="st3">
        <div>
          <div className="lbl">Longitud</div>
          <div className="v">{m.stats ? `${fmt(m.stats.len, 2)} m` : "—"}</div>
        </div>
        <div>
          <div className="lbl">Error de cierre</div>
          <div className="v">{m.stats ? `${Math.round(m.stats.closeErr * 100)} cm` : "—"}</div>
        </div>
        <div>
          <div className="lbl">Giro sobrante</div>
          <div className="v">{m.stats ? `${fmt(m.stats.errH, 1)}°` : "—"}</div>
        </div>
      </div>
      <div className="acts" style={{ marginTop: 10 }}>
        <button type="button" className="sb" onClick={c.rehacerMapa}>
          Rehacer en la próxima vuelta
        </button>
        <button type="button" className="sb red" onClick={() => c.goTab("control")}>
          Ir al tablero
        </button>
      </div>
    </Card>
  );
}

function solveH(from: { x: number; y: number }[], to: { x: number; y: number }[]): number[] {
  const A: number[][] = [],
    b: number[] = [];
  for (let i = 0; i < 4; i++) {
    const { x, y } = from[i],
      { x: u, y: v } = to[i];
    A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]);
    b.push(u);
    A.push([0, 0, 0, x, y, 1, -v * x, -v * y]);
    b.push(v);
  }
  for (let col = 0; col < 8; col++) {
    let p = col;
    for (let r = col + 1; r < 8; r++) if (Math.abs(A[r][col]) > Math.abs(A[p][col])) p = r;
    [A[col], A[p]] = [A[p], A[col]];
    [b[col], b[p]] = [b[p], b[col]];
    for (let r = 0; r < 8; r++) {
      if (r === col) continue;
      const f = A[r][col] / A[col][col];
      for (let k = col; k < 8; k++) A[r][k] -= f * A[col][k];
      b[r] -= f * b[col];
    }
  }
  return b.map((v, i) => v / A[i][i]);
}

function DesdeFoto() {
  const c = useConsola();
  const col = colores();
  const pcv = useRef<HTMLCanvasElement>(null);
  const wcv = useRef<HTMLCanvasElement>(null);
  const src = useRef(document.createElement("canvas"));
  const srcData = useRef<ImageData | null>(null);
  const corners = useRef<{ x: number; y: number }[]>([]);
  const [estado, setEstado] = useState<[string, string]>(["Sin foto", "tag"]);
  const [step, setStep] = useState(0);
  const [fase, setFase] = useState<"drop" | "marcar" | "listo">("drop");
  const [pw, setPw] = useState("2.44");
  const [ph, setPh] = useState("1.22");
  const [thr, setThr] = useState(90);

  const drawPhoto = () => {
    const cv = pcv.current!;
    const s = src.current;
    const w = cv.clientWidth || 500,
      h = Math.round((w * s.height) / s.width),
      dpr = window.devicePixelRatio || 1;
    cv.width = w * dpr;
    cv.height = h * dpr;
    cv.style.height = h + "px";
    const x = cv.getContext("2d")!;
    x.setTransform(dpr, 0, 0, dpr, 0, 0);
    x.drawImage(s, 0, 0, w, h);
    const k = w / s.width;
    const cs = corners.current;
    if (cs.length) {
      x.strokeStyle = col["--red"];
      x.lineWidth = 2;
      x.beginPath();
      cs.forEach((p, i) => (i ? x.lineTo(p.x * k, p.y * k) : x.moveTo(p.x * k, p.y * k)));
      if (cs.length === 4) x.closePath();
      x.stroke();
      cs.forEach((p, i) => {
        x.fillStyle = col["--red"];
        x.beginPath();
        x.arc(p.x * k, p.y * k, 9, 0, Math.PI * 2);
        x.fill();
        x.fillStyle = "#fff";
        x.font = `600 10px ${col["--mono"]}`;
        x.textAlign = "center";
        x.fillText(String(i + 1), p.x * k, p.y * k + 3.5);
        x.textAlign = "start";
      });
    }
  };

  const warp = () => {
    const Wm = parseFloat(pw) || 2.44,
      Hm = parseFloat(ph) || 1.22,
      W = 520,
      H = Math.max(60, Math.round((W * Hm) / Wm));
    const h = solveH(
      [
        { x: 0, y: 0 },
        { x: W, y: 0 },
        { x: W, y: H },
        { x: 0, y: H },
      ],
      corners.current,
    );
    const inv = c.line === "blanca";
    const cv = wcv.current!;
    cv.width = W;
    cv.height = H;
    const x = cv.getContext("2d")!,
      out = x.createImageData(W, H),
      d = srcData.current!.data,
      sw = src.current.width,
      sh = src.current.height;
    for (let y = 0; y < H; y++)
      for (let xx = 0; xx < W; xx++) {
        const den = h[6] * xx + h[7] * y + 1,
          u = Math.round((h[0] * xx + h[1] * y + h[2]) / den),
          v = Math.round((h[3] * xx + h[4] * y + h[5]) / den),
          o = (y * W + xx) * 4;
        let on = false;
        if (u >= 0 && v >= 0 && u < sw && v < sh) {
          const i = (v * sw + u) * 4,
            l = 0.299 * d[i] + 0.587 * d[i + 1] + 0.114 * d[i + 2];
          on = inv ? l > 255 - thr : l < thr;
        }
        const cc = on ? [255, 45, 85] : [11, 13, 18];
        out.data[o] = cc[0];
        out.data[o + 1] = cc[1];
        out.data[o + 2] = cc[2];
        out.data[o + 3] = 255;
      }
    x.putImageData(out, 0, 0);
    cv.style.display = "block";
    setEstado([`1 px = ${fmt((Wm * 1000) / W, 1)} mm`, "tag good"]);
    setStep(3);
  };

  const loadPhoto = (file: File) => {
    const img = new Image();
    img.onload = () => {
      const s = src.current;
      const k = Math.min(1, 1200 / Math.max(img.width, img.height));
      s.width = Math.round(img.width * k);
      s.height = Math.round(img.height * k);
      const sx = s.getContext("2d", { willReadFrequently: true })!;
      sx.drawImage(img, 0, 0, s.width, s.height);
      srcData.current = sx.getImageData(0, 0, s.width, s.height);
      corners.current = [];
      setFase("marcar");
      setEstado(["Marca 4 esquinas", "tag red"]);
      setStep(1);
      requestAnimationFrame(drawPhoto);
      URL.revokeObjectURL(img.src);
    };
    img.src = URL.createObjectURL(file);
  };

  const onPointer = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (corners.current.length >= 4) return;
    const cv = pcv.current!,
      r = cv.getBoundingClientRect(),
      k = src.current.width / r.width;
    corners.current = [...corners.current, { x: (e.clientX - r.left) * k, y: (e.clientY - r.top) * k }];
    drawPhoto();
    if (corners.current.length === 4) {
      setStep(2);
      warp();
    }
  };

  const textos = [
    "Sube una foto de la pista, lo más desde arriba posible.",
    "Toca las 4 esquinas: arriba izq., arriba der., abajo der., abajo izq.",
    "Ajusta el umbral hasta que solo quede la línea.",
    "Extraer el trazo ordenado (fuera de este curso).",
  ];

  return (
    <Card className="s6" pbi="HU-32" sprint="W">
      <div className="hd">
        <h2>Desde una foto</h2>
        <span className={estado[1]}>{estado[0]}</span>
      </div>
      <ol className="steps">
        {textos.map((t, i) => (
          <li key={i} className={i < step ? "done" : i === step ? "cur" : "todo"}>
            <span>{i + 1}</span>
            {t}
          </li>
        ))}
      </ol>
      <label className="drop" style={{ display: fase === "drop" ? "grid" : "none" }}>
        <input
          type="file"
          accept="image/*"
          onChange={(e) => e.target.files?.[0] && loadPhoto(e.target.files[0])}
        />
        <span>
          <b>Elige una foto</b>
          <br />o arrástrala aquí
        </span>
      </label>
      <canvas
        ref={pcv}
        className="pcv"
        aria-label="Foto de la pista: toca las 4 esquinas"
        style={{ display: fase !== "drop" ? "block" : "none" }}
        onPointerDown={onPointer}
      />
      <div className="pctl" style={{ display: fase !== "drop" ? "grid" : "none" }}>
        <label className="fld">
          <span className="lbl">Ancho (m)</span>
          <input className="inp" inputMode="decimal" value={pw} onChange={(e) => { setPw(e.target.value); if (corners.current.length === 4) warp(); }} />
        </label>
        <label className="fld">
          <span className="lbl">Largo (m)</span>
          <input className="inp" inputMode="decimal" value={ph} onChange={(e) => { setPh(e.target.value); if (corners.current.length === 4) warp(); }} />
        </label>
        <label className="fld thr">
          <span className="lbl">Umbral {thr}</span>
          <input type="range" min={20} max={220} value={thr} onChange={(e) => { setThr(+e.target.value); if (corners.current.length === 4) warp(); }} />
        </label>
      </div>
      <canvas ref={wcv} className="wcv" aria-label="Pista corregida y binarizada" style={{ display: "none" }} />
      <div className="acts" style={{ display: fase !== "drop" ? "grid" : "none" }}>
        <button
          type="button"
          className="sb"
          onClick={() => {
            corners.current = [];
            if (wcv.current) wcv.current.style.display = "none";
            setEstado(["Marca 4 esquinas", "tag red"]);
            setStep(1);
            drawPhoto();
          }}
        >
          Marcar esquinas de nuevo
        </button>
        <button type="button" className="sb" disabled>
          Extraer trazo
        </button>
      </div>
    </Card>
  );
}

export function Mapa() {
  const c = useConsola();
  const why = c.perfil.r.mapaVel
    ? "Permitido por este perfil, pero la función queda fuera de este curso (HU-33)."
    : `Bloqueado por ${c.perfil.comp} · ${c.perfil.cat}: el robot solo puede guiarse por la línea, sin movimientos pre-programados.`;
  return (
    <section className="view on dv" aria-label="Mapa de pista">
      <DesdeVuelta />
      <DesdeFoto />
      <Card className="s6" pbi="HU-33" sprint="W">
        <div className="hd">
          <h2>Perfil de velocidad por mapa</h2>
          <span className={`tag ${c.perfil.r.mapaVel ? "" : "warn"}`}>{c.perfil.r.mapaVel ? "Fuera del curso" : "Bloqueado"}</span>
        </div>
        <p className="muted" style={{ margin: "0 0 10px", fontSize: 13 }}>
          Frenar antes de cada curva usando el mapa. Solo se habilita si el perfil de reglamento lo permite.
        </p>
        <div>
          <div className="lockrow">
            {ICO.lock}
            <span>{why}</span>
          </div>
        </div>
      </Card>
      <Card className="s6">
        <div className="hd">
          <h2>Para qué sirve el mapa</h2>
        </div>
        <p className="rule" style={{ border: 0, padding: 0, background: "none" }}>
          <b>Solo para analizar en la laptop.</b> Muchik Rumble 4 exige que el robot base su movimiento únicamente en el
          sensado de la línea, sin movimientos pre-programados. Además, cada intento es de una sola vuelta.
        </p>
      </Card>
    </section>
  );
}

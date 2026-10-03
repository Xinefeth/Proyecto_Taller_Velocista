// Verificación del entorno (EN-03): API, base de datos y tiempo real, con ayuda si algo falla.
import { useConexion } from "../stores/ConexionContext";
import type { EstadoConexion } from "../types/api";

const AYUDA: Record<string, string> = {
  API: "cd api · uvicorn app.main:app --reload --port 8000",
  "Base de datos": "docker compose up -d · cd api · alembic upgrade head",
  "Tiempo real": "Depende de la API en el puerto 8000",
};

function Fila({ nombre, estado }: { nombre: string; estado: EstadoConexion }) {
  return (
    <div className="chk">
      <span className={`dot ${estado}`} aria-hidden="true" />
      <span>
        {nombre}:{" "}
        <b>{estado === "ok" ? "conectada" : estado === "falla" ? "sin conexión" : "revisando"}</b>
      </span>
      {estado === "falla" && <span className="ayuda m">{AYUDA[nombre]}</span>}
    </div>
  );
}

export function Sistema() {
  const { salud, api, baseDeDatos, tiempoReal, mensajes } = useConexion();
  const listo = api === "ok" && baseDeDatos === "ok" && tiempoReal === "ok";
  return (
    <div className="pend">
      <div className="card">
        <div className="hd">
          <span className="lbl">Entorno {salud ? `· ${salud.entorno}` : ""}</span>
          <span className="lbl">{listo ? "Listo para trabajar" : "Revisa lo que falta"}</span>
        </div>
        <Fila nombre="API" estado={api} />
        <Fila nombre="Base de datos" estado={baseDeDatos} />
        <Fila nombre="Tiempo real" estado={tiempoReal} />
      </div>
      <div className="card">
        <div className="hd">
          <span className="lbl">Mensajes en vivo (/ws/consola)</span>
        </div>
        {mensajes.length === 0 ? (
          <p className="muted">Aún no llegan mensajes.</p>
        ) : (
          <ul className="m">
            {mensajes.slice(0, 15).map((m, i) => (
              <li key={i}>
                <span className="id">{m.origen}</span>
                <span>
                  {m.tipo} · {JSON.stringify(m.datos).slice(0, 90)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

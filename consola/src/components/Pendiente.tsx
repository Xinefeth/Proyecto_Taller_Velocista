// Panel que muestra qué ítems del backlog construyen una pantalla todavía no migrada.
import type { Seccion } from "../secciones";

export function Pendiente({ seccion }: { seccion: Seccion }) {
  return (
    <div className="card pend">
      <h2>{seccion.titulo}</h2>
      <p className="muted">
        Esta pantalla se migra desde el prototipo con los siguientes ítems del Product Backlog:
      </p>
      <ul>
        {seccion.pendientes.map(([id, titulo]) => (
          <li key={id}>
            <span className="id m">{id}</span>
            <span>{titulo}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

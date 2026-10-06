// Aviso breve (toast) de la consola (Protoripo.html).
import { useConsola } from "../stores/ConsolaContext";

export function Toast() {
  const { toast } = useConsola();
  return (
    <div id="toast" role="status" aria-live="polite" className={toast ? "show" : ""}>
      {toast}
    </div>
  );
}

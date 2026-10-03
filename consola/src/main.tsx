import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/geist-sans/300.css";
import "@fontsource/geist-sans/400.css";
import "@fontsource/geist-sans/500.css";
import "@fontsource/geist-sans/600.css";
import "@fontsource/geist-mono/400.css";
import "@fontsource/geist-mono/500.css";
import "./styles/prototipo.css";
import "./styles/app.css";
import App from "./App";
import { ProveedorConexion } from "./stores/ConexionContext";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ProveedorConexion>
      <App />
    </ProveedorConexion>
  </StrictMode>,
);

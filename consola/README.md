# Consola

Frontend en **React 18 + TypeScript + Vite** con el sistema visual del prototipo ("APAEC Mission Control"). La estructura sigue DO-02: las páginas no llaman a la red; todo pasa por `services/`.

## Arranque

```bash
cd consola
npm ci            # versiones exactas de package-lock.json
npm run dev       # http://localhost:5173 (proxy de /api y /ws hacia :8000)
```

## Estructura

```
src/
├── main.tsx  App.tsx    Entrada y estructura: barra lateral + franja superior + página
├── secciones.ts         Secciones del prototipo y los ítems del backlog que las construyen
├── pages/               Una página por pestaña (Control, Telemetría, Corridas, Mapa, Catálogo, Armador, Reglamento, Sistema)
├── components/          Barra lateral, franja superior, indicadores, íconos
├── services/            api.ts (HTTP) · ws.ts (WebSocket) — únicos que usan la red
├── hooks/               useSalud · useTiempoReal
├── stores/              Contexto de conexión compartido
├── types/               Tipos de respuestas y mensajes
└── styles/              prototipo.css (tal cual del prototipo) · app.css
```

## Comandos

| Qué | Comando |
| --- | --- |
| Desarrollo | `npm run dev` |
| Pruebas | `npm test` |
| Tipos | `npm run typecheck` |
| Lint | `npm run lint` |
| Formato | `npm run format` |
| Compilar para pista | `npm run build` (la API sirve `dist/` en `:8000`) |

## Reglas

- Solo `src/services/` usa `fetch` y `WebSocket` (lo hace cumplir ESLint).
- Sin CDN ni fuentes externas: las fuentes Geist se empaquetan con `@fontsource`.
- Las reglas críticas (competencia, calibración, rangos, cálculo de J) viven en la API; la consola solo ayuda visualmente.
- Cada pantalla se migra del prototipo en su ítem (EN-19 y las HU listadas en `secciones.ts`).

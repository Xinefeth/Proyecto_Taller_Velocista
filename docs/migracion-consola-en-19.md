# Migración del prototipo a la consola (EN-19)

Migración de la maqueta v2 **`Protoripo.html`** (“APAEC Lab · Consola y gestión”, un único archivo HTML + CSS + JS de ~1 749 líneas) a la aplicación **React 18 + TypeScript + Vite** del monorepo (`/consola`), respetando la estructura de carpetas, la lógica y la arquitectura existentes.

- **Ítem principal:** EN-19 (migrar el prototipo de la consola a la app).
- **Ítems cubiertos de paso:** EN-02, EN-05, HU-01–HU-11, HU-13–HU-33, SP-01, SP-03, HU-27–HU-29.
- **Rama:** `en-19/migrar-prototipo-consola` (sin commits; no se sube nada sin permiso).
- **Fecha:** 5 de octubre de 2026.

---

## 1. Resultado

Las **7 secciones** del prototipo quedaron migradas a React y funcionando de punta a punta en modo **Simulado**:

| Sección | Vista | Ítems |
|---|---|---|
| Control | `pages/Control.tsx` | EN-19, HU-13–HU-18, HU-21–HU-24, HU-30, HU-11 |
| Telemetría | `pages/Telemetria.tsx` | HU-21, HU-25, EN-20 |
| Corridas y optimización | `pages/Corridas.tsx` | HU-19, HU-20, HU-26, HU-27, HU-28, HU-29 |
| Mapa de pista | `pages/Mapa.tsx` | HU-30, SP-03, HU-32, HU-33 |
| Catálogo | `pages/Catalogo.tsx` | HU-01–HU-05, EN-17 |
| Armador | `pages/Armador.tsx` | HU-06–HU-10, HU-12 (Won’t) |
| Reglamento | `pages/Reglamento.tsx` | HU-10, HU-11, SP-01 |

Verificado en el navegador (dev server): se calibra, arranca en modo simulado, el robot recorre la pista, **se construye el mapa desde la vuelta 1**, se cronometra por sectores, se registran corridas y el ingeniero de pista propone ajustes; las tres vistas de gestión renderizan con datos reales y cálculos en vivo. **Sin errores de consola.**

---

## 2. Decisiones de arquitectura

1. **Separación en capas puras + estado + UI.** El prototipo mezclaba datos, física, lógica de negocio y manipulación directa del DOM en un IIFE. Se separó en:
   - **Datos** (`src/datos/`): constantes semilla (catálogo, robots, perfiles, controladores).
   - **Tipos** (`src/types/`): interfaces del dominio y de corridas.
   - **Lógica** (`src/logica/`): funciones puras y clases sin DOM (formato, dominio, simulador, ingeniero, lienzos).
   - **Estado** (`src/stores/ConsolaContext.tsx`): un único store con el bucle de simulación y las acciones.
   - **UI** (`src/components/`, `src/pages/`): componentes React que consumen el store.

2. **El bucle de simulación vive en el store, no en los componentes.** Un solo `requestAnimationFrame` avanza el `Simulador` a ~1000 Hz (pasos de `DT = 0,002 s`), registra vueltas/corridas y sube un contador `tick` para que las vistas en vivo se re-rendericen. Los valores de alta frecuencia (posición del simulador, batería, buffers de señales, mapa) viven en **refs**, no en estado de React, para no re-renderizar en cada paso de física.

3. **Lienzos imperativos sobre refs.** Los canvas (mapa, señales, salud, reconstrucción) se dibujan con funciones puras (`src/logica/lienzos.ts`) a través del hook `useCanvas`, que redibuja en cada frame y al redimensionar. Esto reproduce fielmente el render del prototipo sin forzar estado reactivo por píxel.

4. **Reutilización total de `prototipo.css`.** El sistema visual ya estaba extraído en `src/styles/prototipo.css` (es el stylesheet del propio prototipo, formateado). La migración **no reescribe estilos**: reusa las clases existentes (`.card`, `.mc`, `.go`, `.bars`, `.runchart`, `.ct`, `.slot`, `.rt`, `.blp`, `.bottom-nav`, chips `.pbi`, etc.).

5. **Modo Simulado vs. Robot (EN-05).** El store implementa el modo **Simulado** completo (la maqueta). El interruptor **Robot** queda como gancho: al no haber robot real, vuelve a Simulado (igual que el prototipo). El camino al backend real (`services/api.ts`, `services/ws.ts`) se conserva para cuando se cablee EN-04/EN-12/EN-24.

6. **Capa del backlog como datos + CSS.** Los chips `data-pbi`/`data-sprint` se centralizan en el componente `Card`; la visibilidad y la atenuación por alcance las maneja el CSS existente (`body.show-pbi`, `body[data-scope]`).

---

## 3. Estructura de archivos

### Nuevos

```
src/
├─ datos/
│  ├─ tipos.ts            # TIPOS de componente con capacidades (DO-03)
│  ├─ catalogo.ts         # CAT (25 componentes semilla) + RANURAS del armador
│  ├─ robots.ts           # ROBOTS con versiones y piezas + TIPO
│  ├─ reglamento.ts       # PERFILES (MR4 A/S/M + Club), GENERALES, REGLAS
│  └─ controladores.ts    # PDEF (parámetros), CTRL (PID/adaptativo/difuso), psum, differs
├─ types/
│  ├─ dominio.ts          # Componente, Robot, Version, Perfil, Setup, Hechos, Chequeo…
│  └─ corridas.ts         # Vuelta, Corrida
├─ logica/
│  ├─ formato.ts          # fmt, clamp, money, num, clone
│  ├─ dominio.ts          # facts, compat (HU-08), checks (HU-10), complies, manifest (EN-02)
│  ├─ simulador.ts        # TRACK, Simulador (física), construirMapa (HU-30)
│  ├─ ingeniero.ts        # Ingeniero: Twiddle (HU-27) + bayesiana (HU-28)
│  └─ lienzos.ts          # helpers de canvas + drawMap/drawChart/drawHealth/drawRec
├─ hooks/
│  └─ useCanvas.ts        # redibuja un canvas por frame y en resize
├─ stores/
│  └─ ConsolaContext.tsx  # store central: bucle de simulación, estado y acciones
├─ components/
│  ├─ Card.tsx            # tarjeta + chip de backlog (data-pbi/data-sprint)
│  ├─ IconosUI.tsx        # íconos de severidad y de acción
│  ├─ BottomNav.tsx       # navegación móvil
│  ├─ BacklogLayer.tsx    # capa del backlog (IDs y alcance)
│  ├─ Toast.tsx           # avisos
│  ├─ Drawer.tsx          # ficha del componente (HU-03)
│  ├─ RegistroModal.tsx   # registrar componente (HU-02 / HU-05)
│  ├─ ManifiestoModal.tsx # manifiesto del robot (EN-02)
│  └─ Capas.tsx           # scrim + modales
└─ pages/                 # Control, Telemetria, Corridas, Mapa, Catalogo, Armador, Reglamento
```

### Modificados

- `src/App.tsx` — estructura (riel, franja, vista activa, nav móvil, backlog, modales, toast); navegación vía store.
- `src/components/Rail.tsx` — riel con grupos Robot/Gestión + botón Backlog.
- `src/components/Strip.tsx` — franja con selector de robot, batería/enlace simulados, tiempos, fuente y chip de reglamento.
- `src/main.tsx` — envuelve la app en `ProveedorConsola`.
- `src/App.test.tsx` — pruebas adaptadas a la nueva UI.

### Eliminados (andamiaje que el prototipo reemplaza)

- `src/components/Pendiente.tsx`, `src/secciones.ts`, `src/components/Indicador.tsx`.

### Conservados sin montar (camino al backend real)

- `src/stores/ConexionContext.tsx`, `src/pages/Sistema.tsx`, `src/hooks/useSalud.ts`, `src/hooks/useTiempoReal.ts`, `src/services/api.ts`, `src/services/ws.ts` (+ sus tests). Siguen siendo la base para el **modo Robot**/salud (EN-05, EN-24); hoy no los monta la app.

---

## 4. Mapeo prototipo → React (lo relevante)

- **Modelo de datos (DO-03):** `TYPES/CAT/SLOTS/ROBOTS/PROFILES` → `src/datos/*`. Encoder, IMU y turbina se modelan aunque el Velocista 001 no los use.
- **Hechos y reglas:** `facts()` (costo, masa, consumo, sensores…), `compat()` (HU-08), `checks()` (HU-10), `complies()` y `manifest()` (EN-02) → `src/logica/dominio.ts`, puras y testeables (reciben catálogo/robots por parámetro).
- **Controladores (HU-17, EN-21, HU-31):** PID, PID adaptativo y difuso con sus parámetros, presets y `psum` → `src/datos/controladores.ts`. El simulador los “enchufa” por `ctrl`.
- **Física (EN-10 conceptual):** `sim.step()` con error de posición, PID/adaptativo/difuso, compensación de batería, sectores S1–S3 y clasificación de tramos → `src/logica/simulador.ts`.
- **Mapa (HU-30, solo análisis):** estimación PWM→movimiento durante la vuelta 1 y corrección de deriva (`construirMapa`).
- **Métrica J (SP-01):** `J = tiempo + 2 × error acumulado`; `J = 120` si no termina. Vive en `registrarCorrida` del store.
- **Ingeniero de pista (HU-27/HU-28):** `Ingeniero` con Twiddle y una bayesiana (proceso gaussiano aproximado por muestreo) → `src/logica/ingeniero.ts`.
- **Interacción:** los `document.getElementById(...).textContent = ...`, `addEventListener`, `localStorage` y el `requestAnimationFrame` del prototipo se tradujeron a estado/acciones del store, `useState`/`useEffect` y refs. La persistencia (`perfil`, `pbi`, `scope`) usa `localStorage` con el mismo prefijo `apaec.v2.*`.

---

## 5. Verificación

| Comprobación | Comando | Resultado |
|---|---|---|
| Tipos | `npm run typecheck` | ✅ sin errores |
| Lint | `npm run lint` | ✅ sin errores |
| Pruebas | `npm run test` | ✅ 7/7 |
| Build | `npm run build` | ✅ (JS 275 kB / 86 kB gzip; CSS 85 kB / 37 kB gzip) |
| Navegador | `npm run dev` | ✅ 7 vistas OK, ciclo calibrar→arrancar→vuelta→mapa→corrida, **0 errores de consola** |

---

## 6. Pendientes y notas

- **Modo Robot real (EN-05/EN-12):** hoy vuelve a Simulado. Falta cablear WebSocket/manifiesto reales contra el firmware y la API.
- **Persistencia en la API (EN-04/EN-17/EN-20):** catálogo, robots, setups y corridas viven en memoria (estado del store, semilla de `src/datos`). Al implementar EN-04 se sustituye la semilla por llamadas a `services/api.ts`.
- **Despliegue en la nube (EN-24):** decidir en DO-02 cómo conecta el robot cuando la consola va por HTTPS (`wss://` al servidor o un puente), ya que `wss://` no puede abrir `ws://` al ESP32.
- **Rendimiento:** en las vistas Robot el store sube `tick` por frame (como el prototipo). Las vistas de gestión solo se re-renderizan por acción del usuario. Si en un equipo lento se nota, se puede separar el contexto en “estructural” y “vivo”.
- **Sistema/salud (EN-03):** `Sistema.tsx` + `ConexionContext` quedan listos pero fuera del riel del prototipo; reubicarlos cuando exista el modo Robot.

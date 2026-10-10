# Especificaciones (Spec-Driven Development)

Una carpeta por historia de usuario, con `spec.md` (qué y por qué), `plan.md` (cómo, con
tecnología) y `tasks.md` (tareas). La constitución del proyecto está en
[`.specify/memory/constitution.md`](../.specify/memory/constitution.md).

| HU | Carpeta | Módulos que toca | Estado |
|---|---|---|---|
| HU-13 · Seleccionar el robot | [`013-select-robot`](013-select-robot/) | builder, devices, catalog, consola | Backend listo; **integración consola→API pendiente** (la consola usa datos locales) |
| HU-14 · Estado del robot | [`014-robot-status`](014-robot-status/) | gateway, system, consola | Barra existe con **datos simulados**; tiempos (1 s / 2 s) **sin verificar** |
| HU-15 · Regleta de sensores | [`015-sensor-strip`](015-sensor-strip/) | gateway, devices, consola | **Pendiente**: falta la vista de 16 barras + posición (mm) + centrada (solo WebSocket) |
| HU-16 · Calibrar y arrancar | [`016-calibrate-and-start`](016-calibrate-and-start/) | devices, gateway, consola | **Cumplido** salvo verificar tiempo de calibración (< 20 s) |

## Convención

- Nombres de carpeta en inglés (`013-select-robot`, …); el contenido en español con los
  identificadores técnicos en inglés.
- El estado distingue: **cumplido**, **parcial/pendiente** y **no verificado** (lo que no
  se pudo comprobar sin robot real o sin PostgreSQL levantado).
- Pendientes transversales a varias HU: campos aún en español (ver
  [`docs/rename-glosario.md`](../docs/rename-glosario.md)), el ejemplo del manifiesto con
  texto aleatorio en Swagger, y la respuesta `503` sin documentar.

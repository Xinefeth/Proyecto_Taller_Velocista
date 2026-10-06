# EN-03 · Repositorio y entorno

Documentación técnica del habilitador **EN-03 — Preparar el repositorio y el entorno**: la base común (monorepo, control de versiones, entorno de desarrollo, calidad y CI) sobre la que los cuatro integrantes trabajan en paralelo sin chocar.

- **Tipo:** Habilitador (EN) · **Prioridad:** Must · **Sprint:** 1 (semana 1) · **Responsable:** CTR.
- **Fuente de verdad operativa:** [`README.md`](../../README.md) (arranque) y [`CONTRIBUTING.md`](../../CONTRIBUTING.md) (flujo de trabajo). Este documento explica **el porqué** de cada decisión.

## 1. Criterios de aceptación y cómo se cumplen

| Criterio (Product Backlog v5) | Cómo se cumple |
|---|---|
| Carpetas `/consola`, `/api` y `/firmware` con README de arranque | Monorepo con los tres subproyectos, cada uno con su `README.md` de arranque (§3, §4) |
| Convención de ramas y commits | Definidas en `CONTRIBUTING.md`: ramas `tipo/ID-descripcion` y Conventional Commits en español (§6) |
| Cualquiera clona y levanta el entorno en menos de 15 min | Un solo script (`scripts/setup.sh` / `setup.ps1`) deja el entorno listo de punta a punta (§4) |
| *(DoD)* Integrado en `main`, probado y documentado | CI en cada PR (API + consola + firmware) y este documento (§5, §7) |

## 2. Decisiones de ingeniería

1. **Monorepo multi-stack.** Un solo repositorio con tres tecnologías (Python/FastAPI, React/TS, C++/PlatformIO). Motivo: el sistema es pequeño, los contratos (REST y mensajes) cruzan las tres partes y conviene versionarlos juntos; un cambio de contrato entra en un solo PR coherente.

2. **Local y offline por diseño.** Todo corre en una laptop y una Wi-Fi propia, sin internet. PostgreSQL se publica **solo en `127.0.0.1`** (nunca a la red), y la consola no usa CDNs ni fuentes externas (Geist se empaqueta con `@fontsource`). > Nota: el *Project Charter v1.3* introduce el despliegue en la nube (EN-24); ese cambio se aborda en su propio ítem y en DO-02. Este documento describe el entorno de **desarrollo** local.

3. **Versiones fijadas (builds reproducibles).** La API usa `requirements.lock` (versiones exactas) y la consola `package-lock.json` con `npm ci`. Así "funciona en mi máquina" = "funciona en la tuya" = "funciona en CI".

4. **Setup idempotente en un comando.** El script detecta requisitos, crea `.env`, levanta la base, instala dependencias, aplica migraciones y genera los `config.h` del firmware. Se puede re-ejecutar sin romper nada (no pisa `.env` ni `config.h` existentes).

5. **Calidad automatizada y uniforme.** Formato, lint, tipos y pruebas por subproyecto, con las mismas reglas en local (pre-commit opcional) y en CI (obligatorio en cada PR).

## 3. Estructura del monorepo

```
apaec-lab/
├── api/                Backend · Python 3.12 · FastAPI · monolito modular (DO-02)
├── consola/            Frontend · React 18 · TypeScript · Vite
├── firmware/
│   ├── velocista/      Robot · ESP32-S3 · PlatformIO
│   └── cronometro/     Cronómetro de meta · ESP32 · PlatformIO
├── docs/               Arquitectura (DO-02), despliegue en pista, repositorio (este doc)
├── scripts/            setup.sh (Linux/macOS) · setup.ps1 (Windows)
├── .github/            CI (workflows/ci.yml), CODEOWNERS, plantillas de PR e issues
├── docker-compose.yml  PostgreSQL 16 local (solo 127.0.0.1)
├── .env.example        Plantilla de variables de entorno
├── .editorconfig       Estilo transversal (charset, EOL, indentación)
├── .gitattributes      Normalización de finales de línea
├── .gitignore          Ignora secretos, artefactos y dependencias
└── .pre-commit-config.yaml   Hooks opcionales de formato antes del commit
```

Cada subproyecto es autónomo (sus dependencias, sus pruebas, su README) pero comparte la configuración transversal de la raíz (§5).

## 4. Entorno de desarrollo

### Requisitos (una vez)

| Herramienta | Versión | Para |
|---|---|---|
| Git | 2.40+ | Control de versiones |
| Python | 3.12+ | API |
| Node.js | 20 o 22 LTS | Consola |
| Docker Desktop | reciente | PostgreSQL ([alternativa sin Docker](../postgres-sin-docker.md)) |
| VS Code + PlatformIO | — | Solo firmware |

### Qué hace el script de setup

`scripts/setup.sh` (Linux/macOS) y `scripts/setup.ps1` (Windows) ejecutan, en orden:

1. **Verifica requisitos** — busca Python ≥ 3.12 y Node; aborta con mensaje claro si falta alguno.
2. **Variables de entorno** — copia `.env.example` → `.env` si no existe (no lo pisa).
3. **PostgreSQL** — `docker compose up -d db` y espera a `pg_isready` (hasta 30 s). Si no hay Docker, avisa y remite a `docs/postgres-sin-docker.md`.
4. **API** — crea `.venv`, instala `requirements.lock` + el paquete editable, y aplica `alembic upgrade head` si la base está lista.
5. **Consola** — `npm ci` (instalación reproducible).
6. **Firmware** — genera `include/config.h` desde `config.example.h` en ambos proyectos (para completar Wi-Fi/IP/token).

Al terminar imprime los dos comandos para levantar API y consola. Objetivo medido: **< 15 min** desde el clon (criterio de EN-03; cada integrante anota su tiempo en su primer día, ver `CONTRIBUTING.md`).

### Levantar

```bash
# Terminal 1 · API  → http://localhost:8000  (OpenAPI en /docs, salud en /api/salud)
cd api && source .venv/bin/activate      # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 · Consola → http://localhost:5173  (proxy de /api y /ws hacia :8000)
cd consola && npm run dev
```

## 5. Configuración transversal

| Archivo | Rol | Puntos clave |
|---|---|---|
| `.env.example` → `.env` | Secretos y configuración local | BD, `SECRET_KEY`, `CORS_ORIGINS`, tokens de dispositivo. `.env` **nunca** se sube |
| `docker-compose.yml` | PostgreSQL 16 | `postgres:16-alpine`, publicado en `127.0.0.1:5432`, volumen con nombre, `healthcheck` con `pg_isready` |
| `.editorconfig` | Estilo | UTF-8, EOL `lf`, nueva línea final, sin espacios colgantes; 2 espacios (4 en Python); `crlf` en `.ps1` |
| `.gitattributes` | Finales de línea | `* text=auto eol=lf`; `.ps1` → `crlf`; imágenes como binario |
| `.gitignore` | Qué no se versiona | `.env`, `config.h`, `.venv/`, `node_modules/`, `dist/`, `.pio/`, cachés, logs |
| `.pre-commit-config.yaml` | Hooks opcionales | Ruff (solo `api/`), fin de archivo, espacios, conflictos de merge, detección de claves privadas |

## 6. Convenciones de ramas y commits (resumen)

Detalle completo en `CONTRIBUTING.md`.

- **Ramas:** `main` (siempre funciona, protegida, solo por PR con 1 aprobación) + una rama por ítem `tipo/ID-descripcion-corta` (tipos `feat`, `fix`, `docs`, `chore`, `test`, `spike`), p. ej. `feat/HU-01-lista-catalogo`.
- **Commits:** Conventional Commits en español — `tipo(alcance): descripción en imperativo [ID]`. Alcances: `api`, `consola`, `velocista`, `cronometro`, `db`, `docs`, `repo`. Ej.: `chore(repo): configura docker-compose para PostgreSQL [EN-03]`.
- **PR:** plantilla obligatoria, 1 revisión, CI en verde, *Squash and merge* y borrar la rama. Nadie integra su propio PR. CODEOWNERS pide la revisión del responsable del área.

## 7. Calidad y CI

Cada subproyecto trae sus herramientas; el flujo de trabajo (`.github/workflows/ci.yml`) las ejecuta en **cada pull request y push a `main`**, en tres jobs en paralelo:

| Job | Pasos |
|---|---|
| **api** | Levanta PostgreSQL de servicio → `ruff format --check` + `ruff check` → `alembic upgrade head` → `pytest --cov` |
| **consola** | `npm ci` → `format:check` → `lint` → `typecheck` → `test` → `build` |
| **firmware** (matriz velocista/cronometro) | `pio test -e native` (lógica pura en PC) → `pio run` (compila para la placa) |

Comandos equivalentes en local:

| Subproyecto | Formato / lint | Tipos | Pruebas |
|---|---|---|---|
| `api/` | `ruff format . && ruff check .` | — | `pytest` (`--cov` para cobertura) |
| `consola/` | `npm run lint` · `npm run format` | `npm run typecheck` | `npm test` |
| `firmware/<proyecto>/` | clang-format (VS Code) | — | `pio test -e native` |

> El CI es solo para desarrollo: **el sistema en pista no depende de él** para funcionar.

## 8. Redes y puertos

| Servicio | Desarrollo | En pista |
|---|---|---|
| API + WebSocket | `localhost:8000` | `192.168.50.10:8000` |
| Consola | `localhost:5173` (dev) | servida por la API en `:8000` |
| PostgreSQL | `127.0.0.1:5432` | `127.0.0.1:5432` (nunca expuesto a la red) |
| Robot / cronómetro | — | `192.168.50.101` / `192.168.50.102` |

## 9. Estado y notas

- **EN-03 entregado** (commit `chore(repo): estructura del monorepo, entorno y pruebas [EN-03]`): estructura, entorno reproducible, convenciones y CI operativos; los tres subproyectos levantan en limpio.
- La **lógica de cada ítem** se construye encima de esta base en sus propios PR (API: EN-04 y las HU; consola: EN-19 y las HU; firmware: EN-09/EN-10/EN-12…).
- **Secretos:** nunca subir `.env` ni los `config.h` del firmware; usar siempre los `*.example` como plantilla.
- **Relacionado:** arquitectura en [`docs/arquitectura`](../arquitectura) (DO-02); despliegue en pista en [`docs/despliegue-pista.md`](../despliegue-pista.md); migración de la consola en [`docs/migracion-consola-en-19.md`](../migracion-consola-en-19.md).

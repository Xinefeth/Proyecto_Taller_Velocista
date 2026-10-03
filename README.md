# APAEC Lab · Sistema de gestión y optimización para competencia robótica

Plataforma local del club para registrar componentes, armar robots, operar el **Velocista 001** en pista, cronometrar sus vueltas y optimizar su controlador (Muchik Rumble 4 · Senior).

Todo funciona en una laptop y una red Wi-Fi propia, **sin internet**. La arquitectura está en [`docs/arquitectura`](docs/arquitectura) (DO-02).

## Estructura

```
apaec-lab/
├── api/          Backend · Python 3.12 · FastAPI · monolito modular (DO-02)
├── consola/      Frontend · React 18 · TypeScript · Vite (sistema visual del prototipo)
├── firmware/
│   ├── velocista/    Robot · ESP32-S3 · PlatformIO
│   └── cronometro/   Cronómetro de meta · ESP32 · PlatformIO
├── docs/         Arquitectura, despliegue en pista y documentos técnicos
├── scripts/      Arranque automático (Windows y Linux/macOS)
├── .github/      CI, plantillas de PR e issues, CODEOWNERS
└── docker-compose.yml   PostgreSQL 16 local
```

## Arranque rápido (menos de 15 minutos)

### 1. Requisitos (una sola vez)

| Herramienta | Versión | Para qué |
| --- | --- | --- |
| [Git](https://git-scm.com/) | 2.40+ | Control de versiones |
| [Python](https://www.python.org/downloads/) | 3.12 | API |
| [Node.js](https://nodejs.org/) | 20 o 22 LTS | Consola |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | reciente | PostgreSQL ([alternativa sin Docker](docs/postgres-sin-docker.md)) |
| VS Code + PlatformIO | — | Solo para quien trabaja en firmware |

### 2. Clonar y preparar

```bash
git clone <url-del-repo> apaec-lab
cd apaec-lab
bash scripts/setup.sh                                          # Linux / macOS
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1     # Windows
```

El script crea `.env`, levanta PostgreSQL, instala las dependencias exactas de API y consola, aplica las migraciones y crea los `config.h` del firmware.

### 3. Levantar

```bash
# Terminal 1 · API en http://localhost:8000 (documentación en /docs)
cd api && source .venv/bin/activate        # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 · Consola en http://localhost:5173
cd consola && npm run dev
```

La franja superior de la consola muestra **API**, **Base de datos** y **Tiempo real**. Si los tres están en **OK**, el entorno está listo. El botón **SISTEMA** de la barra lateral explica qué hacer si algo falla.

## Pruebas

| Dónde | Comando | Qué cubre |
| --- | --- | --- |
| `api/` | `pytest` | Unitarias, integración (PostgreSQL), WebSocket y reglas de arquitectura de DO-02 |
| `consola/` | `npm test` | Servicios y navegación |
| `consola/` | `npm run lint && npm run typecheck` | Estilo, tipos y que solo `services/` llame a la red |
| `firmware/<proyecto>/` | `pio test -e native` | Lógica pura en PC |

El CI ejecuta todo en cada pull request.

## Puertos

| Servicio | Desarrollo | En pista |
| --- | --- | --- |
| API + WebSocket | `localhost:8000` | `192.168.50.10:8000` |
| Consola | `localhost:5173` | servida por la API en `:8000` |
| PostgreSQL | `127.0.0.1:5432` | `127.0.0.1:5432` (nunca expuesto a la red) |
| Robot / cronómetro | — | `192.168.50.101` / `192.168.50.102` |

## Cómo trabajamos

Ramas, commits, pull requests y responsables por carpeta: [CONTRIBUTING.md](CONTRIBUTING.md). Despliegue en la pista: [docs/despliegue-pista.md](docs/despliegue-pista.md).

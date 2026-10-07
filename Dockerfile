# syntax=docker/dockerfile:1
# Imagen única que sirve la API, los WebSocket y la consola compilada.
# Pensada para Render (o cualquier plataforma Docker). En pista se sigue usando
# la laptop local con docker-compose + uvicorn; esto NO reemplaza ese flujo.

# --- Etapa 1: compilar la consola (Vite) ---
# Se conserva el layout del repo (/repo/consola + /repo/docs) porque el chequeo
# de tipos importa docs/contrato/ejemplos/*.json con rutas relativas al repo.
FROM node:20-alpine AS consola
WORKDIR /repo/consola
COPY consola/package.json consola/package-lock.json ./
RUN npm ci
COPY consola/ ./
COPY docs/ /repo/docs/
RUN npm run build          # genera /repo/consola/dist

# --- Etapa 2: API + consola compilada ---
FROM python:3.12-slim AS api
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias de la API (psycopg[binary] ya trae libpq, no hace falta compilar).
WORKDIR /app/api
COPY api/requirements.lock ./
RUN pip install -r requirements.lock

# Código de la API. RAIZ_REPO = parents[3] de app/core/config.py = /app
COPY api/ /app/api/
# Datos iniciales que leen las semillas (RAIZ_REPO/docs/datos/*.json).
COPY docs/ /app/docs/
# La consola compilada va donde main.py la monta: /app/consola/dist
COPY --from=consola /repo/consola/dist /app/consola/dist

EXPOSE 8000
# Al arrancar: migra, carga datos base, asegura datos simulados y levanta uvicorn.
# Todo es idempotente, así que reinicios y re-deploys no duplican nada.
CMD ["sh", "-c", "alembic upgrade head && python -m app.semillas && python -m app.generador --corridas ${SEED_CORRIDAS:-40} && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

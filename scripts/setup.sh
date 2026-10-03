#!/usr/bin/env bash
# Prepara el entorno de APAEC Lab en Linux o macOS. Uso: bash scripts/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

verde() { printf "\033[32m%s\033[0m\n" "$1"; }
amarillo() { printf "\033[33m%s\033[0m\n" "$1"; }
rojo() { printf "\033[31m%s\033[0m\n" "$1"; }

echo "== APAEC Lab · preparación del entorno =="

# 1. Requisitos
PY=""
for c in python3.12 python3 python; do
  if command -v "$c" >/dev/null && "$c" -c 'import sys; exit(0 if sys.version_info[:2]>=(3,12) else 1)'; then PY="$c"; break; fi
done
[ -z "$PY" ] && { rojo "Falta Python 3.12 o superior."; exit 1; }
command -v node >/dev/null || { rojo "Falta Node.js 20 o superior."; exit 1; }
verde "Python: $($PY --version) · Node: $(node --version)"

# 2. Variables de entorno
if [ ! -f .env ]; then cp .env.example .env; verde "Creado .env desde .env.example"; else echo ".env ya existe, no se toca"; fi

# 3. PostgreSQL
DB_OK=0
if command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  docker compose up -d db
  echo -n "Esperando a PostgreSQL"
  for _ in $(seq 1 30); do
    if docker compose exec -T db pg_isready -q >/dev/null 2>&1; then DB_OK=1; break; fi
    echo -n "."; sleep 1
  done
  echo
  [ $DB_OK -eq 1 ] && verde "PostgreSQL listo en 127.0.0.1:5432" || amarillo "PostgreSQL no respondió a tiempo."
else
  amarillo "Docker no está disponible. Instala PostgreSQL 16 siguiendo docs/postgres-sin-docker.md"
fi

# 4. API
pushd api >/dev/null
[ -d .venv ] || "$PY" -m venv .venv
./.venv/bin/pip install -q --upgrade pip
./.venv/bin/pip install -q -r requirements.lock
./.venv/bin/pip install -q -e . --no-deps
verde "Dependencias de la API instaladas"
if [ $DB_OK -eq 1 ]; then ./.venv/bin/alembic upgrade head && verde "Migraciones aplicadas"; fi
popd >/dev/null

# 5. Consola
pushd consola >/dev/null
npm ci --no-fund --no-audit
verde "Dependencias de la consola instaladas"
popd >/dev/null

# 6. Firmware
for p in velocista cronometro; do
  f="firmware/$p/include/config.h"
  [ -f "$f" ] || { cp "firmware/$p/include/config.example.h" "$f"; echo "Creado $f (completa tu Wi-Fi e IP)"; }
done

echo
verde "Entorno listo. Siguiente paso:"
echo "  Terminal 1:  cd api && source .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "  Terminal 2:  cd consola && npm run dev"
echo "  Abre http://localhost:5173"

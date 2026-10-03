# Prepara el entorno de APAEC Lab en Windows.
# Uso: powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

function Verde($t) { Write-Host $t -ForegroundColor Green }
function Amarillo($t) { Write-Host $t -ForegroundColor Yellow }

Write-Host "== APAEC Lab · preparación del entorno =="

# 1. Requisitos
$py = $null
foreach ($c in @("py -3.12", "python")) {
  try {
    $v = Invoke-Expression "$c -c `"import sys; print(sys.version_info[:2] >= (3,12))`"" 2>$null
    if ($v -eq "True") { $py = $c; break }
  } catch {}
}
if (-not $py) { throw "Falta Python 3.12 o superior (https://www.python.org/downloads/)." }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw "Falta Node.js 20 o superior (https://nodejs.org/)." }
Verde "Python OK · Node $(node --version)"

# 2. Variables de entorno
if (-not (Test-Path .env)) { Copy-Item .env.example .env; Verde "Creado .env desde .env.example" }
else { Write-Host ".env ya existe, no se toca" }

# 3. PostgreSQL
$dbOk = $false
$docker = Get-Command docker -ErrorAction SilentlyContinue
if ($docker) {
  docker info *> $null
  if ($LASTEXITCODE -eq 0) {
    docker compose up -d db
    Write-Host -NoNewline "Esperando a PostgreSQL"
    for ($i = 0; $i -lt 30; $i++) {
      docker compose exec -T db pg_isready -q *> $null
      if ($LASTEXITCODE -eq 0) { $dbOk = $true; break }
      Write-Host -NoNewline "."; Start-Sleep -Seconds 1
    }
    Write-Host ""
    if ($dbOk) { Verde "PostgreSQL listo en 127.0.0.1:5432" } else { Amarillo "PostgreSQL no respondió a tiempo." }
  } else { Amarillo "Docker Desktop está instalado pero no está abierto. Ábrelo y vuelve a correr el script." }
} else { Amarillo "Docker no está disponible. Instala PostgreSQL 16 siguiendo docs/postgres-sin-docker.md" }

# 4. API
Push-Location api
if (-not (Test-Path .venv)) { Invoke-Expression "$py -m venv .venv" }
& .\.venv\Scripts\python.exe -m pip install -q --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.lock
& .\.venv\Scripts\python.exe -m pip install -q -e . --no-deps
Verde "Dependencias de la API instaladas"
if ($dbOk) { & .\.venv\Scripts\alembic.exe upgrade head; Verde "Migraciones aplicadas" }
Pop-Location

# 5. Consola
Push-Location consola
npm ci --no-fund --no-audit
Verde "Dependencias de la consola instaladas"
Pop-Location

# 6. Firmware
foreach ($p in @("velocista", "cronometro")) {
  $f = "firmware/$p/include/config.h"
  if (-not (Test-Path $f)) { Copy-Item "firmware/$p/include/config.example.h" $f; Write-Host "Creado $f (completa tu Wi-Fi e IP)" }
}

Write-Host ""
Verde "Entorno listo. Siguiente paso:"
Write-Host "  Terminal 1:  cd api; .venv\Scripts\activate; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host "  Terminal 2:  cd consola; npm run dev"
Write-Host "  Abre http://localhost:5173"

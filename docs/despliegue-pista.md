# Despliegue en pista

Configuración de la laptop servidor para pruebas y competencia, sin internet.

## Red

| Equipo | IP (reserva DHCP por MAC en el router) |
| --- | --- |
| Router Wi-Fi 2,4 GHz (WPA2) | 192.168.50.1 |
| Laptop servidor | 192.168.50.10 |
| Laptop del operador (opcional) | 192.168.50.20 |
| Velocista 001 | 192.168.50.101 |
| Cronómetro de meta | 192.168.50.102 |

## Antes de ir a la pista (con internet)

1. `git pull` y `bash scripts/setup.sh` (o `setup.ps1`).
2. `cd consola && npm run build`.
3. Carga el firmware con `API_HOST "192.168.50.10"` en el robot y el cronómetro.
4. Respaldo de la base: `docker compose exec db pg_dump -U apaec_app apaec_lab > respaldos/apaec_$(date +%F).sql`.

## En la pista (sin internet)

1. Enciende el router y conecta la laptop a su Wi-Fi.
2. `docker compose up -d`
3. `cd api && uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Abre `http://192.168.50.10:8000` y enciende robot y cronómetro.

## Firewall de la laptop servidor

**Windows (PowerShell como administrador):**
```powershell
New-NetFirewallRule -DisplayName "APAEC API" -Direction Inbound -Protocol TCP -LocalPort 8000 -RemoteAddress 192.168.50.0/24 -Action Allow
```

**Linux (ufw):**
```bash
sudo ufw allow from 192.168.50.0/24 to any port 8000 proto tcp
sudo ufw deny 5432
```

PostgreSQL ya está limitado a `127.0.0.1` por `docker-compose.yml`.

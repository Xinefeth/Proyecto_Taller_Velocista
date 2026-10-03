# PostgreSQL sin Docker

Usa esta guía si no puedes instalar Docker Desktop.

## Windows

1. Descarga el instalador de PostgreSQL 16 desde https://www.postgresql.org/download/windows/.
2. Instálalo con las opciones por defecto (puerto **5432**). Anota la contraseña del usuario `postgres`.
3. Abre **SQL Shell (psql)**, entra como `postgres` y ejecuta (usa la misma clave de tu `.env`):

```sql
CREATE USER apaec_app WITH PASSWORD 'cambia-esta-clave';
CREATE DATABASE apaec_lab OWNER apaec_app;
```

## Ubuntu / Debian

```bash
sudo apt install postgresql
sudo -u postgres psql -c "CREATE USER apaec_app WITH PASSWORD 'cambia-esta-clave';"
sudo -u postgres psql -c "CREATE DATABASE apaec_lab OWNER apaec_app;"
```

## macOS

```bash
brew install postgresql@16 && brew services start postgresql@16
psql postgres -c "CREATE USER apaec_app WITH PASSWORD 'cambia-esta-clave';"
psql postgres -c "CREATE DATABASE apaec_lab OWNER apaec_app;"
```

## Verificar

```bash
cd api
alembic upgrade head
```

Debe terminar con `Running upgrade -> 0001_base`. Asegúrate de que PostgreSQL escuche solo en `localhost` (valor por defecto de `listen_addresses`).

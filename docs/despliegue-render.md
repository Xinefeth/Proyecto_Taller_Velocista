# Despliegue en la nube (Render)

El sistema funcionando por internet, sin depender del hardware físico. Arranca con
la **base de datos vacía**: los datos (catálogo, robots, etc.) se cargan a mano por
la consola/API. Esto convive con el [despliegue en pista](despliegue-pista.md): el
mismo código corre en ambos; solo cambia a qué host apuntan los dispositivos.

> Para una competencia real sin internet, usa el despliegue en pista. La nube es
> para acceso remoto y para mostrar el sistema.

## Qué se despliega

Un **único servicio web** (imagen Docker) que sirve, bajo la misma URL:

- la **API REST** (`/api/...`),
- los **WebSocket** del contrato v1.0 (`/ws/robot`, `/ws/cronometro`, `/ws/consola`),
- la **consola** compilada (SPA de Vite montada en `/` por `app/main.py`).

Más una base **PostgreSQL** gestionada por Render.

## Arranque: solo el esquema (BD vacía)

En cada arranque, el contenedor ejecuta:

1. `alembic upgrade head` — crea/actualiza las tablas (solo esquema, sin sembrar
   ningún dato).
2. `uvicorn app.main:app` — levanta la API, los WebSocket y la consola.

La base queda **vacía**: no se precarga catálogo, robots ni corridas. Todo lo que
aparezca en la consola es lo que cargues tú por la API/consola, que es la forma de
comprobar que la persistencia funciona de verdad.

Si quieres telemetría **en vivo** por el camino real (gateway WS), primero crea un
robot en la consola y luego ejecuta el robot falso apuntando a la nube:

```bash
python api/herramientas/robot_falso.py --url wss://TU-APP.onrender.com/ws/robot --token <DEVICE_TOKEN_VELOCISTA>
```

## Opción A — Blueprint (recomendada)

Con `render.yaml` en la raíz, Render crea servicio + base de un tirón:

1. Sube el repo a GitHub.
2. En Render: **New → Blueprint** y elige este repositorio.
3. Render lee `render.yaml`, crea `apaec-lab-db` y `apaec-lab`, e inyecta
   `DATABASE_URL`, `SECRET_KEY` y los `DEVICE_TOKEN_*` automáticamente.
4. Espera al build (compila la consola y la API) y abre la URL del servicio.

## Opción B — manual (sin Blueprint)

1. **New → PostgreSQL** (plan Free). Copia su *Internal Database URL*.
2. **New → Web Service**, runtime **Docker**, apuntando al repo (usa el `Dockerfile`).
3. En *Environment* del servicio, agrega las variables de la tabla de abajo.

## Variables de entorno

| Variable | Valor |
| --- | --- |
| `DATABASE_URL` | Internal Database URL del Postgres de Render |
| `SECRET_KEY` | cadena larga aleatoria |
| `APP_ENV` | `produccion` |
| `CORS_ORIGINS` | vacío (la consola se sirve del mismo origen) |
| `DEVICE_TOKEN_VELOCISTA` | token del robot (si usarás el robot falso) |
| `DEVICE_TOKEN_CRONOMETRO` | token del cronómetro |

`config.py` acepta `DATABASE_URL` (formato `postgres://` o `postgresql://`) y la
normaliza al driver `postgresql+psycopg://`. En local se siguen usando las
variables `POSTGRES_*` del `.env`; `DATABASE_URL` tiene prioridad si está puesta.

## Base de datos externa / SSL

Si conectas al Postgres por su URL **externa** (fuera de Render), añade el modo
SSL a la variable:

```
DATABASE_URL=postgresql://usuario:clave@host.externo:5432/apaec_lab?sslmode=require
```

La URL **interna** (misma región de Render) no necesita `sslmode`.

## Firmware real contra la nube (opcional)

El sistema puede operar con hardware real por internet si lo necesitas: recompila
el firmware con la URL de la nube en `firmware/*/include/config.h`:

```c
#define API_HOST "TU-APP.onrender.com"
#define API_PORT 443   // wss (TLS)
```

Requiere que la librería WebSocket del ESP32 soporte TLS y que los dispositivos
tengan salida a internet. En competencia esto **no** se recomienda (sin internet
confiable); ahí se usa el despliegue en pista.

## Limitaciones del plan gratuito

- El servicio web **se duerme** tras inactividad: el primer acceso tarda ~30–60 s.
- El Postgres gratuito **caduca a ~30 días**; respáldalo o sube de plan si lo
  necesitas estable.
- WebSockets sí están soportados en el plan Free sobre `wss://`.

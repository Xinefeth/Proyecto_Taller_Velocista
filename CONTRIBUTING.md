# Cómo trabajamos

## Ramas

Usamos un flujo simple basado en `main`:

| Rama | Uso | Reglas |
| --- | --- | --- |
| `main` | Siempre funciona y se puede demostrar | Protegida: solo entra por pull request con 1 revisión aprobada |
| `tipo/ID-descripcion-corta` | Una rama por ítem del backlog | Sale de `main` y vuelve a `main` |

Tipos de rama: `feat`, `fix`, `docs`, `chore`, `test`, `spike`.

Ejemplos:
```
feat/HU-01-lista-catalogo
feat/EN-12-websocket-robot
fix/HU-16-arranque-sin-calibrar
docs/DO-02-arquitectura
spike/SP-01-metrica-j
```

- Nombre en minúsculas, con guiones, sin tildes ni ñ.
- Una rama vive pocos días. Si crece mucho, divide el ítem.
- Antes de abrir el PR: `git pull --rebase origin main`.

## Commits

Seguimos [Conventional Commits](https://www.conventionalcommits.org/es/) en español:

```
tipo(alcance): descripción en imperativo [ID]
```

| Tipo | Cuándo |
| --- | --- |
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de error |
| `docs` | Solo documentación |
| `test` | Agregar o corregir pruebas |
| `refactor` | Cambio interno sin cambiar comportamiento |
| `chore` | Configuración, dependencias, scripts |
| `perf` | Mejora de rendimiento |

Alcances: `api`, `consola`, `velocista`, `cronometro`, `db`, `docs`, `repo`.

Ejemplos:
```
feat(api): agrega endpoint GET /api/componentes [HU-01]
feat(velocista): envía manifiesto al conectar [EN-12]
fix(consola): bloquea arrancar sin calibración [HU-16]
chore(repo): configura docker-compose para PostgreSQL [EN-03]
```

- Descripción en imperativo presente, minúsculas, sin punto final, máximo 72 caracteres.
- El ID del backlog al final entre corchetes.
- Un commit = un cambio con sentido. Nada de "avances" ni "cambios varios".

## Pull requests

1. Título con el mismo formato del commit principal.
2. Llena la plantilla (qué cambia, cómo probarlo, criterios de aceptación).
3. Al menos **1 revisión aprobada** de otro integrante.
4. El CI pasa: formato, lint, tipos, pruebas de API, consola y firmware.
5. Se integra con **Squash and merge** y se borra la rama.

## Definición de Hecho

Un ítem está Hecho cuando:
- cumple todos sus criterios de aceptación,
- tiene pruebas cuando aplica,
- está integrado en `main` mediante PR revisado,
- su documentación (README o docs/) está al día,
- se demostró en la revisión del sprint.

## Estilo de código

| Carpeta | Herramienta | Comando |
| --- | --- | --- |
| `api/` | Ruff (formato y lint) | `ruff format . && ruff check .` |
| `consola/` | Prettier | `npm run format` |
| `firmware/` | clang-format (estilo del archivo `.clang-format`) | desde VS Code |

Opcional: `pip install pre-commit && pre-commit install` revisa el formato antes de cada commit.

## Secretos

Nunca subas `.env`, `config.h` del firmware, contraseñas ni tokens. Usa los archivos `*.example` como plantilla.

## Responsables por carpeta

Asignados según el Product Backlog v5. El responsable revisa los PR de su área (GitHub lo pide solo con `.github/CODEOWNERS`).

| Área | Carpetas | Responsable |
| --- | --- | --- |
| Firmware y hardware | `firmware/` | ALE |
| Base de datos y API | `api/app/core/`, `api/migrations/`, módulos `catalogo`, `armador`, `reglamento`, `corridas` | BDA |
| Consola e integración | `consola/`, `api/app/gateway/` | CTR |
| Algoritmos | módulo `optimizacion` | ALG |
| Repositorio y CI | `.github/`, `scripts/`, `docker-compose.yml` | CTR |
| Documentación | `docs/` | Autor de cada documento; revisan todos |

## Reglas de colaboración

- Nadie integra su propio PR.
- PR pequeños: un ítem o una subtarea; si pasa de unas 400 líneas, se divide.
- Revisión en menos de 24 horas hábiles.
- Actualiza tu rama con `main` a diario: `git pull --rebase origin main`.
- Avisa al equipo antes de cambiar algo que afecta a varios: contrato de mensajes, contrato REST, esquema de la base, CI o `docker-compose.yml`.
- Una sola migración por PR; si dos PR crean migraciones a la vez, el segundo ajusta su `down_revision`.
- Los conflictos de Git los resuelve quien abrió el PR; si tocan código de otro, se resuelven juntos.

## Primer día de un integrante

1. Acepta la invitación al repositorio y configura `git config user.name` y `user.email`.
2. Clona y ejecuta el script de `scripts/`. Anota cuánto tardó (debe ser menos de 15 minutos).
3. Confirma en la consola que API, Base de datos y Tiempo real están en OK.
4. Lee este archivo y la arquitectura en `docs/arquitectura/`.
5. Crea la rama de tu primer ítem y abre un PR en borrador temprano.

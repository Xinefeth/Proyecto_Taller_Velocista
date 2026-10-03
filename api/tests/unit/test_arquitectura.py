"""Reglas de DO-02 verificadas automáticamente en cada PR.

1. Cada módulo tiene router.py, service.py, models.py y schemas.py.
2. Un módulo solo usa de otro su interfaz pública (service o puertos), nunca models, router, schemas ni repository.
3. Los módulos no conocen los canales de entrada (app.gateway).
"""

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"
MODULOS = APP / "modulos"
PUBLICO = {"service", "puertos"}
OBLIGATORIOS = {"__init__.py", "router.py", "service.py", "models.py", "schemas.py"}


def _modulos() -> list[Path]:
    return [m for m in MODULOS.iterdir() if m.is_dir() and not m.name.startswith("__")]


def _imports(archivo: Path) -> list[str]:
    nombres = []
    for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
        if isinstance(nodo, ast.ImportFrom) and nodo.module:
            nombres.append(nodo.module)
            nombres += [f"{nodo.module}.{a.name}" for a in nodo.names]
        elif isinstance(nodo, ast.Import):
            nombres += [a.name for a in nodo.names]
    return nombres


def test_cada_modulo_tiene_la_estructura_de_do02():
    faltantes = [f"{m.name}/{a}" for m in _modulos() for a in OBLIGATORIOS if not (m / a).exists()]
    assert not faltantes, f"Faltan archivos: {faltantes}"


def test_modulos_solo_usan_la_interfaz_publica_de_otros():
    violaciones = []
    for archivo in MODULOS.rglob("*.py"):
        propio = archivo.relative_to(MODULOS).parts[0]
        for nombre in _imports(archivo):
            partes = nombre.split(".")
            if partes[:2] != ["app", "modulos"] or len(partes) < 4:
                continue
            otro, parte = partes[2], partes[3]
            if (
                otro != propio
                and parte not in PUBLICO
                and (MODULOS / otro / f"{parte}.py").exists()
            ):
                violaciones.append(f"{archivo.relative_to(APP)} importa {nombre}")
    assert not violaciones, "Imports prohibidos entre módulos:\n" + "\n".join(violaciones)


def test_modulos_no_dependen_de_los_canales():
    violaciones = [
        f"{archivo.relative_to(APP)} importa {nombre}"
        for archivo in MODULOS.rglob("*.py")
        for nombre in _imports(archivo)
        if nombre.startswith("app.gateway") or nombre == "app.main"
    ]
    assert not violaciones, "\n".join(violaciones)

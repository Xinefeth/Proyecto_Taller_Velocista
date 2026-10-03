"""Validaciones que dependen del manifiesto del robot conectado."""

from typing import Literal

from app.contrato.manifiesto import Canal, Manifiesto
from app.contrato.robot import Setup, ValorCanal


def _valor_valido(canal: Canal, valor: ValorCanal) -> str | None:
    base = canal.tipo.removesuffix("[]")
    valores = valor if isinstance(valor, list) else [valor]
    if canal.tipo.endswith("[]"):
        if not isinstance(valor, list):
            return f"{canal.nombre}: se esperaba un arreglo"
        if len(valor) != canal.longitud:
            return f"{canal.nombre}: se esperaban {canal.longitud} valores y llegaron {len(valor)}"
    elif isinstance(valor, list):
        return f"{canal.nombre}: no se esperaba un arreglo"
    for v in valores:
        if base == "bool":
            if not isinstance(v, bool):
                return f"{canal.nombre}: se esperaba bool"
            continue
        if isinstance(v, bool) or not isinstance(v, int | float):
            return f"{canal.nombre}: se esperaba un número"
        if base == "int" and not float(v).is_integer():
            return f"{canal.nombre}: se esperaba un entero"
        if canal.min is not None and v < canal.min or canal.max is not None and v > canal.max:
            return f"{canal.nombre}: {v} fuera de [{canal.min}, {canal.max}]"
    return None


def revisar_canales(
    manifiesto: Manifiesto, grupo: Literal["estado", "senales"], canales: dict[str, ValorCanal]
) -> list[str]:
    """Devuelve avisos; nunca descarta la muestra completa por un canal raro."""
    avisos = []
    for nombre, valor in canales.items():
        canal = manifiesto.canal(nombre)
        if canal is None:
            avisos.append(f"{nombre}: canal no declarado en el manifiesto")
        elif canal.grupo != grupo:
            avisos.append(f"{nombre}: pertenece al grupo {canal.grupo}, no a {grupo}")
        elif problema := _valor_valido(canal, valor):
            avisos.append(problema)
    return avisos


def revisar_setup(manifiesto: Manifiesto, setup: Setup) -> tuple[str, str] | None:
    """Devuelve (motivo, detalle) si el setup no cabe en lo que el robot declaró."""
    controlador = manifiesto.controlador(setup.controlador)
    if controlador is None:
        return "controlador_no_disponible", f"el robot no tiene el controlador {setup.controlador}"
    for nombre, valor in setup.parametros.items():
        p = controlador.parametro(nombre)
        if p is None:
            return "parametro_desconocido", f"{setup.controlador} no tiene el parámetro {nombre}"
        if not p.min <= valor <= p.max:
            return "fuera_de_rango", f"{nombre}={valor} fuera de [{p.min}, {p.max}]"
        if p.tipo == "int" and not float(valor).is_integer():
            return "fuera_de_rango", f"{nombre} debe ser entero"
    return None

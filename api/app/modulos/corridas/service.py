"""Reglas de negocio del módulo corridas."""

# SP-01: el reglamento de Muchik Rumble 4 limita la vuelta a 120 s.
LIMITE_S = 120.0
PESO_ERROR = 2.0


def calcular_j(tiempo_s: float | None, error_acumulado: float, termino: bool) -> float:
    """Métrica de una corrida (SP-01): J = tiempo + 2 × error acumulado.

    Si el robot no termina la vuelta, J = 120. Menor es mejor.
    """
    if tiempo_s is not None and tiempo_s < 0:
        raise ValueError("el tiempo no puede ser negativo")
    if error_acumulado < 0:
        raise ValueError("el error acumulado no puede ser negativo")
    if not termino or tiempo_s is None:
        return LIMITE_S
    return round(tiempo_s + PESO_ERROR * error_acumulado, 3)

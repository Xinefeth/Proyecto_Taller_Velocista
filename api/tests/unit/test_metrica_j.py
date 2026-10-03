"""SP-01: J = tiempo + 2 × error acumulado; si no termina, J = 120."""

import pytest

from app.modulos.corridas.service import LIMITE_S, calcular_j


def test_vuelta_terminada():
    assert calcular_j(18.42, 2.87, termino=True) == pytest.approx(24.16)


def test_vuelta_no_terminada_vale_el_limite():
    assert calcular_j(35.0, 1.0, termino=False) == LIMITE_S == 120


def test_sin_tiempo_vale_el_limite():
    assert calcular_j(None, 0.5, termino=True) == 120


def test_menor_error_mejora_j_con_el_mismo_tiempo():
    assert calcular_j(18.0, 1.0, True) < calcular_j(18.0, 2.0, True)


@pytest.mark.parametrize(("tiempo", "error"), [(-1.0, 1.0), (10.0, -0.1)])
def test_valores_negativos_se_rechazan(tiempo, error):
    with pytest.raises(ValueError):
        calcular_j(tiempo, error, True)

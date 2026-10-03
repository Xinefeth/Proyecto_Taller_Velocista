"""Puerto del optimizador (DO-02, AD-09): Twiddle y Optuna lo implementan igual.

Así la consola y el módulo corridas no dependen del método elegido (HU-29 los compara).
"""

from typing import Protocol


class Optimizador(Protocol):
    def sugerir(self) -> dict[str, float]:
        """Siguiente setup a probar en pista."""
        ...

    def registrar(self, parametros: dict[str, float], j: float) -> None:
        """Informa el J obtenido con esos parámetros."""
        ...

"""Seguridad transversal.

Estado EN-03: verificación de tokens de dispositivo.
El inicio de sesión de usuarios (JWT en cookie HttpOnly, Argon2) se implementa con el módulo auth.
"""

import hmac


def token_valido(recibido: str | None, esperado: str) -> bool:
    """Compara en tiempo constante para no filtrar información por tiempos de respuesta."""
    if not recibido or not esperado:
        return False
    return hmac.compare_digest(recibido.encode(), esperado.encode())

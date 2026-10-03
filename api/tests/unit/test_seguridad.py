from app.core.seguridad import token_valido


def test_token_correcto():
    assert token_valido("abc123", "abc123")


def test_token_incorrecto_vacio_o_ausente():
    assert not token_valido("abc124", "abc123")
    assert not token_valido("", "abc123")
    assert not token_valido(None, "abc123")
    assert not token_valido("abc123", "")

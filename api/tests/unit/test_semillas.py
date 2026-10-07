"""La semilla cubre los tipos y aportes necesarios para EN-04."""

from app.semillas import leer_componentes_iniciales, leer_tipos_iniciales


def test_tipos_incluyen_encoder_imu_y_turbina_con_capacidades():
    tipos = {t["id"]: t for t in leer_tipos_iniciales()}
    assert set(tipos) == {
        "mcu",
        "exp",
        "linea",
        "mux",
        "motor",
        "driver",
        "bat",
        "reg",
        "rueda",
        "chasis",
        "sw",
        "enc",
        "imu",
        "turb",
    }
    assert any(c.get("campo") == "canales" for c in tipos["linea"]["capacidades"])
    assert any(c.get("campo") == "cpr" for c in tipos["enc"]["capacidades"])
    assert any(c.get("campo") == "ejes" for c in tipos["imu"]["capacidades"])
    assert any(
        c.get("campos") == ["v", "imax"] and c.get("operacion") == "producto"
        for c in tipos["turb"]["capacidades"]
    )


def test_componentes_tienen_tipos_y_especificaciones_declarados():
    tipos = {t["id"]: t for t in leer_tipos_iniciales()}
    componentes = leer_componentes_iniciales()
    assert {c["id"] for c in componentes} == {f"c{i:02d}" for i in range(1, 26)}
    for comp in componentes:
        campos = {c["clave"]: c["tipo"] for c in tipos[comp["tipo_id"]]["campos"]}
        assert comp["especificaciones"].keys() <= campos.keys()
        for clave, valor in comp["especificaciones"].items():
            if campos[clave] == "n":
                assert type(valor) in (int, float)
            else:
                assert isinstance(valor, str)
    por_id = {c["id"]: c for c in componentes}
    assert por_id["c05"]["especificaciones"]["canales"] == 8
    assert por_id["c22"]["especificaciones"]["cpr"] == 12
    assert por_id["c23"]["especificaciones"]["ejes"] == 6
    assert por_id["c24"]["stock"] == 0

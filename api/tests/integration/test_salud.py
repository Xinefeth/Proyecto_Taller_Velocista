def test_salud_responde(cliente):
    r = cliente.get("/api/health")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["api"] == "ok"
    assert cuerpo["base_de_datos"] in {"ok", "sin conexión"}
    assert set(cuerpo["dispositivos"]) == {"velocista", "cronometro"}


def test_openapi_lista_los_modulos(cliente):
    rutas = cliente.get("/openapi.json").json()["paths"]
    tags = {t for ruta in rutas.values() for op in ruta.values() for t in op.get("tags", [])}
    assert {"system", "events"} <= tags

"""Gateway WebSocket con el contrato de mensajes v1.0 (EN-02)."""

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings

URL_ROBOT = f"/ws/robot?token={settings.device_token_velocista}"
URL_CRONO = f"/ws/cronometro?token={settings.device_token_cronometro}"


def conectar_robot(cliente, consola, ejemplo):
    """Conecta el robot, envía el manifiesto y consume los mensajes iniciales."""
    robot = cliente.websocket_connect(URL_ROBOT).__enter__()
    consola.receive_json()  # enlace
    robot.send_json(ejemplo("velocista.manifiesto.json"))
    assert robot.receive_json()["datos"] == {"ok": True}
    assert consola.receive_json()["tipo"] == "manifiesto"
    return robot


def test_dispositivo_sin_token_o_con_token_ajeno_es_rechazado(cliente):
    for url in ("/ws/robot", f"/ws/robot?token={settings.device_token_cronometro}"):
        with pytest.raises(WebSocketDisconnect):
            with cliente.websocket_connect(url) as ws:
                ws.receive_text()


def test_consola_recibe_estado_inicial_y_enlaces(cliente):
    with cliente.websocket_connect("/ws/consola") as consola:
        assert consola.receive_json()["datos"]["dispositivos"] == {
            "velocista": False,
            "cronometro": False,
        }
        with cliente.websocket_connect(URL_CRONO):
            assert consola.receive_json()["datos"] == {
                "dispositivo": "cronometro",
                "conectado": True,
            }
            assert cliente.get("/api/salud").json()["dispositivos"]["cronometro"] is True
        assert consola.receive_json()["datos"]["conectado"] is False


def test_datos_antes_del_manifiesto_se_descartan(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        with cliente.websocket_connect(URL_ROBOT) as robot:
            consola.receive_json()
            robot.send_json(ejemplo("velocista.estado.json"))
            assert consola.receive_json()["datos"]["codigo"] == "manifiesto_faltante"


def test_estado_se_redistribuye_sin_ack(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        robot = conectar_robot(cliente, consola, ejemplo)
        robot.send_json(ejemplo("velocista.estado.json"))
        reenviado = consola.receive_json()
        assert (
            reenviado["origen"] == "velocista"
            and reenviado["datos"]["canales"]["bateria_v"] == 8.12
        )
        assert (
            cliente.get("/api/dispositivos/velocista/manifiesto").json()["controlador_activo"]
            == "pid"
        )
        robot.__exit__(None, None, None)


def test_mensaje_invalido_se_reporta(cliente):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        with cliente.websocket_connect(URL_ROBOT) as robot:
            consola.receive_json()
            robot.send_text("esto no es json")
            assert consola.receive_json()["datos"]["codigo"] == "mensaje_invalido"
            robot.send_json({"tipo": "estado", "seq": 1, "ts": 0, "datos": {"bateria": 8}})
            assert consola.receive_json()["datos"]["codigo"] == "mensaje_invalido"


def test_canal_fuera_de_rango_avisa_y_la_muestra_llega(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        robot = conectar_robot(cliente, consola, ejemplo)
        senales = ejemplo("velocista.senales.json")
        senales["datos"]["canales"]["error"] = 4.0
        robot.send_json(senales)
        assert consola.receive_json()["datos"]["codigo"] == "canal_invalido"
        assert consola.receive_json()["tipo"] == "senales"
        robot.__exit__(None, None, None)


def test_senales_fuera_de_orden_se_descartan(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        robot = conectar_robot(cliente, consola, ejemplo)
        s = ejemplo("velocista.senales.json")
        robot.send_json(s)
        assert consola.receive_json()["tipo"] == "senales"
        viejo = ejemplo("velocista.senales.json")
        viejo["datos"]["t_ms"] -= 100
        robot.send_json(viejo)
        robot.send_json(ejemplo("velocista.estado.json"))
        assert consola.receive_json()["tipo"] == "estado"  # la señal vieja no llegó
        robot.__exit__(None, None, None)


def test_corte_duplicado_se_confirma_pero_no_se_repite(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        with cliente.websocket_connect(URL_CRONO) as crono:
            consola.receive_json()
            corte = ejemplo("cronometro.corte.json")
            crono.send_json(corte)
            ack = crono.receive_json()
            assert ack["tipo"] == "ack" and ack["seq"] == corte["seq"]
            assert consola.receive_json()["tipo"] == "corte"
            crono.send_json(corte)  # reintento del mismo seq
            assert crono.receive_json()["seq"] == corte["seq"]
            crono.send_json(ejemplo("cronometro.estado.json"))
            assert (
                consola.receive_json()["tipo"] == "estado"
            )  # el corte no se redistribuyó dos veces


def test_comandos_validados_y_enviados(cliente, ejemplo):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        robot = conectar_robot(cliente, consola, ejemplo)
        robot.send_json(ejemplo("velocista.estado.json"))
        consola.receive_json()

        r = cliente.post(
            "/api/dispositivos/velocista/comandos",
            json={"tipo": "setup", "datos": {"controlador": "pid", "parametros": {"kp": 9}}},
        )
        assert r.status_code == 422 and r.json()["detail"]["motivo"] == "fuera_de_rango"

        r = cliente.post(
            "/api/dispositivos/velocista/comandos",
            json={"tipo": "setup", "datos": {"controlador": "pid", "parametros": {"kp": 0.4}}},
        )
        assert r.status_code == 202
        recibido = robot.receive_json()
        assert recibido["tipo"] == "setup" and recibido["seq"] == r.json()["seq"]
        robot.__exit__(None, None, None)


def test_comando_a_dispositivo_desconectado(cliente):
    r = cliente.post("/api/dispositivos/velocista/comandos", json={"tipo": "detener"})
    assert r.status_code == 409 and r.json()["detail"]["motivo"] == "desconectado"

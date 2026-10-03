"""Gateway WebSocket (estado EN-03). Las pruebas del contrato de mensajes pertenecen a EN-02."""

import pytest
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings

URL_ROBOT = f"/ws/robot?token={settings.device_token_velocista}"
URL_CRONO = f"/ws/cronometro?token={settings.device_token_cronometro}"


def test_dispositivo_sin_token_es_rechazado(cliente):
    with pytest.raises(WebSocketDisconnect):
        with cliente.websocket_connect("/ws/robot") as ws:
            ws.receive_text()


def test_token_de_otro_dispositivo_es_rechazado(cliente):
    with pytest.raises(WebSocketDisconnect):
        with cliente.websocket_connect(f"/ws/robot?token={settings.device_token_cronometro}") as ws:
            ws.receive_text()


def test_consola_recibe_estado_inicial_y_enlaces(cliente):
    with cliente.websocket_connect("/ws/consola") as consola:
        hola = consola.receive_json()
        assert hola["tipo"] == "hola" and hola["datos"]["dispositivos"] == {
            "velocista": False,
            "cronometro": False,
        }
        with cliente.websocket_connect(URL_CRONO):
            enlace = consola.receive_json()
            assert enlace["datos"] == {"dispositivo": "cronometro", "conectado": True}
            assert cliente.get("/api/salud").json()["dispositivos"]["cronometro"] is True
        assert consola.receive_json()["datos"]["conectado"] is False


def test_mensaje_del_robot_se_redistribuye_a_la_consola(cliente):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        with cliente.websocket_connect(URL_ROBOT) as robot:
            consola.receive_json()
            robot.send_json({"tipo": "estado", "datos": {"bateria_v": 8.1}})
            reenviado = consola.receive_json()
            assert reenviado["origen"] == "velocista" and reenviado["tipo"] == "estado"
            assert reenviado["datos"]["datos"]["bateria_v"] == 8.1


def test_mensaje_que_no_es_json_se_reporta(cliente):
    with cliente.websocket_connect("/ws/consola") as consola:
        consola.receive_json()
        with cliente.websocket_connect(URL_ROBOT) as robot:
            consola.receive_json()
            robot.send_text("esto no es json")
            assert consola.receive_json()["tipo"] == "mensaje_invalido"

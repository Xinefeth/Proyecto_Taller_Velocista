"""Robot falso para probar la API y la consola sin hardware.

Habla el contrato v1.0: envía el manifiesto de ejemplo, estado a 1 Hz,
señales a 20 Hz mientras "corre" y responde los comandos con ack.

Uso (con la API levantada):
    python herramientas/robot_falso.py                       # local, ws://localhost:8000
    python herramientas/robot_falso.py --host 192.168.50.10  # pista, red local
    python herramientas/robot_falso.py --url wss://apaec-lab.onrender.com/ws/robot  # nube
"""

import argparse
import asyncio
import json
import math
import random
import time
from pathlib import Path

import websockets

EJEMPLOS = Path(__file__).resolve().parents[2] / "docs" / "contrato" / "ejemplos"


class RobotFalso:
    def __init__(self) -> None:
        self.manifiesto = json.loads((EJEMPLOS / "velocista.manifiesto.json").read_text())["datos"]
        self.seq = 0
        self.inicio = time.monotonic()
        self.estado = "listo"
        self.calibrado = False
        self.modo = "prueba"
        self.linea = "negra"
        self.error_acumulado = 0.0
        self.inicio_vuelta = self.ms()

    def ms(self) -> int:
        return int((time.monotonic() - self.inicio) * 1000)

    def sobre(self, tipo: str, datos: dict, seq: int | None = None) -> str:
        if seq is None:
            self.seq += 1
            seq = self.seq
        return json.dumps({"tipo": tipo, "seq": seq, "ts": self.ms(), "datos": datos})

    def comando(self, tipo: str, datos: dict) -> dict:
        if (
            self.modo == "competencia"
            and self.estado == "corriendo"
            and tipo not in ("detener", "cierre_vuelta")
        ):
            return {"ok": False, "motivo": "bloqueado_competencia"}
        if tipo == "calibrar":
            self.calibrado = True
        elif tipo == "arrancar":
            if not self.calibrado:
                return {"ok": False, "motivo": "no_calibrado"}
            self.estado, self.inicio_vuelta, self.error_acumulado = "corriendo", self.ms(), 0.0
        elif tipo == "detener":
            self.estado = "detenido"
        elif tipo == "modo":
            self.modo = datos["modo"]
        elif tipo == "linea":
            self.linea = datos["color"]
        elif tipo == "setup":
            pid = self.manifiesto["controladores"][0]
            rangos = {p["nombre"]: p for p in pid["parametros"]}
            for nombre, valor in datos["parametros"].items():
                if nombre not in rangos:
                    return {"ok": False, "motivo": "parametro_desconocido", "detalle": nombre}
                if not rangos[nombre]["min"] <= valor <= rangos[nombre]["max"]:
                    return {"ok": False, "motivo": "fuera_de_rango", "detalle": nombre}
                rangos[nombre]["valor"] = valor
        elif tipo != "cierre_vuelta":
            return {"ok": False, "motivo": "comando_desconocido"}
        return {"ok": True}

    async def correr(self, url: str, token: str) -> None:
        async with websockets.connect(url, additional_headers={"X-Device-Token": token}) as ws:
            print(f"Conectado a {url}")
            await ws.send(self.sobre("manifiesto", self.manifiesto))
            await asyncio.gather(self.escuchar(ws), self.telemetria(ws))

    async def escuchar(self, ws) -> None:
        async for crudo in ws:
            msg = json.loads(crudo)
            if msg["tipo"] == "ack":
                continue
            print(f"<- {msg['tipo']} {msg['datos']}")
            respuesta = self.comando(msg["tipo"], msg["datos"])
            await ws.send(self.sobre("ack", respuesta, seq=msg["seq"]))
            if msg["tipo"] == "cierre_vuelta" and respuesta["ok"]:
                vuelta = {
                    "id_vuelta": msg["datos"]["id_vuelta"],
                    "tiempo_interno_ms": self.ms() - self.inicio_vuelta,
                    "error_acumulado": round(self.error_acumulado, 3),
                    "lineas_perdidas": 0,
                    "bateria_v": 7.9,
                }
                self.inicio_vuelta, self.error_acumulado = self.ms(), 0.0
                await ws.send(self.sobre("vuelta", vuelta))

    async def telemetria(self, ws) -> None:
        tick = 0
        while True:
            await asyncio.sleep(0.05)
            tick += 1
            if tick % 20 == 0:
                estado = {
                    "estado": self.estado,
                    "calibrado": self.calibrado,
                    "modo": self.modo,
                    "linea": self.linea,
                    "controlador": "pid",
                    "lazo_hz": 1000,
                    "rssi_dbm": -55,
                    "canales": {"bateria_v": round(8.2 - tick / 20000, 2)},
                }
                await ws.send(self.sobre("estado", estado))
            if self.estado == "corriendo":
                error = round(0.4 * math.sin(tick / 8) + random.uniform(-0.05, 0.05), 3)
                self.error_acumulado += abs(error) * 0.05
                centro = 7.5 + error * 7.5
                regleta = [max(0, int(1000 - 350 * abs(i - centro) ** 1.5)) for i in range(16)]
                senales = {
                    "t_ms": self.ms(),
                    "canales": {
                        "error": error,
                        "regleta": regleta,
                        "pwm_izq": int(160 + 80 * error),
                        "pwm_der": int(160 - 80 * error),
                    },
                }
                await ws.send(self.sobre("senales", senales))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--host", default="localhost")
    p.add_argument("--puerto", default=8000, type=int)
    p.add_argument("--tls", action="store_true", help="usar wss:// (TLS); puerto 443 por defecto")
    p.add_argument("--url", help="URL WebSocket completa (p. ej. wss://host/ws/robot); ignora host/puerto")
    p.add_argument("--token", default="dev-token-velocista")
    a = p.parse_args()
    if a.url:
        url = a.url
    else:
        esquema = "wss" if a.tls else "ws"
        puerto = 443 if (a.tls and a.puerto == 8000) else a.puerto
        url = f"{esquema}://{a.host}:{puerto}/ws/robot"
    try:
        asyncio.run(RobotFalso().correr(url, a.token))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

"""Comprueba la muestra que emite el robot falso sin abrir conexiones."""

import asyncio
import json
from unittest.mock import AsyncMock

import pytest

from herramientas.robot_falso import RobotFalso


def test_fake_robot_emits_sixteen_readings(monkeypatch):
    robot = RobotFalso()
    robot.estado = "running"
    samples = []

    class SampleCaptured(Exception):
        pass

    async def capture(payload):
        samples.append(json.loads(payload))
        raise SampleCaptured

    monkeypatch.setattr("herramientas.robot_falso.asyncio.sleep", AsyncMock())
    socket = AsyncMock()
    socket.send.side_effect = capture
    with pytest.raises(SampleCaptured):
        asyncio.run(robot.telemetria(socket))

    sample = samples[0]
    assert sample["tipo"] == "senales"
    readings = sample["datos"]["canales"]["regleta"]
    assert len(readings) == 16
    assert all(isinstance(value, int) and 0 <= value <= 1000 for value in readings)
    assert max(readings) > 500

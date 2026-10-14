"""Módulo configuracion: modo de funcionamiento y color de línea del robot (HU-18).

Persiste el último modo (prueba/competencia) y color de línea (negra/blanca) por robot y los envía
al robot por el puerto del gateway (app.core.actividad). El estado queda en la base de datos.

Reglas del monolito modular (DO-02, sección 5):
- Otros módulos solo usan `configuracion.service` (interfaz pública), nunca `models` ni `router`.
- Este módulo es dueño de su tabla y no importa app.gateway: usa el puerto app.core.actividad.
"""

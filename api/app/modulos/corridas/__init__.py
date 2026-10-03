"""Módulo corridas: Emparejar corte + vuelta + setup, calcular J, telemetría por vuelta y exportar CSV.

Ítems: SP-01, HU-19, HU-20, HU-26, EN-20. Responsable: BDA + CTR.

Reglas del monolito modular (DO-02, sección 5):
- Otros módulos solo usan `corridas.service` (interfaz pública), nunca `models` ni `router`.
- Este módulo es dueño de sus tablas.
"""

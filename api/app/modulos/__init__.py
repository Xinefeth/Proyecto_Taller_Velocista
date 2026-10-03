"""Módulos del monolito modular (DO-02, sección 5).

Cada módulo: router.py (Controller) · service.py (lógica e interfaz pública) ·
models.py (tablas) · schemas.py (DTO) · repository.py opcional.

catalogo      Tipos de componente, componentes, inventario          HU-01 a HU-05
armador       Robots, versiones, piezas, compatibilidad             HU-06 a HU-09
reglamento    Perfiles de reglamento y validación                   HU-10, HU-11
corridas      Corridas, métrica J, telemetría por vuelta            HU-19, HU-20, HU-26
optimizacion  Twiddle y optimización bayesiana                      HU-27 a HU-29
eventos       Registro de eventos del sistema                       HU-23
auth          Usuarios, roles, tokens de dispositivo                por definir
"""

# HU-16 · Calibrar los sensores y arrancar

**Fuente: backlog del curso**

- **Story Points:** 0.5
- **Rama sugerida:** `016-calibrate-and-start`

## Historia de usuario

> Como piloto, quiero calibrar y arrancar el robot desde la consola, para prepararlo
> rápido en la pista.

## Criterios de aceptación (oficiales)

1. **ARRANCAR** queda bloqueado hasta calibrar.
2. La **calibración toma menos de 20 s** (el reglamento da 1 min para todo).
3. **Detener** siempre está disponible.

### Equivalente Given/When/Then

- **Dado** un robot sin calibrar, **cuando** el piloto intenta arrancar, **entonces** el
  arranque está bloqueado hasta que calibre.
- **Dado** que el piloto lanza la calibración, **cuando** se ejecuta, **entonces**
  termina en menos de 20 s.
- **Dado** cualquier estado del robot, **cuando** el piloto quiere detener, **entonces**
  la acción de detener está disponible.

## Requisitos funcionales

- **FR-001** El arranque está bloqueado mientras el robot no esté calibrado.
- **FR-002** El piloto puede lanzar la calibración desde la consola.
- **FR-003** La calibración termina en menos de 20 segundos.
- **FR-004** La acción de detener está siempre disponible.

## Fuera de alcance

- Afinar parámetros del controlador (setup) y optimización.
- La visualización de la regleta durante la calibración (HU-15).

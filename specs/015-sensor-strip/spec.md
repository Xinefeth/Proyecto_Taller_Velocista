# HU-15 · Visualizar la regleta de sensores

**Fuente: backlog del curso**

- **Story Points:** 0.5
- **Rama sugerida:** `015-sensor-strip`

## Historia de usuario

> Como piloto, quiero ver los 16 canales con la posición y el error, para calibrar y
> detectar sensores fallados.

## Criterios de aceptación (oficiales)

1. Muestra las **16 lecturas** como barras con su valor.
2. Muestra la **posición (mm)**, el **error** y si está **centrada**.

### Equivalente Given/When/Then

- **Dado** un robot con su regleta (16 canales, 2 sensores QTR-8A), **cuando** el piloto
  abre la vista de la regleta, **entonces** ve las 16 lecturas como barras con su valor.
- **Dado** que llegan lecturas de la regleta, **cuando** se actualizan, **entonces** la
  vista muestra la posición en mm, el error y si la línea está centrada.

## Requisitos funcionales

- **FR-001** El sistema muestra las 16 lecturas de la regleta como barras.
- **FR-002** Cada barra muestra su valor.
- **FR-003** El sistema muestra la posición de la línea en mm.
- **FR-004** El sistema muestra el error.
- **FR-005** El sistema indica si la línea está centrada.

## Nota de arquitectura

HU-15 **no tiene endpoint REST**: su flujo es por **WebSocket**. Los 16 canales (2
sensores QTR-8A) se declaran en el manifiesto y sus valores llegan en el mensaje
`senales` por `/ws/robot`, que el gateway redifunde a la consola por `/ws/consola`.

## Fuera de alcance

- El resto de la telemetría (tiempos de vuelta, PWM de motores).
- Lanzar la calibración o el arranque (HU-16).

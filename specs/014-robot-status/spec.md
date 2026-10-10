# HU-14 · Consultar el estado del robot

**Fuente: backlog del curso**

- **Story Points:** 0.5
- **Rama sugerida:** `014-robot-status`

## Historia de usuario

> Como piloto, quiero ver batería, enlace, lazo y estado, para saber si el robot está
> listo para correr.

## Criterios de aceptación (oficiales)

1. La barra superior muestra **batería (V)**, **enlace (dBm y ms)**, **lazo (Hz)** y
   **estado**.
2. Se actualiza **al menos 1 vez por segundo**.
3. Si se pierde el enlace, se indica en **menos de 2 s**.

### Equivalente Given/When/Then

- **Dado** un robot conectado, **cuando** el piloto mira la barra superior, **entonces**
  ve la batería en voltios, el enlace en dBm y ms, el lazo en Hz y el estado actual.
- **Dado** el robot conectado, **cuando** pasa el tiempo, **entonces** la barra se
  refresca al menos una vez por segundo.
- **Dado** que el enlace se pierde, **cuando** ocurre, **entonces** la consola lo indica
  en menos de 2 segundos.

## Requisitos funcionales

- **FR-001** La barra superior muestra la batería en voltios.
- **FR-002** La barra superior muestra el enlace en dBm y en ms.
- **FR-003** La barra superior muestra el lazo en Hz.
- **FR-004** La barra superior muestra el estado del robot.
- **FR-005** La información se actualiza al menos una vez por segundo.
- **FR-006** La pérdida de enlace se indica en menos de 2 segundos.

## Fuera de alcance

- Enviar comandos al robot (HU-16).
- El detalle por canal de la regleta (HU-15).

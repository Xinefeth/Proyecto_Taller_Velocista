# HU-13 · Seleccionar el robot

**Fuente: backlog del curso**

- **Story Points:** 0.5
- **Rama sugerida:** `013-select-robot`

## Historia de usuario

> Como piloto, quiero elegir el robot, para que la consola muestre solo lo que ese robot
> tiene.

## Criterios de aceptación (oficiales)

1. Lista los robots del armador y muestra **tipo, versión y firmware**.
2. Los paneles se arman según sus **sensores y actuadores**: sin encoder no aparece ese
   panel.

### Equivalente Given/When/Then

- **Dado** que hay robots registrados en el armador, **cuando** el piloto abre la
  selección de robot, **entonces** ve la lista con el tipo, la versión y el firmware de
  cada uno.
- **Dado** un robot seleccionado, **cuando** la consola arma su vista, **entonces**
  muestra únicamente los paneles de los dispositivos que ese robot declara; si el robot
  no tiene encoder, el panel de encoder no aparece.

## Requisitos funcionales

- **FR-001** El sistema lista los robots registrados.
- **FR-002** Por cada robot muestra su tipo, su versión y su firmware.
- **FR-003** Al seleccionar un robot, la vista muestra solo los paneles correspondientes
  a los sensores y actuadores que ese robot declara.
- **FR-004** Si el robot no declara un dispositivo (p. ej. encoder), su panel no aparece.

## Fuera de alcance

- Crear, editar o archivar robots y versiones (eso es del armado, otra historia).
- Conexión con el robot físico y telemetría en vivo (HU-14/HU-15).

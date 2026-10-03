# EN-02 · Contrato de mensajes y manifiesto

| Contenido | Ubicación |
| --- | --- |
| Documento técnico | `EN-02_Documentacion_tecnica_contrato_v1.docx` |
| Ejemplo JSON de cada mensaje (validados en cada `pytest`) | `ejemplos/` |
| JSON Schema generados desde el código | `schemas/` (`cd api && python -m app.contrato.exportar`) |
| Implementación de referencia | `api/app/contrato/` |

Convención de nombres de los ejemplos: `<emisor>.<tipo>.json`, donde el emisor `api_a_velocista` representa los mensajes que la API envía al robot.

Todo cambio del contrato actualiza en el mismo PR: `api/app/contrato/`, los ejemplos, los esquemas, el firmware y el documento técnico.

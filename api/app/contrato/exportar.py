"""Genera los JSON Schema del contrato en docs/contrato/schemas.

Uso: python -m app.contrato.exportar
"""

import json

from app.contrato.catalogo import CATALOGO
from app.core.config import RAIZ_REPO

DESTINO = RAIZ_REPO / "docs" / "contrato" / "schemas"


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for (emisor, tipo), definicion in CATALOGO.items():
        nombre = f"{emisor.replace('->', '_a_')}.{tipo}.schema.json"
        esquema = definicion.modelo.model_json_schema()
        esquema["$comment"] = f"Frecuencia: {definicion.frecuencia}. Ack: {definicion.requiere_ack}"
        (DESTINO / nombre).write_text(json.dumps(esquema, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(CATALOGO)} esquemas en {DESTINO}")


if __name__ == "__main__":
    main()

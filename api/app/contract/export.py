"""Genera los JSON Schema del contrato en docs/contrato/schemas.

Uso: python -m app.contract.export
"""

import json

from app.contract.catalog import CATALOG
from app.core.config import RAIZ_REPO

DESTINO = RAIZ_REPO / "docs" / "contrato" / "schemas"


def main() -> None:
    DESTINO.mkdir(parents=True, exist_ok=True)
    for (emisor, tipo), definicion in CATALOG.items():
        nombre = f"{emisor.replace('->', '_a_')}.{tipo}.schema.json"
        esquema = definicion.model.model_json_schema()
        esquema["$comment"] = f"Frecuencia: {definicion.frequency}. Ack: {definicion.requires_ack}"
        (DESTINO / nombre).write_text(json.dumps(esquema, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(CATALOG)} esquemas en {DESTINO}")


if __name__ == "__main__":
    main()

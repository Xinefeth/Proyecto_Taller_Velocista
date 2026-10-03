"""Base del esquema: tabla de eventos del sistema.

Las tablas del dominio (catálogo, robots, corridas...) se agregan cuando se
apruebe el modelo de datos de DO-03, cada una en su propia migración.

Revision ID: 0001_base
Revises:
Create Date: 2026-09-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0001_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evento",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column(
            "fecha", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("sistema", sa.String(40), nullable=False),
        sa.Column("nivel", sa.String(10), nullable=False, server_default="info"),
        sa.Column("mensaje", sa.Text, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evento")

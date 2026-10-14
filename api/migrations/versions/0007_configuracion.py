"""Modo de funcionamiento y color de línea persistidos por robot (HU-18).

Revision ID: 0007_configuracion
Revises: 0005_operaciones
"""

import sqlalchemy as sa
from alembic import op

revision = "0007_configuracion"
down_revision = "0005_operaciones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracion_robot",
        sa.Column("robot_id", sa.String(40), primary_key=True),
        sa.Column("modo", sa.String(20), nullable=True),
        sa.Column("linea", sa.String(20), nullable=True),
        sa.Column(
            "actualizado_en",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["robot_id"], ["robot.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "modo IS NULL OR modo IN ('prueba', 'competencia')", name="ck_config_modo"
        ),
        sa.CheckConstraint("linea IS NULL OR linea IN ('negra', 'blanca')", name="ck_config_linea"),
    )


def downgrade() -> None:
    op.drop_table("configuracion_robot")

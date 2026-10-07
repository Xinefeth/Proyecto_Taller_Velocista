"""Identificación de robots sin versiones (EN-04 / DO-03).

Revision ID: 0003_robot
Revises: 0002_catalogo
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_robot"
down_revision = "0002_catalogo"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "robot",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("codigo_corto", sa.String(12), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("firmware", sa.String(20), nullable=True),
        sa.Column("version_actual_id", sa.BigInteger(), nullable=True),
        sa.Column("archivado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.UniqueConstraint("codigo_corto"),
        sa.CheckConstraint("btrim(id) <> ''", name="ck_robot_id_no_vacio"),
        sa.CheckConstraint("btrim(nombre) <> ''", name="ck_robot_nombre_no_vacio"),
        sa.CheckConstraint("btrim(codigo_corto) <> ''", name="ck_robot_codigo_no_vacio"),
        sa.CheckConstraint("tipo IN ('velocista', 'minisumo')", name="ck_robot_tipo"),
        # No permite punteros inválidos antes de implementar version y su FK.
        sa.CheckConstraint("version_actual_id IS NULL", name="ck_robot_sin_version"),
    )


def downgrade() -> None:
    op.drop_table("robot")

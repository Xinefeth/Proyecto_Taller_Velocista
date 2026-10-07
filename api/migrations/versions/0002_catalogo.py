"""Tipos de componente, catálogo e inventario (EN-04 / DO-03).

Revision ID: 0002_catalogo
Revises: 0001_base
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002_catalogo"
down_revision = "0001_base"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tipo_componente",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("color", sa.String(7), nullable=False),
        sa.Column(
            "campos", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "capacidades", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.CheckConstraint("btrim(id) <> ''", name="ck_tipo_id_no_vacio"),
        sa.CheckConstraint("btrim(nombre) <> ''", name="ck_tipo_nombre_no_vacio"),
        sa.CheckConstraint("color ~ '^#[0-9A-Fa-f]{6}$'", name="ck_tipo_color"),
        sa.CheckConstraint("jsonb_typeof(campos) = 'array'", name="ck_tipo_campos_array"),
        sa.CheckConstraint("jsonb_typeof(capacidades) = 'array'", name="ck_tipo_capacidades_array"),
    )
    op.create_table(
        "componente",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column("tipo_id", sa.String(40), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("precio", sa.Numeric(12, 2), nullable=False),
        sa.Column("masa_g", sa.Numeric(12, 3), nullable=False),
        sa.Column("tienda", sa.String(200), nullable=False, server_default=""),
        sa.Column("consumo_a", sa.Numeric(12, 4), nullable=True),
        sa.Column(
            "especificaciones",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("archivado", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["tipo_id"], ["tipo_componente.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("btrim(id) <> ''", name="ck_componente_id_no_vacio"),
        sa.CheckConstraint("btrim(nombre) <> ''", name="ck_componente_nombre_no_vacio"),
        sa.CheckConstraint("precio > 0 AND precio <> 'NaN'::numeric", name="ck_componente_precio"),
        sa.CheckConstraint("masa_g >= 0 AND masa_g <> 'NaN'::numeric", name="ck_componente_masa"),
        sa.CheckConstraint(
            "consumo_a IS NULL OR (consumo_a >= 0 AND consumo_a <> 'NaN'::numeric)",
            name="ck_componente_consumo",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(especificaciones) = 'object'", name="ck_componente_specs_objeto"
        ),
    )
    op.create_index("ix_componente_tipo_id", "componente", ["tipo_id"])
    op.create_table(
        "inventario",
        sa.Column("componente_id", sa.String(40), primary_key=True),
        sa.Column("stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("revision", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.ForeignKeyConstraint(["componente_id"], ["componente.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("stock >= 0", name="ck_inventario_stock"),
        sa.CheckConstraint("revision >= 1", name="ck_inventario_revision"),
    )


def downgrade() -> None:
    op.drop_table("inventario")
    op.drop_index("ix_componente_tipo_id", table_name="componente")
    op.drop_table("componente")
    op.drop_table("tipo_componente")

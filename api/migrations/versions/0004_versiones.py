"""Ranuras, versiones y piezas históricas (EN-04 / DO-03)."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0004_versiones"
down_revision = "0003_robot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ranura",
        sa.Column("id", sa.String(40), primary_key=True),
        sa.Column(
            "tipo_id",
            sa.String(40),
            sa.ForeignKey("tipo_componente.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("obligatoria", sa.Boolean(), nullable=False),
        sa.Column("cantidad_editable", sa.Boolean(), nullable=False),
        sa.Column("depende_reglamento", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "version",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "robot_id",
            sa.String(40),
            sa.ForeignKey("robot.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("nota", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False),
        sa.UniqueConstraint("robot_id", "ordinal", name="uq_version_ordinal"),
        sa.UniqueConstraint("id", "robot_id", name="uq_version_pertenencia"),
        sa.CheckConstraint("id BETWEEN 1 AND 9007199254740991", name="ck_version_id"),
        sa.CheckConstraint("ordinal >= 0", name="ck_version_ordinal"),
        sa.CheckConstraint("char_length(nota) <= 1000", name="ck_version_nota"),
        sa.CheckConstraint(
            "estado IN ('Actual','Anterior','Descartada','Concepto','Borrador')",
            name="ck_version_estado",
        ),
    )
    op.create_index("ix_version_robot_id", "version", ["robot_id"])
    op.create_index(
        "uq_version_actual",
        "version",
        ["robot_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'Actual'"),
    )
    op.create_table(
        "version_componente",
        sa.Column(
            "version_id",
            sa.BigInteger(),
            sa.ForeignKey("version.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "ranura_id",
            sa.String(40),
            sa.ForeignKey("ranura.id", ondelete="RESTRICT"),
            primary_key=True,
        ),
        sa.Column(
            "componente_id",
            sa.String(40),
            sa.ForeignKey("componente.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("componente_snapshot", postgresql.JSONB(), nullable=False),
        sa.CheckConstraint("cantidad > 0", name="ck_version_componente_cantidad"),
        sa.CheckConstraint(
            "jsonb_typeof(componente_snapshot) = 'object'", name="ck_version_componente_snapshot"
        ),
    )
    op.create_index("ix_version_componente_componente_id", "version_componente", ["componente_id"])
    op.drop_constraint("ck_robot_sin_version", "robot", type_="check")
    op.create_foreign_key(
        "fk_robot_version_actual",
        "robot",
        "version",
        ["version_actual_id", "id"],
        ["id", "robot_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    # No borra historial al bajar una base poblada: el llamador debe resolverlo.
    op.drop_constraint("fk_robot_version_actual", "robot", type_="foreignkey")
    op.create_check_constraint("ck_robot_sin_version", "robot", "version_actual_id IS NULL")
    op.drop_table("version_componente")
    op.drop_table("version")
    op.drop_table("ranura")

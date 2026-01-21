"""Add purchase decisions table

Revision ID: 002
Revises: 001
Create Date: 2026-01-21 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create purchase_decisions table
    op.create_table(
        "purchase_decisions",
        sa.Column("decision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=100), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("decision_category", sa.String(length=50), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("analysis", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "alternatives", postgresql.JSON(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("conditions", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("actual_purchase", sa.Boolean(), nullable=True),
        sa.Column("regret_level", sa.Integer(), nullable=True),
        sa.Column("user_feedback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
        ),
        sa.PrimaryKeyConstraint("decision_id"),
    )
    # Create index on user_id for faster lookups
    op.create_index(
        op.f("ix_purchase_decisions_user_id"),
        "purchase_decisions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_purchase_decisions_user_id"), table_name="purchase_decisions"
    )
    op.drop_table("purchase_decisions")

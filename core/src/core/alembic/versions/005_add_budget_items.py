"""add budget_items table

Revision ID: 005
Revises: 004
Create Date: 2026-01-24

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create budget_items table."""
    op.create_table(
        "budget_items",
        sa.Column("item_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("budget_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("transaction_date", sa.DateTime, nullable=False),
        sa.Column("decision_id", UUID(as_uuid=True), nullable=True),
        sa.Column("exceeded_budget", sa.Boolean, default=False),
        sa.Column("category_spent_before", sa.Numeric(10, 2), nullable=True),
        sa.Column("category_spent_after", sa.Numeric(10, 2), nullable=True),
        sa.Column("category_limit", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_planned", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(
            ["budget_id"], ["budgets.budget_id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["decision_id"], ["purchase_decisions.decision_id"], ondelete="SET NULL"
        ),
    )

    # Add indexes for common queries
    op.create_index("ix_budget_items_budget_id", "budget_items", ["budget_id"])
    op.create_index("ix_budget_items_user_id", "budget_items", ["user_id"])
    op.create_index("ix_budget_items_category", "budget_items", ["category"])
    op.create_index(
        "ix_budget_items_transaction_date", "budget_items", ["transaction_date"]
    )
    op.create_index("ix_budget_items_decision_id", "budget_items", ["decision_id"])


def downgrade() -> None:
    """Drop budget_items table."""
    op.drop_index("ix_budget_items_decision_id")
    op.drop_index("ix_budget_items_transaction_date")
    op.drop_index("ix_budget_items_category")
    op.drop_index("ix_budget_items_user_id")
    op.drop_index("ix_budget_items_budget_id")
    op.drop_table("budget_items")

"""Budget management service."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Budget
from core.models.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    CategoryBudget,
)


class BudgetService:
    """Handle budget CRUD operations."""

    def __init__(self, db: Session):
        """Initialize budget service."""
        self.db = db

    def create_budget(self, user_id: UUID, budget_data: BudgetCreate) -> Budget:
        """Create a new budget."""
        # Convert Pydantic models to dict for JSON storage
        # Convert Decimals to floats for JSON compatibility
        categories_dict = {
            key: {"limit": float(value.limit), "spent": float(value.spent)}
            for key, value in budget_data.categories.items()
        }

        budget = Budget(
            user_id=user_id,
            name=budget_data.name,
            total_monthly=budget_data.total_monthly,
            period_start=budget_data.period_start,
            period_end=budget_data.period_end,
            categories=categories_dict,
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def get_budget(self, budget_id: UUID, user_id: UUID) -> Optional[Budget]:
        """Get a budget by ID for a specific user."""
        return (
            self.db.query(Budget)
            .filter(Budget.budget_id == budget_id, Budget.user_id == user_id)
            .first()
        )

    def list_budgets(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[Budget]:
        """List all budgets for a user."""
        return (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id)
            .order_by(Budget.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_budget(
        self, budget_id: UUID, user_id: UUID, budget_update: BudgetUpdate
    ) -> Optional[Budget]:
        """Update a budget."""
        budget = self.get_budget(budget_id, user_id)
        if not budget:
            return None

        update_data = budget_update.model_dump(exclude_unset=True)

        # Convert categories if present (they're already dicts after model_dump)
        if "categories" in update_data and update_data["categories"]:
            categories_dict = {}
            for key, value in update_data["categories"].items():
                if isinstance(value, dict):
                    # Already a dict from model_dump, ensure floats
                    categories_dict[key] = {
                        "limit": float(value.get("limit", 0)),
                        "spent": float(value.get("spent", 0)),
                    }
                else:
                    # Pydantic model (shouldn't happen but handle it)
                    categories_dict[key] = {
                        "limit": float(value.limit),
                        "spent": float(value.spent),
                    }
            update_data["categories"] = categories_dict

        for key, value in update_data.items():
            setattr(budget, key, value)

        budget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def delete_budget(self, budget_id: UUID, user_id: UUID) -> bool:
        """Delete a budget."""
        budget = self.get_budget(budget_id, user_id)
        if not budget:
            return False

        self.db.delete(budget)
        self.db.commit()
        return True

    def update_category_spending(
        self, budget_id: UUID, user_id: UUID, category: str, amount: float
    ) -> Optional[Budget]:
        """Update spending amount for a specific category."""
        budget = self.get_budget(budget_id, user_id)
        if not budget or category not in budget.categories:
            return None

        # Update the spending amount
        categories_copy = budget.categories.copy()
        categories_copy[category]["spent"] = float(amount)
        budget.categories = categories_copy

        # Flag as modified for SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(budget, "categories")

        budget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(budget)
        return budget

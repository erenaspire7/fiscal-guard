"""Budget management service."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from core.database.models import Budget, BudgetItem
from core.models.budget import (
    BudgetAnalysisOverTime,
    BudgetCreate,
    BudgetItemCreate,
    BudgetUpdate,
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

    def get_active_budget(self, user_id: UUID) -> Optional[Budget]:
        """Get the currently active budget for a user (period contains today)."""
        today = datetime.utcnow().date()
        return (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
            .order_by(Budget.created_at.desc())
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

    def update_category_limit(
        self, budget_id: UUID, user_id: UUID, category: str, new_limit: float
    ) -> Optional[Budget]:
        """Update limit for a specific category."""
        budget = self.get_budget(budget_id, user_id)
        if not budget or category not in budget.categories:
            return None

        # Update the limit
        categories_copy = budget.categories.copy()
        categories_copy[category]["limit"] = float(new_limit)
        budget.categories = categories_copy

        # Update total monthly budget to reflect change
        total_limit = sum(cat["limit"] for cat in categories_copy.values())
        budget.total_monthly = Decimal(str(total_limit))

        # Flag as modified for SQLAlchemy to detect the change
        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(budget, "categories")

        budget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def add_category(
        self, budget_id: UUID, user_id: UUID, category: str, limit: float
    ) -> Optional[Budget]:
        """Add a new category to a budget."""
        budget = self.get_budget(budget_id, user_id)
        if not budget:
            return None

        if category in budget.categories:
            return budget  # Already exists

        categories_copy = budget.categories.copy()
        categories_copy[category] = {"limit": float(limit), "spent": 0}
        budget.categories = categories_copy

        total_limit = sum(cat["limit"] for cat in categories_copy.values())
        budget.total_monthly = Decimal(str(total_limit))

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(budget, "categories")

        budget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(budget)
        return budget

    def add_budget_item(
        self,
        budget_id: UUID,
        user_id: UUID,
        item_data: BudgetItemCreate,
    ) -> Optional[BudgetItem]:
        """Add a budget item and update budget category spending.

        This method:
        1. Records the individual transaction
        2. Tracks whether it exceeded the budget
        3. Updates the budget's category spending
        """
        budget = self.get_budget(budget_id, user_id)
        if not budget:
            return None

        category = item_data.category
        if category not in budget.categories:
            return None

        # Get current category state
        category_info = budget.categories[category]
        spent_before = Decimal(str(category_info.get("spent", 0)))
        limit = Decimal(str(category_info.get("limit", 0)))
        spent_after = spent_before + item_data.amount

        # Check if this exceeds budget
        exceeded_budget = spent_after > limit

        # Create budget item
        budget_item = BudgetItem(
            budget_id=budget_id,
            user_id=user_id,
            item_name=item_data.item_name,
            amount=item_data.amount,
            category=category,
            transaction_date=item_data.transaction_date,
            decision_id=item_data.decision_id,
            exceeded_budget=exceeded_budget,
            category_spent_before=spent_before,
            category_spent_after=spent_after,
            category_limit=limit,
            notes=item_data.notes,
            is_planned=item_data.is_planned,
        )
        # Update budget category spending before adding item to avoid
        # SAWarning: Session.add() during flush (triggered by dirty budget state)
        categories_copy = budget.categories.copy()
        categories_copy[category]["spent"] = float(spent_after)
        budget.categories = categories_copy

        from sqlalchemy.orm.attributes import flag_modified

        flag_modified(budget, "categories")
        budget.updated_at = datetime.utcnow()

        self.db.add(budget_item)
        self.db.commit()
        self.db.refresh(budget_item)
        return budget_item

    def get_budget_items(
        self,
        budget_id: UUID,
        user_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[BudgetItem]:
        """Get budget items for a budget, optionally filtered by category."""
        query = self.db.query(BudgetItem).filter(
            BudgetItem.budget_id == budget_id,
            BudgetItem.user_id == user_id,
        )

        if category:
            query = query.filter(BudgetItem.category == category)

        return (
            query.order_by(BudgetItem.transaction_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_budget_with_items(self, budget_id: UUID, user_id: UUID) -> Optional[Budget]:
        """Get budget with all its items loaded."""
        budget = self.get_budget(budget_id, user_id)
        if not budget:
            return None

        # Eagerly load items
        self.db.refresh(budget, ["budget_items"])
        return budget

    def analyze_budgets_over_time(
        self, user_id: UUID, num_periods: int = 6
    ) -> BudgetAnalysisOverTime:
        """Analyze budget performance over multiple periods.

        This provides insights into spending trends and budget adherence
        over time, which can influence guard scores.
        """
        # Get recent budgets ordered by period_start
        budgets = (
            self.db.query(Budget)
            .filter(Budget.user_id == user_id)
            .order_by(Budget.period_start.desc())
            .limit(num_periods)
            .all()
        )

        if not budgets:
            return BudgetAnalysisOverTime(
                periods=[],
                average_adherence=100.0,
                trend="stable",
                category_insights={},
                over_budget_count=0,
            )

        # Analyze each period
        periods = []
        adherence_scores = []
        over_budget_count = 0
        category_data = {}

        for budget in reversed(budgets):  # Oldest to newest for trend analysis
            total_limit = float(budget.total_monthly)
            total_spent = sum(
                cat_info.get("spent", 0) for cat_info in budget.categories.values()
            )
            adherence = (
                ((total_limit - total_spent) / total_limit * 100)
                if total_limit > 0
                else 100.0
            )
            adherence = max(0, adherence)  # Cap at 0 if overspent
            adherence_scores.append(adherence)

            # Count over-budget categories
            period_over_budget = sum(
                1
                for cat_info in budget.categories.values()
                if cat_info.get("spent", 0) > cat_info.get("limit", 0)
            )
            over_budget_count += period_over_budget

            # Collect category data
            for cat_name, cat_info in budget.categories.items():
                if cat_name not in category_data:
                    category_data[cat_name] = {
                        "periods": [],
                        "limits": [],
                        "spent": [],
                    }
                category_data[cat_name]["periods"].append(str(budget.period_start))
                category_data[cat_name]["limits"].append(cat_info.get("limit", 0))
                category_data[cat_name]["spent"].append(cat_info.get("spent", 0))

            periods.append(
                {
                    "budget_id": str(budget.budget_id),
                    "name": budget.name,
                    "period_start": str(budget.period_start),
                    "period_end": str(budget.period_end),
                    "total_limit": total_limit,
                    "total_spent": total_spent,
                    "adherence_percentage": round(adherence, 2),
                    "over_budget_categories": period_over_budget,
                }
            )

        # Calculate trend
        average_adherence = sum(adherence_scores) / len(adherence_scores)

        trend = "stable"
        if len(adherence_scores) >= 3:
            # Compare recent 3 periods to previous periods
            recent_avg = sum(adherence_scores[-3:]) / 3
            if len(adherence_scores) > 3:
                older_avg = sum(adherence_scores[:-3]) / (len(adherence_scores) - 3)
                if recent_avg > older_avg + 10:
                    trend = "improving"
                elif recent_avg < older_avg - 10:
                    trend = "declining"

        # Create category insights
        category_insights = {}
        for cat_name, cat_info in category_data.items():
            avg_spent = sum(cat_info["spent"]) / len(cat_info["spent"])
            avg_limit = sum(cat_info["limits"]) / len(cat_info["limits"])
            utilization = (avg_spent / avg_limit * 100) if avg_limit > 0 else 0

            category_insights[cat_name] = {
                "average_spent": round(avg_spent, 2),
                "average_limit": round(avg_limit, 2),
                "average_utilization": round(utilization, 2),
                "periods_tracked": len(cat_info["periods"]),
            }

        return BudgetAnalysisOverTime(
            periods=periods,
            average_adherence=round(average_adherence, 2),
            trend=trend,
            category_insights=category_insights,
            over_budget_count=over_budget_count,
        )

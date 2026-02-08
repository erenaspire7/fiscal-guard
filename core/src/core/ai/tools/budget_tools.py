"""Tools for budget-related handlers (query, expense, modification)."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from strands import tool

from core.models.budget import BudgetItemCreate
from core.models.context import UserFinancialContext
from core.services.budget import BudgetService


def create_budget_tools(
    db_session: Session,
    user_id: str,
    financial_context: Optional[UserFinancialContext] = None,
):
    """Create budget tools with database session and bound user_id.

    All tools fetch fresh data from the DB to avoid stale context issues
    when mutations (add category, log expense, update limit) occur mid-turn
    or across agent handoffs.

    Args:
        db_session: Database session
        user_id: User ID to bind to the tools
        financial_context: Pre-fetched financial context (unused, kept for API compat)
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValueError(f"Invalid user_id format: {user_id}")

    budget_service = BudgetService(db_session)

    def _get_active_budget():
        """Helper to get fresh active budget from DB."""
        return budget_service.get_active_budget(user_uuid)

    @tool
    def get_budget_summary() -> dict:
        """Get the overall budget summary including all categories, spending, and remaining amounts.

        Returns:
            Budget overview with total spent, total limit, remaining, and per-category breakdown.
        """
        budget = _get_active_budget()
        if not budget:
            return {"has_budget": False, "message": "No active budget found."}

        days_remaining = (budget.period_end - datetime.utcnow().date()).days
        total_limit = float(budget.total_monthly)
        total_spent = sum(cat.get("spent", 0) for cat in budget.categories.values())
        total_remaining = total_limit - total_spent
        percentage_used = (total_spent / total_limit * 100) if total_limit > 0 else 0

        categories = {}
        for name, cat in budget.categories.items():
            cat_limit = float(cat.get("limit", 0))
            cat_spent = float(cat.get("spent", 0))
            cat_remaining = cat_limit - cat_spent
            cat_pct = (cat_spent / cat_limit * 100) if cat_limit > 0 else 0
            categories[name] = {
                "spent": cat_spent,
                "limit": cat_limit,
                "remaining": cat_remaining,
                "percentage_used": round(cat_pct, 1),
            }

        return {
            "has_budget": True,
            "budget_name": budget.name,
            "total_spent": total_spent,
            "total_limit": total_limit,
            "total_remaining": total_remaining,
            "percentage_used": round(percentage_used, 1),
            "period_start": budget.period_start.isoformat(),
            "period_end": budget.period_end.isoformat(),
            "days_remaining": days_remaining,
            "categories": categories,
        }

    @tool
    def get_category_spending(category: str) -> dict:
        """Get detailed spending information for a specific budget category.

        Args:
            category: The budget category name to look up (e.g., 'groceries', 'entertainment')

        Returns:
            Category spending details including spent, limit, remaining, and percentage used.
        """
        category_lower = category.lower()

        budget = _get_active_budget()
        if not budget:
            return {"found": False, "message": "No active budget found."}

        days_remaining = (budget.period_end - datetime.utcnow().date()).days

        if category_lower not in budget.categories:
            valid_cats = list(budget.categories.keys())
            return {
                "found": False,
                "category": category,
                "message": f"Category '{category}' not found.",
                "available_categories": valid_cats,
            }

        cat = budget.categories[category_lower]
        cat_limit = float(cat.get("limit", 0))
        cat_spent = float(cat.get("spent", 0))
        cat_remaining = cat_limit - cat_spent
        cat_pct = (cat_spent / cat_limit * 100) if cat_limit > 0 else 0
        total_days = (budget.period_end - budget.period_start).days
        elapsed_days = total_days - days_remaining

        return {
            "found": True,
            "category": category_lower,
            "spent": cat_spent,
            "limit": cat_limit,
            "remaining": cat_remaining,
            "percentage_used": round(cat_pct, 1),
            "days_remaining": days_remaining,
            "elapsed_days": elapsed_days,
            "total_days": total_days,
        }

    @tool
    def get_spending_trends(days: int) -> dict:
        """Get spending trends over a specified number of days.

        Args:
            days: Number of days to analyze (e.g., 7, 30, 90)

        Returns:
            Spending trend analysis with per-category breakdown and overall trajectory.
        """
        analysis = budget_service.analyze_budgets_over_time(user_uuid)

        return {
            "days_requested": days,
            "periods_analyzed": len(analysis.periods),
            "average_adherence": analysis.average_adherence,
            "trend": analysis.trend,
            "over_budget_count": analysis.over_budget_count,
            "category_insights": analysis.category_insights,
            "periods": analysis.periods,
        }

    @tool
    def log_expense(item_name: str, amount: float, category: str) -> dict:
        """Log an expense to the budget. Records the transaction and updates category spending.

        Args:
            item_name: Name/description of the expense (e.g., 'coffee', 'uber ride')
            amount: The expense amount in dollars (e.g., 12.50)
            category: The budget category to log under (e.g., 'food', 'transport')

        Returns:
            Result with success status, updated spending, and budget impact.
        """
        category_lower = category.lower()

        budget = _get_active_budget()
        if not budget:
            return {"success": False, "error": "No active budget found."}

        if category_lower not in budget.categories:
            valid_cats = list(budget.categories.keys())
            return {
                "success": False,
                "error": f"Category '{category}' not found in budget.",
                "available_categories": valid_cats,
            }

        try:
            item_data = BudgetItemCreate(
                item_name=item_name,
                amount=Decimal(str(amount)),
                category=category_lower,
                transaction_date=datetime.utcnow(),
                is_planned=False,
            )

            result = budget_service.add_budget_item(
                budget_id=budget.budget_id,
                user_id=user_uuid,
                item_data=item_data,
            )

            if not result:
                return {
                    "success": False,
                    "error": f"Failed to log expense for '{item_name}'.",
                }

            spent_after = float(result.category_spent_after)
            limit = float(result.category_limit)
            remaining = limit - spent_after

            return {
                "success": True,
                "item_name": item_name,
                "amount": amount,
                "category": category_lower,
                "category_spent_after": spent_after,
                "category_limit": limit,
                "category_remaining": remaining,
                "exceeded_budget": result.exceeded_budget,
            }
        except Exception as e:
            return {"success": False, "error": f"Error logging expense: {str(e)}"}

    @tool
    def update_category_limit(category: str, new_limit: float) -> dict:
        """Update the spending limit for a budget category.

        Args:
            category: The budget category to update (e.g., 'groceries', 'entertainment')
            new_limit: The new spending limit in dollars (e.g., 500.00)

        Returns:
            Result with old limit, new limit, and current spending status.
        """
        category_lower = category.lower()

        budget = _get_active_budget()
        if not budget:
            return {"success": False, "error": "No active budget found."}

        if category_lower not in budget.categories:
            valid_cats = list(budget.categories.keys())
            return {
                "success": False,
                "error": f"Category '{category}' not found.",
                "available_categories": valid_cats,
            }

        cat = budget.categories[category_lower]
        old_limit = float(cat.get("limit", 0))
        current_spent = float(cat.get("spent", 0))

        try:
            updated = budget_service.update_category_limit(
                budget_id=budget.budget_id,
                user_id=user_uuid,
                category=category_lower,
                new_limit=new_limit,
            )

            if not updated:
                return {"success": False, "error": "Failed to update category limit."}

            return {
                "success": True,
                "category": category_lower,
                "old_limit": old_limit,
                "new_limit": new_limit,
                "current_spent": current_spent,
                "remaining": new_limit - current_spent,
            }
        except Exception as e:
            return {"success": False, "error": f"Error updating limit: {str(e)}"}

    @tool
    def add_budget_category(category: str, limit: float) -> dict:
        """Add a new category to the budget with a specified spending limit.

        Args:
            category: The name of the new category to add (e.g., 'subscriptions', 'pets')
            limit: The spending limit for the new category in dollars (REQUIRED - must be greater than 0)

        Returns:
            Result with success status and the new category details.
        """
        category_lower = category.lower()

        budget = _get_active_budget()
        if not budget:
            return {"success": False, "error": "No active budget found."}

        if category_lower in budget.categories:
            return {
                "success": False,
                "error": f"Category '{category}' already exists.",
            }

        if limit <= 0:
            return {
                "success": False,
                "error": "Category limit must be greater than 0. Please specify a valid spending limit.",
            }

        try:
            updated = budget_service.add_category(
                budget_id=budget.budget_id,
                user_id=user_uuid,
                category=category_lower,
                limit=limit,
            )

            if not updated:
                return {"success": False, "error": "Failed to add category."}

            return {
                "success": True,
                "category": category_lower,
                "limit": limit,
            }
        except Exception as e:
            return {"success": False, "error": f"Error adding category: {str(e)}"}

    return [
        get_budget_summary,
        get_category_spending,
        get_spending_trends,
        log_expense,
        update_category_limit,
        add_budget_category,
    ]

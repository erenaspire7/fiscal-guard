"""Service for building shared user financial context.

Builds a UserFinancialContext once per request with standardized queries,
eliminating redundant DB lookups across the intent classifier, agents, and handlers.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Budget, Goal, PurchaseDecision
from core.models.context import (
    ActiveBudgetContext,
    BudgetCategoryContext,
    GoalContext,
    RecentDecisionContext,
    UserFinancialContext,
)


class ContextBuilder:
    """Builds comprehensive user financial context."""

    def __init__(self, db: Session):
        self.db = db

    def build_context(self, user_id: UUID) -> UserFinancialContext:
        """Build complete financial context for a user.

        Uses standardized queries: budget must span today,
        goals must be active, decisions within last 30 days.
        """
        budget_ctx = self._build_budget_context(user_id)
        goals_ctx = self._build_goals_context(user_id)
        decisions_ctx = self._build_decisions_context(user_id)

        return UserFinancialContext(
            user_id=user_id,
            active_budget=budget_ctx,
            active_goals=goals_ctx,
            recent_decisions=decisions_ctx,
            has_budget=budget_ctx is not None,
            has_goals=len(goals_ctx) > 0,
        )

    def _build_budget_context(self, user_id: UUID) -> Optional[ActiveBudgetContext]:
        """Build active budget context.

        Standardized query: period_start <= today AND period_end >= today.
        """
        today = date.today()
        budget = (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

        if not budget:
            return None

        categories = {}
        total_spent = Decimal("0")
        total_limit = Decimal("0")

        for cat_name, details in budget.categories.items():
            limit = Decimal(str(details.get("limit", 0)))
            spent = Decimal(str(details.get("spent", 0)))
            remaining = limit - spent
            pct = float((spent / limit * 100) if limit > 0 else 0)

            categories[cat_name] = BudgetCategoryContext(
                name=cat_name,
                limit=limit,
                spent=spent,
                remaining=remaining,
                percentage_used=pct,
            )
            total_spent += spent
            total_limit += limit

        total_remaining = total_limit - total_spent
        total_pct = float((total_spent / total_limit * 100) if total_limit > 0 else 0)

        return ActiveBudgetContext(
            budget_id=budget.budget_id,
            name=budget.name,
            total_monthly=budget.total_monthly,
            period_start=budget.period_start,
            period_end=budget.period_end,
            categories=categories,
            total_spent=total_spent,
            total_limit=total_limit,
            total_remaining=total_remaining,
            percentage_used=total_pct,
        )

    def _build_goals_context(self, user_id: UUID) -> list[GoalContext]:
        """Build active goals context."""
        goals = (
            self.db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.is_completed == False)
            .order_by(Goal.created_at.desc())
            .all()
        )

        result = []
        for goal in goals:
            target = Decimal(str(goal.target_amount))
            current = Decimal(str(goal.current_amount))
            remaining = target - current
            pct = float((current / target * 100) if target > 0 else 0)

            result.append(
                GoalContext(
                    goal_id=goal.goal_id,
                    goal_name=goal.goal_name,
                    target_amount=target,
                    current_amount=current,
                    remaining=remaining,
                    percentage_complete=pct,
                    priority=goal.priority,
                    deadline=goal.deadline,
                )
            )
        return result

    def _build_decisions_context(self, user_id: UUID) -> list[RecentDecisionContext]:
        """Build recent decisions context (last 30 days)."""
        cutoff = datetime.utcnow() - timedelta(days=30)

        decisions = (
            self.db.query(PurchaseDecision)
            .filter(
                PurchaseDecision.user_id == user_id,
                PurchaseDecision.created_at > cutoff,
            )
            .order_by(PurchaseDecision.created_at.desc())
            .limit(20)
            .all()
        )

        return [
            RecentDecisionContext(
                decision_id=d.decision_id,
                item_name=d.item_name,
                amount=Decimal(str(d.amount)),
                category=d.category,
                score=d.score,
                decision_category=d.decision_category,
                actual_purchase=d.actual_purchase,
                regret_level=d.regret_level,
                created_at=d.created_at,
            )
            for d in decisions
        ]

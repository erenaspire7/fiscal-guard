"""Shared context models for conversation processing.

Built once per request in ConversationService, then passed through
to the intent classifier and all handlers to eliminate redundant DB queries.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BudgetCategoryContext(BaseModel):
    """Context for a single budget category."""

    name: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percentage_used: float


class ActiveBudgetContext(BaseModel):
    """Active budget context with all categories."""

    budget_id: UUID
    name: str
    total_monthly: Decimal
    period_start: date
    period_end: date
    categories: dict[str, BudgetCategoryContext]
    total_spent: Decimal
    total_limit: Decimal
    total_remaining: Decimal
    percentage_used: float


class GoalContext(BaseModel):
    """Context for a single financial goal."""

    goal_id: UUID
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    remaining: Decimal
    percentage_complete: float
    priority: str
    deadline: Optional[date] = None


class RecentDecisionContext(BaseModel):
    """Context for a recent purchase decision."""

    decision_id: UUID
    item_name: str
    amount: Decimal
    category: Optional[str]
    score: int
    decision_category: Optional[str]
    actual_purchase: Optional[bool]
    regret_level: Optional[int]
    created_at: datetime


class UserFinancialContext(BaseModel):
    """Comprehensive financial context built once per message."""

    user_id: UUID
    active_budget: Optional[ActiveBudgetContext] = None
    active_goals: List[GoalContext] = Field(default_factory=list)
    recent_decisions: List[RecentDecisionContext] = Field(default_factory=list)
    has_budget: bool = False
    has_goals: bool = False

    def get_category_names(self) -> List[str]:
        """Get budget category names (for slim classifier context)."""
        if not self.active_budget:
            return []
        return list(self.active_budget.categories.keys())

    def get_recent_decision_names(self) -> List[str]:
        """Get recent decision item names (for slim classifier context)."""
        return [d.item_name for d in self.recent_decisions]

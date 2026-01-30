"""Pydantic models for Budget."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBudget(BaseModel):
    """Budget category with limit and spent amount."""

    limit: Decimal = Field(..., ge=0)
    spent: Decimal = Field(default=Decimal("0"), ge=0)


class BudgetBase(BaseModel):
    """Base budget model."""

    name: str = Field(..., min_length=1, max_length=255)
    total_monthly: Decimal = Field(..., ge=0)
    period_start: date
    period_end: date
    categories: Dict[str, CategoryBudget]


class BudgetCreate(BudgetBase):
    """Budget creation model."""

    pass


class BudgetUpdate(BaseModel):
    """Budget update model."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    total_monthly: Optional[Decimal] = Field(None, ge=0)
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    categories: Optional[Dict[str, CategoryBudget]] = None


class BudgetResponse(BudgetBase):
    """Budget response model."""

    budget_id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetItemBase(BaseModel):
    """Base budget item model."""

    item_name: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=100)
    transaction_date: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    is_planned: bool = False


class BudgetItemCreate(BudgetItemBase):
    """Budget item creation model."""

    decision_id: Optional[UUID] = None


class BudgetItemResponse(BudgetItemBase):
    """Budget item response model."""

    item_id: UUID
    budget_id: UUID
    user_id: UUID
    decision_id: Optional[UUID] = None
    exceeded_budget: bool
    category_spent_before: Optional[Decimal] = None
    category_spent_after: Optional[Decimal] = None
    category_limit: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BudgetWithItems(BudgetResponse):
    """Budget response with items."""

    items: list["BudgetItemResponse"] = Field(default_factory=list)


class BudgetAnalysisOverTime(BaseModel):
    """Analysis of budget performance over multiple periods."""

    periods: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of budget periods with performance metrics",
    )
    average_adherence: float = Field(
        ...,
        description="Average budget adherence percentage across periods",
        ge=0,
        le=100,
    )
    trend: str = Field(
        ..., description="Trend direction: improving, declining, or stable"
    )
    category_insights: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-category insights across periods",
    )
    over_budget_count: int = Field(
        ..., description="Number of times budgets were exceeded", ge=0
    )

"""Pydantic models for Budget."""
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional
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


class ChatBudgetImportRequest(BaseModel):
    """Request model for chat-based budget import."""

    message: str = Field(..., min_length=1)
    conversation_history: Optional[list[Dict[str, str]]] = None


class ChatBudgetImportResponse(BaseModel):
    """Response model for chat-based budget import."""

    response: str
    budget_data: Optional[BudgetCreate] = None
    is_complete: bool = False

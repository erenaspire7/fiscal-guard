"""Pydantic models for Goal."""
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GoalBase(BaseModel):
    """Base goal model."""

    goal_name: str = Field(..., min_length=1, max_length=255)
    target_amount: Decimal = Field(..., ge=0)
    current_amount: Decimal = Field(default=Decimal("0"), ge=0)
    priority: Literal["high", "medium", "low"] = "medium"
    deadline: Optional[date] = None


class GoalCreate(GoalBase):
    """Goal creation model."""

    pass


class GoalUpdate(BaseModel):
    """Goal update model."""

    goal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    target_amount: Optional[Decimal] = Field(None, ge=0)
    current_amount: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[Literal["high", "medium", "low"]] = None
    deadline: Optional[date] = None
    is_completed: Optional[bool] = None


class GoalResponse(GoalBase):
    """Goal response model."""

    goal_id: UUID
    user_id: UUID
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    progress_percentage: float = Field(default=0.0)

    class Config:
        from_attributes = True

    @property
    def calculate_progress(self) -> float:
        """Calculate progress percentage."""
        if self.target_amount == 0:
            return 0.0
        return float((self.current_amount / self.target_amount) * 100)

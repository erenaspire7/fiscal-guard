"""Pydantic models for purchase decisions."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DecisionScore(str, Enum):
    """Decision score categories."""

    STRONG_NO = "strong_no"  # 1-3
    MILD_NO = "mild_no"  # 4-5
    NEUTRAL = "neutral"  # 6
    MILD_YES = "mild_yes"  # 7-8
    STRONG_YES = "strong_yes"  # 9-10


class PurchaseCategory(str, Enum):
    """Purchase categories."""

    ESSENTIAL = "essential"
    DISCRETIONARY = "discretionary"
    INVESTMENT = "investment"
    IMPULSE = "impulse"


class PurchaseDecisionRequest(BaseModel):
    """Request to make a purchase decision."""

    item_name: str = Field(..., description="Name of the item to purchase")
    amount: Decimal = Field(..., description="Purchase amount", gt=0)
    category: Optional[str] = Field(
        None, description="Budget category this falls under"
    )
    reason: Optional[str] = Field(None, description="Why the user wants to buy this")
    urgency: Optional[str] = Field(None, description="How urgent is this purchase")


class BudgetAnalysis(BaseModel):
    """Analysis of budget impact."""

    category: Optional[str] = Field(None, description="Budget category")
    current_spent: Decimal = Field(..., description="Current spending in category")
    limit: Decimal = Field(..., description="Category limit")
    remaining: Decimal = Field(..., description="Remaining budget")
    percentage_used: float = Field(..., description="Percentage of budget used")
    would_exceed: bool = Field(..., description="Would this purchase exceed the limit")
    impact_description: str = Field(
        ..., description="Human-readable impact description"
    )


class GoalAnalysis(BaseModel):
    """Analysis of goal impact."""

    goal_name: str = Field(..., description="Name of the goal")
    target_amount: Decimal = Field(..., description="Target amount for goal")
    current_amount: Decimal = Field(..., description="Current progress")
    remaining: Decimal = Field(..., description="Remaining to reach goal")
    deadline: Optional[datetime] = Field(None, description="Goal deadline")
    impact_description: str = Field(
        ..., description="Human-readable impact description"
    )


class DecisionAnalysis(BaseModel):
    """Complete analysis for a purchase decision."""

    budget_analysis: Optional[BudgetAnalysis] = None
    affected_goals: list[GoalAnalysis] = Field(default_factory=list)
    purchase_category: PurchaseCategory = Field(..., description="Category of purchase")
    financial_health_score: float = Field(
        ..., description="Overall financial health (0-100)", ge=0, le=100
    )


class PurchaseDecision(BaseModel):
    """Purchase decision response."""

    score: int = Field(..., description="Decision score from 1-10", ge=1, le=10)
    decision_category: DecisionScore = Field(..., description="Decision category")
    reasoning: str = Field(..., description="Detailed reasoning for the decision")
    analysis: DecisionAnalysis = Field(..., description="Detailed analysis")
    alternatives: Optional[list[str]] = Field(
        None, description="Alternative suggestions"
    )
    conditions: Optional[list[str]] = Field(
        None, description="Conditions under which this might be a better decision"
    )


class PurchaseDecisionResponse(BaseModel):
    """Response containing the decision."""

    decision: PurchaseDecision
    decision_id: UUID


class PurchaseDecisionCreate(BaseModel):
    """Create a decision record in the database."""

    user_id: UUID
    item_name: str
    amount: Decimal
    category: Optional[str]
    reason: Optional[str]
    urgency: Optional[str]
    score: int
    decision_category: DecisionScore
    reasoning: str
    analysis: dict  # JSON field
    alternatives: Optional[list[str]]
    conditions: Optional[list[str]]


class PurchaseDecisionDB(BaseModel):
    """Purchase decision from database."""

    id: UUID
    user_id: UUID
    item_name: str
    amount: Decimal
    category: Optional[str]
    reason: Optional[str]
    urgency: Optional[str]
    score: int
    decision_category: DecisionScore
    reasoning: str
    analysis: dict
    alternatives: Optional[list[str]]
    conditions: Optional[list[str]]
    created_at: datetime
    user_feedback: Optional[str] = None
    actual_purchase: Optional[bool] = None
    regret_level: Optional[int] = None

    model_config = {"from_attributes": True}


class DecisionFeedback(BaseModel):
    """User feedback on a decision."""

    actual_purchase: bool = Field(
        ..., description="Did the user actually make the purchase"
    )
    regret_level: Optional[int] = Field(
        None, description="Regret level 1-10 (only if purchased)", ge=1, le=10
    )
    feedback: Optional[str] = Field(None, description="Additional feedback from user")

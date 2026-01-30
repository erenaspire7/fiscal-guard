"""Pydantic models for cart analysis (browser extension)."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.models.decision import BudgetAnalysis, GoalAnalysis, PurchaseDecision


class CartItem(BaseModel):
    """Individual cart item extracted from screenshot."""

    model_config = ConfigDict(json_encoders={Decimal: float})

    item_name: str = Field(..., description="Product name/title")
    price: Decimal = Field(..., description="Unit price (not total)", gt=0)
    quantity: int = Field(..., description="Number of items", gt=0)
    urgency_badge: Optional[str] = Field(
        None, description="Urgency indicators like 'Limited time deal', 'Only 2 left'"
    )
    confidence: float = Field(
        ...,
        description="Extraction confidence score (0.0 to 1.0)",
        ge=0.0,
        le=1.0,
    )


class CartAnalysisRequest(BaseModel):
    """Request to analyze cart items."""

    items: list[CartItem] = Field(..., description="Extracted cart items")
    page_url: str = Field(..., description="URL of the shopping page")
    page_type: str = Field(
        ..., description="Type of page: 'cart', 'checkout', 'product'"
    )


class ItemDecisionResult(BaseModel):
    """Decision result for a single cart item."""

    model_config = ConfigDict(json_encoders={Decimal: float})

    item_name: str
    price: Decimal
    quantity: int
    total_amount: Decimal
    urgency_badge: Optional[str]
    decision: PurchaseDecision


class AggregateRecommendation(BaseModel):
    """Aggregate recommendation for entire cart."""

    model_config = ConfigDict(json_encoders={Decimal: float})

    total_amount: Decimal = Field(..., description="Total cart value")
    overall_score: int = Field(
        ..., description="Weighted average score (1-10)", ge=1, le=10
    )
    overall_recommendation: str = Field(..., description="Summary recommendation text")
    items_to_remove: list[str] = Field(
        default_factory=list, description="Items with low scores"
    )
    items_to_keep: list[str] = Field(
        default_factory=list, description="Items with high scores"
    )
    budget_impact: Optional[BudgetAnalysis] = Field(
        None, description="Overall budget impact"
    )
    goal_impact: list[GoalAnalysis] = Field(
        default_factory=list, description="Impact on goals"
    )


class CartAnalysisResponse(BaseModel):
    """Complete cart analysis response."""

    items: list[ItemDecisionResult] = Field(
        ..., description="Individual item decisions"
    )
    aggregate: AggregateRecommendation = Field(
        ..., description="Aggregate recommendation"
    )
    conversation_id: UUID = Field(..., description="Conversation ID for follow-up chat")
    requires_clarification: bool = Field(
        default=False, description="Whether clarification is needed"
    )

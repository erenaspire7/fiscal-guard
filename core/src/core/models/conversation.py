"""Pydantic models for conversation management."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """Single message in a conversation."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None  # Intent, decision_id, etc.


class ConversationIntent(BaseModel):
    """Classified user intent from conversational message."""

    intent: Literal[
        "purchase_decision",
        "purchase_feedback",
        "budget_query",
        "goal_update",
        "general_question",
        "small_talk",
        "log_expense",
        "budget_modification",
    ]
    confidence: float = Field(..., ge=0, le=1)
    extracted_entities: dict = Field(
        default_factory=dict,
        description="Extracted entities like item_name, amount, category, goal_name, etc.",
    )
    references_previous: bool = Field(
        default=False,
        description="Whether message references a previous conversation/decision",
    )
    suggested_clarification: Optional[str] = Field(
        None, description="Question to ask if intent is unclear"
    )


class ConversationResponse(BaseModel):
    """Response from conversation service."""

    message: str
    requires_clarification: bool = False
    context: Optional[dict] = None  # State to maintain across turns
    metadata: Optional[dict] = None  # IDs, updates, etc.


class ConversationRequest(BaseModel):
    """Request to process a conversational message."""

    message: str
    conversation_history: list[ConversationMessage] = Field(
        default_factory=list, description="Last N messages in the conversation"
    )

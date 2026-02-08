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

    primary_intent: Literal[
        "purchase_decision",
        "purchase_feedback",
        "budget_query",
        "goal_update",
        "general_question",
        "small_talk",
        "log_expense",
        "budget_modification",
    ] = Field(..., description="Primary intent detected in the user's message")
    additional_intents: list[str] = Field(
        default_factory=list,
        description="Additional intents detected in the same message (for multi-action requests)",
    )
    confidence: float = Field(
        ..., ge=0, le=1, description="Confidence score for the classification"
    )
    needs_clarification: bool = Field(
        default=False,
        description="Whether the message requires clarification before processing",
    )
    clarification_question: Optional[str] = Field(
        None, description="Question to ask if intent is unclear or confidence is low"
    )
    context_summary: str = Field(
        default="",
        description="Brief summary of what the user wants to accomplish (for handler guidance)",
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
    session_id: Optional[str] = Field(
        None,
        description="Optional session ID for prompt override testing (internal use only)",
    )

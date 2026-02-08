"""Conversation service V2 using Strands multi-agent swarm orchestration.

This uses a swarm-based architecture where agents hand off control to each other,
providing better error handling, simpler execution, and clearer debugging.
"""

import os
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.ai.agents.conversation_swarm import SwarmOrchestrator
from core.models.conversation import (
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
)
from core.services.context_builder import ContextBuilder


class ConversationService:
    """
    Swarm-based conversation service using Strands multi-agent orchestration.

    Advantages over graph-based approach:
    - Simpler execution: agents hand off directly (no graph building)
    - Better error propagation: handoffs are explicit
    - Natural multi-turn: agents maintain shared context
    - Easier debugging: clear handoff chain
    - Persistent state across turns (no context loss)
    """

    def __init__(self, db: Session):
        """Initialize conversation service.

        Args:
            db: Database session
        """
        self.db = db
        self.context_builder = ContextBuilder(db)

        # Swarm orchestrators are created per-user to maintain conversation state
        self._user_orchestrators = {}  # user_id -> SwarmOrchestrator

    def _get_or_create_orchestrator(self, user_id: UUID) -> SwarmOrchestrator:
        """Get existing swarm orchestrator for user or create a new one.

        Args:
            user_id: User ID

        Returns:
            Swarm orchestrator for this user
        """
        user_id_str = str(user_id)
        if user_id_str not in self._user_orchestrators:
            self._user_orchestrators[user_id_str] = SwarmOrchestrator(self.db, user_id)
        return self._user_orchestrators[user_id_str]

    def handle_message(
        self, user_id: UUID, request: ConversationRequest
    ) -> ConversationResponse:
        """Process a conversational message through the agent swarm.

        Args:
            user_id: User ID
            request: Conversation request with message and history

        Returns:
            Conversation response
        """
        # Build financial context once
        financial_context = self.context_builder.build_context(user_id)

        # Get or create swarm orchestrator for this user
        orchestrator = self._get_or_create_orchestrator(user_id)

        # Process message through swarm
        response_text = orchestrator.process_message(
            user_message=request.message,
            conversation_history=request.conversation_history,
            financial_context=financial_context,
        )

        return ConversationResponse(message=response_text)

    async def stream_handle_message(self, user_id: UUID, request: ConversationRequest):
        """Stream conversational message through the agent swarm.

        Args:
            user_id: User ID
            request: Conversation request with message and history

        Yields:
            Response chunks
        """
        # Build financial context once
        financial_context = self.context_builder.build_context(user_id)

        # Get or create swarm orchestrator for this user
        orchestrator = self._get_or_create_orchestrator(user_id)

        # Stream message through swarm
        async for chunk in orchestrator.stream_message(
            user_message=request.message,
            conversation_history=request.conversation_history,
            financial_context=financial_context,
        ):
            yield chunk

    def reset_conversation(self, user_id: UUID):
        """Reset conversation state for a user (start fresh).

        Args:
            user_id: User ID
        """
        user_id_str = str(user_id)
        if user_id_str in self._user_orchestrators:
            del self._user_orchestrators[user_id_str]

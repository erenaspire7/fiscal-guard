"""Main conversation service for routing messages to appropriate handlers."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.ai.agents.intent_classifier import IntentClassifier
from core.models.context import UserFinancialContext
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationRequest,
    ConversationResponse,
)
from core.models.decision import PurchaseDecisionRequest
from core.services.context_builder import ContextBuilder
from core.services.decision import DecisionService
from core.services.handlers.budget_modification_handler import BudgetModificationHandler
from core.services.handlers.budget_query_handler import BudgetQueryHandler
from core.services.handlers.expense_handler import ExpenseHandler
from core.services.handlers.feedback_handler import PurchaseFeedbackHandler
from core.services.handlers.general_assistant_handler import GeneralAssistantHandler
from core.services.handlers.goal_update_handler import GoalUpdateHandler
from core.services.handlers.small_talk_handler import SmallTalkHandler


class ConversationService:
    """Main service for routing conversational messages to appropriate handlers."""

    def __init__(self, db: Session):
        """Initialize conversation service.

        Args:
            db: Database session
        """
        self.db = db
        self.context_builder = ContextBuilder(db)
        self.intent_classifier = IntentClassifier(db)
        self.decision_service = DecisionService(db)
        self.feedback_handler = PurchaseFeedbackHandler(db)
        self.budget_handler = BudgetQueryHandler(db)
        self.goal_handler = GoalUpdateHandler(db)
        self.expense_handler = ExpenseHandler(db)
        self.budget_modifier = BudgetModificationHandler(db)
        self.assistant = GeneralAssistantHandler(db)
        self.small_talk_handler = SmallTalkHandler(db)

    def handle_message(
        self, user_id: UUID, request: ConversationRequest
    ) -> ConversationResponse:
        """Route message based on classified intent.

        Args:
            user_id: User ID
            request: Conversation request with message and history

        Returns:
            Conversation response
        """
        # Build financial context once for the entire request
        financial_context = self.context_builder.build_context(user_id)

        # Classify intent (pass session_id for prompt override)
        intent = self.intent_classifier.classify(
            request.message,
            request.conversation_history,
            user_id,
            request.session_id,
            financial_context,
        )

        # Check if we need clarification
        if intent.confidence < 0.7 and intent.suggested_clarification:
            return ConversationResponse(
                message=intent.suggested_clarification, requires_clarification=True
            )

        # Route to appropriate handler based on intent
        if intent.intent == "purchase_decision":
            return self._handle_purchase_decision(
                user_id, intent, request.message, request.session_id, financial_context
            )

        elif intent.intent == "purchase_feedback":
            return self._handle_purchase_feedback(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "budget_query":
            return self._handle_budget_query(user_id, intent, financial_context)

        elif intent.intent == "goal_update":
            return self._handle_goal_update(user_id, intent, financial_context)

        elif intent.intent == "log_expense":
            return self._handle_log_expense(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "budget_modification":
            return self._handle_budget_modification(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "small_talk":
            return self.small_talk_handler.handle(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "general_question":
            return self._handle_general_question(
                user_id, intent, request.conversation_history, financial_context
            )

        else:
            return ConversationResponse(
                message="I'm not sure what you're asking. Could you rephrase that?",
                requires_clarification=True,
            )

    async def stream_handle_message(self, user_id: UUID, request: ConversationRequest):
        """Route message based on classified intent and stream response.

        Args:
            user_id: User ID
            request: Conversation request with message and history

        Yields:
            Chunks of response
        """
        # Build financial context once for the entire request
        financial_context = self.context_builder.build_context(user_id)

        # Classify intent
        intent = self.intent_classifier.classify(
            request.message,
            request.conversation_history,
            user_id,
            financial_context=financial_context,
        )

        # Check if we need clarification
        if intent.confidence < 0.7 and intent.suggested_clarification:
            yield {
                "data": intent.suggested_clarification,
                "requires_clarification": True,
            }
            return

        # Route to appropriate handler based on intent
        if intent.intent == "general_question":
            async for chunk in self.assistant.stream_handle(
                user_id, intent, request.conversation_history, financial_context
            ):
                yield chunk
            return

        if intent.intent == "small_talk":
            async for chunk in self.small_talk_handler.stream_handle(
                user_id, intent, request.conversation_history, financial_context
            ):
                yield chunk
            return

        # For other intents, use standard handling
        response = None
        if intent.intent == "purchase_decision":
            response = self._handle_purchase_decision(
                user_id, intent, request.message, financial_context=financial_context
            )

        elif intent.intent == "purchase_feedback":
            response = self._handle_purchase_feedback(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "budget_query":
            response = self._handle_budget_query(user_id, intent, financial_context)

        elif intent.intent == "goal_update":
            response = self._handle_goal_update(user_id, intent, financial_context)

        elif intent.intent == "log_expense":
            response = self._handle_log_expense(
                user_id, intent, request.conversation_history, financial_context
            )

        elif intent.intent == "budget_modification":
            response = self._handle_budget_modification(
                user_id, intent, request.conversation_history, financial_context
            )

        else:
            yield {
                "data": "I'm not sure what you're asking. Could you rephrase that?",
                "requires_clarification": True,
            }
            return

        if response:
            yield {
                "data": response.message,
                "metadata": response.metadata,
                "requires_clarification": response.requires_clarification,
            }

    def _handle_purchase_decision(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        original_message: str,
        session_id: Optional[str] = None,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle purchase decision request.

        Args:
            user_id: User ID
            intent: Classified intent
            original_message: Original user message
            session_id: Optional session ID for prompt override testing
            financial_context: Pre-fetched financial context

        Returns:
            Conversation response
        """
        # Build purchase decision request from extracted entities
        entities = intent.extracted_entities

        decision_request = PurchaseDecisionRequest(
            item_name=entities.get("item_name"),
            amount=entities.get("amount"),
            category=entities.get("category"),
            urgency=entities.get("urgency"),
            reason=entities.get("reason"),
            user_message=original_message,
        )

        # Use existing decision service (pass session_id and financial_context)
        decision_response = self.decision_service.create_decision(
            user_id, decision_request, session_id, financial_context
        )

        # Convert to conversation response
        decision = decision_response.decision

        # Build user-friendly message
        message_parts = [
            f"**Decision Score: {decision.score}/10** ({decision.decision_category.value.replace('_', ' ').title()})",
            "",
            f"**Reasoning:**",
            decision.reasoning,
        ]

        # Add budget analysis if available
        if decision.analysis.budget_analysis:
            budget = decision.analysis.budget_analysis
            message_parts.append("")
            message_parts.append(f"**Budget Impact ({budget.category.value}):**")
            message_parts.append(budget.impact_description)

        # Add alternatives if available
        if decision.alternatives:
            message_parts.append("")
            message_parts.append("**Alternatives:**")
            for alt in decision.alternatives:
                message_parts.append(f"- {alt}")

        # Add conditions if available
        if decision.conditions:
            message_parts.append("")
            message_parts.append("**This might make more sense if:**")
            for cond in decision.conditions:
                message_parts.append(f"- {cond}")

        return ConversationResponse(
            message="\n".join(message_parts),
            metadata={
                "decision_id": str(decision_response.decision_id),
                "score": decision.score,
                "category": decision.decision_category.value,
            },
            requires_clarification=decision_response.requires_clarification,
        )

    def _handle_purchase_feedback(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle purchase feedback.

        Args:
            user_id: User ID
            intent: Classified intent
            conversation_history: Recent messages
            financial_context: Pre-fetched financial context

        Returns:
            Conversation response
        """
        response = self.feedback_handler.handle(
            user_id, intent, conversation_history, financial_context
        )

        # Merge context into metadata so it's passed back to the frontend
        if response.context:
            if response.metadata is None:
                response.metadata = {}
            response.metadata["context"] = response.context

        return response

    def _handle_budget_query(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle budget query."""
        return self.budget_handler.handle(user_id, intent, financial_context)

    def _handle_goal_update(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle goal update."""
        return self.goal_handler.handle(user_id, intent, financial_context)

    def _handle_log_expense(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle expense logging."""
        return self.expense_handler.handle(
            user_id, intent, conversation_history, financial_context
        )

    def _handle_budget_modification(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle budget modification."""
        return self.budget_modifier.handle(
            user_id, intent, conversation_history, financial_context
        )

    def _handle_general_question(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Handle general financial question."""
        return self.assistant.handle(
            user_id, intent, conversation_history, financial_context
        )

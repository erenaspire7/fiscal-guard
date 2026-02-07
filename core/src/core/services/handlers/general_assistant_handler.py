"""Handler for general financial questions and advice."""

from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.models.context import UserFinancialContext
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)
from core.observability.pii_redaction import create_trace_attributes


class GeneralAssistantHandler:
    """Handle general financial questions and provide personalized advice."""

    def __init__(self, db: Session):
        """Initialize general assistant handler.

        Args:
            db: Database session
        """
        self.db = db

        # Initialize Gemini model
        self.model = GeminiModel(
            client_args={
                "api_key": settings.google_api_key,
            },
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        self.system_prompt = """You are a helpful, empathetic financial advisor inside a personal finance app.

Your priority is to answer the user's ACTUAL QUESTION.

Rules:
- Always directly answer the user's question first.
- Use the user's financial context only if it helps answer the question.
- Do NOT default to a generic "you're doing great / budget status" summary unless the user asked for a status check.
- Be concise (1-2 short paragraphs, or a tight bullet list).
- Give actionable next steps.
- Use a warm, conversational tone.

If the user asks about:
- earning more money / increasing income: give practical ideas (negotiation, job search strategy, upskilling, side income), and ask 1 clarifying question if needed.
- budgeting / "how am I doing": then summarize their context and give 2-3 concrete actions.
- goals: talk about goal progress and next steps."""

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Process general financial question and provide advice.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent conversation messages
            financial_context: Pre-fetched financial context

        Returns:
            Conversation response with personalized advice
        """
        # Format pre-fetched context for the prompt
        context = self._format_context_for_prompt(
            financial_context, conversation_history
        )

        # Create trace attributes with PII redaction
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),
            session_id=str(uuid4()),
            action="general_advice",
        )

        # Create agent for advice generation
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            trace_attributes=trace_attributes,
        )

        # Get the user's question from the most recent message
        user_question = (
            conversation_history[-1].content
            if conversation_history
            else intent.extracted_entities.get("topic", "").strip()
        )

        # Build prompt
        prompt = f"""USER QUESTION:
{user_question}

USER FINANCIAL CONTEXT (use only if relevant):
{context}

INSTRUCTIONS:
1) Answer the user's question directly.
2) Only reference budget/goals/decision stats if they are clearly relevant to the question.
3) Provide 3-6 actionable suggestions.
4) Ask at most ONE clarifying question if it would materially improve the advice.

Now respond."""
        # Get response
        response = agent(prompt)

        # Extract message
        if hasattr(response, "output"):
            message = response.output
        else:
            message = str(response)

        return ConversationResponse(message=message)

    async def stream_handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ):
        """Process general financial question and provide advice as a stream.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent conversation messages
            financial_context: Pre-fetched financial context

        Yields:
            Chunks of the response
        """
        # Format pre-fetched context for the prompt
        context = self._format_context_for_prompt(
            financial_context, conversation_history
        )

        # Create trace attributes with PII redaction
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),
            session_id=str(uuid4()),
            action="general_advice_stream",
        )

        # Create agent for advice generation
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            trace_attributes=trace_attributes,
        )

        # Get the user's question from the most recent message
        user_question = (
            conversation_history[-1].content
            if conversation_history
            else intent.extracted_entities.get("topic", "").strip()
        )

        # Build prompt
        prompt = f"""USER QUESTION:
{user_question}

USER FINANCIAL CONTEXT (use only if relevant):
{context}

INSTRUCTIONS:
1) Answer the user's question directly.
2) Only reference budget/goals/decision stats if they are clearly relevant to the question.
3) Provide 3-6 actionable suggestions.
4) Ask at most ONE clarifying question if it would materially improve the advice.

Now respond."""

        # Stream response
        async for event in agent.stream_async(prompt):
            # Only yield text data chunks to ensure JSON serializability
            # and proper streaming behavior. We filter out lifecycle events
            # that might contain non-serializable objects (like Agent instances).
            if isinstance(event, dict) and "data" in event:
                yield {"data": event["data"]}

    def _format_context_for_prompt(
        self,
        financial_context: Optional[UserFinancialContext],
        conversation_history: List[ConversationMessage],
    ) -> str:
        """Format pre-fetched financial context into a string for the LLM prompt.

        Args:
            financial_context: Pre-fetched financial context
            conversation_history: Recent messages

        Returns:
            Context string
        """
        context_parts = []

        if financial_context:
            # Budget status
            budget = financial_context.active_budget
            if budget:
                context_parts.append("BUDGET STATUS:")
                context_parts.append(
                    f"- Total Spent: ${budget.total_spent:.2f} / ${budget.total_limit:.2f} ({budget.percentage_used:.0f}%)"
                )
                context_parts.append("- Category Breakdown:")
                for name, cat in budget.categories.items():
                    status = "OVER" if cat.spent > cat.limit else "OK"
                    context_parts.append(
                        f"  * {name}: ${cat.spent:.2f} / ${cat.limit:.2f} ({cat.percentage_used:.0f}%) - {status}"
                    )
            else:
                context_parts.append("BUDGET STATUS: No active budget")

            # Goals
            if financial_context.active_goals:
                context_parts.append("\nGOALS:")
                for goal in financial_context.active_goals:
                    context_parts.append(
                        f"- {goal.goal_name}: ${goal.current_amount:.2f} / ${goal.target_amount:.2f} ({goal.percentage_complete:.0f}% complete, ${goal.remaining_amount:.2f} remaining)"
                    )
            else:
                context_parts.append("\nGOALS: No active goals")

            # Decision stats
            decisions = financial_context.recent_decisions
            if decisions:
                avg_score = sum(d.score for d in decisions) / len(decisions)
                total_requested = sum(float(d.amount) for d in decisions)

                decisions_by_category = {}
                for d in decisions:
                    cat = d.decision_category
                    decisions_by_category[cat] = decisions_by_category.get(cat, 0) + 1

                decisions_with_feedback = [
                    d for d in decisions if d.actual_purchase is not None
                ]
                purchased_count = sum(
                    1 for d in decisions_with_feedback if d.actual_purchase
                )
                avg_regret = None
                if decisions_with_feedback:
                    regrets = [
                        d.regret_level
                        for d in decisions_with_feedback
                        if d.regret_level is not None
                    ]
                    if regrets:
                        avg_regret = sum(regrets) / len(regrets)

                context_parts.append("\nPURCHASE DECISIONS (Last 30 days):")
                context_parts.append(f"- Total Decisions: {len(decisions)}")
                context_parts.append(f"- Average Score: {avg_score:.1f}/10")
                context_parts.append(
                    f"- Total Amount Considered: ${total_requested:.2f}"
                )
                context_parts.append(
                    f"- Decisions by Category: {dict(decisions_by_category)}"
                )
                if decisions_with_feedback:
                    context_parts.append(
                        f"- Actually Purchased: {purchased_count}/{len(decisions_with_feedback)}"
                    )
                if avg_regret is not None:
                    context_parts.append(f"- Average Regret Level: {avg_regret:.1f}/10")
            else:
                context_parts.append("\nPURCHASE DECISIONS: No recent decisions")
        else:
            context_parts.append("BUDGET STATUS: Unknown")
            context_parts.append("\nGOALS: Unknown")
            context_parts.append("\nPURCHASE DECISIONS: Unknown")

        # Conversation context
        if conversation_history:
            context_parts.append("\nRECENT CONVERSATION:")
            for msg in conversation_history[-3:]:
                context_parts.append(f"  {msg.role}: {msg.content[:100]}...")

        return "\n".join(context_parts)

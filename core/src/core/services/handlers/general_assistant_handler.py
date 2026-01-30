"""Handler for general financial questions and advice."""

from datetime import datetime, timedelta
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.database.models import Budget, Goal, PurchaseDecision
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
    ) -> ConversationResponse:
        """Process general financial question and provide advice.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent conversation messages

        Returns:
            Conversation response with personalized advice
        """
        # Build comprehensive context
        context = self._build_comprehensive_context(user_id, conversation_history)

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
    ):
        """Process general financial question and provide advice as a stream.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent conversation messages

        Yields:
            Chunks of the response
        """
        # Build comprehensive context
        context = self._build_comprehensive_context(user_id, conversation_history)

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

    def _build_comprehensive_context(
        self, user_id: UUID, conversation_history: List[ConversationMessage]
    ) -> str:
        """Build comprehensive context about user's financial situation.

        Args:
            user_id: User ID
            conversation_history: Recent messages

        Returns:
            Context string
        """
        context_parts = []

        # Budget analysis
        active_budget = (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_end >= datetime.utcnow(),
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

        if active_budget:
            total_spent = sum(
                cat.get("spent", 0) for cat in active_budget.categories.values()
            )
            total_limit = sum(
                cat.get("limit", 0) for cat in active_budget.categories.values()
            )
            budget_percentage = (
                (total_spent / total_limit * 100) if total_limit > 0 else 0
            )

            context_parts.append(f"BUDGET STATUS:")
            context_parts.append(
                f"- Total Spent: ${total_spent:.2f} / ${total_limit:.2f} ({budget_percentage:.0f}%)"
            )
            context_parts.append("- Category Breakdown:")

            for category, details in active_budget.categories.items():
                spent = details.get("spent", 0)
                limit = details.get("limit", 0)
                cat_percentage = (spent / limit * 100) if limit > 0 else 0
                status = "OVER" if spent > limit else "OK"
                context_parts.append(
                    f"  * {category}: ${spent:.2f} / ${limit:.2f} ({cat_percentage:.0f}%) - {status}"
                )
        else:
            context_parts.append("BUDGET STATUS: No active budget")

        # Goals analysis
        active_goals = (
            self.db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.is_completed == False)
            .order_by(Goal.created_at.desc())
            .all()
        )

        if active_goals:
            context_parts.append("\nGOALS:")
            for goal in active_goals:
                progress_percentage = (
                    (goal.current_amount / goal.target_amount * 100)
                    if goal.target_amount > 0
                    else 0
                )
                remaining = goal.target_amount - goal.current_amount
                context_parts.append(
                    f"- {goal.goal_name}: ${goal.current_amount:.2f} / ${goal.target_amount:.2f} ({progress_percentage:.0f}% complete, ${remaining:.2f} remaining)"
                )
        else:
            context_parts.append("\nGOALS: No active goals")

        # Purchase decision analysis (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_decisions = (
            self.db.query(PurchaseDecision)
            .filter(
                PurchaseDecision.user_id == user_id,
                PurchaseDecision.created_at > thirty_days_ago,
            )
            .order_by(PurchaseDecision.created_at.desc())
            .all()
        )

        if recent_decisions:
            avg_score = sum(d.score for d in recent_decisions) / len(recent_decisions)
            total_requested = sum(float(d.amount) for d in recent_decisions)

            # Count by decision category
            decisions_by_category = {}
            for d in recent_decisions:
                cat = d.decision_category
                decisions_by_category[cat] = decisions_by_category.get(cat, 0) + 1

            # Regret analysis
            decisions_with_feedback = [
                d for d in recent_decisions if d.actual_purchase is not None
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
            context_parts.append(f"- Total Decisions: {len(recent_decisions)}")
            context_parts.append(f"- Average Score: {avg_score:.1f}/10")
            context_parts.append(f"- Total Amount Considered: ${total_requested:.2f}")
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

        # Conversation context
        if conversation_history:
            context_parts.append("\nRECENT CONVERSATION:")
            for msg in conversation_history[-3:]:
                context_parts.append(f"  {msg.role}: {msg.content[:100]}...")

        return "\n".join(context_parts)

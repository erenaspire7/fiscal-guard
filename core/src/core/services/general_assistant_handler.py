"""Handler for general financial questions and advice."""

import json
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

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

        self.system_prompt = """You are a helpful, empathetic financial advisor having a conversation with a user.

Your role:
- Provide personalized financial advice based on the user's context
- Be encouraging and supportive
- Reference specific data from their budget, goals, and purchase history
- Give actionable recommendations
- Be extremely concise (aim for 1-2 paragraphs maximum)
- Use a warm, conversational tone
- Celebrate wins and provide constructive guidance for challenges

When analyzing their financial health, consider:
- Budget adherence (are they staying within limits?)
- Goal progress (are they making steady progress?)
- Purchase decision patterns (quality of decisions, regret patterns)
- Overall trajectory (improving or declining?)

Provide specific, actionable advice tailored to their situation."""

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

        # Create agent for advice generation
        agent = Agent(model=self.model, system_prompt=self.system_prompt)

        # Get the user's question from the most recent message
        user_question = (
            conversation_history[-1].content
            if conversation_history
            else intent.extracted_entities.get("topic", "How am I doing financially?")
        )

        # Build prompt
        prompt = f"""User Question: {user_question}

USER FINANCIAL CONTEXT:
{context}

Provide personalized, actionable financial advice based on their specific situation. Reference concrete data from their budget, goals, and decision history."""

        # Get response
        response = agent(prompt)

        # Extract message
        if hasattr(response, "output"):
            message = response.output
        else:
            message = str(response)

        return ConversationResponse(message=message)

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

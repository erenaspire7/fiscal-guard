"""Handler for budget query conversations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.models.context import ActiveBudgetContext, UserFinancialContext
from core.models.conversation import ConversationIntent, ConversationResponse


class BudgetQueryHandler:
    """Handle budget queries and provide spending information."""

    def __init__(self, db: Session):
        """Initialize budget query handler.

        Args:
            db: Database session
        """
        self.db = db

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Process budget query and provide information.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            financial_context: Pre-fetched financial context

        Returns:
            Conversation response with budget information
        """
        budget = financial_context.active_budget if financial_context else None

        if not budget:
            return ConversationResponse(
                message="You don't have an active budget set up yet. Would you like to create one?",
                requires_clarification=True,
            )

        # Extract requested category
        category = intent.extracted_entities.get("category")

        # If specific category requested
        if category and category in budget.categories:
            return self._handle_category_query(budget, category)

        # Otherwise provide overall budget summary
        return self._handle_overall_query(budget)

    def _handle_category_query(
        self, budget: ActiveBudgetContext, category: str
    ) -> ConversationResponse:
        """Handle query for a specific budget category.

        Args:
            budget: Active budget context
            category: Category name

        Returns:
            Response with category details
        """
        cat = budget.categories[category]
        days_remaining = (budget.period_end - datetime.utcnow().date()).days

        message_parts = [
            f"**{category.capitalize()} Budget:**",
            f"- Spent: ${cat.spent:.2f}",
            f"- Limit: ${cat.limit:.2f}",
            f"- Remaining: ${cat.remaining:.2f}",
            f"- Usage: {cat.percentage_used:.0f}%",
        ]

        if cat.remaining < 0:
            message_parts.append(
                f"\n You're ${abs(cat.remaining):.2f} over budget in this category!"
            )
        elif cat.percentage_used >= 90:
            message_parts.append(
                f"\n You're at {cat.percentage_used:.0f}% of your budget with {days_remaining} days left in the period. Be careful with spending!"
            )
        elif cat.percentage_used <= 50 and days_remaining > 0:
            total_days = (budget.period_end - budget.period_start).days
            elapsed_days = total_days - days_remaining
            daily_rate = cat.spent / max(1, elapsed_days)
            projected = cat.spent + (daily_rate * days_remaining)
            if projected <= cat.limit:
                message_parts.append(
                    f"\n You're doing great! At {cat.percentage_used:.0f}% usage with {days_remaining} days left, you're on track to stay under budget."
                )
            else:
                message_parts.append(
                    f"\n You're at {cat.percentage_used:.0f}% with {days_remaining} days left. Watch your spending to stay under budget."
                )

        return ConversationResponse(message="\n".join(message_parts))

    def _handle_overall_query(
        self, budget: ActiveBudgetContext
    ) -> ConversationResponse:
        """Handle query for overall budget status.

        Args:
            budget: Active budget context

        Returns:
            Response with overall budget summary
        """
        days_remaining = (budget.period_end - datetime.utcnow().date()).days

        message_parts = [
            f"**Budget Overview ({budget.name}):**",
            f"- Total Spent: ${budget.total_spent:.2f}",
            f"- Total Budget: ${budget.total_limit:.2f}",
            f"- Remaining: ${budget.total_remaining:.2f}",
            f"- Usage: {budget.percentage_used:.0f}%",
            f"- Days Remaining: {days_remaining}",
            "",
            "**By Category:**",
        ]

        for name, cat in budget.categories.items():
            if cat.remaining < 0:
                emoji = "🔴"
            elif cat.percentage_used >= 90:
                emoji = "🟡"
            else:
                emoji = "🟢"

            message_parts.append(
                f"{emoji} **{name.capitalize()}**: ${cat.spent:.2f} / ${cat.limit:.2f} ({cat.percentage_used:.0f}%)"
            )

        message_parts.append("")
        if budget.total_remaining < 0:
            message_parts.append(
                f"**Warning:** You're ${abs(budget.total_remaining):.2f} over your total budget!"
            )
        elif budget.percentage_used >= 90:
            message_parts.append(
                f"**Caution:** You've used {budget.percentage_used:.0f}% of your budget with {days_remaining} days remaining. Be mindful of spending!"
            )
        elif budget.percentage_used <= 50 and days_remaining > 0:
            message_parts.append(
                f"**Great job!** You're at {budget.percentage_used:.0f}% usage with {days_remaining} days left. Keep it up!"
            )
        else:
            message_parts.append(
                f"You're at {budget.percentage_used:.0f}% of your budget. Stay on track!"
            )

        return ConversationResponse(message="\n".join(message_parts))

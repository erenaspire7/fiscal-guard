"""Handler for budget query conversations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Budget
from core.models.conversation import ConversationIntent, ConversationResponse


class BudgetQueryHandler:
    """Handle budget queries and provide spending information."""

    def __init__(self, db: Session):
        """Initialize budget query handler.

        Args:
            db: Database session
        """
        self.db = db

    def handle(self, user_id: UUID, intent: ConversationIntent) -> ConversationResponse:
        """Process budget query and provide information.

        Args:
            user_id: User ID
            intent: Classified intent with entities

        Returns:
            Conversation response with budget information
        """
        # Get active budget
        active_budget = self._get_active_budget(user_id)

        if not active_budget:
            return ConversationResponse(
                message="You don't have an active budget set up yet. Would you like to create one?",
                requires_clarification=True,
            )

        # Extract requested category
        category = intent.extracted_entities.get("category")

        # If specific category requested
        if category and category in active_budget.categories:
            return self._handle_category_query(active_budget, category)

        # Otherwise provide overall budget summary
        return self._handle_overall_query(active_budget)

    def _get_active_budget(self, user_id: UUID) -> Optional[Budget]:
        """Get user's active budget.

        Args:
            user_id: User ID

        Returns:
            Active budget if found
        """
        return (
            self.db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_end >= datetime.utcnow(),
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

    def _handle_category_query(
        self, budget: Budget, category: str
    ) -> ConversationResponse:
        """Handle query for a specific budget category.

        Args:
            budget: Active budget
            category: Category name

        Returns:
            Response with category details
        """
        details = budget.categories[category]
        spent = details.get("spent", 0)
        limit = details.get("limit", 0)
        remaining = limit - spent
        percentage = (spent / limit * 100) if limit > 0 else 0

        # Calculate days remaining in period
        days_remaining = (budget.period_end - datetime.utcnow().date()).days

        # Build response message
        message_parts = [
            f"💰 **{category.capitalize()} Budget:**",
            f"- Spent: ${spent:.2f}",
            f"- Limit: ${limit:.2f}",
            f"- Remaining: ${remaining:.2f}",
            f"- Usage: {percentage:.0f}%",
        ]

        # Add contextual advice
        if remaining < 0:
            message_parts.append(
                f"\n⚠️ You're ${abs(remaining):.2f} over budget in this category!"
            )
        elif percentage >= 90:
            message_parts.append(
                f"\n⚠️ You're at {percentage:.0f}% of your budget with {days_remaining} days left in the period. Be careful with spending!"
            )
        elif percentage <= 50:
            daily_rate = spent / max(
                1, (budget.period_end - budget.period_start).days - days_remaining
            )
            projected = spent + (daily_rate * days_remaining)
            if projected <= limit:
                message_parts.append(
                    f"\n✅ You're doing great! At {percentage:.0f}% usage with {days_remaining} days left, you're on track to stay under budget."
                )
            else:
                message_parts.append(
                    f"\n📊 You're at {percentage:.0f}% with {days_remaining} days left. Watch your spending to stay under budget."
                )

        return ConversationResponse(message="\n".join(message_parts))

    def _handle_overall_query(self, budget: Budget) -> ConversationResponse:
        """Handle query for overall budget status.

        Args:
            budget: Active budget

        Returns:
            Response with overall budget summary
        """
        # Calculate totals
        total_spent = sum(cat.get("spent", 0) for cat in budget.categories.values())
        total_limit = sum(cat.get("limit", 0) for cat in budget.categories.values())
        total_remaining = total_limit - total_spent
        total_percentage = (total_spent / total_limit * 100) if total_limit > 0 else 0

        # Calculate days remaining
        days_remaining = (budget.period_end - datetime.utcnow().date()).days

        message_parts = [
            f"💰 **Budget Overview ({budget.name}):**",
            f"- Total Spent: ${total_spent:.2f}",
            f"- Total Budget: ${total_limit:.2f}",
            f"- Remaining: ${total_remaining:.2f}",
            f"- Usage: {total_percentage:.0f}%",
            f"- Days Remaining: {days_remaining}",
            "",
            "**By Category:**",
        ]

        # Add category breakdown
        for category, details in budget.categories.items():
            spent = details.get("spent", 0)
            limit = details.get("limit", 0)
            remaining = limit - spent
            percentage = (spent / limit * 100) if limit > 0 else 0

            # Emoji based on status
            if remaining < 0:
                emoji = "🔴"
            elif percentage >= 90:
                emoji = "🟡"
            else:
                emoji = "🟢"

            message_parts.append(
                f"{emoji} **{category.capitalize()}**: ${spent:.2f} / ${limit:.2f} ({percentage:.0f}%)"
            )

        # Add overall assessment
        message_parts.append("")
        if total_remaining < 0:
            message_parts.append(
                f"⚠️ **Warning:** You're ${abs(total_remaining):.2f} over your total budget!"
            )
        elif total_percentage >= 90:
            message_parts.append(
                f"⚠️ **Caution:** You've used {total_percentage:.0f}% of your budget with {days_remaining} days remaining. Be mindful of spending!"
            )
        elif total_percentage <= 50 and days_remaining > 0:
            message_parts.append(
                f"✅ **Great job!** You're at {total_percentage:.0f}% usage with {days_remaining} days left. Keep it up!"
            )
        else:
            message_parts.append(
                f"📊 You're at {total_percentage:.0f}% of your budget. Stay on track!"
            )

        return ConversationResponse(message="\n".join(message_parts))

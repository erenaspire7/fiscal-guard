"""Handler for budget modification conversations."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Budget
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)
from core.services.budget import BudgetService


class BudgetModificationHandler:
    """Handle requests to modify budget limits."""

    def __init__(self, db: Session):
        """Initialize budget modification handler.

        Args:
            db: Database session
        """
        self.db = db
        self.budget_service = BudgetService(db)

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
    ) -> ConversationResponse:
        """Process budget modification request.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent messages

        Returns:
            Conversation response
        """
        # Get active budget
        active_budget = self._get_active_budget(user_id)

        if not active_budget:
            return ConversationResponse(
                message="You don't have an active budget set up yet. Would you like to create one?",
                requires_clarification=True,
            )

        entities = intent.extracted_entities
        category = entities.get("category")
        amount_val = entities.get("amount")
        operation = entities.get("operation", "set")  # set, increase, decrease

        # Validate category
        if not category:
            return ConversationResponse(
                message="Which category would you like to update?",
                requires_clarification=True,
            )

        category = category.lower()
        if category not in active_budget.categories:
            valid_cats = ", ".join(active_budget.categories.keys())
            return ConversationResponse(
                message=f"I don't see a '{category}' category. Your active categories are: {valid_cats}.",
                requires_clarification=True,
            )

        # Validate amount
        if not amount_val:
            return ConversationResponse(
                message="How much should I change the budget by?",
                requires_clarification=True,
            )

        try:
            if isinstance(amount_val, str):
                amount_clean = amount_val.replace("$", "").replace(",", "")
                amount = Decimal(amount_clean)
            else:
                amount = Decimal(str(amount_val))
        except (ValueError, TypeError):
            return ConversationResponse(
                message="I didn't understand that amount. Could you repeat it?",
                requires_clarification=True,
            )

        # Calculate new limit
        current_limit = Decimal(str(active_budget.categories[category]["limit"]))
        new_limit = current_limit

        if operation == "increase":
            new_limit += amount
        elif operation == "decrease":
            new_limit -= amount
            if new_limit < 0:
                new_limit = Decimal("0")
        else:  # "set" or default
            new_limit = amount

        # Update budget
        try:
            updated_budget = self.budget_service.update_category_limit(
                budget_id=active_budget.budget_id,
                user_id=user_id,
                category=category,
                new_limit=float(new_limit),
            )

            if not updated_budget:
                return ConversationResponse(
                    message="Sorry, I encountered an error updating the budget."
                )

            # Build response
            msg = f"✅ Updated **{category}** budget."
            msg += f"\nNew Limit: ${new_limit:.2f} (was ${current_limit:.2f})"

            # Add status info
            spent = Decimal(str(updated_budget.categories[category]["spent"]))
            remaining = new_limit - spent

            msg += f"\nStatus: ${spent:.2f} spent, ${remaining:.2f} remaining."

            return ConversationResponse(message=msg)

        except Exception:
            return ConversationResponse(
                message="Something went wrong while updating the budget."
            )

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

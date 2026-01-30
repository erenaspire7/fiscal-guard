"""Handler for expense logging conversations."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Budget
from core.models.budget import BudgetItemCreate
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)
from core.services.budget import BudgetService


class ExpenseHandler:
    """Handle requests to log expenses."""

    def __init__(self, db: Session):
        """Initialize expense handler.

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
        """Process expense logging request.

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

        # Validate amount
        amount_val = entities.get("amount")
        if not amount_val:
            return ConversationResponse(
                message="I couldn't identify the amount. How much did you spend?",
                requires_clarification=True,
            )

        try:
            # Handle string amounts like "$100" or "100.50"
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

        # Validate category
        category = entities.get("category")

        # If category is missing, check if it was mentioned in the message or use a default
        if not category:
            # Simple fallback for now: check if "general" exists
            if "general" in active_budget.categories:
                category = "general"
            else:
                return ConversationResponse(
                    message="Which category should this go under?",
                    requires_clarification=True,
                )

        # Normalize category
        category = category.lower()

        # Check if category exists in budget
        if category not in active_budget.categories:
            valid_cats = ", ".join(active_budget.categories.keys())
            return ConversationResponse(
                message=f"I don't see a '{category}' category. Your active categories are: {valid_cats}.",
                requires_clarification=True,
            )

        # Item name
        item_name = entities.get("item_name") or "Expense"

        try:
            # Create the budget item
            item_data = BudgetItemCreate(
                item_name=item_name,
                amount=amount,
                category=category,
                transaction_date=datetime.utcnow(),
                is_planned=False,
            )

            result = self.budget_service.add_budget_item(
                budget_id=active_budget.budget_id,
                user_id=user_id,
                item_data=item_data,
            )

            if not result:
                return ConversationResponse(
                    message="Sorry, I encountered an error logging that expense."
                )

            # Parse result for feedback
            spent_after = result.category_spent_after
            limit = result.category_limit
            remaining = limit - spent_after

            msg = f"✅ Logged ${amount:.2f} for '{item_name}' in **{category}**."
            msg += f"\nCategory status: ${spent_after:.2f} / ${limit:.2f} (${remaining:.2f} remaining)."

            if result.exceeded_budget:
                msg += f"\n⚠️ **Warning:** You are now over budget in this category!"
            elif remaining < (limit * Decimal("0.1")):
                msg += (
                    f"\n⚠️ Careful, you have less than 10% remaining in this category."
                )

            return ConversationResponse(message=msg)

        except Exception as e:
            return ConversationResponse(
                message="Something went wrong while logging the expense."
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

"""Handler for expense logging conversations."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from core.models.budget import BudgetItemCreate
from core.models.context import ActiveBudgetContext, UserFinancialContext
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)
from core.services.budget import BudgetService


class ExpenseHandler:
    """Handle requests to log expenses."""

    def __init__(self, db: Session):
        self.db = db
        self.budget_service = BudgetService(db)

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Process expense logging request (single or multiple items)."""
        budget_ctx = financial_context.active_budget if financial_context else None

        if not budget_ctx:
            return ConversationResponse(
                message="You don't have an active budget set up yet. Would you like to create one?",
                requires_clarification=True,
            )

        items = self._normalize_items(intent.extracted_entities)

        if not items:
            return ConversationResponse(
                message="I couldn't identify the amount. How much did you spend?",
                requires_clarification=True,
            )

        # Check if ALL items are missing amounts — give a single friendly prompt
        all_missing_amounts = all(not item.get("amount") for item in items)
        if all_missing_amounts:
            item_names = [item.get("item_name") or "item" for item in items]
            names_str = ", ".join(item_names)
            return ConversationResponse(
                message=f"How much did you spend on each? ({names_str})",
                requires_clarification=True,
            )

        successes: List[str] = []
        errors: List[str] = []

        for item in items:
            success_msg, error_msg = self._log_single_item(user_id, budget_ctx, item)
            if success_msg:
                successes.append(success_msg)
            if error_msg:
                errors.append(error_msg)

        # Deduplicate errors (e.g. same missing category repeated for each item)
        unique_errors = list(dict.fromkeys(errors))

        # Build combined response
        if not successes and unique_errors:
            return ConversationResponse(
                message="\n".join(unique_errors),
                requires_clarification=True,
            )

        parts = []
        if len(successes) == 1:
            parts.append(successes[0])
        else:
            parts.append(f"Logged {len(successes)} expenses:")
            for msg in successes:
                parts.append(f"- {msg}")

        if unique_errors:
            parts.append("")
            for msg in unique_errors:
                parts.append(msg)

        return ConversationResponse(message="\n".join(parts))

    def _normalize_items(self, entities: dict) -> List[dict]:
        """Normalize entities into a list of {amount, category, item_name} dicts.

        Supports both multi-item format (items array) and single-item format.
        Returns items even if amounts are missing (caller handles that case).
        """
        # Multi-item path
        items = entities.get("items")
        if isinstance(items, list) and len(items) > 0:
            return items

        # Single-item path — wrap in list if any entity is present
        if entities.get("amount") is not None or entities.get("item_name"):
            return [
                {
                    "amount": entities.get("amount"),
                    "category": entities.get("category"),
                    "item_name": entities.get("item_name"),
                }
            ]

        return []

    def _log_single_item(
        self,
        user_id: UUID,
        budget_ctx: ActiveBudgetContext,
        item: dict,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Validate and log a single expense item.

        Returns:
            (success_message, error_message) — exactly one will be non-None.
        """
        # Parse amount
        amount_val = item.get("amount")
        if not amount_val:
            item_name = item.get("item_name") or "an item"
            return None, f"Couldn't identify the amount for '{item_name}'."

        try:
            if isinstance(amount_val, str):
                amount_clean = amount_val.replace("$", "").replace(",", "")
                amount = Decimal(amount_clean)
            else:
                amount = Decimal(str(amount_val))
        except (ValueError, TypeError):
            item_name = item.get("item_name") or "an item"
            return None, f"Didn't understand the amount for '{item_name}'."

        # Resolve category
        category = item.get("category")
        if not category:
            if "general" in budget_ctx.categories:
                category = "general"
            else:
                item_name = item.get("item_name") or "an item"
                return None, f"Which category should '{item_name}' go under?"

        category = category.lower()

        if category not in budget_ctx.categories:
            valid_cats = ", ".join(budget_ctx.categories.keys())
            return None, (
                f"There's no '{category}' category in your budget. "
                f"Your current categories are: {valid_cats}. "
                f"Would you like me to add a '{category}' category to your budget?"
            )

        item_name = item.get("item_name") or "Expense"

        try:
            item_data = BudgetItemCreate(
                item_name=item_name,
                amount=amount,
                category=category,
                transaction_date=datetime.utcnow(),
                is_planned=False,
            )

            result = self.budget_service.add_budget_item(
                budget_id=budget_ctx.budget_id,
                user_id=user_id,
                item_data=item_data,
            )

            if not result:
                return None, f"Error logging ${amount:.2f} for '{item_name}'."

            spent_after = result.category_spent_after
            limit = result.category_limit
            remaining = limit - spent_after

            msg = f"Logged ${amount:.2f} for '{item_name}' in **{category}**."
            msg += f" ({category}: ${spent_after:.2f} / ${limit:.2f}, ${remaining:.2f} remaining)"

            if result.exceeded_budget:
                msg += " — **over budget!**"
            elif remaining < (limit * Decimal("0.1")):
                msg += " — less than 10% remaining"

            return msg, None

        except Exception:
            return None, f"Something went wrong logging '{item_name}'."

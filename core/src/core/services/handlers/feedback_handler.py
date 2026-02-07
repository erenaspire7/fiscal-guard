"""Handler for purchase feedback conversations."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from core.database.models import Budget, Goal, PurchaseDecision
from core.models.context import UserFinancialContext
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)


class PurchaseFeedbackHandler:
    """Handle feedback about actual purchases made."""

    def __init__(self, db: Session):
        """Initialize feedback handler.

        Args:
            db: Database session
        """
        self.db = db

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> ConversationResponse:
        """Process purchase feedback and update records.

        Args:
            user_id: User ID
            intent: Classified intent with entities
            conversation_history: Recent conversation messages
            financial_context: Pre-fetched financial context

        Returns:
            Conversation response
        """
        # Extract entities from intent
        purchased = intent.extracted_entities.get("purchased", True)
        regret_level = intent.extracted_entities.get("regret_level")
        payment_source = intent.extracted_entities.get("payment_source")

        # Check conversation history for context from previous assistant messages
        context_from_history = self._extract_context_from_history(conversation_history)

        # Find related decision
        related_decision = self._find_related_decision(
            user_id,
            conversation_history,
            intent.extracted_entities,
            context_from_history,
        )

        if not related_decision:
            return ConversationResponse(
                message="What item are you referring to? I don't see a recent purchase decision in our conversation.",
                requires_clarification=True,
            )

        # Check if we're in a multi-step flow by looking at the last assistant message
        current_step = context_from_history.get("step")

        # If we previously asked for regret level and now got a number, extract it
        if current_step == "regret" and regret_level is None:
            # Try to parse the user's last message as a number
            last_user_msg = (
                conversation_history[-1].content if conversation_history else ""
            )
            try:
                # Extract first number from the message
                import re

                numbers = re.findall(r"\d+", last_user_msg)
                if numbers:
                    regret_level = int(numbers[0])
                    if not (1 <= regret_level <= 10):
                        regret_level = None
            except (ValueError, IndexError):
                pass

        # If we previously asked for payment source and now got an answer, extract it
        if current_step == "source" and payment_source is None:
            last_user_msg = (
                conversation_history[-1].content.lower() if conversation_history else ""
            )
            if "budget" in last_user_msg:
                payment_source = "budget"
            elif "saving" in last_user_msg:
                payment_source = "savings"
            elif "goal" in last_user_msg:
                payment_source = "goal"

            # Also retrieve regret_level from context if it was provided earlier
            if regret_level is None:
                regret_level = context_from_history.get("regret_level")

        # Multi-step conversation for complete feedback
        if regret_level is None and purchased:
            return ConversationResponse(
                message=f"You bought the {related_decision.item_name} for ${related_decision.amount}. On a scale of 1-10, do you regret it? (1=no regret, 10=major regret)",
                requires_clarification=True,
                context={
                    "decision_id": str(related_decision.decision_id),
                    "step": "regret",
                    "purchased": purchased,
                },
            )

        if payment_source is None and purchased:
            return ConversationResponse(
                message="Where did the money come from? (budget / savings / goal funds)",
                requires_clarification=True,
                context={
                    "decision_id": str(related_decision.decision_id),
                    "step": "source",
                    "regret_level": regret_level,
                    "purchased": purchased,
                },
            )

        # Update decision record
        self._update_decision_feedback(
            related_decision.decision_id,
            purchased=purchased,
            regret_level=regret_level if purchased else None,
            payment_source=payment_source if purchased else None,
        )

        # If didn't purchase, just confirm
        if not purchased:
            return ConversationResponse(
                message=f"Got it! I've noted that you didn't end up buying the {related_decision.item_name}. Good restraint! 💪",
                metadata={"updated_decision": str(related_decision.decision_id)},
            )

        # Build response parts
        response_parts = [
            f"Got it! Updated your records for {related_decision.item_name} (${related_decision.amount})."
        ]

        # Update budget if from budget
        if payment_source == "budget":
            category = related_decision.category
            if category:
                budget_status = self._update_budget_spent(
                    user_id, category, float(related_decision.amount), financial_context
                )
                if budget_status:
                    response_parts.append(budget_status)

        # Update goals if from goal funds
        if payment_source == "goal_funds" or payment_source == "goal":
            goal_name = intent.extracted_entities.get("goal_name")
            if goal_name:
                goal_status = self._deduct_from_goal(
                    user_id,
                    goal_name,
                    float(related_decision.amount),
                    financial_context,
                )
                if goal_status:
                    response_parts.append(goal_status)

        # Add regret analysis if applicable
        if regret_level is not None:
            if regret_level >= 7:
                response_parts.append(
                    f"\n⚠️ Your regret level of {regret_level}/10 is quite high. Consider reflecting on what led to this decision to avoid similar regrets in the future."
                )
            elif regret_level <= 3:
                response_parts.append(
                    f"\n✅ Your regret level of {regret_level}/10 suggests this was a reasonable decision for you."
                )

        return ConversationResponse(
            message="\n\n".join(response_parts),
            metadata={
                "updated_decision": str(related_decision.decision_id),
                "updated_budget": payment_source == "budget",
                "updated_goals": payment_source in ["goal_funds", "goal"],
            },
        )

    def _extract_context_from_history(
        self, conversation_history: List[ConversationMessage]
    ) -> dict:
        """Extract context from previous assistant messages.

        Args:
            conversation_history: Recent messages

        Returns:
            Dictionary with context information
        """
        context = {}

        # Look at the most recent assistant messages for context
        for msg in reversed(conversation_history):
            if msg.role == "assistant" and msg.metadata:
                # Merge metadata from recent assistant messages
                if "context" in msg.metadata:
                    context.update(msg.metadata["context"])
                # Also check top-level metadata fields
                for key in ["decision_id", "step", "regret_level", "purchased"]:
                    if key in msg.metadata:
                        context[key] = msg.metadata[key]

                # If we found context, we can stop
                if context:
                    break

        return context

    def _find_related_decision(
        self,
        user_id: UUID,
        conversation_history: List[ConversationMessage],
        entities: dict,
        context: dict,
    ) -> Optional[PurchaseDecision]:
        """Find the decision being referenced.

        Args:
            user_id: User ID
            conversation_history: Recent messages
            entities: Extracted entities
            context: Context from previous messages

        Returns:
            Related decision if found
        """
        # 1. Check if there's a decision_id in the context from previous messages
        if "decision_id" in context:
            try:
                from uuid import UUID as UUIDType

                decision_id = (
                    UUIDType(context["decision_id"])
                    if isinstance(context["decision_id"], str)
                    else context["decision_id"]
                )
                decision = (
                    self.db.query(PurchaseDecision)
                    .filter(
                        PurchaseDecision.decision_id == decision_id,
                        PurchaseDecision.user_id == user_id,
                    )
                    .first()
                )
                if decision:
                    return decision
            except (ValueError, KeyError):
                pass

        # 2. Check if there's an explicit decision_id in message metadata
        for msg in reversed(conversation_history):
            if msg.metadata and "decision_id" in msg.metadata:
                try:
                    from uuid import UUID as UUIDType

                    decision_id = (
                        UUIDType(msg.metadata["decision_id"])
                        if isinstance(msg.metadata["decision_id"], str)
                        else msg.metadata["decision_id"]
                    )
                    decision = (
                        self.db.query(PurchaseDecision)
                        .filter(
                            PurchaseDecision.decision_id == decision_id,
                            PurchaseDecision.user_id == user_id,
                        )
                        .first()
                    )
                    if decision:
                        return decision
                except (ValueError, KeyError):
                    pass

        # 2. Look for explicit item name in entities
        item_name = entities.get("item_name")
        if item_name:
            # Find recent decision with similar item name
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            recent_decisions = (
                self.db.query(PurchaseDecision)
                .filter(
                    PurchaseDecision.user_id == user_id,
                    PurchaseDecision.created_at > twenty_four_hours_ago,
                )
                .order_by(PurchaseDecision.created_at.desc())
                .all()
            )

            for decision in recent_decisions:
                item_lower = item_name.lower()
                decision_item_lower = decision.item_name.lower()
                if (
                    item_lower in decision_item_lower
                    or decision_item_lower in item_lower
                ):
                    return decision

        # 3. Find most recent decision (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        decision = (
            self.db.query(PurchaseDecision)
            .filter(
                PurchaseDecision.user_id == user_id,
                PurchaseDecision.created_at > twenty_four_hours_ago,
            )
            .order_by(PurchaseDecision.created_at.desc())
            .first()
        )

        return decision

    def _update_decision_feedback(
        self,
        decision_id: UUID,
        purchased: bool,
        regret_level: Optional[int],
        payment_source: Optional[str],
    ) -> None:
        """Update decision record with feedback.

        Args:
            decision_id: Decision ID
            purchased: Whether the purchase was made
            regret_level: Regret level 1-10
            payment_source: Where money came from
        """
        decision = (
            self.db.query(PurchaseDecision)
            .filter(PurchaseDecision.decision_id == decision_id)
            .first()
        )

        if decision:
            decision.actual_purchase = purchased
            decision.regret_level = regret_level
            if payment_source:
                # Store payment source in user_feedback field for now
                feedback_text = f"Payment source: {payment_source}"
                decision.user_feedback = feedback_text

            self.db.commit()

    def _update_budget_spent(
        self,
        user_id: UUID,
        category: str,
        amount: float,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> Optional[str]:
        """Update budget category spent amount.

        Args:
            user_id: User ID
            category: Budget category
            amount: Amount to add to spent
            financial_context: Pre-fetched financial context

        Returns:
            Status message if successful
        """
        # Use context to get budget_id, then load ORM object for write
        budget_ctx = financial_context.active_budget if financial_context else None

        if budget_ctx and category in budget_ctx.categories:
            active_budget = (
                self.db.query(Budget)
                .filter(Budget.budget_id == budget_ctx.budget_id)
                .first()
            )
        else:
            active_budget = (
                self.db.query(Budget)
                .filter(
                    Budget.user_id == user_id,
                    Budget.period_start <= datetime.utcnow().date(),
                    Budget.period_end >= datetime.utcnow().date(),
                )
                .first()
            )

        if not active_budget or category not in active_budget.categories:
            return None

        # Update the spending amount
        categories_copy = active_budget.categories.copy()
        current_spent = categories_copy[category].get("spent", 0)
        new_spent = current_spent + amount
        categories_copy[category]["spent"] = new_spent

        active_budget.categories = categories_copy
        flag_modified(active_budget, "categories")

        active_budget.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(active_budget)

        # Build status message
        limit = categories_copy[category]["limit"]
        remaining = limit - new_spent
        percentage = (new_spent / limit * 100) if limit > 0 else 0

        if remaining < 0:
            status = f"⚠️ {category.capitalize()} budget: ${new_spent:.2f} / ${limit:.2f} ({percentage:.0f}% used - ${abs(remaining):.2f} over budget)"
        elif percentage >= 90:
            status = f"⚠️ {category.capitalize()} budget: ${new_spent:.2f} / ${limit:.2f} ({percentage:.0f}% used - ${remaining:.2f} remaining)"
        else:
            status = f"✅ {category.capitalize()} budget: ${new_spent:.2f} / ${limit:.2f} ({percentage:.0f}% used - ${remaining:.2f} remaining)"

        return status

    def _deduct_from_goal(
        self,
        user_id: UUID,
        goal_name: str,
        amount: float,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> Optional[str]:
        """Deduct amount from goal if funds came from there.

        Args:
            user_id: User ID
            goal_name: Goal name
            amount: Amount to deduct
            financial_context: Pre-fetched financial context

        Returns:
            Status message if successful
        """
        goal_name_lower = goal_name.lower()
        matching_goal = None

        # Use context for name matching, then load ORM object by ID for write
        goal_contexts = financial_context.active_goals if financial_context else []
        if goal_contexts:
            for g in goal_contexts:
                if (
                    goal_name_lower in g.goal_name.lower()
                    or g.goal_name.lower() in goal_name_lower
                ):
                    matching_goal = (
                        self.db.query(Goal)
                        .filter(Goal.goal_id == g.goal_id, Goal.user_id == user_id)
                        .first()
                    )
                    break
        else:
            # Fallback to DB query
            goals = (
                self.db.query(Goal)
                .filter(Goal.user_id == user_id, Goal.is_completed == False)
                .all()
            )
            for g in goals:
                if (
                    goal_name_lower in g.goal_name.lower()
                    or g.goal_name.lower() in goal_name_lower
                ):
                    matching_goal = g
                    break

        if not matching_goal:
            return None

        # Deduct amount
        new_amount = matching_goal.current_amount - amount
        if new_amount < 0:
            new_amount = 0

        matching_goal.current_amount = new_amount
        matching_goal.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(matching_goal)

        # Build status message
        remaining = matching_goal.target_amount - new_amount
        percentage = (
            (new_amount / matching_goal.target_amount * 100)
            if matching_goal.target_amount > 0
            else 0
        )

        status = f"📉 {matching_goal.goal_name}: ${new_amount:.2f} / ${matching_goal.target_amount:.2f} ({percentage:.0f}% complete - ${remaining:.2f} remaining)"

        return status

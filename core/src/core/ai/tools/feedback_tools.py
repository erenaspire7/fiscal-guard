"""Tools for purchase feedback handler."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from strands import tool

from core.database.models import Budget, Goal, PurchaseDecision
from core.models.context import UserFinancialContext


def create_feedback_tools(
    db_session: Session,
    user_id: str,
    financial_context: Optional[UserFinancialContext] = None,
):
    """Create feedback tools with database session and bound user_id.

    Args:
        db_session: Database session
        user_id: User ID to bind to the tools
        financial_context: Pre-fetched financial context (optional)
    """
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValueError(f"Invalid user_id format: {user_id}")

    @tool
    def find_recent_decision(item_name: Optional[str] = None) -> dict:
        """Find a recent purchase decision, optionally by item name. Searches the last 24 hours.

        Args:
            item_name: Optional item name to search for (fuzzy matched). If not provided, returns the most recent decision.

        Returns:
            Decision details including item name, amount, category, score, and decision ID.
        """
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

        if item_name:
            recent = (
                db_session.query(PurchaseDecision)
                .filter(
                    PurchaseDecision.user_id == user_uuid,
                    PurchaseDecision.created_at > twenty_four_hours_ago,
                )
                .order_by(PurchaseDecision.created_at.desc())
                .all()
            )

            item_lower = item_name.lower()
            for decision in recent:
                decision_item_lower = decision.item_name.lower()
                if (
                    item_lower in decision_item_lower
                    or decision_item_lower in item_lower
                ):
                    return {
                        "found": True,
                        "decision_id": str(decision.decision_id),
                        "item_name": decision.item_name,
                        "amount": float(decision.amount),
                        "category": decision.category,
                        "score": decision.score,
                        "decision_category": decision.decision_category,
                        "already_has_feedback": decision.actual_purchase is not None,
                    }

            return {
                "found": False,
                "message": f"No recent decision found matching '{item_name}'.",
            }

        # No item name — return most recent
        decision = (
            db_session.query(PurchaseDecision)
            .filter(
                PurchaseDecision.user_id == user_uuid,
                PurchaseDecision.created_at > twenty_four_hours_ago,
            )
            .order_by(PurchaseDecision.created_at.desc())
            .first()
        )

        if not decision:
            return {"found": False, "message": "No recent purchase decisions found."}

        return {
            "found": True,
            "decision_id": str(decision.decision_id),
            "item_name": decision.item_name,
            "amount": float(decision.amount),
            "category": decision.category,
            "score": decision.score,
            "decision_category": decision.decision_category,
            "already_has_feedback": decision.actual_purchase is not None,
        }

    @tool
    def record_purchase_feedback(
        decision_id: str,
        purchased: bool,
        regret_level: Optional[int] = None,
        payment_source: Optional[str] = None,
    ) -> dict:
        """Record feedback about whether a purchase was actually made.

        Args:
            decision_id: The decision ID to update
            purchased: Whether the user actually bought the item
            regret_level: Regret level from 1-10 (1=no regret, 10=major regret). Required if purchased is True.
            payment_source: Where the money came from: 'budget', 'savings', or 'goal'. Required if purchased is True.

        Returns:
            Confirmation of the feedback recorded.
        """
        try:
            decision_uuid = UUID(decision_id)
        except ValueError:
            return {"success": False, "error": "Invalid decision ID."}

        decision = (
            db_session.query(PurchaseDecision)
            .filter(
                PurchaseDecision.decision_id == decision_uuid,
                PurchaseDecision.user_id == user_uuid,
            )
            .first()
        )

        if not decision:
            return {"success": False, "error": "Decision not found."}

        decision.actual_purchase = purchased
        if purchased and regret_level is not None:
            decision.regret_level = max(1, min(10, regret_level))
        if purchased and payment_source:
            decision.user_feedback = f"Payment source: {payment_source}"

        db_session.commit()

        return {
            "success": True,
            "decision_id": decision_id,
            "item_name": decision.item_name,
            "amount": float(decision.amount),
            "purchased": purchased,
            "regret_level": regret_level if purchased else None,
            "payment_source": payment_source if purchased else None,
        }

    def _apply_budget_update(category_lower: str, amount: float):
        """Mutate budget in session without committing. Returns (result_dict, success)."""
        budget_ctx = financial_context.active_budget if financial_context else None

        if budget_ctx and category_lower in budget_ctx.categories:
            active_budget = (
                db_session.query(Budget)
                .filter(Budget.budget_id == budget_ctx.budget_id)
                .first()
            )
        else:
            active_budget = (
                db_session.query(Budget)
                .filter(
                    Budget.user_id == user_uuid,
                    Budget.period_start <= datetime.utcnow().date(),
                    Budget.period_end >= datetime.utcnow().date(),
                )
                .first()
            )

        if not active_budget or category_lower not in active_budget.categories:
            return {
                "success": False,
                "error": f"No active budget or category '{category_lower}' not found.",
            }, False

        categories_copy = active_budget.categories.copy()
        current_spent = categories_copy[category_lower].get("spent", 0)
        new_spent = current_spent + amount
        categories_copy[category_lower]["spent"] = new_spent

        active_budget.categories = categories_copy
        flag_modified(active_budget, "categories")
        active_budget.updated_at = datetime.utcnow()

        limit = categories_copy[category_lower]["limit"]
        remaining = limit - new_spent

        return {
            "success": True,
            "category": category_lower,
            "spent": new_spent,
            "limit": limit,
            "remaining": remaining,
            "percentage_used": round((new_spent / limit * 100) if limit > 0 else 0, 1),
        }, True

    def _apply_goal_deduction(goal_name_lower: str, amount: float):
        """Mutate goal in session without committing. Returns (result_dict, success)."""
        matching_goal = None

        goal_contexts = financial_context.active_goals if financial_context else []
        for g in goal_contexts:
            if (
                goal_name_lower in g.goal_name.lower()
                or g.goal_name.lower() in goal_name_lower
            ):
                matching_goal = (
                    db_session.query(Goal)
                    .filter(Goal.goal_id == g.goal_id, Goal.user_id == user_uuid)
                    .first()
                )
                break

        if not matching_goal:
            goals = (
                db_session.query(Goal)
                .filter(Goal.user_id == user_uuid, Goal.is_completed == False)
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
            return {
                "success": False,
                "error": f"Could not find a goal matching '{goal_name_lower}'.",
            }, False

        new_amount = max(0, float(matching_goal.current_amount) - amount)
        matching_goal.current_amount = new_amount
        matching_goal.updated_at = datetime.utcnow()

        target = float(matching_goal.target_amount)
        remaining = target - new_amount
        percentage = (new_amount / target * 100) if target > 0 else 0

        return {
            "success": True,
            "goal_name": matching_goal.goal_name,
            "amount_deducted": amount,
            "current_amount": new_amount,
            "target_amount": target,
            "remaining": remaining,
            "percentage_complete": round(percentage, 1),
        }, True

    @tool
    def update_budget_for_purchase(category: str, amount: float) -> dict:
        """Update budget category spending when a purchase was made from the budget.

        Args:
            category: The budget category the purchase falls under
            amount: The purchase amount to add to spending

        Returns:
            Updated budget category status.
        """
        result, _ = _apply_budget_update(category.lower(), amount)
        if result["success"]:
            db_session.commit()
        return result

    @tool
    def deduct_from_goal(goal_name: str, amount: float) -> dict:
        """Deduct an amount from a financial goal when a purchase was funded from goal savings.

        Args:
            goal_name: The name of the goal to deduct from (fuzzy matched)
            amount: The amount to deduct in dollars

        Returns:
            Updated goal status after deduction.
        """
        result, _ = _apply_goal_deduction(goal_name.lower(), amount)
        if result["success"]:
            db_session.commit()
        return result

    @tool
    def record_purchase_with_budget_update(
        decision_id: str,
        purchased: bool,
        category_override: Optional[str] = None,
        regret_level: Optional[int] = None,
        payment_source: Optional[str] = None,
    ) -> dict:
        """Record purchase feedback AND update budget in one call. Handles category changes intelligently.

        Use this tool when the user confirms they made a purchase. This will:
        1. Record the purchase feedback (purchased=True/False, regret_level, payment_source)
        2. If purchased=True, automatically update the budget category spending
        3. Handle category overrides (e.g., if user created a new category after the decision)

        Args:
            decision_id: The decision ID to update
            purchased: Whether the user actually bought the item
            category_override: Optional category to use instead of the decision's original category
                              (useful when user creates a more appropriate category after the decision)
            regret_level: Regret level from 1-10 (default: 5 if not provided)
            payment_source: Where money came from: 'budget', 'savings', or goal name (default: 'budget')

        Returns:
            Combined result with feedback recorded and budget updated.
        """
        try:
            decision_uuid = UUID(decision_id)
        except ValueError:
            return {"success": False, "error": "Invalid decision ID."}

        decision = (
            db_session.query(PurchaseDecision)
            .filter(
                PurchaseDecision.decision_id == decision_uuid,
                PurchaseDecision.user_id == user_uuid,
            )
            .first()
        )

        if not decision:
            return {"success": False, "error": "Decision not found."}

        # Determine which category to use
        target_category = (
            category_override.lower() if category_override else decision.category
        )
        amount = float(decision.amount)

        # Record feedback
        decision.actual_purchase = purchased
        if purchased:
            decision.regret_level = regret_level if regret_level is not None else 5
            decision.user_feedback = f"Payment source: {payment_source or 'budget'}"
            if category_override:
                decision.user_feedback += f" | Category changed from '{decision.category}' to '{target_category}'"

        result = {
            "success": True,
            "decision_id": decision_id,
            "item_name": decision.item_name,
            "amount": amount,
            "purchased": purchased,
            "category_used": target_category,
            "original_category": decision.category,
            "category_changed": category_override is not None,
        }

        # If purchased, apply secondary mutations without intermediate commits
        if purchased:
            payment_src = payment_source or "budget"

            if payment_src == "budget":
                budget_result, _ = _apply_budget_update(target_category, amount)
                if budget_result.get("success"):
                    result["budget_updated"] = True
                    result["category_spent_after"] = budget_result["spent"]
                    result["category_limit"] = budget_result["limit"]
                    result["category_remaining"] = budget_result["remaining"]
                else:
                    result["budget_updated"] = False
                    result["budget_error"] = budget_result.get("error")
            elif payment_src == "savings":
                result["budget_updated"] = False
                result["note"] = "Paid from savings - budget not affected"
            else:
                # Assume it's a goal name
                goal_result, _ = _apply_goal_deduction(payment_src, amount)
                if goal_result.get("success"):
                    result["goal_deducted"] = True
                    result["goal_name"] = goal_result["goal_name"]
                    result["goal_current_amount"] = goal_result["current_amount"]
                else:
                    result["goal_deducted"] = False
                    result["goal_error"] = goal_result.get("error")

        # Single commit for all mutations
        db_session.commit()
        return result

    return [
        find_recent_decision,
        record_purchase_feedback,
        update_budget_for_purchase,
        deduct_from_goal,
        record_purchase_with_budget_update,
    ]

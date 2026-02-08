"""Tools for goal update handler."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from strands import tool

from core.database.models import Goal
from core.models.context import UserFinancialContext


def create_goal_tools(
    db_session: Session,
    user_id: str,
    financial_context: Optional[UserFinancialContext] = None,
):
    """Create goal tools with database session and bound user_id.

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
    def get_goals_summary() -> dict:
        """Get a summary of all active financial goals with progress.

        Returns:
            List of active goals with name, target, current amount, remaining, percentage, priority, and deadline.
        """
        if financial_context and financial_context.has_goals:
            goals = []
            for g in financial_context.active_goals:
                goal_data = {
                    "goal_name": g.goal_name,
                    "target_amount": float(g.target_amount),
                    "current_amount": float(g.current_amount),
                    "remaining": float(g.remaining),
                    "percentage_complete": round(g.percentage_complete, 1),
                    "priority": g.priority,
                }
                if g.deadline:
                    goal_data["deadline"] = g.deadline.isoformat()
                    days_left = (g.deadline - datetime.utcnow().date()).days
                    goal_data["days_until_deadline"] = days_left
                goals.append(goal_data)

            return {
                "has_goals": True,
                "total_goals": len(goals),
                "goals": goals,
            }

        return {"has_goals": False, "total_goals": 0, "goals": []}

    @tool
    def add_goal_progress(goal_name: str, amount: float) -> dict:
        """Add money toward a financial goal. Fuzzy matches the goal name. Automatically marks the goal as completed if the target is reached.

        Args:
            goal_name: The name of the goal to update (fuzzy matched against existing goals)
            amount: The amount to add toward the goal in dollars (e.g., 50.00)

        Returns:
            Result with updated goal progress, completion status, and remaining amount.
        """
        # Fuzzy match goal name using pre-fetched context
        goal_contexts = financial_context.active_goals if financial_context else []
        matched_goal_id = None
        matched_goal_name = None

        goal_name_lower = goal_name.lower()
        for g in goal_contexts:
            if (
                goal_name_lower in g.goal_name.lower()
                or g.goal_name.lower() in goal_name_lower
            ):
                matched_goal_id = g.goal_id
                matched_goal_name = g.goal_name
                break

        if not matched_goal_id:
            available = [g.goal_name for g in goal_contexts]
            return {
                "success": False,
                "error": f"Could not find a goal matching '{goal_name}'.",
                "available_goals": available,
            }

        # Load ORM object for write
        goal = (
            db_session.query(Goal)
            .filter(Goal.goal_id == matched_goal_id, Goal.user_id == user_uuid)
            .first()
        )

        if not goal:
            return {"success": False, "error": "Goal not found in database."}

        old_amount = float(goal.current_amount)
        new_amount = old_amount + amount

        completed = new_amount >= float(goal.target_amount)
        if completed:
            new_amount = float(goal.target_amount)
            goal.is_completed = True
            goal.completion_date = datetime.utcnow()

        goal.current_amount = new_amount
        goal.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(goal)

        target = float(goal.target_amount)
        remaining = target - new_amount
        percentage = (new_amount / target * 100) if target > 0 else 0

        result = {
            "success": True,
            "goal_name": matched_goal_name,
            "amount_added": amount,
            "previous_amount": old_amount,
            "current_amount": new_amount,
            "target_amount": target,
            "remaining": remaining,
            "percentage_complete": round(percentage, 1),
            "completed": completed,
        }

        if goal.deadline:
            days_left = (goal.deadline - datetime.utcnow().date()).days
            result["days_until_deadline"] = days_left
            if not completed and days_left > 0:
                monthly_needed = remaining / max(1, days_left / 30)
                result["monthly_savings_needed"] = round(monthly_needed, 2)

        return result

    return [get_goals_summary, add_goal_progress]

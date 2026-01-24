"""Handler for goal update conversations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.database.models import Goal
from core.models.conversation import ConversationIntent, ConversationResponse


class GoalUpdateHandler:
    """Handle goal progress updates."""

    def __init__(self, db: Session):
        """Initialize goal update handler.

        Args:
            db: Database session
        """
        self.db = db

    def handle(self, user_id: UUID, intent: ConversationIntent) -> ConversationResponse:
        """Process goal update and provide confirmation.

        Args:
            user_id: User ID
            intent: Classified intent with entities

        Returns:
            Conversation response with goal update confirmation
        """
        # Extract entities
        goal_name = intent.extracted_entities.get("goal_name")
        amount = intent.extracted_entities.get("amount")

        if not goal_name:
            # Show available goals
            goals = self._get_active_goals(user_id)
            if not goals:
                return ConversationResponse(
                    message="You don't have any active goals yet. Would you like to create one?",
                    requires_clarification=True,
                )

            goal_list = "\n".join([f"- {g.name}" for g in goals])
            return ConversationResponse(
                message=f"Which goal would you like to update?\n\n{goal_list}",
                requires_clarification=True,
            )

        if amount is None:
            return ConversationResponse(
                message=f"How much would you like to add to {goal_name}?",
                requires_clarification=True,
                context={"goal_name": goal_name},
            )

        # Find the goal
        goal = self._find_goal_by_name(user_id, goal_name)

        if not goal:
            goals = self._get_active_goals(user_id)
            goal_list = "\n".join([f"- {g.name}" for g in goals])
            return ConversationResponse(
                message=f"I couldn't find a goal named '{goal_name}'. Your active goals are:\n\n{goal_list}",
                requires_clarification=True,
            )

        # Update the goal
        old_amount = goal.current_amount
        new_amount = old_amount + amount

        # Check if goal is completed
        completed = new_amount >= goal.target_amount
        if completed:
            new_amount = goal.target_amount
            goal.is_completed = True
            goal.completion_date = datetime.utcnow()

        goal.current_amount = new_amount
        goal.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(goal)

        # Build response
        if completed:
            return self._handle_goal_completion(goal, amount)
        else:
            return self._handle_goal_progress(goal, amount)

    def _get_active_goals(self, user_id: UUID) -> list[Goal]:
        """Get user's active goals.

        Args:
            user_id: User ID

        Returns:
            List of active goals
        """
        return (
            self.db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.is_completed == False)
            .order_by(Goal.created_at.desc())
            .all()
        )

    def _find_goal_by_name(self, user_id: UUID, goal_name: str) -> Optional[Goal]:
        """Find goal by name (case-insensitive partial match).

        Args:
            user_id: User ID
            goal_name: Goal name to search for

        Returns:
            Matching goal if found
        """
        goals = self._get_active_goals(user_id)

        goal_name_lower = goal_name.lower()
        for goal in goals:
            if (
                goal_name_lower in goal.name.lower()
                or goal.name.lower() in goal_name_lower
            ):
                return goal

        return None

    def _handle_goal_completion(
        self, goal: Goal, amount_added: float
    ) -> ConversationResponse:
        """Handle when a goal is completed.

        Args:
            goal: Completed goal
            amount_added: Amount that was just added

        Returns:
            Celebratory response
        """
        message = f"""🎉 **Congratulations!** 🎉

You've completed your goal: **{goal.name}**!

You added ${amount_added:.2f}, bringing you to ${goal.current_amount:.2f} / ${goal.target_amount:.2f}.

This is a huge achievement! Keep up the excellent financial discipline! 💪"""

        return ConversationResponse(
            message=message,
            metadata={"goal_id": str(goal.goal_id), "completed": True},
        )

    def _handle_goal_progress(
        self, goal: Goal, amount_added: float
    ) -> ConversationResponse:
        """Handle regular goal progress update.

        Args:
            goal: Goal being updated
            amount_added: Amount that was just added

        Returns:
            Progress response
        """
        remaining = goal.target_amount - goal.current_amount
        percentage = (
            (goal.current_amount / goal.target_amount * 100)
            if goal.target_amount > 0
            else 0
        )

        message_parts = [
            f"✅ **Added ${amount_added:.2f} to {goal.name}!**",
            "",
            f"📊 **Progress:**",
            f"- Current: ${goal.current_amount:.2f}",
            f"- Target: ${goal.target_amount:.2f}",
            f"- Remaining: ${remaining:.2f}",
            f"- Completion: {percentage:.1f}%",
        ]

        # Add motivational message based on progress
        if percentage >= 75:
            message_parts.append(
                f"\n🔥 You're in the home stretch! Only ${remaining:.2f} to go!"
            )
        elif percentage >= 50:
            message_parts.append(
                f"\n💪 You're over halfway there! Keep up the momentum!"
            )
        elif percentage >= 25:
            message_parts.append(
                f"\n📈 Great progress! You're building good financial habits!"
            )
        else:
            message_parts.append(f"\n🌱 Every step counts! You're on your way!")

        # Calculate months to completion if we have contribution history
        if goal.deadline:
            days_until_deadline = (goal.deadline - datetime.utcnow()).days
            if days_until_deadline > 0:
                required_per_month = remaining / max(1, days_until_deadline / 30)
                message_parts.append(
                    f"\n⏰ To reach your goal by the deadline, you'll need to save ~${required_per_month:.2f}/month."
                )

        return ConversationResponse(
            message="\n".join(message_parts),
            metadata={"goal_id": str(goal.goal_id), "progress": percentage},
        )

"""Service layer for purchase decisions."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from core.ai.decision_agent import DecisionAgent
from core.database.models import PurchaseDecision as PurchaseDecisionDB
from core.models.decision import (
    DecisionFeedback,
    PurchaseDecisionCreate,
    PurchaseDecisionRequest,
    PurchaseDecisionResponse,
)
from core.models.decision import (
    PurchaseDecisionDB as PurchaseDecisionDBModel,
)


class DecisionService:
    """Service for managing purchase decisions.

    Note: Tracing is handled automatically by Strands Agent via OpenTelemetry.
    No manual @track decorators needed.
    """

    def __init__(self, db: Session):
        """Initialize decision service.

        Args:
            db: Database session
        """
        self.db = db
        self.agent = DecisionAgent(db)

    def create_decision(
        self, user_id: UUID, request: PurchaseDecisionRequest
    ) -> PurchaseDecisionResponse:
        """Create a new purchase decision.

        The DecisionAgent automatically traces this flow via OpenTelemetry,
        including all tool calls and model interactions.

        Args:
            user_id: User making the purchase request
            request: Purchase request details

        Returns:
            Purchase decision response with decision and ID
        """
        # Use the AI agent to analyze the purchase
        # This is automatically traced via OpenTelemetry
        decision = self.agent.analyze_purchase(user_id, request)

        # Save to database
        # Use mode='json' to properly serialize Decimal fields
        db_decision = PurchaseDecisionDB(
            user_id=user_id,
            item_name=request.item_name,
            amount=request.amount,
            category=request.category,
            reason=request.reason,
            urgency=request.urgency,
            score=decision.score,
            decision_category=decision.decision_category.value,
            reasoning=decision.reasoning,
            analysis=decision.analysis.model_dump(mode="json"),
            alternatives=decision.alternatives,
            conditions=decision.conditions,
        )

        self.db.add(db_decision)
        self.db.commit()
        self.db.refresh(db_decision)

        return PurchaseDecisionResponse(
            decision=decision, decision_id=db_decision.decision_id
        )

    def get_decision(
        self, user_id: UUID, decision_id: UUID
    ) -> Optional[PurchaseDecisionDBModel]:
        """Get a specific decision.

        Args:
            user_id: User ID
            decision_id: Decision ID

        Returns:
            Decision if found and belongs to user, None otherwise
        """
        decision = (
            self.db.query(PurchaseDecisionDB)
            .filter(
                PurchaseDecisionDB.decision_id == decision_id,
                PurchaseDecisionDB.user_id == user_id,
            )
            .first()
        )

        if not decision:
            return None

        return PurchaseDecisionDBModel.model_validate(decision)

    def list_decisions(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[PurchaseDecisionDBModel]:
        """List user's decisions.

        Args:
            user_id: User ID
            limit: Maximum number of decisions to return
            offset: Number of decisions to skip

        Returns:
            List of decisions
        """
        decisions = (
            self.db.query(PurchaseDecisionDB)
            .filter(PurchaseDecisionDB.user_id == user_id)
            .order_by(PurchaseDecisionDB.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return [PurchaseDecisionDBModel.model_validate(d) for d in decisions]

    def add_feedback(
        self, user_id: UUID, decision_id: UUID, feedback: DecisionFeedback
    ) -> Optional[PurchaseDecisionDBModel]:
        """Add user feedback to a decision.

        Args:
            user_id: User ID
            decision_id: Decision ID
            feedback: User feedback

        Returns:
            Updated decision if found, None otherwise
        """
        decision = (
            self.db.query(PurchaseDecisionDB)
            .filter(
                PurchaseDecisionDB.decision_id == decision_id,
                PurchaseDecisionDB.user_id == user_id,
            )
            .first()
        )

        if not decision:
            return None

        # Update feedback fields
        decision.actual_purchase = feedback.actual_purchase
        decision.regret_level = feedback.regret_level
        decision.user_feedback = feedback.feedback

        self.db.commit()
        self.db.refresh(decision)

        return PurchaseDecisionDBModel.model_validate(decision)

    def get_decision_stats(self, user_id: UUID) -> dict:
        """Get decision statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with decision statistics
        """
        all_decisions = (
            self.db.query(PurchaseDecisionDB)
            .filter(PurchaseDecisionDB.user_id == user_id)
            .all()
        )

        if not all_decisions:
            return {
                "total_decisions": 0,
                "average_score": 0.0,
                "total_requested": 0.0,
                "decisions_by_category": {},
                "feedback_rate": 0.0,
            }

        total = len(all_decisions)
        avg_score = sum(d.score for d in all_decisions) / total
        total_requested = sum(float(d.amount) for d in all_decisions)

        # Count by decision category
        category_counts = {}
        for d in all_decisions:
            cat = d.decision_category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Calculate feedback rate
        with_feedback = sum(1 for d in all_decisions if d.actual_purchase is not None)
        feedback_rate = (with_feedback / total * 100) if total > 0 else 0

        return {
            "total_decisions": total,
            "average_score": round(avg_score, 1),
            "total_requested": round(total_requested, 2),
            "decisions_by_category": category_counts,
            "feedback_rate": round(feedback_rate, 1),
        }

    def get_dashboard_summary(self, user_id: UUID) -> dict:
        """Get summary data for the dashboard.

        Args:
            user_id: User ID

        Returns:
            Dictionary containing guard score, trend, and recent decisions.
        """
        # Get recent decisions to calculate performance
        recent_decisions = (
            self.db.query(PurchaseDecisionDB)
            .filter(PurchaseDecisionDB.user_id == user_id)
            .order_by(PurchaseDecisionDB.created_at.desc())
            .limit(20)
            .all()
        )

        if not recent_decisions:
            return {
                "guard_score": 0,
                "score_status": "New",
                "score_trend": [],
                "recent_decisions": [],
            }

        avg_score = sum(d.score for d in recent_decisions) / len(recent_decisions)
        guard_score = int(avg_score * 10)

        # Trend data (reverse to chronological order for sparkline)
        trend = [
            {
                "score": d.score,
                "date": d.created_at.isoformat(),
                "item_name": d.item_name,
            }
            for d in reversed(recent_decisions)
        ]

        # Determine status
        if guard_score >= 80:
            status = "Thriving"
        elif guard_score >= 60:
            status = "Stable"
        else:
            status = "At Risk"

        return {
            "guard_score": guard_score,
            "score_status": status,
            "score_trend": trend,
            "recent_decisions": [
                {
                    "decision_id": d.decision_id,
                    "item_name": d.item_name,
                    "amount": float(d.amount),
                    "score": d.score,
                    "category": d.category,
                    "created_at": d.created_at,
                }
                for d in recent_decisions[:5]
            ],
        }

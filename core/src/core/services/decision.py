"""Service layer for purchase decisions."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from core.ai.agents.decision_agent import DecisionAgent
from core.database.models import Budget
from core.database.models import PurchaseDecision as PurchaseDecisionDB
from core.models.budget import BudgetItemCreate
from core.models.cart import (
    AggregateRecommendation,
    CartAnalysisResponse,
    CartItem,
    ItemDecisionResult,
)
from core.models.context import UserFinancialContext
from core.models.decision import (
    BudgetCategory,
    DecisionFeedback,
    PurchaseDecisionListResponse,
    PurchaseDecisionRequest,
    PurchaseDecisionResponse,
)
from core.models.decision import (
    PurchaseDecisionDB as PurchaseDecisionDBModel,
)
from core.services.budget import BudgetService


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
        self.budget_service = BudgetService(db)

    def create_decision(
        self,
        user_id: UUID,
        request: PurchaseDecisionRequest,
        session_id: Optional[str] = None,
        financial_context: Optional[UserFinancialContext] = None,
    ) -> PurchaseDecisionResponse:
        """Create a new purchase decision.

        The DecisionAgent automatically traces this flow via OpenTelemetry,
        including all tool calls and model interactions.

        Args:
            user_id: User making the purchase request
            request: Purchase request details
            session_id: Optional session ID for prompt override testing
            financial_context: Pre-fetched financial context (budget, goals, decisions)

        Returns:
            Purchase decision response with decision and ID
        """
        # Create agent for this request (allows prompt override via session_id)
        agent = DecisionAgent(self.db, session_id=session_id)

        # Use the AI agent to analyze the purchase
        # This is automatically traced via OpenTelemetry
        decision, clarification_question, related_decision_id = agent.analyze_purchase(
            user_id, request, financial_context
        )

        # If we need clarification, don't save yet - return response asking for confirmation
        if clarification_question and not request.is_follow_up:
            # Create a temporary decision ID for the response
            from uuid import uuid4

            temp_decision_id = uuid4()

            return PurchaseDecisionResponse(
                decision=decision,
                decision_id=temp_decision_id,
                requires_clarification=True,
                clarification_question=clarification_question,
                related_decision_id=related_decision_id,
            )

        # If this is a follow-up confirming the same item, update the existing decision
        if request.is_follow_up and request.related_decision_id:
            existing_decision = (
                self.db.query(PurchaseDecisionDB)
                .filter(
                    PurchaseDecisionDB.decision_id == request.related_decision_id,
                    PurchaseDecisionDB.user_id == user_id,
                )
                .first()
            )

            if existing_decision:
                # Update the existing decision with new analysis
                existing_decision.score = decision.score
                existing_decision.decision_category = decision.decision_category.value
                existing_decision.reasoning = decision.reasoning
                existing_decision.analysis = decision.analysis.model_dump(mode="json")
                existing_decision.alternatives = decision.alternatives
                existing_decision.conditions = decision.conditions

                # Update fields from request if they were refined
                if request.item_name:
                    existing_decision.item_name = request.item_name
                if request.amount:
                    existing_decision.amount = request.amount
                if request.category:
                    existing_decision.category = request.category.value
                if request.reason:
                    existing_decision.reason = request.reason
                if request.urgency:
                    existing_decision.urgency = request.urgency

                self.db.commit()
                self.db.refresh(existing_decision)

                return PurchaseDecisionResponse(
                    decision=decision, decision_id=existing_decision.decision_id
                )

        # Save to database as a new decision
        # Use mode='json' to properly serialize Decimal fields
        # After analyze_purchase, request should have all fields populated (from extraction or original)
        db_decision = PurchaseDecisionDB(
            user_id=user_id,
            item_name=request.item_name
            or "Unknown Item",  # Fallback in case extraction failed
            amount=request.amount or 0,  # Fallback
            category=request.category.value
            if request.category
            else None,  # Convert enum to string for DB
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
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PurchaseDecisionListResponse:
        """List user's decisions.

        Args:
            user_id: User ID
            limit: Maximum number of decisions to return
            offset: Number of decisions to skip
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Paginated list of decisions
        """
        query = self.db.query(PurchaseDecisionDB).filter(
            PurchaseDecisionDB.user_id == user_id
        )

        if start_date:
            query = query.filter(PurchaseDecisionDB.created_at >= start_date)

        if end_date:
            query = query.filter(PurchaseDecisionDB.created_at <= end_date)

        # Get total count
        total = query.count()

        decisions = (
            query.order_by(PurchaseDecisionDB.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items = [PurchaseDecisionDBModel.model_validate(d) for d in decisions]

        return PurchaseDecisionListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    def add_feedback(
        self, user_id: UUID, decision_id: UUID, feedback: DecisionFeedback
    ) -> Optional[PurchaseDecisionDBModel]:
        """Add user feedback to a decision.

        If the user actually made the purchase, this will create a budget item
        to track it and update the budget accordingly.

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
        if feedback.feedback is not None:
            decision.user_feedback = feedback.feedback

        # If user actually made the purchase, record it as a budget item
        if feedback.actual_purchase and decision.category:
            # Find the active budget (budget containing current date)
            active_budget = (
                self.db.query(Budget)
                .filter(
                    Budget.user_id == user_id,
                    Budget.period_start <= datetime.utcnow().date(),
                    Budget.period_end >= datetime.utcnow().date(),
                )
                .first()
            )

            if active_budget and decision.category in active_budget.categories:
                # Create budget item to track this purchase
                budget_item_data = BudgetItemCreate(
                    item_name=decision.item_name,
                    amount=Decimal(str(decision.amount)),
                    category=decision.category,
                    transaction_date=datetime.utcnow(),
                    decision_id=decision_id,
                    notes=feedback.feedback,
                    is_planned=decision.score
                    >= 7,  # Consider it planned if AI recommended it
                )

                # Add to budget and update spending
                self.budget_service.add_budget_item(
                    budget_id=active_budget.budget_id,
                    user_id=user_id,
                    item_data=budget_item_data,
                )

        self.db.commit()
        self.db.refresh(decision)

        return PurchaseDecisionDBModel.model_validate(decision)

    @staticmethod
    def _calculate_behavioral_score(decision) -> float:
        """Calculate a behavioral score (0-10) reflecting user's financial behavior.

        Unlike the raw AI score (which measures "is this a good purchase?"),
        the behavioral score measures "did the user make a good financial decision?"

        - Resisting a bad purchase (low AI score + didn't buy) = high score
        - Following good advice (high AI score + bought + low regret) = high score
        - Ignoring warnings (low AI score + bought + high regret) = low score
        - No feedback yet = use raw AI score as default
        """
        ai_score = decision.score

        if decision.actual_purchase is None:
            return float(ai_score)

        bought = decision.actual_purchase
        regret = decision.regret_level

        if not bought:
            if ai_score <= 5:
                # Resisted bad purchase — reward (ai_score=1 -> 9.0, ai_score=5 -> 7.0)
                return 9.0 - (ai_score - 1) * 0.5
            elif ai_score >= 7:
                # Skipped a good purchase — slight penalty
                return max(4.0, 8.0 - ai_score * 0.4)
            else:
                # Mid-range, ambiguous
                return 6.0
        else:
            if regret is not None and regret >= 7:
                # High regret = bad outcome regardless of AI advice
                return max(1.0, 4.0 - (regret - 7) * 1.0)
            elif regret is not None and regret <= 3:
                # Low regret = good outcome
                if ai_score >= 7:
                    return float(ai_score)
                else:
                    # Ignored warning but happy — moderate
                    return 6.0
            else:
                # Moderate regret or no regret data — keep AI score
                return float(ai_score)

    def get_decision_stats(self, user_id: UUID) -> dict:
        """Get decision statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with decision statistics including growth insights
        """
        from datetime import datetime, timedelta

        all_decisions = (
            self.db.query(PurchaseDecisionDB)
            .filter(PurchaseDecisionDB.user_id == user_id)
            .order_by(PurchaseDecisionDB.created_at.asc())
            .all()
        )

        if not all_decisions:
            return {
                "total_decisions": 0,
                "average_score": 0.0,
                "total_requested": 0.0,
                "decisions_by_category": {},
                "feedback_rate": 0.0,
                "capital_retained": 0.0,
                "intercepted_count": 0,
                "impulse_control_growth": 0.0,
                "weekly_scores": [],
            }

        total = len(all_decisions)
        avg_score = (
            sum(self._calculate_behavioral_score(d) for d in all_decisions) / total
        )
        total_requested = sum(float(d.amount) for d in all_decisions)

        # Count by decision category
        category_counts = {}
        for d in all_decisions:
            cat = d.decision_category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Calculate feedback rate
        with_feedback = sum(1 for d in all_decisions if d.actual_purchase is not None)
        feedback_rate = (with_feedback / total * 100) if total > 0 else 0

        # Calculate capital retained (AI recommended "no" and user didn't buy)
        capital_retained = 0.0
        intercepted_count = 0

        for d in all_decisions:
            # AI said "no" (score <= 5) or "mild no" (score 4-5)
            ai_recommended_no = d.score <= 5
            user_didnt_buy = d.actual_purchase == False

            if ai_recommended_no and user_didnt_buy:
                capital_retained += float(d.amount)
                intercepted_count += 1

        # Calculate impulse control growth (last 30 days vs previous 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        sixty_days_ago = datetime.utcnow() - timedelta(days=60)

        recent_decisions = [d for d in all_decisions if d.created_at >= thirty_days_ago]
        previous_decisions = [
            d for d in all_decisions if sixty_days_ago <= d.created_at < thirty_days_ago
        ]

        impulse_control_growth = 0.0
        if recent_decisions and previous_decisions:
            recent_avg = sum(
                self._calculate_behavioral_score(d) for d in recent_decisions
            ) / len(recent_decisions)
            previous_avg = sum(
                self._calculate_behavioral_score(d) for d in previous_decisions
            ) / len(previous_decisions)

            if previous_avg > 0:
                impulse_control_growth = (
                    (recent_avg - previous_avg) / previous_avg
                ) * 100

        # Calculate decision score trend (individual decisions with feedback only)
        # Only include decisions where user provided feedback (actual_purchase is not None)
        decisions_with_feedback = [
            d for d in all_decisions if d.actual_purchase is not None
        ]

        # Get chronological behavioral scores (scaled to 0-100) for decisions with feedback
        weekly_scores = [
            int(self._calculate_behavioral_score(d) * 10)
            for d in decisions_with_feedback
        ]

        # Build detailed trend data with item names and dates for graph display
        trend_data = [
            {
                "score": int(self._calculate_behavioral_score(d) * 10),
                "item_name": d.item_name,
                "date": d.created_at.strftime("%b %d"),
                "amount": float(d.amount),
            }
            for d in decisions_with_feedback
        ]

        return {
            "total_decisions": total,
            "average_score": round(avg_score, 1),
            "total_requested": round(total_requested, 2),
            "decisions_by_category": category_counts,
            "feedback_rate": round(feedback_rate, 1),
            "capital_retained": round(capital_retained, 2),
            "intercepted_count": intercepted_count,
            "impulse_control_growth": round(impulse_control_growth, 1),
            "weekly_scores": weekly_scores,
            "trend_data": trend_data,
        }

    def get_dashboard_summary(self, user_id: UUID) -> dict:
        """Get summary data for the dashboard.

        The guard score is now calculated using:
        1. Recent decision scores (60% weight)
        2. Budget adherence over time (40% weight)

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
                "budget_impact": None,
            }

        # Calculate base behavioral score from decisions (0-10 scale)
        avg_decision_score = sum(
            self._calculate_behavioral_score(d) for d in recent_decisions
        ) / len(recent_decisions)

        # Get budget adherence analysis (0-100 scale)
        budget_analysis = self.budget_service.analyze_budgets_over_time(
            user_id, num_periods=3
        )
        budget_adherence = budget_analysis.average_adherence

        # Calculate composite guard score
        # Decision quality: 60% weight (convert 0-10 to 0-100)
        # Budget adherence: 40% weight (already 0-100)
        decision_component = (avg_decision_score * 10) * 0.6
        budget_component = budget_adherence * 0.4

        guard_score = int(decision_component + budget_component)

        # Apply penalties for over-budget behavior
        if budget_analysis.over_budget_count > 0:
            # Reduce score by 2 points per over-budget occurrence (max penalty: 20 points)
            penalty = min(budget_analysis.over_budget_count * 2, 20)
            guard_score = max(0, guard_score - penalty)

        # Trend data (reverse to chronological order for sparkline)
        # Only include decisions with feedback (actual_purchase is not None)
        # Limit to last 7 decisions with feedback for the graph
        decisions_with_feedback = [
            d for d in recent_decisions if d.actual_purchase is not None
        ][:7]  # Take only the first 7 (most recent)

        trend = [
            {
                "score": self._calculate_behavioral_score(d),  # Behavioral score (0-10)
                "date": d.created_at.strftime("%b %d"),  # Format as "Jan 23"
                "item_name": d.item_name,
            }
            for d in reversed(decisions_with_feedback)  # Chronological order
        ]

        # Determine status with budget awareness
        if guard_score >= 80 and budget_analysis.trend != "declining":
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
            "budget_impact": {
                "adherence": budget_analysis.average_adherence,
                "trend": budget_analysis.trend,
                "over_budget_count": budget_analysis.over_budget_count,
            },
        }

    async def analyze_cart_items(
        self,
        user_id: UUID,
        items: list[CartItem],
        page_url: str,
        page_type: str,
    ) -> CartAnalysisResponse:
        """Analyze cart items from browser extension.

        Processes each item individually using the DecisionAgent,
        then creates an aggregate recommendation.

        Args:
            user_id: User ID
            items: List of extracted cart items
            page_url: URL of the shopping page
            page_type: Type of page (cart, checkout, product)

        Returns:
            Cart analysis response with individual and aggregate decisions
        """
        item_decisions: list[ItemDecisionResult] = []

        # Create agent for cart analysis
        agent = DecisionAgent(self.db)

        # Analyze each item individually
        for item in items:
            # Calculate total amount for this item
            total_amount = item.price * item.quantity

            # Infer category from item name
            category = self._infer_category(item.item_name)

            # Create decision request
            decision_request = PurchaseDecisionRequest(
                item_name=item.item_name,
                amount=total_amount,
                category=category,
                urgency=item.urgency_badge or "normal",
                reason=f"Cart item from {page_url}",
                user_message=None,
            )

            # Use existing decision logic
            decision, clarification_question, related_decision_id = (
                agent.analyze_purchase(user_id, decision_request)
            )

            # Check if this is a duplicate of a recent decision
            # If related_decision_id is set, we found a similar recent purchase
            if related_decision_id and not decision_request.is_follow_up:
                # Update existing decision instead of creating duplicate
                existing_decision = (
                    self.db.query(PurchaseDecisionDB)
                    .filter(
                        PurchaseDecisionDB.decision_id == related_decision_id,
                        PurchaseDecisionDB.user_id == user_id,
                    )
                    .first()
                )

                if existing_decision:
                    # Update the existing decision with new analysis
                    existing_decision.score = decision.score
                    existing_decision.decision_category = (
                        decision.decision_category.value
                    )
                    existing_decision.reasoning = decision.reasoning
                    existing_decision.analysis = decision.analysis.model_dump(
                        mode="json"
                    )
                    existing_decision.alternatives = decision.alternatives
                    existing_decision.conditions = decision.conditions
                    # Don't add a new record, just update existing
                else:
                    # If we can't find the existing decision, create new one
                    db_decision = PurchaseDecisionDB(
                        user_id=user_id,
                        item_name=item.item_name,
                        amount=total_amount,
                        category=category.value,
                        reason=f"Cart item from {page_url}",
                        urgency=item.urgency_badge or "normal",
                        score=decision.score,
                        decision_category=decision.decision_category.value,
                        reasoning=decision.reasoning,
                        analysis=decision.analysis.model_dump(mode="json"),
                        alternatives=decision.alternatives,
                        conditions=decision.conditions,
                    )
                    self.db.add(db_decision)
            else:
                # No duplicate found, save as new decision
                db_decision = PurchaseDecisionDB(
                    user_id=user_id,
                    item_name=item.item_name,
                    amount=total_amount,
                    category=category.value,
                    reason=f"Cart item from {page_url}",
                    urgency=item.urgency_badge or "normal",
                    score=decision.score,
                    decision_category=decision.decision_category.value,
                    reasoning=decision.reasoning,
                    analysis=decision.analysis.model_dump(mode="json"),
                    alternatives=decision.alternatives,
                    conditions=decision.conditions,
                )
                self.db.add(db_decision)

            item_decisions.append(
                ItemDecisionResult(
                    item_name=item.item_name,
                    price=item.price,
                    quantity=item.quantity,
                    total_amount=total_amount,
                    urgency_badge=item.urgency_badge,
                    decision=decision,
                )
            )

        # Commit all decisions at once
        self.db.commit()

        # Generate aggregate recommendation
        aggregate = self._create_aggregate_recommendation(user_id, item_decisions)

        # Create conversation ID for follow-up chat
        conversation_id = uuid4()

        return CartAnalysisResponse(
            items=item_decisions,
            aggregate=aggregate,
            conversation_id=conversation_id,
            requires_clarification=False,
        )

    def _infer_category(self, item_name: str) -> BudgetCategory:
        """Infer budget category from item name.

        Simple keyword-based categorization. Could be enhanced with AI.

        Args:
            item_name: Name of the item

        Returns:
            Inferred budget category
        """
        item_lower = item_name.lower()

        # Entertainment keywords
        if any(
            word in item_lower
            for word in [
                "book",
                "game",
                "movie",
                "music",
                "dvd",
                "blu-ray",
                "streaming",
                "console",
                "controller",
            ]
        ):
            return BudgetCategory.ENTERTAINMENT

        # Groceries keywords
        if any(
            word in item_lower
            for word in [
                "food",
                "snack",
                "coffee",
                "tea",
                "drink",
                "water",
                "juice",
                "milk",
                "cereal",
                "bread",
                "fruit",
                "vegetable",
            ]
        ):
            return BudgetCategory.GROCERIES

        # Dining keywords
        if any(
            word in item_lower
            for word in ["restaurant", "takeout", "delivery", "meal kit"]
        ):
            return BudgetCategory.DINING

        # Transport keywords
        if any(
            word in item_lower
            for word in ["uber", "lyft", "taxi", "gas", "fuel", "parking", "transit"]
        ):
            return BudgetCategory.TRANSPORT

        # Default to shopping
        return BudgetCategory.SHOPPING

    def _create_aggregate_recommendation(
        self,
        user_id: UUID,
        item_decisions: list[ItemDecisionResult],
    ) -> AggregateRecommendation:
        """Create aggregate recommendation from individual item decisions.

        Args:
            user_id: User ID
            item_decisions: List of individual item decisions

        Returns:
            Aggregate recommendation
        """
        # Calculate total amount
        total_amount = sum(item.total_amount for item in item_decisions)

        # Calculate weighted average score (weighted by item price)
        if item_decisions:
            scores = [item.decision.score for item in item_decisions]
            weights = [float(item.total_amount) for item in item_decisions]
            total_weight = sum(weights)

            if total_weight > 0:
                overall_score = int(
                    sum(s * w for s, w in zip(scores, weights)) / total_weight
                )
            else:
                overall_score = int(sum(scores) / len(scores))
        else:
            overall_score = 5

        # Categorize items
        items_to_remove = [
            item.item_name for item in item_decisions if item.decision.score <= 4
        ]

        items_to_keep = [
            item.item_name for item in item_decisions if item.decision.score >= 7
        ]

        # Generate summary recommendation
        if overall_score <= 4:
            recommendation = (
                f"We recommend reconsidering this ${total_amount:.2f} purchase. "
            )
        elif overall_score >= 7:
            recommendation = (
                f"This ${total_amount:.2f} purchase aligns with your financial goals. "
            )
        else:
            recommendation = (
                f"This ${total_amount:.2f} purchase has mixed financial impact. "
            )

        if items_to_remove:
            recommendation += f"Consider removing: {', '.join(items_to_remove[:3])}. "

        # Get budget and goal impact from the first item's decision
        # (assumes budget/goal impact is calculated per-item by the agent)
        budget_impact = None
        goal_impact = []

        if item_decisions:
            first_decision = item_decisions[0].decision
            if first_decision.analysis.budget_analysis:
                budget_impact = first_decision.analysis.budget_analysis
            goal_impact = first_decision.analysis.affected_goals

        return AggregateRecommendation(
            total_amount=total_amount,
            overall_score=overall_score,
            overall_recommendation=recommendation,
            items_to_remove=items_to_remove,
            items_to_keep=items_to_keep,
            budget_impact=budget_impact,
            goal_impact=goal_impact,
        )

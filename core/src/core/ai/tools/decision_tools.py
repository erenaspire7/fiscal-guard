"""Tools for decision analysis agent."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from strands import tool

from core.database.models import Budget, Goal, PurchaseDecision
from core.models.context import UserFinancialContext


class BudgetCheckInput(BaseModel):
    """Input schema for budget check tool."""

    category: str = Field(..., description="Budget category to check")
    amount: float = Field(..., description="Purchase amount to check against budget")


class BudgetCheckOutput(BaseModel):
    """Output schema for budget check tool."""

    category: str
    has_budget: bool
    current_spent: float
    limit: float
    remaining: float
    percentage_used: float
    would_exceed: bool
    impact_description: str


class GoalCheckInput(BaseModel):
    """Input schema for goal check tool."""

    pass


class GoalCheckOutput(BaseModel):
    """Output schema for goal check tool."""

    goals: list[dict]
    total_goals: int
    active_goals: int
    total_target: float
    total_current: float
    total_remaining: float
    impact_description: str


class SpendingAnalysisInput(BaseModel):
    """Input schema for spending analysis tool."""

    pass


class SpendingAnalysisOutput(BaseModel):
    """Output schema for spending analysis tool."""

    total_budget: float
    total_spent: float
    total_remaining: float
    percentage_spent: float
    financial_health_score: float
    analysis_description: str


class PastDecisionsInput(BaseModel):
    """Input schema for past decisions tool."""

    category: Optional[str] = Field(None, description="Category to filter by")
    min_amount: Optional[float] = Field(None, description="Minimum purchase amount")
    max_amount: Optional[float] = Field(None, description="Maximum purchase amount")
    limit: int = Field(10, description="Maximum number of past decisions to return")


class PastDecisionsOutput(BaseModel):
    """Output schema for past decisions tool."""

    decisions: list[dict]
    total_decisions: int
    average_score: float
    category_patterns: dict
    insights: str


class RegretAnalysisInput(BaseModel):
    """Input schema for regret analysis tool."""

    category: Optional[str] = Field(None, description="Category to analyze")


class RegretAnalysisOutput(BaseModel):
    """Output schema for regret analysis tool."""

    total_purchases: int
    purchases_with_feedback: int
    regretted_purchases: int
    regret_rate: float
    average_regret_level: float
    common_regret_patterns: list[str]
    recommendations: str


def _build_budget_impact_description(
    category: str, spent: float, limit: float, amount: float
) -> str:
    """Build a human-readable budget impact description."""
    remaining = limit - spent
    new_spent = spent + amount
    percentage_used = (new_spent / limit * 100) if limit > 0 else 0
    would_exceed = new_spent > limit

    if would_exceed:
        overage = new_spent - limit
        impact = (
            f"This purchase would put you ${overage:.2f} over budget in {category}. "
        )
        impact += (
            f"You've spent ${spent:.2f} of ${limit:.2f}, leaving ${remaining:.2f}. "
        )
        impact += (
            f"After this purchase, you'd be at {percentage_used:.1f}% of your budget."
        )
    elif percentage_used > 80:
        impact = f"This purchase is within budget but would use {percentage_used:.1f}% of your {category} budget. "
        impact += (
            f"You'd have ${limit - new_spent:.2f} remaining for the rest of the period."
        )
    else:
        impact = f"This purchase fits comfortably within your {category} budget. "
        impact += f"You'd be at {percentage_used:.1f}% of budget with ${limit - new_spent:.2f} remaining."

    return impact


def _build_goals_impact_description(
    goals_data: list[dict], total_remaining: float
) -> str:
    """Build a human-readable goals impact description."""
    high_priority_goals = [g for g in goals_data if g["priority"] == "high"]
    if high_priority_goals:
        impact = f"User has {len(high_priority_goals)} high-priority goal(s): "
        impact += ", ".join([g["name"] for g in high_priority_goals[:3]])
        impact += f". Total remaining to reach all goals: ${total_remaining:.2f}. "
        impact += "Consider if this purchase delays progress toward these goals."
    else:
        impact = f"User has {len(goals_data)} active goal(s) with ${total_remaining:.2f} remaining to reach them. "
        impact += "Consider if this money could be better allocated toward goals."
    return impact


def create_decision_tools(
    db_session: Session,
    user_id: str,
    financial_context: Optional[UserFinancialContext] = None,
):
    """Create decision tools with database session and bound user_id.

    The user_id is injected into the tools so it doesn't need to be passed
    by the LLM, preventing PII leakage in prompts.

    If financial_context is provided, tools use pre-fetched data instead of
    querying the database, falling back to DB queries when context is absent.

    Args:
        db_session: Database session
        user_id: User ID to bind to the tools
        financial_context: Pre-fetched financial context (optional)
    """

    # Validate and convert user_id once
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise ValueError(f"Invalid user_id format: {user_id}")

    @tool
    def check_budget(category: str, amount: float) -> dict:
        """Check if a purchase fits within the budget for a specific category.

        Args:
            category: The budget category (e.g., 'groceries', 'entertainment')
            amount: The purchase amount to check

        Returns:
            Budget analysis including current spending, limits, and impact
        """
        category_lower = category.lower()

        # Use pre-fetched context if available
        if financial_context and financial_context.has_budget:
            budget_ctx = financial_context.active_budget

            if category_lower not in budget_ctx.categories:
                return {
                    "category": category,
                    "has_budget": False,
                    "current_spent": 0.0,
                    "limit": 0.0,
                    "remaining": 0.0,
                    "percentage_used": 0.0,
                    "would_exceed": True,
                    "impact_description": f"Category '{category}' not found in budget. User should add this category or use an existing one.",
                }

            cat_data = budget_ctx.categories[category_lower]
            spent = float(cat_data.spent)
            limit = float(cat_data.limit)
            remaining = float(cat_data.remaining)
            new_spent = spent + amount
            percentage_used = (new_spent / limit * 100) if limit > 0 else 0

            return {
                "category": category,
                "has_budget": True,
                "current_spent": spent,
                "limit": limit,
                "remaining": remaining,
                "percentage_used": round(percentage_used, 1),
                "would_exceed": new_spent > limit,
                "impact_description": _build_budget_impact_description(
                    category, spent, limit, amount
                ),
            }

        # Fallback: query DB
        today = date.today()
        budget = (
            db_session.query(Budget)
            .filter(
                Budget.user_id == user_uuid,
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

        if not budget:
            return {
                "category": category,
                "has_budget": False,
                "current_spent": 0.0,
                "limit": 0.0,
                "remaining": 0.0,
                "percentage_used": 0.0,
                "would_exceed": True,
                "impact_description": "No active budget found for user. Cannot verify if purchase fits budget.",
            }

        category_data = budget.categories.get(category_lower)
        if not category_data:
            return {
                "category": category,
                "has_budget": False,
                "current_spent": 0.0,
                "limit": 0.0,
                "remaining": 0.0,
                "percentage_used": 0.0,
                "would_exceed": True,
                "impact_description": f"Category '{category}' not found in budget. User should add this category or use an existing one.",
            }

        limit = float(category_data.get("limit", 0))
        spent = float(category_data.get("spent", 0))
        remaining = limit - spent
        new_spent = spent + amount
        percentage_used = (new_spent / limit * 100) if limit > 0 else 0

        return {
            "category": category,
            "has_budget": True,
            "current_spent": spent,
            "limit": limit,
            "remaining": remaining,
            "percentage_used": round(percentage_used, 1),
            "would_exceed": new_spent > limit,
            "impact_description": _build_budget_impact_description(
                category, spent, limit, amount
            ),
        }

    @tool
    def check_goals() -> dict:
        """Check user's financial goals and how a purchase might impact them.

        Returns:
            Summary of all user goals and their status
        """
        # Use pre-fetched context if available
        if financial_context and financial_context.has_goals:
            goals_data = []
            total_target = 0.0
            total_current = 0.0

            for goal in financial_context.active_goals:
                target = float(goal.target_amount)
                current = float(goal.current_amount)
                remaining = float(goal.remaining)

                total_target += target
                total_current += current

                goals_data.append(
                    {
                        "name": goal.goal_name,
                        "target": target,
                        "current": current,
                        "remaining": remaining,
                        "percentage": round(goal.percentage_complete, 1),
                        "priority": goal.priority,
                        "deadline": goal.deadline.isoformat()
                        if goal.deadline
                        else None,
                    }
                )

            total_remaining = total_target - total_current

            return {
                "goals": goals_data,
                "total_goals": len(goals_data),
                "active_goals": len(goals_data),
                "total_target": round(total_target, 2),
                "total_current": round(total_current, 2),
                "total_remaining": round(total_remaining, 2),
                "impact_description": _build_goals_impact_description(
                    goals_data, total_remaining
                ),
            }

        # Fallback: query DB
        goals = (
            db_session.query(Goal)
            .filter(Goal.user_id == user_uuid, Goal.is_completed == False)
            .order_by(Goal.deadline.asc(), Goal.priority.desc())
            .all()
        )

        if not goals:
            return {
                "goals": [],
                "total_goals": 0,
                "active_goals": 0,
                "total_target": 0.0,
                "total_current": 0.0,
                "total_remaining": 0.0,
                "impact_description": "User has no active financial goals set.",
            }

        goals_data = []
        total_target = 0.0
        total_current = 0.0

        for goal in goals:
            target = float(goal.target_amount)
            current = float(goal.current_amount)
            remaining = target - current
            percentage = (current / target * 100) if target > 0 else 0

            total_target += target
            total_current += current

            goals_data.append(
                {
                    "name": goal.goal_name,
                    "target": target,
                    "current": current,
                    "remaining": remaining,
                    "percentage": round(percentage, 1),
                    "priority": goal.priority,
                    "deadline": goal.deadline.isoformat() if goal.deadline else None,
                }
            )

        total_remaining = total_target - total_current

        return {
            "goals": goals_data,
            "total_goals": len(goals_data),
            "active_goals": len(goals_data),
            "total_target": round(total_target, 2),
            "total_current": round(total_current, 2),
            "total_remaining": round(total_remaining, 2),
            "impact_description": _build_goals_impact_description(
                goals_data, total_remaining
            ),
        }

    @tool
    def analyze_spending() -> dict:
        """Analyze overall spending patterns and financial health.

        Returns:
            Overall financial health analysis
        """
        # Use pre-fetched context if available
        if financial_context and financial_context.has_budget:
            budget_ctx = financial_context.active_budget
            total_budget = float(budget_ctx.total_monthly)
            total_spent = float(budget_ctx.total_spent)
            total_remaining = float(budget_ctx.total_remaining)
            percentage_spent = budget_ctx.percentage_used

            budget_score = max(0, 100 - percentage_spent) * 0.5

            if financial_context.has_goals:
                goal_pcts = [
                    g.percentage_complete for g in financial_context.active_goals
                ]
                avg_goal_progress = sum(goal_pcts) / len(goal_pcts)
                goal_score = avg_goal_progress * 0.3
            else:
                goal_score = 15

            remaining_score = (
                min(
                    100,
                    (total_remaining / total_budget * 100) if total_budget > 0 else 0,
                )
                * 0.2
            )
            financial_health_score = budget_score + goal_score + remaining_score

            if percentage_spent < 50:
                health_status = "excellent"
            elif percentage_spent < 75:
                health_status = "good"
            elif percentage_spent < 90:
                health_status = "fair"
            else:
                health_status = "concerning"

            description = f"Financial health is {health_status}. "
            description += f"You've spent ${total_spent:.2f} of ${total_budget:.2f} ({percentage_spent:.1f}%) this period. "
            description += f"${total_remaining:.2f} remaining. "

            if percentage_spent > 80:
                description += "You're using most of your budget, so be cautious with additional purchases."
            elif percentage_spent < 50:
                description += "You have plenty of budget flexibility."

            return {
                "total_budget": round(total_budget, 2),
                "total_spent": round(total_spent, 2),
                "total_remaining": round(total_remaining, 2),
                "percentage_spent": round(percentage_spent, 1),
                "financial_health_score": round(financial_health_score, 1),
                "analysis_description": description,
            }

        # Fallback: query DB
        today = date.today()
        budget = (
            db_session.query(Budget)
            .filter(
                Budget.user_id == user_uuid,
                Budget.period_start <= today,
                Budget.period_end >= today,
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

        if not budget:
            return {
                "total_budget": 0.0,
                "total_spent": 0.0,
                "total_remaining": 0.0,
                "percentage_spent": 0.0,
                "financial_health_score": 50.0,
                "analysis_description": "No active budget found. Cannot analyze spending patterns.",
            }

        total_budget = float(budget.total_monthly)
        total_spent = sum(
            float(cat.get("spent", 0)) for cat in budget.categories.values()
        )
        total_remaining = total_budget - total_spent
        percentage_spent = (total_spent / total_budget * 100) if total_budget > 0 else 0

        budget_score = max(0, 100 - percentage_spent) * 0.5

        goals = (
            db_session.query(Goal)
            .filter(Goal.user_id == user_uuid, Goal.is_completed == False)
            .all()
        )

        if goals:
            goal_percentages = [
                (float(g.current_amount) / float(g.target_amount) * 100)
                if float(g.target_amount) > 0
                else 0
                for g in goals
            ]
            avg_goal_progress = sum(goal_percentages) / len(goal_percentages)
            goal_score = avg_goal_progress * 0.3
        else:
            goal_score = 15

        remaining_score = min(100, (total_remaining / total_budget * 100)) * 0.2
        financial_health_score = budget_score + goal_score + remaining_score

        if percentage_spent < 50:
            health_status = "excellent"
        elif percentage_spent < 75:
            health_status = "good"
        elif percentage_spent < 90:
            health_status = "fair"
        else:
            health_status = "concerning"

        description = f"Financial health is {health_status}. "
        description += f"You've spent ${total_spent:.2f} of ${total_budget:.2f} ({percentage_spent:.1f}%) this period. "
        description += f"${total_remaining:.2f} remaining. "

        if percentage_spent > 80:
            description += "You're using most of your budget, so be cautious with additional purchases."
        elif percentage_spent < 50:
            description += "You have plenty of budget flexibility."

        return {
            "total_budget": round(total_budget, 2),
            "total_spent": round(total_spent, 2),
            "total_remaining": round(total_remaining, 2),
            "percentage_spent": round(percentage_spent, 1),
            "financial_health_score": round(financial_health_score, 1),
            "analysis_description": description,
        }

    @tool
    def check_past_decisions(
        category: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 10,
    ) -> dict:
        """Check user's past purchase decisions for patterns and learning.

        Args:
            category: Optional category to filter by
            min_amount: Optional minimum amount filter
            max_amount: Optional maximum amount filter
            limit: Maximum number of decisions to return

        Returns:
            Past decisions with patterns and insights
        """
        query = db_session.query(PurchaseDecision).filter(
            PurchaseDecision.user_id == user_uuid
        )

        if category:
            query = query.filter(PurchaseDecision.category == category.lower())

        if min_amount is not None:
            query = query.filter(PurchaseDecision.amount >= min_amount)

        if max_amount is not None:
            query = query.filter(PurchaseDecision.amount <= max_amount)

        decisions = (
            query.order_by(PurchaseDecision.created_at.desc()).limit(limit).all()
        )

        if not decisions:
            return {
                "decisions": [],
                "total_decisions": 0,
                "average_score": 0.0,
                "category_patterns": {},
                "insights": "No past decisions found matching criteria.",
            }

        decisions_data = []
        total_score = 0
        category_counts = {}
        category_scores = {}

        for d in decisions:
            decisions_data.append(
                {
                    "item": d.item_name,
                    "amount": float(d.amount),
                    "category": d.category,
                    "score": d.score,
                    "decision": d.decision_category,
                    "purchased": d.actual_purchase,
                    "regret": d.regret_level,
                    "date": d.created_at.isoformat() if d.created_at else None,
                }
            )

            total_score += d.score

            cat = d.category or "uncategorized"
            category_counts[cat] = category_counts.get(cat, 0) + 1
            if cat not in category_scores:
                category_scores[cat] = []
            category_scores[cat].append(d.score)

        avg_score = total_score / len(decisions)

        insights_parts = []

        if category_counts:
            most_common_cat = max(category_counts, key=category_counts.get)
            insights_parts.append(
                f"Most frequently considered: {most_common_cat} ({category_counts[most_common_cat]} times)"
            )

        if category_scores:
            for cat, scores in category_scores.items():
                avg_cat_score = sum(scores) / len(scores)
                if avg_cat_score < 5:
                    insights_parts.append(
                        f"Historically low scores for {cat} purchases (avg {avg_cat_score:.1f}/10)"
                    )
                elif avg_cat_score > 7:
                    insights_parts.append(
                        f"Historically good scores for {cat} purchases (avg {avg_cat_score:.1f}/10)"
                    )

        with_feedback = [d for d in decisions if d.actual_purchase is not None]
        if with_feedback:
            purchased = [d for d in with_feedback if d.actual_purchase]
            regretted = [d for d in purchased if d.regret_level and d.regret_level >= 6]
            if regretted:
                insights_parts.append(
                    f"Warning: {len(regretted)} past purchases had regret levels ≥6"
                )

        insights = (
            ". ".join(insights_parts) if insights_parts else "No clear patterns yet."
        )

        return {
            "decisions": decisions_data,
            "total_decisions": len(decisions),
            "average_score": round(avg_score, 1),
            "category_patterns": category_counts,
            "insights": insights,
        }

    @tool
    def analyze_regrets(category: Optional[str] = None) -> dict:
        """Analyze user's purchase regrets to identify patterns.

        Args:
            category: Optional category to filter analysis

        Returns:
            Regret analysis with patterns and recommendations
        """
        query = db_session.query(PurchaseDecision).filter(
            PurchaseDecision.user_id == user_uuid
        )

        if category:
            query = query.filter(PurchaseDecision.category == category.lower())

        all_decisions = query.all()

        if not all_decisions:
            return {
                "total_purchases": 0,
                "purchases_with_feedback": 0,
                "regretted_purchases": 0,
                "regret_rate": 0.0,
                "average_regret_level": 0.0,
                "common_regret_patterns": [],
                "recommendations": "No purchase history found.",
            }

        with_feedback = [d for d in all_decisions if d.actual_purchase is not None]
        purchased = [d for d in with_feedback if d.actual_purchase]
        regretted = [d for d in purchased if d.regret_level and d.regret_level >= 6]

        regret_rate = (len(regretted) / len(purchased) * 100) if purchased else 0

        regret_levels = [d.regret_level for d in purchased if d.regret_level]
        avg_regret = sum(regret_levels) / len(regret_levels) if regret_levels else 0

        patterns = []

        if regretted:
            regret_categories = {}
            for d in regretted:
                cat = d.category or "uncategorized"
                regret_categories[cat] = regret_categories.get(cat, 0) + 1

            if regret_categories:
                most_regretted = max(regret_categories, key=regret_categories.get)
                patterns.append(f"Most regrets in {most_regretted} category")

            high_amount_regrets = [d for d in regretted if float(d.amount) > 100]
            if len(high_amount_regrets) > len(regretted) * 0.6:
                patterns.append("Tend to regret expensive purchases (>$100)")

            ignored_warnings = [d for d in regretted if d.score <= 5]
            if ignored_warnings:
                patterns.append(
                    f"Ignored {len(ignored_warnings)} low-score recommendations and regretted it"
                )

        if not purchased:
            recommendations = (
                "No purchase feedback yet. Add feedback to learn patterns."
            )
        elif not regretted:
            recommendations = "Great job! No significant regrets so far. Keep following recommendations."
        else:
            rec_parts = []
            if regret_rate > 30:
                rec_parts.append("High regret rate detected")
            if patterns:
                rec_parts.append(f"Pay attention to: {', '.join(patterns[:2])}")
            if any("ignored" in p.lower() for p in patterns):
                rec_parts.append("Consider following low-score warnings more carefully")

            recommendations = (
                ". ".join(rec_parts) if rec_parts else "Review patterns above"
            )

        return {
            "total_purchases": len(all_decisions),
            "purchases_with_feedback": len(with_feedback),
            "regretted_purchases": len(regretted),
            "regret_rate": round(regret_rate, 1),
            "average_regret_level": round(avg_regret, 1),
            "common_regret_patterns": patterns,
            "recommendations": recommendations,
        }

    @tool
    def save_purchase_decision(
        item_name: str,
        amount: float,
        category: str,
        score: int,
        decision_category: str,
        reasoning: str,
        reason: Optional[str] = None,
        urgency: Optional[str] = None,
        alternatives: Optional[list[str]] = None,
        conditions: Optional[list[str]] = None,
    ) -> dict:
        """Save a purchase decision to the database after analyzing it.

        IMPORTANT: Call this function AFTER you've analyzed the purchase and determined the score.
        This persists the decision so the user can reference it later (e.g., "I bought that item").

        Args:
            item_name: Name of the item being considered
            amount: Purchase amount in dollars
            category: Budget category (groceries, dining, shopping, entertainment, transport, etc.)
            score: Decision score from 1-10 (1=strong no, 10=strong yes)
            decision_category: Classification (strong_no, mild_no, neutral, mild_yes, strong_yes)
            reasoning: Your reasoning for the score
            reason: User's reason for wanting to buy (optional)
            urgency: Purchase urgency level (low, medium, high) (optional)
            alternatives: List of alternative suggestions (optional)
            conditions: List of conditions under which purchase makes sense (optional)

        Returns:
            Confirmation with decision_id for future reference
        """
        # Build analysis dict from current financial context
        analysis = {}

        # Add budget analysis if available
        budget_result = check_budget(category, amount)
        if budget_result.get("has_budget"):
            analysis["budget_analysis"] = {
                "category": category,
                "current_spent": budget_result["current_spent"],
                "limit": budget_result["limit"],
                "remaining": budget_result["remaining"],
                "percentage_used": budget_result["percentage_used"],
                "would_exceed": budget_result["would_exceed"],
                "impact_description": budget_result["impact_description"],
            }

        # Add goals analysis if available
        goals_result = check_goals()
        if goals_result.get("total_goals", 0) > 0:
            analysis["affected_goals"] = [
                {
                    "goal_name": g["name"],
                    "target_amount": g["target_amount"],
                    "current_amount": g["current_amount"],
                    "remaining": g["remaining"],
                    "deadline": g["deadline"],
                    "impact_description": f"${amount} represents {(amount / g['remaining'] * 100):.1f}% of remaining goal",
                }
                for g in goals_result.get("goals", [])
                if g["remaining"] > 0
            ]

        # Add financial health
        spending_result = analyze_spending()
        analysis["financial_health_score"] = spending_result.get(
            "financial_health_score", 50
        )

        # Determine purchase category
        if urgency == "high" or category in ["groceries", "transport"]:
            purchase_category = "essential"
        elif score >= 7:
            purchase_category = "investment"
        elif score <= 4:
            purchase_category = "impulse"
        else:
            purchase_category = "discretionary"

        analysis["purchase_category"] = purchase_category

        # Create decision record
        decision = PurchaseDecision(
            decision_id=uuid4(),
            user_id=user_uuid,
            item_name=item_name,
            amount=Decimal(str(amount)),
            category=category.lower(),
            reason=reason or "User inquiry",
            urgency=urgency or "medium",
            score=score,
            decision_category=decision_category,
            reasoning=reasoning,
            analysis=analysis,
            alternatives=alternatives or [],
            conditions=conditions or [],
            actual_purchase=None,  # Will be set when user provides feedback
            regret_level=None,
            user_feedback=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db_session.add(decision)
        db_session.commit()
        db_session.refresh(decision)

        return {
            "success": True,
            "decision_id": str(decision.decision_id),
            "item_name": item_name,
            "amount": amount,
            "score": score,
            "decision_category": decision_category,
            "message": f"Decision saved with ID: {decision.decision_id}",
        }

    return [
        check_budget,
        check_goals,
        analyze_spending,
        check_past_decisions,
        analyze_regrets,
        save_purchase_decision,
    ]

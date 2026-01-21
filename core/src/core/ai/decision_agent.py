"""AI-powered purchase decision agent using Strands."""

import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.ai.decision_tools import create_decision_tools
from core.config import settings
from core.models.decision import (
    BudgetAnalysis,
    DecisionAnalysis,
    DecisionScore,
    GoalAnalysis,
    PurchaseCategory,
    PurchaseDecision,
    PurchaseDecisionRequest,
)
from core.observability.opik_config import opik_config, track_decision


class DecisionAgent:
    """Handle purchase decision analysis using Strands AI with tools."""

    def __init__(self, db_session: Session):
        """Initialize decision agent.

        Args:
            db_session: SQLAlchemy database session for tool access
        """
        self.db_session = db_session

        # Initialize Gemini model
        model = GeminiModel(
            client_args={
                "api_key": settings.google_api_key,
            },
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.7,
                "max_output_tokens": 4096,
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        # Create decision tools with database session
        tools = create_decision_tools(db_session)

        # Initialize Agent with model and tools
        self.agent = Agent(model=model, tools=tools)

        self.system_prompt = """You are an expert financial advisor helping users make smart purchase decisions.

Your role:
1. Use the available tools to analyze the purchase comprehensively:
   - check_budget: Verify budget impact for the category
   - check_goals: See how this affects financial goals
   - analyze_spending: Overall financial health assessment
   - check_past_decisions: Learn from user's purchase history
   - analyze_regrets: Identify patterns in past regrets

2. Analyze the purchase request comprehensively
3. Provide a decision score from 1-10 where:
   - 1-3: Strong No (would significantly harm financial health)
   - 4-5: Mild No (not recommended but not catastrophic)
   - 6: Neutral (neither good nor bad)
   - 7-8: Mild Yes (reasonable purchase)
   - 9-10: Strong Yes (excellent decision)

4. Categorize the purchase type: essential, discretionary, investment, or impulse

5. Provide detailed reasoning that considers:
   - Budget impact (will it exceed category limits?)
   - Goal impact (will it delay financial goals?)
   - Overall financial health
   - User's past behavior and patterns
   - Regret patterns from similar purchases
   - Value vs cost
   - Urgency and necessity
   - Alternatives

6. Suggest alternatives when appropriate
7. Provide conditions under which this purchase might make more sense
8. Reference past patterns when relevant (e.g., "You've regretted similar purchases before")

IMPORTANT: You must respond ONLY with valid JSON in this exact format:
{
    "score": 7,
    "decision_category": "mild_yes",
    "reasoning": "Detailed explanation of your decision...",
    "purchase_category": "discretionary",
    "financial_health_score": 75.5,
    "budget_analysis": {
        "category": "groceries",
        "current_spent": 250.00,
        "limit": 500.00,
        "remaining": 250.00,
        "percentage_used": 50.0,
        "would_exceed": false,
        "impact_description": "This fits within budget..."
    },
    "affected_goals": [
        {
            "goal_name": "Emergency Fund",
            "target_amount": 5000.00,
            "current_amount": 2000.00,
            "remaining": 3000.00,
            "deadline": "2026-12-31T00:00:00",
            "impact_description": "This purchase might slightly delay reaching this goal..."
        }
    ],
    "alternatives": ["Wait until next pay period", "Consider a cheaper option"],
    "conditions": ["If this is urgent", "If you can cut spending elsewhere"]
}

Be honest, practical, and empathetic. Consider the user's context and help them make decisions that align with their financial goals."""

    @track_decision(name="analyze_purchase")
    def analyze_purchase(
        self, user_id: UUID, request: PurchaseDecisionRequest
    ) -> PurchaseDecision:
        """Analyze a purchase decision request.

        Args:
            user_id: The user making the purchase request
            request: Purchase decision request details

        Returns:
            Purchase decision with score and reasoning
        """
        # Create trace metadata with PII redaction
        metadata = opik_config.create_trace_metadata(
            user_id=str(user_id),
            category=request.category,
            amount=float(request.amount),
            item_type=request.item_name[:50],  # Truncate for privacy
            urgency=request.urgency,
        )
        # Build the prompt with purchase details
        prompt = f"""{self.system_prompt}

PURCHASE REQUEST:
User ID: {str(user_id)}
Item: {request.item_name}
Amount: ${request.amount}
Category: {request.category or "unspecified"}
Reason: {request.reason or "not provided"}
Urgency: {request.urgency or "not specified"}

INSTRUCTIONS:
1. Use check_budget tool to analyze budget impact for the category
2. Use check_goals tool to see how this affects the user's financial goals
3. Use analyze_spending tool to understand overall financial health
4. Use check_past_decisions tool to see if user has made similar purchases (filter by category and amount range)
5. Use analyze_regrets tool to check if user has regret patterns in this category
6. Based on all tool results and patterns, make your decision
7. Reference past behavior in your reasoning if patterns are found
8. Respond with ONLY the JSON decision format (no other text)

Make your decision now:"""

        # Call the agent (it will use tools automatically)
        response = self.agent(prompt)
        response_text = str(response)

        # Parse the JSON response
        try:
            # Try to extract JSON if there's extra text
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)

            # Map score to decision category if not provided
            score = data["score"]
            if "decision_category" not in data:
                if score <= 3:
                    decision_category = DecisionScore.STRONG_NO
                elif score <= 5:
                    decision_category = DecisionScore.MILD_NO
                elif score == 6:
                    decision_category = DecisionScore.NEUTRAL
                elif score <= 8:
                    decision_category = DecisionScore.MILD_YES
                else:
                    decision_category = DecisionScore.STRONG_YES
            else:
                decision_category = DecisionScore(data["decision_category"])

            # Parse budget analysis if present
            budget_analysis = None
            if "budget_analysis" in data and data["budget_analysis"]:
                ba = data["budget_analysis"]
                budget_analysis = BudgetAnalysis(
                    category=ba.get("category"),
                    current_spent=Decimal(str(ba.get("current_spent", 0))),
                    limit=Decimal(str(ba.get("limit", 0))),
                    remaining=Decimal(str(ba.get("remaining", 0))),
                    percentage_used=float(ba.get("percentage_used", 0)),
                    would_exceed=bool(ba.get("would_exceed", False)),
                    impact_description=ba.get("impact_description", ""),
                )

            # Parse affected goals
            affected_goals = []
            if "affected_goals" in data:
                for goal_data in data["affected_goals"]:
                    goal = GoalAnalysis(
                        goal_name=goal_data["goal_name"],
                        target_amount=Decimal(str(goal_data["target_amount"])),
                        current_amount=Decimal(str(goal_data["current_amount"])),
                        remaining=Decimal(str(goal_data["remaining"])),
                        deadline=goal_data.get("deadline"),
                        impact_description=goal_data.get("impact_description", ""),
                    )
                    affected_goals.append(goal)

            # Build analysis
            analysis = DecisionAnalysis(
                budget_analysis=budget_analysis,
                affected_goals=affected_goals,
                purchase_category=PurchaseCategory(
                    data.get("purchase_category", "discretionary")
                ),
                financial_health_score=float(data.get("financial_health_score", 50.0)),
            )

            # Build decision
            decision = PurchaseDecision(
                score=score,
                decision_category=decision_category,
                reasoning=data["reasoning"],
                analysis=analysis,
                alternatives=data.get("alternatives"),
                conditions=data.get("conditions"),
            )

            return decision

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # Fallback if parsing fails
            return PurchaseDecision(
                score=5,
                decision_category=DecisionScore.NEUTRAL,
                reasoning=f"Unable to analyze purchase properly. Agent response: {response_text[:500]}",
                analysis=DecisionAnalysis(
                    purchase_category=PurchaseCategory.DISCRETIONARY,
                    financial_health_score=50.0,
                ),
                alternatives=["Try again with more details"],
                conditions=None,
            )

"""AI-powered purchase decision agent using Strands."""

from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.ai.decision_tools import create_decision_tools
from core.config import settings
from core.database.models import User
from core.models.decision import (
    BudgetAnalysis,
    DecisionAnalysis,
    DecisionScore,
    GoalAnalysis,
    PurchaseCategory,
    PurchaseDecision,
    PurchaseDecisionRequest,
)
from core.observability.pii_redaction import create_trace_attributes


class StructuredPurchaseDecision(BaseModel):
    """Structured output model for purchase decisions.

    This is used by Strands to enforce structured outputs from the LLM.
    """

    score: int = Field(..., description="Decision score from 1-10", ge=1, le=10)
    decision_category: str = Field(
        ...,
        description="Decision category: strong_no, mild_no, neutral, mild_yes, or strong_yes",
    )
    reasoning: str = Field(
        ...,
        description="Detailed reasoning for the decision, referencing budget, goals, and patterns",
    )
    purchase_category: str = Field(
        ...,
        description="Category of purchase: essential, discretionary, investment, or impulse",
    )
    financial_health_score: float = Field(
        ..., description="Overall financial health score (0-100)", ge=0, le=100
    )

    # Budget analysis
    budget_category: Optional[str] = Field(None, description="Budget category")
    budget_current_spent: Optional[float] = Field(None, description="Current spending")
    budget_limit: Optional[float] = Field(None, description="Category limit")
    budget_remaining: Optional[float] = Field(None, description="Remaining budget")
    budget_percentage_used: Optional[float] = Field(None, description="Percentage used")
    budget_would_exceed: Optional[bool] = Field(None, description="Would exceed limit")
    budget_impact: Optional[str] = Field(None, description="Budget impact description")

    # Goals (simplified for structured output)
    affected_goal_names: list[str] = Field(
        default_factory=list, description="Names of affected goals"
    )
    goal_impact_description: Optional[str] = Field(
        None, description="Overall impact on financial goals"
    )

    # Recommendations
    alternatives: list[str] = Field(
        default_factory=list, description="Alternative suggestions"
    )
    conditions: list[str] = Field(
        default_factory=list, description="Conditions under which this might be better"
    )


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

        # Store for per-request agent creation
        self.model = model
        self.tools = tools

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
   - 1-3: Strong No (strong_no) - would significantly harm financial health
   - 4-5: Mild No (mild_no) - not recommended but not catastrophic
   - 6: Neutral (neutral) - neither good nor bad
   - 7-8: Mild Yes (mild_yes) - reasonable purchase
   - 9-10: Strong Yes (strong_yes) - excellent decision

4. Categorize the purchase type:
   - essential: Necessary for basic needs
   - discretionary: Nice to have but not necessary
   - investment: Will provide future value
   - impulse: Emotional or unplanned purchase

5. Provide detailed reasoning that considers:
   - Budget impact (will it exceed category limits?)
   - Goal impact (will it delay financial goals?)
   - Overall financial health
   - User's past behavior and patterns
   - Regret patterns from similar purchases
   - Value vs cost
   - Urgency and necessity

6. Suggest alternatives when appropriate

7. Provide conditions under which this purchase might make more sense

8. Reference past patterns when relevant (e.g., "You've regretted similar purchases before")

Be honest, practical, and empathetic. Consider the user's context and help them make decisions that align with their financial goals."""

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
        # Fetch user persona and strictness
        user = self.db_session.query(User).filter(User.user_id == user_id).first()
        persona = user.persona_tone if user and user.persona_tone else "balanced"
        strictness = (
            user.strictness_level if user and user.strictness_level is not None else 5
        )

        # Generate a unique session ID for this decision
        session_id = str(uuid4())

        # Create trace attributes with PII redaction
        # This is passed to the Agent and automatically sent to Opik via OpenTelemetry
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),  # Will be redacted to "[USER_REDACTED]"
            session_id=session_id,
            category=request.category,
            amount=float(request.amount),
            item_type=request.item_name[:50],  # Truncate for privacy
            urgency=request.urgency,
        )
        # Add persona info to trace for evaluation purposes
        trace_attributes["user.persona"] = persona
        trace_attributes["user.strictness"] = strictness

        # Customize instructions based on persona and strictness
        custom_instructions = f"\n\nUSER PREFERENCES:\n- Persona: {persona}\n- Strictness Level: {strictness}/10\n"

        if persona == "financial_monk":
            custom_instructions += "ADVICE STYLE: You are a Financial Monk. Be extremely frugal, ascetic, and prioritize savings above all else. Use a disciplined, minimalist tone.\n"
        elif persona == "gentle":
            custom_instructions += "ADVICE STYLE: You are a Gentle Guide. Be empathetic, encouraging, and focus on mindful balance. Avoid harsh judgment.\n"
        else:
            custom_instructions += (
                "ADVICE STYLE: Be a balanced, objective financial advisor.\n"
            )

        custom_instructions += (
            f"STRICTNESS: On a scale of 1-10, your strictness is {strictness}. "
        )
        if strictness >= 8:
            custom_instructions += (
                "Be very firm and hold a high bar for any discretionary spending."
            )
        elif strictness <= 3:
            custom_instructions += "Be more flexible and prioritize the user's immediate happiness more than usual."

        # Create agent for this request with trace attributes and structured output
        # OpenTelemetry will automatically trace all interactions
        agent = Agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt + custom_instructions,
            structured_output_model=StructuredPurchaseDecision,  # Enforce structured output!
            trace_attributes=trace_attributes,
        )

        # Build the prompt with purchase details
        prompt = f"""Analyze this purchase decision:

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
4. Use check_past_decisions tool to see if user has made similar purchases
5. Use analyze_regrets tool to check if user has regret patterns in this category
6. Based on all tool results and patterns, provide your decision
7. Reference past behavior in your reasoning if patterns are found
8. REMEMBER: You must act as a {persona} advisor with a strictness of {strictness}/10.

Provide your complete analysis with a decision score, reasoning, and recommendations."""

        # Call the agent (it will use tools automatically)
        # The response will be an AgentResult with JSON string output
        # OpenTelemetry will trace:
        # - The agent invocation
        # - All tool calls (check_budget, check_goals, etc.)
        # - The model calls
        # - Token usage, latency, etc.
        response = agent(prompt)

        # Extract the JSON output from AgentResult
        # The agent returns JSON as a string in response.output
        import json

        if hasattr(response, "output"):
            json_str = response.output
        else:
            # Fallback: convert response to string
            json_str = str(response)

        # Parse JSON string into StructuredPurchaseDecision model
        json_data = json.loads(json_str)
        structured_response = StructuredPurchaseDecision(**json_data)

        # Convert structured response to our domain model
        return self._convert_to_purchase_decision(structured_response)

    def _convert_to_purchase_decision(
        self, structured: StructuredPurchaseDecision
    ) -> PurchaseDecision:
        """Convert structured output to PurchaseDecision domain model.

        Args:
            structured: Structured output from the agent

        Returns:
            PurchaseDecision domain model
        """
        # Map score to decision category
        score = structured.score
        try:
            decision_category = DecisionScore(structured.decision_category)
        except ValueError:
            # Fallback to score-based mapping if invalid category
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

        # Build budget analysis if available
        budget_analysis = None
        if structured.budget_category and structured.budget_limit is not None:
            budget_analysis = BudgetAnalysis(
                category=structured.budget_category,
                current_spent=Decimal(str(structured.budget_current_spent or 0)),
                limit=Decimal(str(structured.budget_limit)),
                remaining=Decimal(str(structured.budget_remaining or 0)),
                percentage_used=float(structured.budget_percentage_used or 0),
                would_exceed=bool(structured.budget_would_exceed or False),
                impact_description=structured.budget_impact or "",
            )

        # Build goal analysis (simplified - we don't have full goal details in structured output)
        affected_goals = []
        if structured.affected_goal_names:
            # For now, we just track the names
            # Full goal details would require querying the database
            # Or we could enhance the structured output to include more details
            pass

        # Parse purchase category
        try:
            purchase_category = PurchaseCategory(structured.purchase_category)
        except ValueError:
            purchase_category = PurchaseCategory.DISCRETIONARY

        # Build analysis
        analysis = DecisionAnalysis(
            budget_analysis=budget_analysis,
            affected_goals=affected_goals,
            purchase_category=purchase_category,
            financial_health_score=float(structured.financial_health_score),
        )

        # Build decision
        decision = PurchaseDecision(
            score=structured.score,
            decision_category=decision_category,
            reasoning=structured.reasoning,
            analysis=analysis,
            alternatives=structured.alternatives if structured.alternatives else None,
            conditions=structured.conditions if structured.conditions else None,
        )

        return decision

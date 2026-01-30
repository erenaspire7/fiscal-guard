"""AI-powered purchase decision agent using Strands."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.ai.tools.decision_tools import create_decision_tools
from core.config import settings
from core.database.models import User
from core.models.decision import (
    BudgetAnalysis,
    BudgetCategory,
    DecisionAnalysis,
    DecisionScore,
    GoalAnalysis,
    PurchaseCategory,
    PurchaseDecision,
    PurchaseDecisionRequest,
)
from core.observability.pii_redaction import create_trace_attributes


class ExtractedPurchaseInfo(BaseModel):
    """Extracted information from natural language purchase request."""

    item_name: str = Field(..., description="Name of the item the user wants to buy")
    amount: float = Field(
        ..., description="Estimated or explicit purchase amount in dollars"
    )
    category: Optional[str] = Field(
        None,
        description="Budget category: shopping, dining, entertainment, groceries, transport, or general",
    )
    urgency: Optional[str] = Field(
        None, description="Urgency level (urgent, normal, can_wait)"
    )
    reason: Optional[str] = Field(
        None, description="User's reason for wanting to buy this"
    )


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
        description="Detailed reasoning for the decision, referencing budget, goals, patterns, and opportunity costs",
    )
    purchase_category: str = Field(
        ...,
        description="Category of purchase: essential, discretionary, investment, or impulse",
    )
    financial_health_score: float = Field(
        ..., description="Overall financial health score (0-100)", ge=0, le=100
    )

    # Opportunity cost analysis
    opportunity_cost_description: str = Field(
        ...,
        description="Clear explanation of what the user is giving up by making this purchase. What else could this money be used for? What goals or alternatives are being sacrificed?",
    )
    opportunity_cost_examples: list[str] = Field(
        default_factory=list,
        description="Concrete examples of alternative uses for this money (e.g., '3 weeks of groceries', 'half your monthly savings goal', '2 months closer to vacation fund')",
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

        # Store for per-request agent creation
        self.model = model
        # Tools will be created per-request with user context

        self.system_prompt = """You are an expert financial advisor helping users make smart purchase decisions through opportunity cost thinking.

Your role:
1. Use the available tools to analyze the purchase comprehensively:
   - check_budget: Verify budget impact for the category
   - check_goals: See how this affects financial goals
   - analyze_spending: Overall financial health assessment
   - check_past_decisions: Learn from user's purchase history
   - analyze_regrets: Identify patterns in past regrets

2. ALWAYS perform opportunity cost analysis - this is critical:
   - What is the user giving up by spending this money?
   - What financial goals will be delayed or sacrificed?
   - What alternative uses would provide more value?
   - Frame the cost in relatable terms (e.g., "This equals X days of groceries" or "This delays your vacation goal by Y weeks")

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

5. Provide concise reasoning (keep it short and punchy) that considers:
   - OPPORTUNITY COST (what are they giving up?)
   - Budget impact (will it exceed category limits?)
   - Goal impact (will it delay financial goals?)
   - Overall financial health
   - User's past behavior and patterns
   - Regret patterns from similar purchases
   - Value vs cost
   - Urgency and necessity

6. Provide concrete opportunity cost examples:
   - Convert the purchase amount into relatable alternatives
   - Reference specific goals from their profile when available
   - Use tangible comparisons (meals, days of work, progress toward savings goals)

7. Suggest alternatives when appropriate

8. Provide conditions under which this purchase might make more sense

9. Reference past patterns when relevant (e.g., "You've regretted similar purchases before")

Be honest, practical, and empathetic. Help users understand the true cost of their decisions by making opportunity costs explicit and relatable.

CRITICAL: Keep your reasoning and analysis extremely concise. Avoid fluff. Get straight to the point. ALWAYS include opportunity cost analysis."""

    def _extract_purchase_info(self, user_message: str) -> ExtractedPurchaseInfo:
        """Extract structured purchase information from natural language.

        Args:
            user_message: Natural language purchase request from user

        Returns:
            Extracted purchase information
        """
        # Create a simple extraction agent
        extraction_agent = Agent(
            model=self.model,
            system_prompt="""You are a helpful assistant that extracts purchase information from natural language.

Extract the following from the user's message:
- item_name: What they want to buy
- amount: How much it costs (if mentioned, otherwise estimate based on the item)
- category: Budget category - must be one of: shopping, dining, entertainment, groceries, transport, general
  * shopping: clothes, electronics, home goods, furniture, etc.
  * dining: restaurants, takeout, food delivery
  * entertainment: movies, games, concerts, subscriptions
  * groceries: supermarket shopping, food ingredients
  * transport: gas, car maintenance, uber, public transit
  * general: anything that doesn't fit the above
- urgency: How urgent is it (urgent, normal, can_wait)
- reason: Why they want to buy it (infer from context if not explicitly stated)

If amount is not mentioned, provide a reasonable estimate based on typical prices.""",
            structured_output_model=ExtractedPurchaseInfo,
        )

        try:
            response = extraction_agent(f"Extract purchase info from: {user_message}")

            # Parse the response
            import json

            json_str = response.output if hasattr(response, "output") else str(response)
            json_data = json.loads(json_str)
            return ExtractedPurchaseInfo(**json_data)
        except Exception as e:
            # If extraction fails (e.g., "I bought it" without context), return minimal info
            # This will cause the main flow to ask for clarification
            return ExtractedPurchaseInfo(
                item_name="Unknown",
                amount=0.0,
                category="general",
                urgency="normal",
                reason=user_message,
            )

    def analyze_purchase(
        self, user_id: UUID, request: PurchaseDecisionRequest
    ) -> tuple[PurchaseDecision, Optional[str], Optional[UUID]]:
        """Analyze a purchase decision request.

        Args:
            user_id: The user making the purchase request
            request: Purchase decision request details

        Returns:
            Purchase decision with score and reasoning
        """
        # If user_message is provided, extract structured info from it
        if request.user_message:
            extracted = self._extract_purchase_info(request.user_message)
            # Update request with extracted info (only if not already provided)
            if not request.item_name:
                request.item_name = extracted.item_name
            if not request.amount:
                request.amount = Decimal(str(extracted.amount))
            if not request.category and extracted.category:
                # Convert string to BudgetCategory enum
                try:
                    request.category = BudgetCategory(extracted.category.lower())
                except ValueError:
                    # Default to general if invalid category
                    request.category = BudgetCategory.GENERAL
            if not request.urgency:
                request.urgency = extracted.urgency
            if not request.reason:
                request.reason = extracted.reason or request.user_message
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

        # Create tools bound to this user
        # This prevents the need to pass user_id in the prompt (PII protection)
        tools = create_decision_tools(self.db_session, str(user_id))

        # Create agent for this request with trace attributes and structured output
        # OpenTelemetry will automatically trace all interactions
        agent = Agent(
            model=self.model,
            tools=tools,
            system_prompt=self.system_prompt + custom_instructions,
            structured_output_model=StructuredPurchaseDecision,  # Enforce structured output!
            trace_attributes=trace_attributes,
        )

        # Build the prompt with purchase details
        prompt = f"""Analyze this purchase decision:

PURCHASE REQUEST:
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
6. CRITICAL - Perform opportunity cost analysis:
   - Based on the user's goals, budget, and spending patterns, what are they giving up?
   - Provide concrete, relatable examples (e.g., "This equals 2 weeks of your grocery budget")
   - Show how this impacts progress toward their specific goals
   - Frame the tradeoff clearly: "This purchase means X instead of Y"
7. Based on all tool results, patterns, AND opportunity costs, provide your decision
8. Reference past behavior in your reasoning if patterns are found
9. REMEMBER: You must act as a {persona} advisor with a strictness of {strictness}/10.

Provide your complete analysis with a decision score, reasoning, opportunity cost analysis, and recommendations."""

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

        # Check if we need clarification about a similar recent purchase
        clarification_question = None
        related_decision_id = None

        if not request.is_follow_up and request.item_name:
            # Query recent decisions directly
            from datetime import timedelta

            from core.database.models import PurchaseDecision as PurchaseDecisionDB

            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)

            # Find recent decisions with similar item names
            recent_decisions = (
                self.db_session.query(PurchaseDecisionDB)
                .filter(
                    PurchaseDecisionDB.user_id == user_id,
                    PurchaseDecisionDB.created_at > twenty_four_hours_ago,
                )
                .order_by(PurchaseDecisionDB.created_at.desc())
                .limit(10)
                .all()
            )

            # Check for similar item names
            for past_decision in recent_decisions:
                # Simple similarity check - if the new item name contains the old one or vice versa
                item_lower = request.item_name.lower()
                past_item_lower = past_decision.item_name.lower()

                if (
                    item_lower in past_item_lower or past_item_lower in item_lower
                ) and len(item_lower) > 3:
                    # Found a recent similar item - ask for clarification
                    clarification_question = f"I see you were considering '{past_decision.item_name}' for ${past_decision.amount} earlier. Is this the same item, or something different?"
                    related_decision_id = past_decision.decision_id
                    break

        # Convert structured response to our domain model
        decision = self._convert_to_purchase_decision(structured_response)

        return decision, clarification_question, related_decision_id

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
            # Convert string to BudgetCategory enum
            try:
                category_enum = BudgetCategory(structured.budget_category.lower())
            except ValueError:
                category_enum = BudgetCategory.GENERAL

            budget_analysis = BudgetAnalysis(
                category=category_enum,
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

        # Build opportunity cost analysis
        from core.models.decision import OpportunityCost

        opportunity_cost = OpportunityCost(
            description=structured.opportunity_cost_description,
            examples=structured.opportunity_cost_examples
            if structured.opportunity_cost_examples
            else [],
        )

        # Build analysis
        analysis = DecisionAnalysis(
            budget_analysis=budget_analysis,
            affected_goals=affected_goals,
            purchase_category=purchase_category,
            financial_health_score=float(structured.financial_health_score),
            opportunity_cost=opportunity_cost,
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

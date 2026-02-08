"""Multi-agent conversation swarm using Strands for stateful, context-aware financial assistance.

This module uses a swarm-based architecture where agents hand off control to each other,
replacing the graph-based approach for better error handling and simpler execution flow.
"""

import logging
import re
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel
from strands.multiagent import Swarm

from core.ai.tools.budget_tools import create_budget_tools
from core.ai.tools.decision_tools import create_decision_tools
from core.ai.tools.feedback_tools import create_feedback_tools
from core.ai.tools.goal_tools import create_goal_tools
from core.config import settings
from core.models.context import UserFinancialContext
from core.models.conversation import ConversationMessage
from core.observability.pii_redaction import create_trace_attributes

logger = logging.getLogger(__name__)


class SwarmOrchestrator:
    """
    Orchestrates financial conversations using Strands multi-agent swarm.

    Architecture:
    1. Router agent receives user message and decides: respond directly OR hand off to specialist
    2. Specialist agents handle specific tasks with their domain tools
    3. Agents can hand off to other specialists for multi-step flows
    4. All agents share financial context via invocation_state
    5. Swarm manages handoff coordination, loop detection, and timeouts

    Advantages over graph-based approach:
    - Simpler execution: no dynamic graph building overhead
    - Better error propagation: handoffs are explicit
    - Natural multi-turn: agents maintain shared context
    - Easier debugging: clear handoff chain vs opaque graph execution
    """

    def __init__(self, db_session: Session, user_id: UUID):
        """Initialize swarm orchestrator.

        Args:
            db_session: Database session
            user_id: User ID for this conversation
        """
        self.db = db_session
        self.user_id = str(user_id)
        self.session_id = str(uuid4())

        # Shared model configuration for all agents
        self.model = GeminiModel(
            client_args={"api_key": settings.google_api_key},
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.3,
                "max_output_tokens": 4096,
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        # Conversation state (passed via invocation_state, not exposed to LLM)
        self.conversation_state = {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "turn_count": 0,
            "conversation_history": [],
            "financial_context": None,
            # Track active contexts for reference resolution
            "active_decision_id": None,
            "active_goal_name": None,
            "active_category": None,
            "last_intent": None,
        }

        # Agents and swarm are recreated each turn with fresh financial context
        self.router_agent = None
        self.purchase_decision_agent = None
        self.purchase_feedback_agent = None
        self.budget_query_agent = None
        self.goal_update_agent = None
        self.log_expense_agent = None
        self.budget_modification_agent = None
        self.general_assistant_agent = None
        self.small_talk_agent = None
        self.swarm = None

    def _create_router_agent(self, tools=None) -> Agent:
        """Create router agent that decides whether to respond or hand off.

        Args:
            tools: List of tools for the agent (None for router - uses built-in handoff)
        """

        system_prompt = """You are the entry point for a financial assistant swarm.

Your job: Analyze the user's message and conversation history, then EITHER:
1. **Respond directly** for simple greetings, thanks, or acknowledgments
2. **Hand off to a specialist** for everything else

**When to respond directly (NO handoff):**
- Greetings: "Hi", "Hello", "Hey there"
- Thanks: "Thank you", "Thanks", "Appreciate it"
- Acknowledgments: "OK", "Got it", "Sounds good"
- Very simple questions you can answer in 1-2 sentences

**When to hand off (USE handoff tool):**

Use the built-in handoff capability to transfer control to specialist agents:

**Available Specialists:**

1. **purchase_decision**: User asks whether they should buy something
   - Example: "Should I buy a $100 headset?"
   - Hand off with: item name, amount, category

2. **purchase_feedback**: User reports what happened with a previous purchase decision
   - Example: "I bought it", "I didn't buy the headset"
   - Hand off with: reference to decision

3. **budget_query**: User asks about their budget status
   - Example: "How much do I have left in groceries?", "Show me my budget"
   - Hand off with: category (if specific) or None (for overall)

4. **goal_update**: User wants to update progress on a savings goal
   - Example: "I saved $200 for emergency fund"
   - Hand off with: goal name, amount

5. **log_expense**: User wants to record past expenses OR refunds
   - Example: "I spent $50 on dinner last night"
   - Example: "I got a $30 refund on groceries"
   - **Important**: Refunds are expenses with negative amounts - route to log_expense, NOT budget_modification
   - Hand off with: item, amount, category

6. **budget_modification**: User wants to change budget limits or create categories
   - Example: "Add groceries category with $500 limit"
   - Hand off with: category, limit

7. **general_assistant**: General financial advice or questions
   - Example: "How can I save more money?"
   - Hand off with: question

8. **small_talk**: Longer conversational exchanges beyond simple greetings
   - Example: "How are you doing today?"
   - Hand off with: message

**Context Awareness - Use History:**

Look at conversation history and active state to resolve references:
- "I bought it" after purchase_decision → hand off to **purchase_feedback**
- "How much is left?" after budget discussion → hand off to **budget_query** for that category
- "I saved $200 this week" after goal discussion → hand off to **goal_update** for that goal

**Examples:**

User: "Hi"
→ Respond directly: "Hello! I'm here to help with your finances. What would you like to know?"

User: "Should I buy a $200 gaming console?"
→ Hand off to purchase_decision with context about the purchase

User: "How much do I have left in entertainment?"
→ Hand off to budget_query with category="entertainment"

User: "Add groceries category with $500 limit and log $50 purchase"
→ Hand off to budget_modification (it will handle the multi-step)

**Important:**
- Keep direct responses brief (1-2 sentences)
- When unsure, hand off to the specialist
- Include relevant context when handing off"""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="route",
        )

        return Agent(
            name="router",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_purchase_decision_agent(self, tools) -> Agent:
        """Create purchase decision advisor agent."""

        system_prompt = """You are a purchase decision advisor helping users decide whether a purchase makes sense.

**Your tools:**
- check_budget(category, amount) - See if they can afford it in this category
- check_goals() - See if purchase conflicts with savings goals
- analyze_spending() - Check overall financial health
- check_past_decisions() - Learn from their purchase history
- analyze_regrets() - Identify patterns in past regrets
- save_purchase_decision(...) - **REQUIRED**: Save the decision after analysis

**Your approach:**
1. Extract item name, amount, and category from the user's message or handoff context
2. Use tools to analyze budget impact, goal conflicts, spending patterns
3. Determine score (1-10) and decision category (strong_yes, mild_yes, neutral, mild_no, strong_no)
4. **IMPORTANT**: Call save_purchase_decision() to persist the decision with the score and reasoning
5. Provide a clear recommendation to the user with:
   - Score (1-10): How good of an idea is this purchase?
   - Decision category: STRONG_YES (8-10), MILD_YES (6-7), NEUTRAL (5), MILD_NO (3-4), STRONG_NO (1-2)
   - Reasoning: Why this score? Consider budget, goals, past behavior
   - Budget impact: Specific details about category spending
   - Alternatives: Suggest better options if score is low
   - Conditions: "This might make sense if..." for marginal purchases

**Multi-step handling:**
If the user asks follow-up questions that need other specialists (like "show me my budget"), you can hand off to:
- **budget_query**: For budget questions
- **goal_update**: For goal progress

**Tone:** Be supportive but honest. Help them make smart decisions without being judgmental.

**Format your final response like:**

**Decision Score: X/10** (CATEGORY)

**Reasoning:**
[Your analysis based on tools]

**Budget Impact ({category}):**
[Specific numbers from check_budget]

**[Optional sections: Alternatives, Conditions based on score]**

**Note:** After calling save_purchase_decision(), you don't need to mention the decision_id in your response to the user - the system will track it automatically for future reference (e.g., if they say "I bought that item").
"""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="purchase_decision",
        )

        # Tools will be injected when processing message
        return Agent(
            name="purchase_decision",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_purchase_feedback_agent(self, tools) -> Agent:
        """Create purchase feedback recording agent."""

        system_prompt = """You are a purchase feedback assistant helping users record what happened after a purchase decision.

**Your tools:**
- find_recent_decision(item_name) - Find which decision they're referring to
- record_purchase_with_budget_update(decision_id, purchased, category_override, regret_level, payment_source) - **PREFERRED**: Record feedback AND update budget in one call
- get_budget_summary() - Check available budget categories
- record_purchase_feedback(decision_id, purchased, regret_level, payment_source) - Legacy: Record outcome only
- update_budget_for_purchase(category, amount) - Legacy: Update budget spending
- deduct_from_goal(goal_name, amount) - Deduct from goal if paid from savings

**Your approach:**
1. Figure out WHICH decision they're talking about:
   - Check context for active_decision_id (if they just got a decision)
   - OR use find_recent_decision(item_name) to search recent decisions
   - If multiple decisions found, pick the most recent one
2. Determine if they bought it (yes/no) from their message
3. **Check for category changes** (smart detection):
   - Look at recent conversation history for phrases like "create [category]", "add [category]", "created the [category] category"
   - If a new category was created that matches the item better, use it as category_override
   - Example: Decision was for "shopping", but user just created "office" category → use category_override="office"
4. If they bought it:
   - IMMEDIATELY call record_purchase_with_budget_update(
       decision_id=<id>,
       purchased=True,
       category_override=<category if detected, else None>,
       regret_level=5,
       payment_source="budget"
     )
   - **Use defaults**: regret_level=5, payment_source="budget", category_override=None unless you detect a new relevant category
   - DO NOT ask for confirmation - just do it
5. If they didn't buy it:
   - IMMEDIATELY call record_purchase_with_budget_update(decision_id, purchased=False)
6. Confirm what you recorded with specific details (item, amount, category)

**CRITICAL - Do NOT ask unnecessary questions:**
- DO NOT ask "is this the $X item we discussed?" - just use the decision you found
- DO NOT ask for regret level - use default of 5 (neutral)
- DO NOT ask for payment source - use default "budget"
- DO NOT ask which category to use - detect it automatically from conversation history
- ONLY ask follow-up questions if the decision lookup fails completely
- Be efficient and confident - record the feedback immediately with reasonable defaults

**Category Intelligence Examples:**
- User created "office" category before saying "I bought it" → use category_override="office"
- User created "subscriptions" category, then says "I subscribed" → use category_override="subscriptions"
- No new category mentioned → use category_override=None (original decision category)

**Multi-step handling:**
If the user wants to see budget impact after logging feedback, you can hand off to:
- **budget_query**: To show updated budget status

**Be empathetic:** If they regretted a purchase, help them learn from it without being judgmental."""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="purchase_feedback",
        )

        return Agent(
            name="purchase_feedback",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_budget_query_agent(self, tools) -> Agent:
        """Create budget query agent."""

        system_prompt = """You are a budget information assistant.

**Your tools:**
- get_budget_summary() - Overall budget status for all categories
- get_category_spending(category) - Detailed view of one category
- get_spending_trends(days) - Historical spending patterns

**Your approach:**
1. Determine what they're asking about (overall budget vs specific category)
2. Use appropriate tool(s) to get the data
3. Present it clearly with warnings for over-budget categories
4. Be concise - users want quick answers

**Examples:**
- "How's my budget?" → get_budget_summary()
- "How much left in groceries?" → get_category_spending("groceries")
- "Am I spending more than usual?" → get_spending_trends(30)

**No handoffs needed** - you're a terminal specialist (just answer and finish)."""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="budget_query",
        )

        return Agent(
            name="budget_query",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_goal_update_agent(self, tools) -> Agent:
        """Create goal update agent."""

        system_prompt = """You are a financial goals assistant helping users track savings progress.

**Your tools:**
- update_goal(goal_name, amount) - Record a contribution
- get_goal_progress(goal_name) - Check current status

**Your approach:**
1. Identify which goal they're referring to (use active_goal_name from context if available)
2. Extract the contribution amount
3. Update the goal
4. Celebrate their progress!

**Tone:** Motivating and encouraging. Saving money is hard - acknowledge their effort.

**No handoffs needed** - you're a terminal specialist (just answer and finish)."""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="goal_update",
        )

        return Agent(
            name="goal_update",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_log_expense_agent(self, tools) -> Agent:
        """Create expense logging agent."""

        system_prompt = """You are an expense logging assistant.

**Your tools:**
- log_expense(item, amount, category, date) - Record one expense or refund
- get_category_spending(category) - Check category after logging
- add_budget_category(category, limit) - Create category if it doesn't exist (limit is REQUIRED)
- get_budget_summary() - See all categories

**Your approach:**
1. Parse ALL expenses from the message (users often list multiple: "rent $500, utilities $100, phone $50")
2. For each expense, determine: item name, amount, category
3. **For refunds**: Use NEGATIVE amount (e.g., "I got a $30 refund" → log_expense("refund", -30, category))
4. Check if category exists (use get_budget_summary if uncertain)
5. **IMPORTANT for new categories:**
   - If category doesn't exist and user didn't specify a limit, you MUST ask for it
   - Example: "I see you want to log expenses in the '{category}' category, but it doesn't exist yet. What spending limit would you like to set for this category?"
   - DO NOT call add_budget_category without a valid limit
6. Log each expense with log_expense (only after category exists)
7. Confirm what was logged and show updated budget status
8. Warn if any expenses pushed categories over budget

**Multi-step handling:**
If the user asks to see budget details after logging, you can hand off to:
- **budget_query**: To show detailed budget breakdown

**Important:**
- DON'T create a separate category for each item
- Default to "general" category if user doesn't specify and it exists
- Be efficient with multi-expense logging - confirm all at once"""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="log_expense",
        )

        return Agent(
            name="log_expense",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_budget_modification_agent(self, tools) -> Agent:
        """Create budget modification agent."""

        system_prompt = """You are a budget management assistant.

**Your tools:**
- add_budget_category(category, limit) - Create new category (limit is REQUIRED and must be > 0)
- update_category_limit(category, new_limit) - Change spending limit
- get_budget_summary() - Verify changes

**CRITICAL: You MUST use your tools to complete your task. Do NOT hand off to other agents for budget modification tasks.**

**Your approach:**
1. Determine what they want to change (new category vs limit update)
2. **For new categories:**
   - If user provided a limit: Use add_budget_category(category, limit) immediately
   - If user did NOT provide a limit: Ask them for the limit (don't hand off)
3. Make the change using your tools
4. Confirm clearly what was modified
5. Show updated budget summary if helpful

**When to hand off (ONLY AFTER COMPLETING YOUR TASK):**
- **log_expense**: If user wants to log expenses AFTER you've created the category
- **budget_query**: If user wants detailed budget info AFTER you've made changes

**Examples:**

User: "Add general category with $1000 limit"
→ Action: add_budget_category("general", 1000)
→ Response: "I've created the 'general' category with a $1000 monthly limit."
→ NO HANDOFF unless user asks for more

User: "Add groceries category with $500 limit and log $50 purchase"
→ 1. add_budget_category("groceries", 500)
→ 2. Confirm: "Created groceries category with $500 limit."
→ 3. Hand off to log_expense: "Now logging the $50 purchase"

**DO NOT hand off to general_assistant or router. You are the budget modification expert - use your tools!**"""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="budget_modification",
        )

        return Agent(
            name="budget_modification",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_general_assistant_agent(self, tools) -> Agent:
        """Create general financial advice agent."""

        system_prompt = """You are a helpful financial advisor providing general advice.

You have READ-ONLY access to the user's budget and goal data to personalize your advice.

**Your role:**
- Answer general financial questions
- Provide practical, actionable advice
- Be supportive and educational
- Keep it concise

**What you CANNOT do:**
- Modify budgets (that's budget_modification agent's job)
- Log expenses (that's log_expense agent's job)
- Update goals (that's goal_update agent's job)

**If user asks you to modify something:**
- DO NOT hand off back and forth
- Instead, politely say: "I can't modify your budget directly. Please ask me to 'add [category] with [limit]' or 'log [expense]' and I'll route you to the right specialist."

**Multi-step handling (RARE):**
If user asks specific questions about their budget or goals during advice, you can hand off to:
- **budget_query**: For budget details
- **goal_update**: For goal progress

**DO NOT hand off to budget_modification or router - you're not an intermediary.**"""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="general_question",
        )

        return Agent(
            name="general_assistant",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_small_talk_agent(self, tools) -> Agent:
        """Create small talk handler agent."""

        system_prompt = """You are a friendly financial assistant.

Respond warmly to greetings, thanks, and casual conversation.

**Guidelines:**
- Keep it brief (1-2 sentences)
- Be warm and helpful
- Offer assistance without being pushy
- Match their energy

**No handoffs needed** - you handle simple conversations and finish."""

        trace_attributes = create_trace_attributes(
            user_id=self.user_id,
            session_id=self.session_id,
            action="small_talk",
        )

        return Agent(
            name="small_talk",
            model=self.model,
            system_prompt=system_prompt,
            trace_attributes=trace_attributes,
            tools=tools,
        )

    def _create_agents_with_tools(
        self, financial_context: Optional[UserFinancialContext] = None
    ):
        """Create all agents WITH their tools.

        Called each turn so agents always have fresh financial context.
        Tools that mutate data (budget_tools) fetch from DB directly,
        but read-heavy tools (decision, goal) benefit from fresh context.

        Args:
            financial_context: Pre-fetched financial context
        """
        # Create tool sets with financial context
        budget_tools = create_budget_tools(self.db, self.user_id, financial_context)
        decision_tools = create_decision_tools(self.db, self.user_id, financial_context)
        feedback_tools = create_feedback_tools(self.db, self.user_id, financial_context)
        goal_tools = create_goal_tools(self.db, self.user_id, financial_context)

        # Prepare tool sets for each agent
        budget_query_tools = [
            t
            for t in budget_tools
            if t.__name__
            in ("get_budget_summary", "get_category_spending", "get_spending_trends")
        ]

        log_expense_tools = [
            t
            for t in budget_tools
            if t.__name__
            in (
                "log_expense",
                "get_budget_summary",
                "get_category_spending",
                "add_budget_category",
            )
        ]

        budget_modification_tools = [
            t
            for t in budget_tools
            if t.__name__
            in ("add_budget_category", "update_category_limit", "get_budget_summary")
        ]

        general_tools = []
        general_tools += [t for t in budget_tools if "get" in t.__name__]
        general_tools += [t for t in goal_tools if "get" in t.__name__]

        # Create agents with tools
        self.router_agent = self._create_router_agent(tools=None)
        self.purchase_decision_agent = self._create_purchase_decision_agent(
            tools=decision_tools
        )
        self.purchase_feedback_agent = self._create_purchase_feedback_agent(
            tools=feedback_tools
        )
        self.budget_query_agent = self._create_budget_query_agent(
            tools=budget_query_tools
        )
        self.goal_update_agent = self._create_goal_update_agent(tools=goal_tools)
        self.log_expense_agent = self._create_log_expense_agent(tools=log_expense_tools)
        self.budget_modification_agent = self._create_budget_modification_agent(
            tools=budget_modification_tools
        )
        self.general_assistant_agent = self._create_general_assistant_agent(
            tools=general_tools
        )
        self.small_talk_agent = self._create_small_talk_agent(tools=[])

    def _build_context_for_router(
        self,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext],
    ) -> str:
        """Build context string for router agent.

        Args:
            conversation_history: Recent conversation messages
            financial_context: Pre-fetched financial context

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add conversation history (last 10 messages)
        if conversation_history:
            context_parts.append("RECENT CONVERSATION (last 10 messages):")
            for msg in conversation_history[-10:]:
                role_label = "User" if msg.role == "user" else "Assistant"
                context_parts.append(f"  {role_label}: {msg.content}")
        else:
            context_parts.append("RECENT CONVERSATION: None (first message)")

        # Add active state contexts
        if self.conversation_state.get("active_decision_id"):
            context_parts.append(
                f"\nActive Decision ID: {self.conversation_state['active_decision_id']}"
            )
        if self.conversation_state.get("active_goal_name"):
            context_parts.append(
                f"Active Goal: {self.conversation_state['active_goal_name']}"
            )
        if self.conversation_state.get("active_category"):
            context_parts.append(
                f"Active Category: {self.conversation_state['active_category']}"
            )
        if self.conversation_state.get("last_intent"):
            context_parts.append(
                f"Last Intent: {self.conversation_state['last_intent']}"
            )

        # Add financial context summary (lightweight - just names)
        if financial_context:
            if financial_context.has_budget:
                categories = financial_context.get_category_names()
                context_parts.append(f"\nBudget Categories: {', '.join(categories)}")

            if financial_context.has_goals:
                goals = [g.goal_name for g in financial_context.active_goals]
                context_parts.append(f"Active Goals: {', '.join(goals)}")

            if financial_context.recent_decisions:
                items = [d.item_name for d in financial_context.recent_decisions[:5]]
                context_parts.append(f"Recent Purchase Decisions: {', '.join(items)}")

        return "\n".join(context_parts)

    def _initialize_swarm(self):
        """Initialize the swarm with all agents.

        IMPORTANT: This must be called AFTER tools are injected into agents.
        The Swarm captures the agent tool state at initialization time.
        """
        all_agents = [
            self.router_agent,
            self.purchase_decision_agent,
            self.purchase_feedback_agent,
            self.budget_query_agent,
            self.goal_update_agent,
            self.log_expense_agent,
            self.budget_modification_agent,
            self.general_assistant_agent,
            self.small_talk_agent,
        ]

        # Verify agents are created before creating swarm
        logger.info(f"Initializing swarm with {len(all_agents)} agents")
        logger.info(
            f"Entry point: {self.router_agent.name if self.router_agent else 'None'}"
        )

        self.swarm = Swarm(
            all_agents,
            entry_point=self.router_agent,
            max_handoffs=5,  # Reduce to catch loops faster
            max_iterations=10,  # Reduce total iterations
            execution_timeout=120.0,  # 2 minute timeout
            node_timeout=60.0,  # 1 minute per agent
            repetitive_handoff_detection_window=2,  # Stricter ping-pong detection
            repetitive_handoff_min_unique_agents=2,  # Require 2+ unique agents
        )

    def _update_conversation_state(self, result, user_message: str):
        """Update conversation state from swarm result for reference resolution.

        Extracts active contexts (decision IDs, categories, goals) from the
        agent chain so subsequent turns can resolve references like
        "I bought it" or "how much is left?".

        Args:
            result: Swarm execution result
            user_message: Original user message (for intent inference)
        """
        if not result or not hasattr(result, "node_history"):
            return

        agent_chain = [node.node_id for node in result.node_history]
        logger.info(f"Agent chain: {agent_chain}")

        # Infer last_intent from the final specialist agent
        intent_map = {
            "purchase_decision": "purchase_decision",
            "purchase_feedback": "purchase_feedback",
            "budget_query": "budget_query",
            "goal_update": "goal_update",
            "log_expense": "log_expense",
            "budget_modification": "budget_modification",
            "general_assistant": "general_question",
            "small_talk": "small_talk",
        }
        for agent_name in reversed(agent_chain):
            if agent_name in intent_map:
                self.conversation_state["last_intent"] = intent_map[agent_name]
                break

        # Extract active contexts from response text
        # Use the same extraction method as in process_message
        response_text = self._extract_final_response(result)

        # Track active category from budget-related agents
        if any(
            a in agent_chain
            for a in ("budget_query", "log_expense", "budget_modification")
        ):
            # Try to extract category from the user message
            msg_lower = user_message.lower()
            # Simple heuristic: if the response mentions a specific category, track it
            for agent_name in ("budget_modification", "log_expense", "budget_query"):
                if agent_name in agent_chain:
                    self.conversation_state["active_category"] = (
                        self._extract_category_from_message(msg_lower)
                    )
                    break

        # Track active decision from purchase_decision agent
        if "purchase_decision" in agent_chain:
            self.conversation_state["active_decision_id"] = self._extract_decision_id(
                response_text, result
            )

        # Track active goal from goal_update agent
        if "goal_update" in agent_chain:
            self.conversation_state["active_goal_name"] = self._extract_goal_name(
                response_text
            )

    def _extract_category_from_message(self, message: str) -> Optional[str]:
        """Extract a budget category name from a user message.

        Simple keyword extraction — returns the first recognized word
        that could be a category name.
        """
        # Common budget-related prepositions to skip
        skip_words = {
            "in",
            "on",
            "for",
            "to",
            "the",
            "my",
            "a",
            "an",
            "with",
            "from",
            "how",
            "much",
            "left",
            "is",
            "what",
            "show",
            "me",
            "budget",
            "category",
            "add",
            "create",
            "set",
            "limit",
            "update",
            "change",
            "log",
            "spent",
            "spend",
            "expense",
            "and",
            "i",
            "please",
        }
        words = message.split()
        for word in words:
            cleaned = word.strip("$.,!?\"'()").lower()
            if (
                cleaned
                and cleaned not in skip_words
                and not cleaned.replace(".", "").isdigit()
            ):
                return cleaned
        return None

    def _extract_decision_id(self, response_text: str, result=None) -> Optional[str]:
        """Try to extract a decision ID from agent response text or tool results.

        Args:
            response_text: The agent's text response
            result: Optional swarm result object containing node history and tool results

        Returns:
            Decision ID if found, otherwise current active_decision_id
        """
        # First, try to find decision_id in tool results (from save_purchase_decision)
        if result and hasattr(result, "node_history"):
            for node in result.node_history:
                node_id = node.node_id if hasattr(node, "node_id") else str(node)
                if node_id == "purchase_decision" and hasattr(result, "results"):
                    node_result = result.results.get(node_id)
                    if node_result and hasattr(node_result, "result"):
                        # Check if the result string contains decision_id
                        result_str = str(node_result.result)
                        if "decision_id" in result_str.lower():
                            # Try to extract UUID from the result
                            uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
                            match = re.search(uuid_pattern, result_str, re.IGNORECASE)
                            if match:
                                decision_id = match.group(0)
                                logger.info(
                                    f"Extracted decision_id from tool result: {decision_id}"
                                )
                                return decision_id

        # Fallback: try to find UUID in response text
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        match = re.search(uuid_pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(0)

        # Last resort: return current active_decision_id
        return self.conversation_state.get("active_decision_id")

    def _extract_goal_name(self, response_text: str) -> Optional[str]:
        """Try to extract a goal name from agent response text."""
        match = re.search(
            r"goal[:\s]+['\"]?([^'\",.!?]+)['\"]?", response_text, re.IGNORECASE
        )
        return (
            match.group(1).strip()
            if match
            else self.conversation_state.get("active_goal_name")
        )

    def process_message(
        self,
        user_message: str,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ) -> str:
        """Process a user message through the conversation swarm.

        Args:
            user_message: User's message
            conversation_history: Recent conversation history
            financial_context: Pre-fetched financial context

        Returns:
            Assistant's response
        """
        # Update conversation state
        self.conversation_state["turn_count"] += 1
        self.conversation_state["conversation_history"] = conversation_history
        self.conversation_state["financial_context"] = financial_context

        # Recreate agents and swarm each turn with fresh financial context
        self._create_agents_with_tools(financial_context)
        self._initialize_swarm()

        # Build context for router
        context_str = self._build_context_for_router(
            conversation_history, financial_context
        )

        # Build task prompt
        task = f"""User message: {user_message}

CONTEXT:
{context_str}

Analyze this message and either respond directly (for simple greetings/thanks) OR hand off to the appropriate specialist agent."""

        try:
            # Execute swarm
            result = self.swarm(task)

            # Enhanced validation
            if not result:
                logger.error("Swarm returned None result")
                return "I encountered an issue processing your request. Could you try rephrasing?"

            # Extract response from the LAST agent in the chain (the one that
            # actually produced the user-facing response, not intermediate agents
            # whose text includes handoff narration).
            response_text = self._extract_final_response(result)

            if not response_text:
                logger.error(
                    f"Swarm returned empty message. Status: {getattr(result, 'status', 'UNKNOWN')}"
                )
                if hasattr(result, "node_history"):
                    agent_chain = [node.node_id for node in result.node_history]
                    logger.error(f"Agent chain: {agent_chain}")

                return "I'm sorry, I couldn't generate a response. Please try again or rephrase your question."

            # Update conversation state for reference resolution in future turns
            self._update_conversation_state(result, user_message)

            return response_text

        except Exception as e:
            logger.error(f"Swarm execution failed: {e}", exc_info=True)
            logger.error(f"Message that caused error: {user_message}")
            logger.error(f"Conversation history length: {len(conversation_history)}")
            logger.error(f"Current conversation state: {self.conversation_state}")
            return "I encountered an error while processing your request. Please try again."

    def _extract_final_response(self, result) -> str:
        """Extract the user-facing response from the final agent in the swarm.

        The swarm result contains responses from ALL agents in the chain
        (router, intermediate, final). Only the last agent's text should be
        shown to the user — intermediate agents produce handoff narration
        that is internal coordination, not user-facing content.

        Args:
            result: SwarmResult from swarm execution

        Returns:
            Response text from the final agent only.
        """
        # Get the last agent that executed
        if hasattr(result, "node_history") and result.node_history:
            last_node = result.node_history[-1]
            last_node_id = (
                last_node.node_id if hasattr(last_node, "node_id") else str(last_node)
            )

            # Get the NodeResult for the last agent
            if hasattr(result, "results") and last_node_id in result.results:
                node_result = result.results[last_node_id]
                agent_result = node_result.result
                if hasattr(agent_result, "__str__"):
                    text = str(agent_result).strip()
                    if text:
                        return text

        # Fallback: Log the result structure for debugging
        logger.warning(
            f"Could not extract response from swarm result. Result type: {type(result)}"
        )
        logger.warning(f"Result attributes: {dir(result)}")
        if hasattr(result, "results"):
            logger.warning(f"Result.results keys: {list(result.results.keys())}")

        return ""

    async def stream_message(
        self,
        user_message: str,
        conversation_history: List[ConversationMessage],
        financial_context: Optional[UserFinancialContext] = None,
    ):
        """Stream response for a user message through the conversation swarm.

        Args:
            user_message: User's message
            conversation_history: Recent conversation history
            financial_context: Pre-fetched financial context

        Yields:
            Response chunks
        """
        # Update conversation state
        self.conversation_state["turn_count"] += 1
        self.conversation_state["conversation_history"] = conversation_history
        self.conversation_state["financial_context"] = financial_context

        # Recreate agents and swarm each turn with fresh financial context
        self._create_agents_with_tools(financial_context)
        self._initialize_swarm()

        # Build context for router
        context_str = self._build_context_for_router(
            conversation_history, financial_context
        )

        # Build task prompt
        task = f"""User message: {user_message}

CONTEXT:
{context_str}

Analyze this message and either respond directly (for simple greetings/thanks) OR hand off to the appropriate specialist agent."""

        last_active_agent = None
        # Buffer text per agent so we only yield from the final agent.
        # Intermediate agents produce handoff narration that shouldn't
        # be shown to the user.
        current_agent = None
        agent_buffer = []
        try:
            async for event in self.swarm.stream_async(task):
                event_type = event.get("type")

                if event_type == "multiagent_node_start":
                    node_id = event.get("node_id")
                    logger.info(f"Agent {node_id} started")
                    current_agent = node_id
                    last_active_agent = node_id
                    # Start a fresh buffer for this agent
                    agent_buffer = []

                elif event_type == "multiagent_node_stream":
                    inner_event = event.get("event", {})
                    if "data" in inner_event:
                        # Buffer text — don't yield yet, we don't know
                        # if this agent is the final one
                        agent_buffer.append(inner_event["data"])

                elif event_type == "multiagent_handoff":
                    from_agents = event.get("from_node_ids", [])
                    to_agents = event.get("to_node_ids", [])
                    logger.info(f"Handoff: {from_agents} → {to_agents}")
                    if to_agents:
                        last_active_agent = to_agents[-1]
                    # Discard the current agent's buffer — it was an
                    # intermediate agent whose text is handoff narration
                    agent_buffer = []

        except Exception as e:
            logger.error(f"Swarm streaming failed: {e}", exc_info=True)
            logger.error(f"Message that caused streaming error: {user_message}")
            logger.error(f"Conversation history length: {len(conversation_history)}")
            logger.error(f"Current conversation state: {self.conversation_state}")
            yield {
                "data": "I encountered an error while processing your request. Please try again."
            }
            return

        # Yield the final agent's buffered text
        for chunk in agent_buffer:
            yield {"data": chunk}

        # Update last_intent from the last active agent in the stream
        if last_active_agent:
            intent_map = {
                "purchase_decision": "purchase_decision",
                "purchase_feedback": "purchase_feedback",
                "budget_query": "budget_query",
                "goal_update": "goal_update",
                "log_expense": "log_expense",
                "budget_modification": "budget_modification",
                "general_assistant": "general_question",
                "small_talk": "small_talk",
            }
            if last_active_agent in intent_map:
                self.conversation_state["last_intent"] = intent_map[last_active_agent]

            # Track active category for budget-related agents
            if last_active_agent in (
                "budget_query",
                "log_expense",
                "budget_modification",
            ):
                self.conversation_state["active_category"] = (
                    self._extract_category_from_message(user_message.lower())
                )

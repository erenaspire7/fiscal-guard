"""AI-powered intent classifier for conversational messages."""

import json
from datetime import datetime, timedelta
from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.database.models import Budget, Goal, PurchaseDecision
from core.models.conversation import ConversationIntent, ConversationMessage
from core.observability.pii_redaction import create_trace_attributes


class IntentClassifier:
    """Classify user intent from conversational messages."""

    def __init__(self, db_session: Session):
        """Initialize intent classifier.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session

        # Initialize Gemini model
        self.model = GeminiModel(
            client_args={
                "api_key": settings.google_api_key,
            },
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.3,  # Lower temperature for more consistent classification
                "max_output_tokens": 1024,
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        self.system_prompt = """You are an expert at classifying user intent in financial conversations.

Classify the user's message into ONE of these intents:

1. **purchase_decision**: User is asking whether they should buy something
   - "Should I buy X?"
   - "I want to get a new laptop for $1500"
   - "Thinking about ordering takeout"

2. **purchase_feedback**: User is reporting what happened with a previous purchase decision
   - "I bought it"
   - "I ended up getting the headset"
   - "I regret buying X"
   - "Didn't buy it after all"

3. **budget_query**: User is asking about their budget status
   - "How much do I have left for groceries?"
   - "What's my entertainment budget?"
   - "Am I over budget this month?"
   - "Show me my spending"

4. **goal_update**: User wants to update progress on a financial goal
   - "Add $500 to emergency fund"
   - "I saved $200 this month"
   - "Put $100 toward house down payment"

5. **log_expense**: User wants to log a past expense
   - "I spent $100 on groceries"
   - "Log $50 for gas"
   - "Just bought a coffee for $5"
   - "I used $100 dollars in transport for this month"

6. **budget_modification**: User wants to change their budget limits
   - "Increase my dining budget by $50"
   - "Lower the shopping limit to $200"
   - "Add $100 to groceries for this month"
   - "I need to reduce my transport budget"

7. **general_question**: General financial advice or questions
   - "What should I focus on financially?"
   - "Am I doing well?"
   - "How can I improve my financial health?"
   - "How do I make more money?"
   - "How can I increase my income?"
   - "How can I negotiate a raise?"

8. **small_talk**: Short conversational messages that are not asking for financial analysis or an action.
   - "Hi"
   - "Hello"
   - "Hey"
   - "Thanks"
   - "Thank you"
   - "Got it, thanks!"
   - "Awesome, appreciate it"
   - "lol"
   - "nice"

If the user's message is primarily greeting/acknowledgement/small talk, classify it as **small_talk** (NOT general_question).

Extract relevant entities based on the intent:
- For purchase_decision: item_name, amount, category, urgency, reason
- For purchase_feedback: purchased (bool), regret_level (1-10), payment_source (budget/savings/goal)
- For budget_query: category
- For goal_update: goal_name, amount
- For log_expense: amount, category, item_name
- For budget_modification: category, amount, operation (increase/decrease/set)
- For general_question: topic, question_type, keywords
- For small_talk: no entities needed

For **general_question**, enrich extracted_entities as follows:
- question_type: ONE of ["financial_health", "increase_income", "reduce_spending", "debt", "investing", "savings", "goals", "other"]
- keywords: a list of 2-8 short keywords/phrases from the user message (e.g. ["raise", "negotiation", "career"], ["side hustle", "freelance", "income"], ["credit card", "interest", "payoff"])

Also determine:
- Confidence level (0-1)
- Whether this references a previous message/decision
- If unclear, suggest a clarification question

Be intelligent about context - if the user says "I bought it" right after asking about a purchase, it's purchase_feedback."""

    def classify(
        self,
        user_message: str,
        conversation_history: List[ConversationMessage],
        user_id: UUID,
    ) -> ConversationIntent:
        """Classify user intent with context.

        Args:
            user_message: The user's message to classify
            conversation_history: Recent conversation messages
            user_id: User ID for context gathering

        Returns:
            Classified intent with extracted entities
        """
        # Build context from conversation history
        context = self._build_context(conversation_history, user_id)

        # Create trace attributes with PII redaction
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),
            session_id=str(uuid4()),
            action="intent_classification",
            message_length=len(user_message),
        )

        # Create agent for intent classification
        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            structured_output_model=ConversationIntent,
            trace_attributes=trace_attributes,
        )

        # Build the prompt
        prompt = f"""Classify this message:

USER MESSAGE: {user_message}

CONTEXT:
{context}

Provide the intent classification with extracted entities."""

        # Get classification
        response = agent(prompt)

        # Parse response
        if hasattr(response, "output"):
            json_str = response.output
        else:
            json_str = str(response)

        json_data = json.loads(json_str)
        return ConversationIntent(**json_data)

    def _build_context(
        self, conversation_history: List[ConversationMessage], user_id: UUID
    ) -> str:
        """Build context string including history, budget, goals, and recent decisions.

        Args:
            conversation_history: Recent messages
            user_id: User ID

        Returns:
            Context string for the agent
        """
        context_parts = []

        # Add conversation history (last 3 messages)
        if conversation_history:
            recent_messages = conversation_history[-3:]
            context_parts.append("RECENT CONVERSATION:")
            for msg in recent_messages:
                context_parts.append(f"  {msg.role}: {msg.content}")
        else:
            context_parts.append("RECENT CONVERSATION: None (first message)")

        # Get recent decisions (last 24 hours)
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_decisions = (
            self.db_session.query(PurchaseDecision)
            .filter(
                PurchaseDecision.user_id == user_id,
                PurchaseDecision.created_at > twenty_four_hours_ago,
            )
            .order_by(PurchaseDecision.created_at.desc())
            .limit(5)
            .all()
        )

        if recent_decisions:
            context_parts.append("\nRECENT PURCHASE DECISIONS:")
            for decision in recent_decisions:
                context_parts.append(
                    f"  - {decision.item_name} for ${decision.amount} (Score: {decision.score}/10, Category: {decision.decision_category})"
                )
        else:
            context_parts.append("\nRECENT PURCHASE DECISIONS: None")

        # Get active budget
        active_budget = (
            self.db_session.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.period_end >= datetime.utcnow(),
            )
            .order_by(Budget.created_at.desc())
            .first()
        )

        if active_budget:
            context_parts.append("\nACTIVE BUDGET:")
            context_parts.append(f"  Total Monthly: ${active_budget.total_monthly}")
            context_parts.append("  Categories:")
            for category, details in active_budget.categories.items():
                spent = details.get("spent", 0)
                limit = details.get("limit", 0)
                remaining = limit - spent
                context_parts.append(
                    f"    - {category}: ${spent}/${limit} (${remaining} remaining)"
                )
        else:
            context_parts.append("\nACTIVE BUDGET: None")

        # Get active goals
        active_goals = (
            self.db_session.query(Goal)
            .filter(Goal.user_id == user_id, Goal.is_completed == False)
            .order_by(Goal.created_at.desc())
            .limit(5)
            .all()
        )

        if active_goals:
            context_parts.append("\nACTIVE GOALS:")
            for goal in active_goals:
                remaining = goal.target_amount - goal.current_amount
                context_parts.append(
                    f"  - {goal.goal_name}: ${goal.current_amount}/${goal.target_amount} (${remaining} remaining)"
                )
        else:
            context_parts.append("\nACTIVE GOALS: None")

        return "\n".join(context_parts)

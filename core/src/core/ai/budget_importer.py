"""AI-powered budget import using Strands."""

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.models.budget import BudgetCreate, CategoryBudget, ChatBudgetImportResponse


class BudgetImporter:
    """Handle chat-based budget import using Strands AI."""

    def __init__(self):
        """Initialize budget importer."""
        # Initialize Gemini model
        model = GeminiModel(
            client_args={
                "api_key": settings.google_api_key,
            },
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.7,
                "max_output_tokens": 2048,
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        # Initialize Agent with the model
        self.agent = Agent(model=model, tools=[])

        self.system_prompt = """You are a helpful financial assistant that helps users create their monthly budget through conversation.

Your goal is to extract the following information:
1. Budget name (default to current month/year if not specified)
2. Total monthly budget
3. Budget categories with their limits (e.g., groceries: $500, rent: $1500, etc.)
4. Period start and end dates (default to current month if not specified)

When you have all the information needed, respond with JSON in this exact format:
{
    "complete": true,
    "budget": {
        "name": "January 2026 Budget",
        "total_monthly": "3000.00",
        "period_start": "2026-01-01",
        "period_end": "2026-01-31",
        "categories": {
            "rent": {"limit": "1500.00", "spent": "0"},
            "groceries": {"limit": "500.00", "spent": "0"},
            "transportation": {"limit": "300.00", "spent": "0"}
        }
    }
}

If you need more information, respond with:
{
    "complete": false,
    "message": "Your conversational response asking for clarification"
}

Be friendly, conversational, and help users think through their budget categories."""

    def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> ChatBudgetImportResponse:
        """Process a message in the budget import conversation."""
        # Build the full prompt with conversation history
        if conversation_history:
            # Format conversation history
            history_text = "\n\n".join(
                [
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in conversation_history
                ]
            )
            full_prompt = f"{self.system_prompt}\n\nConversation so far:\n{history_text}\n\nUSER: {user_message}"
        else:
            full_prompt = f"{self.system_prompt}\n\nUSER: {user_message}"

        # Call the agent
        response = self.agent(full_prompt)
        assistant_message = str(response)

        # Try to parse as JSON
        try:
            data = json.loads(assistant_message)

            if data.get("complete"):
                # Extract budget data
                budget_data = data.get("budget", {})

                # Convert to BudgetCreate model
                categories = {}
                for cat_name, cat_data in budget_data.get("categories", {}).items():
                    categories[cat_name] = CategoryBudget(
                        limit=Decimal(str(cat_data["limit"])),
                        spent=Decimal(str(cat_data.get("spent", "0"))),
                    )

                budget_create = BudgetCreate(
                    name=budget_data["name"],
                    total_monthly=Decimal(str(budget_data["total_monthly"])),
                    period_start=date.fromisoformat(budget_data["period_start"]),
                    period_end=date.fromisoformat(budget_data["period_end"]),
                    categories=categories,
                )

                return ChatBudgetImportResponse(
                    response="Great! I've gathered all your budget information. Here's what I have:",
                    budget_data=budget_create,
                    is_complete=True,
                )
            else:
                # Still gathering information
                return ChatBudgetImportResponse(
                    response=data.get("message", assistant_message),
                    budget_data=None,
                    is_complete=False,
                )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If not valid JSON or missing fields, treat as conversational response
            return ChatBudgetImportResponse(
                response=assistant_message,
                budget_data=None,
                is_complete=False,
            )

    def start_conversation(self) -> ChatBudgetImportResponse:
        """Start a new budget import conversation."""
        greeting = (
            "Hi! I'm here to help you set up your budget. "
            "Let's start with the basics: what's your total monthly budget? "
            "And what are the main categories you'd like to track, like rent, groceries, entertainment, etc.?"
        )
        return ChatBudgetImportResponse(
            response=greeting,
            budget_data=None,
            is_complete=False,
        )

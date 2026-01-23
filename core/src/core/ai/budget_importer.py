"""AI-powered budget import using Strands."""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.models.budget import BudgetCreate, CategoryBudget, ChatBudgetImportResponse


class StructuredCategoryBudget(BaseModel):
    """Structured output for a budget category."""

    limit: float = Field(..., description="Budget limit for this category", gt=0)
    spent: float = Field(
        default=0.0, description="Amount already spent in this category", ge=0
    )


class StructuredBudgetData(BaseModel):
    """Structured output for complete budget data."""

    name: str = Field(
        ..., description="Name of the budget (e.g., 'January 2026 Budget')"
    )
    total_monthly: float = Field(..., description="Total monthly budget amount", gt=0)
    period_start: str = Field(
        ..., description="Budget period start date in ISO format (YYYY-MM-DD)"
    )
    period_end: str = Field(
        ..., description="Budget period end date in ISO format (YYYY-MM-DD)"
    )
    categories: Dict[str, StructuredCategoryBudget] = Field(
        ...,
        description="Dictionary of category names to their budget limits (e.g., {'rent': {'limit': 1500, 'spent': 0}})",
    )


class StructuredBudgetImportResponse(BaseModel):
    """Structured output for budget import conversation."""

    complete: bool = Field(
        ...,
        description="True if all budget information has been gathered, False if more info is needed",
    )
    message: str = Field(
        ...,
        description="Conversational response to the user. If complete=False, ask for missing information. If complete=True, confirm what was gathered.",
    )
    budget: Optional[StructuredBudgetData] = Field(
        None,
        description="Complete budget data. Only provided when complete=True and all information is available.",
    )


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

        # Store model for per-request agent creation
        self.model = model

        self.system_prompt = """You are a helpful financial assistant that helps users create their monthly budget through conversation.

Your goal is to extract the following information:
1. Budget name (default to current month/year if not specified, e.g., "January 2026 Budget")
2. Total monthly budget amount
3. Budget categories with their limits (e.g., groceries: $500, rent: $1500, etc.)
4. Period start and end dates (default to current month if not specified)

Guidelines:
- Be friendly and conversational
- Help users think through common budget categories (rent/mortgage, groceries, utilities, transportation, entertainment, savings, etc.)
- If they give a total but no categories, suggest breaking it down
- If they give categories without amounts, ask for specific limits
- Default the budget name to "[Month] [Year] Budget" if not specified
- Default period to current month (1st to last day) if not specified

When you have ALL required information:
- Set complete=True
- Provide all budget details in the budget field
- Write a friendly confirmation message

When you need MORE information:
- Set complete=False
- budget field should be null
- Ask specific questions about what's missing in the message field

Be natural and helpful, like a financial advisor having a conversation."""

    def process_message(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> ChatBudgetImportResponse:
        """Process a message in the budget import conversation.

        Args:
            user_message: The user's message
            conversation_history: Optional list of previous messages in format
                [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]

        Returns:
            ChatBudgetImportResponse with conversational response and optional budget data
        """
        # Build the full prompt with conversation history
        if conversation_history:
            # Format conversation history
            history_text = "\n".join(
                [
                    f"{msg['role'].upper()}: {msg['content']}"
                    for msg in conversation_history
                ]
            )
            full_prompt = f"""Previous conversation:
{history_text}

USER: {user_message}

Based on the entire conversation, determine if you have all the information needed to create a complete budget. If yes, set complete=True and provide all budget details. If no, ask for the missing information."""
        else:
            full_prompt = f"""USER: {user_message}

Analyze this message and determine if you have enough information to create a complete budget. If not, ask for what's missing."""

        # Create agent with structured output for this request
        agent = Agent(
            model=self.model,
            tools=[],
            system_prompt=self.system_prompt,
            structured_output_model=StructuredBudgetImportResponse,
        )

        # Call the agent - response will be StructuredBudgetImportResponse
        response = agent(full_prompt)
        structured_response: StructuredBudgetImportResponse = response

        # Convert to domain model
        if structured_response.complete and structured_response.budget:
            # Convert structured budget to BudgetCreate
            budget_create = self._convert_to_budget_create(structured_response.budget)

            return ChatBudgetImportResponse(
                response=structured_response.message,
                budget_data=budget_create,
                is_complete=True,
            )
        else:
            # Still gathering information
            return ChatBudgetImportResponse(
                response=structured_response.message,
                budget_data=None,
                is_complete=False,
            )

    def _convert_to_budget_create(
        self, structured_budget: StructuredBudgetData
    ) -> BudgetCreate:
        """Convert structured budget to BudgetCreate domain model.

        Args:
            structured_budget: Structured budget data from LLM

        Returns:
            BudgetCreate domain model
        """
        # Convert categories
        categories = {}
        for cat_name, cat_data in structured_budget.categories.items():
            categories[cat_name.lower()] = CategoryBudget(
                limit=Decimal(str(cat_data.limit)),
                spent=Decimal(str(cat_data.spent)),
            )

        # Parse dates
        period_start = date.fromisoformat(structured_budget.period_start)
        period_end = date.fromisoformat(structured_budget.period_end)

        return BudgetCreate(
            name=structured_budget.name,
            total_monthly=Decimal(str(structured_budget.total_monthly)),
            period_start=period_start,
            period_end=period_end,
            categories=categories,
        )

    def start_conversation(self) -> ChatBudgetImportResponse:
        """Start a new budget import conversation.

        Returns:
            Initial greeting message
        """
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

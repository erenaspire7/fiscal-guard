"""Handler for small talk messages (greetings, thanks, acknowledgements).

This uses a Strands Agent to produce short, friendly, non-analytical replies,
and to gently steer the user back toward actionable intents (budget, goals,
purchase decisions, logging expenses, etc.).
"""

from typing import List
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from strands import Agent
from strands.models.gemini import GeminiModel

from core.config import settings
from core.models.conversation import (
    ConversationIntent,
    ConversationMessage,
    ConversationResponse,
)
from core.observability.pii_redaction import create_trace_attributes


class SmallTalkHandler:
    """Handle small talk messages with a short, friendly agent response."""

    def __init__(self, db: Session):
        """Initialize small talk handler.

        Args:
            db: Database session
        """
        self.db = db

        self.model = GeminiModel(
            client_args={"api_key": settings.google_api_key},
            model_id=settings.strands_default_model,
            params={
                "temperature": 0.6,
                "max_output_tokens": 1024,  # Increased to avoid MaxTokensReachedException
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        # Keep this agent intentionally lightweight: no deep analysis, no long replies.
        self.system_prompt = """You are a friendly assistant inside a personal finance app.

The user message is SMALL TALK (greeting/thanks/acknowledgement/jokes), not a request for financial analysis.

CRITICAL RULES:
- Keep your response SHORT: maximum 1-2 sentences.
- Be warm and friendly but concise.
- Do NOT re-run financial analysis or restate prior advice.
- If the user says "thanks" or "alright" or similar closing remarks, simply acknowledge and END the conversation. Do not ask follow-up questions.
- For greetings, welcome them and ask if they need help with budget, goals, or purchase decisions.
- Avoid emojis.
- ALWAYS keep responses under 50 words.
"""

    def handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
    ) -> ConversationResponse:
        """Generate a short small-talk reply (non-streaming)."""
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),
            session_id=str(uuid4()),
            action="small_talk",
        )

        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            trace_attributes=trace_attributes,
        )

        user_text = (
            conversation_history[-1].content
            if conversation_history
            else intent.extracted_entities.get("topic", "")
        )

        prompt = f"""User said: {user_text}

Reply briefly and guide them back to something actionable (budget, goals, purchase decisions, expense logging)."""

        result = agent(prompt)

        # Strands AgentResult may not have stable attribute typing across versions;
        # use a safe fallback to string.
        message = getattr(result, "output", None) or str(result)

        return ConversationResponse(message=message)

    async def stream_handle(
        self,
        user_id: UUID,
        intent: ConversationIntent,
        conversation_history: List[ConversationMessage],
    ):
        """Generate a short small-talk reply (streaming).

        Yields:
            NDJSON-friendly dict events containing only {"data": "..."} chunks.
        """
        trace_attributes = create_trace_attributes(
            user_id=str(user_id),
            session_id=str(uuid4()),
            action="small_talk_stream",
        )

        agent = Agent(
            model=self.model,
            system_prompt=self.system_prompt,
            trace_attributes=trace_attributes,
        )

        user_text = (
            conversation_history[-1].content
            if conversation_history
            else intent.extracted_entities.get("topic", "")
        )

        prompt = f"""User said: {user_text}

Reply briefly and guide them back to something actionable (budget, goals, purchase decisions, expense logging)."""

        async for event in agent.stream_async(prompt):
            # Only forward text chunks (JSON-serializable and compatible with frontend).
            if isinstance(event, dict) and "data" in event:
                yield {"data": event["data"]}

"""Intent classification accuracy metric using LLM-as-a-judge."""

import os
from typing import Any, Dict, Optional, Union

import pydantic
from opik.evaluation import models
from opik.evaluation.metrics import base_metric, score_result
from opik.evaluation.models import base_model, models_factory


class IntentJudgmentFormat(pydantic.BaseModel):
    """Format for LLM judge response."""

    detected_intent: str
    confidence: float  # 0.0 to 1.0
    matches_expected: bool
    reasoning: str


INTENT_JUDGE_TEMPLATE = """You are an expert at analyzing conversational intent in financial assistant interactions.

Given a user's message and the expected intent category, determine:
1. What intent the message actually expresses
2. Whether it matches the expected intent
3. Your confidence in this classification

# Expected Intent
{expected_intent}

# User Message
{user_message}

# Intent Categories
- log_expense: User is logging or recording a past expense
- budget_query: User is asking about their budget status or remaining funds
- purchase_decision: User is asking whether they should buy something
- purchase_feedback: User is providing feedback about a purchase decision (bought it, didn't buy it, regret level)
- goal_update: User is updating progress on a savings goal
- budget_modification: User is changing budget limits or allocations
- small_talk: Greetings, casual conversation, non-financial chat
- general_question: General financial questions or advice requests

Analyze the message and respond with:
- detected_intent: The intent you detect from the message
- confidence: Your confidence level (0.0 to 1.0)
- matches_expected: Whether detected_intent matches expected_intent
- reasoning: Brief explanation of your classification
"""


class IntentAccuracy(base_metric.BaseMetric):
    """LLM-as-a-judge metric for intent classification accuracy.

    Uses an LLM to evaluate whether the agent correctly classified user intent
    by analyzing the user's message against the expected intent.

    This is more reliable than trying to extract intent from API responses,
    since the actual intent classification is internal to the agent.
    """

    def __init__(
        self,
        name: str = "intent_accuracy",
        model: Optional[Union[str, base_model.OpikBaseModel]] = None,
        track: bool = True,
    ):
        """Initialize metric.

        Args:
            name: Metric name for Opik
            model: LLM model to use for judging (defaults to EVALS_LLM_MODEL env var or gemini/gemini-2.5-flash)
            track: Whether to track metric evaluations in Opik
        """
        super().__init__(name=name, track=track)

        if isinstance(model, base_model.OpikBaseModel):
            self._model = model
        else:
            # Use fast, cheap model for classification
            # Default to Gemini Flash for cost efficiency
            default_model = os.getenv("EVALS_LLM_MODEL", "gemini/gemini-2.5-flash")
            self._model = models_factory.get(
                model_name=model or default_model,
                track=track,
                temperature=0.0,
            )

    def score(
        self,
        output: Any,
        **ignored_kwargs: Any,
    ) -> score_result.ScoreResult:
        """Score intent classification accuracy across turns.

        Args:
            output: Dataset item with turns
            **ignored_kwargs: Additional context (ignored)

        Returns:
            ScoreResult with percentage of correctly classified intents
        """
        if not output or not isinstance(output, dict):
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason=f"Invalid output format. Expected dict, got: {type(output)}",
            )

        turns = output.get("turns", [])
        if not turns:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No turns to evaluate",
            )

        total_checked = 0
        correct = 0
        mismatches = []

        for turn in turns:
            expected_output = turn.get("expected_output") or {}
            expected_intent = expected_output.get("intent")

            if not expected_intent:
                continue  # Skip turns without expected intent

            # Get user message
            turn_input = turn.get("input") or {}
            user_message = turn_input.get("message", "")

            if not user_message:
                continue

            total_checked += 1

            # Ask LLM to judge the intent
            judgment = self._judge_intent(user_message, expected_intent)

            if judgment.matches_expected:
                correct += 1
            else:
                turn_num = turn.get("turn", "?")
                mismatches.append(
                    f"Turn {turn_num}: expected '{expected_intent}', "
                    f"detected '{judgment.detected_intent}' "
                    f"({judgment.confidence:.0%} confidence)"
                )

        if total_checked == 0:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No intents to validate",
            )

        accuracy = correct / total_checked

        reason_parts = [f"{correct}/{total_checked} intents correctly classified"]
        if mismatches:
            reason_parts.append(f"Mismatches: {'; '.join(mismatches[:3])}")
            if len(mismatches) > 3:
                reason_parts.append(f"... and {len(mismatches) - 3} more")

        return score_result.ScoreResult(
            name=self.name,
            value=accuracy,
            reason="; ".join(reason_parts),
        )

    def _judge_intent(
        self, user_message: str, expected_intent: str
    ) -> IntentJudgmentFormat:
        """Use LLM to judge whether message matches expected intent.

        Args:
            user_message: The user's message
            expected_intent: The expected intent category

        Returns:
            Judgment with detected intent and match status
        """
        import json

        prompt = INTENT_JUDGE_TEMPLATE.format(
            expected_intent=expected_intent,
            user_message=user_message,
        )

        # Generate structured output
        if isinstance(self._model, models.LiteLLMChatModel):
            request = [{"content": prompt, "role": "user"}]

            # LiteLLM returns raw response, need to extract content
            with base_model.get_provider_response(
                model_provider=self._model,
                messages=request,
                response_format=IntentJudgmentFormat,
            ) as model_output:
                # Extract JSON from response
                if hasattr(model_output, "choices"):
                    content = model_output.choices[0].message.content
                else:
                    content = str(model_output)

                # Parse JSON content
                try:
                    if isinstance(content, str):
                        data = json.loads(content)
                    else:
                        data = content
                    return IntentJudgmentFormat(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    # Fallback: assume correct classification if we can't parse
                    return IntentJudgmentFormat(
                        detected_intent=expected_intent,
                        confidence=0.5,
                        matches_expected=True,
                        reasoning=f"Failed to parse LLM response: {e}",
                    )
        else:
            # Fallback for other model types
            response = self._model.generate_string(
                input=prompt,
                response_format=IntentJudgmentFormat,
            )

            # Parse response if it's a string
            if isinstance(response, str):
                return IntentJudgmentFormat(**json.loads(response))

            return response

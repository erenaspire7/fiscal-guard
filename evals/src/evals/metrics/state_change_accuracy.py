"""State change accuracy metric using LLM-as-a-judge for multi-turn scenarios."""

import os
from typing import Any, Dict, List, Optional, Union

import pydantic
from opik.evaluation import models
from opik.evaluation.metrics import base_metric, score_result
from opik.evaluation.models import base_model, models_factory


class StateChangeJudgmentFormat(pydantic.BaseModel):
    """Format for LLM judge response on state changes."""

    expected_changes_valid: bool
    validation_errors: List[str]
    confidence: float  # 0.0 to 1.0
    reasoning: str


STATE_CHANGE_JUDGE_TEMPLATE = """You are an expert at validating database state changes in financial applications.

Analyze whether the expected state changes align with the actual validation results.

# Turn Context
Turn {turn_number}: "{user_message}"
Assistant Response: "{assistant_message}"

# Expected State Changes
{expected_changes}

# Actual Validation Results
Validation Status: {validation_status}
Checks Performed: {validation_checked}
Errors: {validation_errors}

# Your Task
Determine if the state changes were correctly validated. Consider:
1. Do the validation results match what we'd expect from the conversation?
2. Are the errors (if any) legitimate issues or false positives?
3. If validation passed, did the expected changes actually occur?
4. If validation failed, is it because state changes didn't happen or because of other issues?

Respond with:
- expected_changes_valid: true if state changes were properly validated
- validation_errors: list of any actual errors you identify (empty if none)
- confidence: your confidence in this assessment (0.0 to 1.0)
- reasoning: brief explanation of your judgment
"""


class StateChangeAccuracy(base_metric.BaseMetric):
    """LLM-as-a-judge metric for database state change validation.

    Uses an LLM to evaluate whether expected state changes were correctly
    validated, considering the conversation context and validation results.

    This is more nuanced than simple pass/fail because it can:
    - Identify false positives in validation errors
    - Understand context from the conversation
    - Assess whether validation failures are legitimate
    """

    def __init__(
        self,
        name: str = "state_change_accuracy",
        model: Optional[Union[str, base_model.OpikBaseModel]] = None,
        track: bool = True,
    ):
        """Initialize metric.

        Args:
            name: Metric name for Opik
            model: LLM model to use for judging (defaults to EVALS_STATE_JUDGE_MODEL env var or gemini/gemini-2.5-flash)
            track: Whether to track metric evaluations in Opik
        """
        super().__init__(name=name, track=track)

        if isinstance(model, base_model.OpikBaseModel):
            self._model = model
        else:
            # Use model for complex validation reasoning
            # Can use same model as intent or a more powerful one via env var
            default_model = os.getenv(
                "EVALS_STATE_JUDGE_MODEL", "gemini/gemini-2.5-flash"
            )
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
        """Score state change validation accuracy.

        Args:
            output: Dataset item with turns containing state_validation
            **ignored_kwargs: Additional context (ignored)

        Returns:
            ScoreResult with percentage of correctly validated state changes
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

        total_with_changes = 0
        correctly_validated = 0
        issues = []

        for turn in turns:
            expected_output = turn.get("expected_output", {})
            expected_changes = expected_output.get("state_changes", [])

            if not expected_changes:
                continue  # Skip turns without expected state changes

            total_with_changes += 1

            # Get turn context
            turn_num = turn.get("turn", "?")
            turn_input = turn.get("input") or {}
            user_message = turn_input.get("message", "")

            actual_output = turn.get("actual_output") or {}
            assistant_message = actual_output.get("message", "")

            state_validation = turn.get("state_validation") or {}

            # Use LLM to judge the validation
            judgment = self._judge_state_change(
                turn_number=turn_num,
                user_message=user_message,
                assistant_message=assistant_message,
                expected_changes=expected_changes,
                validation_valid=state_validation.get("valid", False),
                validation_checked=state_validation.get("checked", 0),
                validation_errors=state_validation.get("errors", []),
            )

            if judgment.expected_changes_valid:
                correctly_validated += 1
            else:
                issues.append(f"Turn {turn_num}: {judgment.reasoning[:100]}")

        if total_with_changes == 0:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No state changes to validate",
            )

        accuracy = correctly_validated / total_with_changes

        reason_parts = [
            f"{correctly_validated}/{total_with_changes} state changes correctly validated"
        ]
        if issues:
            reason_parts.append(f"Issues: {'; '.join(issues[:3])}")
            if len(issues) > 3:
                reason_parts.append(f"... and {len(issues) - 3} more")

        return score_result.ScoreResult(
            name=self.name,
            value=accuracy,
            reason="; ".join(reason_parts),
        )

    def _judge_state_change(
        self,
        turn_number: int,
        user_message: str,
        assistant_message: str,
        expected_changes: List[Dict[str, Any]],
        validation_valid: bool,
        validation_checked: int,
        validation_errors: List[str],
    ) -> StateChangeJudgmentFormat:
        """Use LLM to judge whether state changes were correctly validated.

        Args:
            turn_number: Turn number
            user_message: User's message
            assistant_message: Assistant's response
            expected_changes: Expected state changes
            validation_valid: Whether validation passed
            validation_checked: Number of validations performed
            validation_errors: Validation error messages

        Returns:
            Judgment on validation correctness
        """
        # Format expected changes for readability
        changes_text = "\n".join(
            f"- {change.get('field', '?')}: {change.get('operation', '?')} {change.get('value', '?')}"
            for change in expected_changes
        )

        errors_text = (
            "\n".join(f"- {err}" for err in validation_errors)
            if validation_errors
            else "None"
        )

        prompt = STATE_CHANGE_JUDGE_TEMPLATE.format(
            turn_number=turn_number,
            user_message=user_message,
            assistant_message=assistant_message,
            expected_changes=changes_text,
            validation_status="PASSED" if validation_valid else "FAILED",
            validation_checked=validation_checked,
            validation_errors=errors_text,
        )

        # Generate structured output
        import json

        if isinstance(self._model, models.LiteLLMChatModel):
            request = [{"content": prompt, "role": "user"}]

            # LiteLLM returns raw response, need to extract content
            with base_model.get_provider_response(
                model_provider=self._model,
                messages=request,
                response_format=StateChangeJudgmentFormat,
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
                    return StateChangeJudgmentFormat(**data)
                except (json.JSONDecodeError, TypeError) as e:
                    # Fallback: assume validation is correct if we can't parse
                    return StateChangeJudgmentFormat(
                        expected_changes_valid=validation_valid,
                        validation_errors=[],
                        confidence=0.5,
                        reasoning=f"Failed to parse LLM response: {e}",
                    )
        else:
            # Fallback for other model types
            response = self._model.generate_string(
                input=prompt,
                response_format=StateChangeJudgmentFormat,
            )

            # Parse response if it's a string
            if isinstance(response, str):
                return StateChangeJudgmentFormat(**json.loads(response))

            return response

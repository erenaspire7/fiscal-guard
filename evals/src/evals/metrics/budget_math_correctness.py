"""Budget math correctness metric."""

import re
from typing import Any, Dict

from opik.evaluation.metrics import base_metric, score_result


class BudgetMathCorrectness(base_metric.BaseMetric):
    """Verify budget percentage calculations are correct.

    Checks if the agent correctly calculates what percentage of the budget
    would be used by the purchase.
    """

    def __init__(self, tolerance: float = 5.0, name: str = "budget_math_correctness"):
        """Initialize metric.

        Args:
            tolerance: Maximum allowed percentage difference (default: 5%)
            name: Metric name for Opik
        """
        super().__init__(name=name)
        self.tolerance = tolerance

    def score(
        self,
        output: Any,
        expected_output: Dict[str, Any],
        **ignored_kwargs: Any,
    ) -> score_result.ScoreResult:
        """Score the output.

        Args:
            output: Actual output from the agent
            expected_output: Expected output schema
            **ignored_kwargs: Additional context (ignored)

        Returns:
            Score object with value 0.0-1.0
        """
        # Extract expected budget analysis
        budget_analysis = expected_output.get("budget_analysis")
        if not budget_analysis:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No budget analysis specified - skipping evaluation",
            )

        expected_percentage = budget_analysis.get("percentage_used")
        if expected_percentage is None:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No expected percentage_used specified - skipping evaluation",
            )

        # Extract actual percentage from reasoning text
        # The agent should mention the percentage in its reasoning
        if not output or not isinstance(output, dict):
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason=f"Invalid output format. Expected dict, got: {type(output)}",
            )

        message = output.get("message", "")

        # Look for percentage patterns like "225%", "22.5%", etc.
        percentage_pattern = r"(\d+(?:\.\d+)?)\s*%"
        matches = re.findall(percentage_pattern, message)

        if not matches:
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason=f"No percentage found in reasoning. Expected ~{expected_percentage}%",
            )

        # Check if any match is close to expected
        percentages_found = [float(m) for m in matches]
        closest = min(percentages_found, key=lambda x: abs(x - expected_percentage))
        difference = abs(closest - expected_percentage)

        is_correct = difference <= self.tolerance

        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if is_correct else 0.0,
            reason=f"Expected: {expected_percentage}%, Found: {percentages_found}, Closest: {closest}%, Difference: {difference:.1f}% (tolerance: ±{self.tolerance}%)",
        )

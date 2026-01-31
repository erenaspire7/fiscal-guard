"""Decision category accuracy metric."""

from typing import Any, Dict

from opik.evaluation.metrics import base_metric, score_result


class DecisionCategoryAccuracy(base_metric.BaseMetric):
    """Measure accuracy of decision category classification.

    Categories: strong_no, mild_no, neutral, mild_yes, strong_yes
    """

    def __init__(self, name: str = "decision_category_accuracy"):
        """Initialize metric.

        Args:
            name: Metric name for Opik
        """
        super().__init__(name=name)

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
            Score object with value 0.0 or 1.0
        """
        # Extract expected category
        expected_category = expected_output.get("decision_category")
        if expected_category is None:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No expected decision_category specified - skipping evaluation",
            )

        # Extract actual category from output
        if not output or not isinstance(output, dict):
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason=f"Invalid output format. Expected dict, got: {type(output)}",
            )

        metadata = output.get("metadata", {})
        actual_category = metadata.get("category")

        if actual_category is None:
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason="No decision category found in output metadata",
            )

        # Exact match required
        is_match = actual_category == expected_category

        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if is_match else 0.0,
            reason=f"Expected: {expected_category}, Actual: {actual_category}",
        )

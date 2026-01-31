"""Score accuracy metric for purchase decisions."""

from typing import Any, Dict, Optional

from opik.evaluation.metrics import base_metric, score_result


class ScoreAccuracy(base_metric.BaseMetric):
    """Measure accuracy of decision scores (1-10).

    Scores are considered accurate if they are within ±1 of the expected value.
    """

    def __init__(self, tolerance: int = 1, name: str = "score_accuracy"):
        """Initialize metric.

        Args:
            tolerance: Maximum allowed difference from expected score (default: 1)
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
            output: Actual output from the agent (full response dict)
            expected_output: Expected output schema
            **ignored_kwargs: Additional context (ignored)

        Returns:
            Score object with value 0.0-1.0 and reason
        """
        # Extract expected score
        expected_score = expected_output.get("score")
        if expected_score is None:
            return score_result.ScoreResult(
                name=self.name,
                value=1.0,
                reason="No expected score specified - skipping evaluation",
            )

        # Extract actual score from output
        # Output structure: {"message": "...", "metadata": {"score": X, ...}}
        if not output or not isinstance(output, dict):
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason=f"Invalid output format. Expected dict with metadata.score, got: {type(output)}",
            )

        metadata = output.get("metadata", {})
        actual_score = metadata.get("score")

        if actual_score is None:
            return score_result.ScoreResult(
                name=self.name,
                value=0.0,
                reason="No score found in output metadata",
            )

        # Check if within tolerance
        difference = abs(actual_score - expected_score)
        is_accurate = difference <= self.tolerance

        return score_result.ScoreResult(
            name=self.name,
            value=1.0 if is_accurate else 0.0,
            reason=f"Expected: {expected_score}, Actual: {actual_score}, Difference: {difference} (tolerance: ±{self.tolerance})",
        )

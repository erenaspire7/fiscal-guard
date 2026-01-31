"""Run evaluations on Opik datasets."""

import json
import sys
from pathlib import Path
from typing import List, Optional

from opik import Opik
from opik.evaluation import evaluate

from evals.metrics import (
    BudgetMathCorrectness,
    DecisionCategoryAccuracy,
    IntentAccuracy,
    ScoreAccuracy,
    StateChangeAccuracy,
)


class EvaluationRunner:
    """Run evaluations on Opik datasets."""

    def __init__(self, opik_workspace: Optional[str] = None):
        """Initialize evaluation runner.

        Args:
            opik_workspace: Opik workspace name (optional)
        """
        self.opik_client = Opik(workspace=opik_workspace)

    def evaluation_task(self, dataset_entry: dict) -> dict:
        """Evaluation task for Opik.

        This is called for each entry in the dataset.
        Since we've already run the scenarios and captured actual_output,
        we just return it here for scoring.

        Args:
            dataset_entry: Entry from the dataset

        Returns:
            Dict with output and expected for scoring
        """
        # For multi-turn scenarios, the whole entry serves as output
        if "turns" in dataset_entry:
            return {
                "output": dataset_entry,
                "expected_output": {},
                "context": dataset_entry.get("context"),
            }

        return {
            "output": dataset_entry.get("actual_output"),
            "expected_output": dataset_entry.get("expected_output"),
            "context": dataset_entry.get("context"),
        }

    def run_evaluation(
        self,
        dataset_name: str,
        metrics: Optional[List[str]] = None,
        experiment_name: Optional[str] = None,
    ) -> dict:
        """Run evaluation on a dataset.

        Args:
            dataset_name: Name of the Opik dataset
            metrics: List of metric names to use (default: all)
            experiment_name: Name for the experiment (default: dataset_name + timestamp)

        Returns:
            Evaluation results summary
        """
        print(f"\n🔬 Running evaluation: {dataset_name}")

        # Get dataset
        try:
            dataset = self.opik_client.get_dataset(name=dataset_name)
            print(f"   Dataset found: {len(dataset.get_items())} items")
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            sys.exit(1)

        # Select metrics
        available_metrics = {
            "score_accuracy": ScoreAccuracy(),
            "decision_category_accuracy": DecisionCategoryAccuracy(),
            "budget_math_correctness": BudgetMathCorrectness(),
            "state_change_accuracy": StateChangeAccuracy(),
            "intent_accuracy": IntentAccuracy(),
        }

        if metrics:
            selected_metrics = [
                available_metrics[m] for m in metrics if m in available_metrics
            ]
            if not selected_metrics:
                print(
                    f"❌ No valid metrics specified. Available: {list(available_metrics.keys())}"
                )
                sys.exit(1)
        else:
            # Use all metrics by default
            selected_metrics = list(available_metrics.values())

        print(f"   Metrics: {[m.name for m in selected_metrics]}")

        # Run evaluation
        print(f"\n   Running evaluation...")
        evaluation = evaluate(
            dataset=dataset,
            task=self.evaluation_task,
            scoring_metrics=selected_metrics,
            experiment_config={
                "experiment_name": experiment_name or f"{dataset_name}-eval",
            },
        )

        print(f"\n✅ Evaluation complete!")

        # Print summary
        print(f"\n📊 Results Summary:")
        for metric in selected_metrics:
            print(f"   {metric.name}: {evaluation}")

        return evaluation

    def run_all_evaluations(self, dataset_prefix: str = "fiscal-guard-") -> List[dict]:
        """Run evaluations on all datasets with a given prefix.

        Args:
            dataset_prefix: Prefix to filter datasets by

        Returns:
            List of evaluation results
        """
        print(
            f"\n🔬 Running all evaluations for datasets starting with: {dataset_prefix}"
        )

        # List all datasets
        datasets = self.opik_client.list_datasets()
        matching_datasets = [
            ds for ds in datasets if ds["name"].startswith(dataset_prefix)
        ]

        if not matching_datasets:
            print(f"❌ No datasets found with prefix: {dataset_prefix}")
            return []

        print(f"   Found {len(matching_datasets)} datasets")

        # Run evaluation on each
        results = []
        for dataset in matching_datasets:
            result = self.run_evaluation(dataset["name"])
            results.append(result)

        return results


def main():
    """CLI entry point for running evaluations."""
    import argparse

    parser = argparse.ArgumentParser(description="Run evaluations on Opik datasets")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Dataset name to evaluate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all fiscal-guard datasets",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="+",
        choices=[
            "score_accuracy",
            "decision_category_accuracy",
            "budget_math_correctness",
            "state_change_accuracy",
            "intent_accuracy",
        ],
        help="Metrics to use (default: all)",
    )
    parser.add_argument(
        "--experiment-name",
        type=str,
        help="Name for the experiment (optional)",
    )
    parser.add_argument(
        "--opik-workspace",
        type=str,
        help="Opik workspace name (optional)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Save results to JSON file (optional)",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dataset and not args.all:
        print("❌ Must specify either --dataset or --all")
        sys.exit(1)

    # Run evaluation
    runner = EvaluationRunner(opik_workspace=args.opik_workspace)

    if args.all:
        results = runner.run_all_evaluations()
    else:
        results = runner.run_evaluation(
            dataset_name=args.dataset,
            metrics=args.metrics,
            experiment_name=args.experiment_name,
        )

    # Save results if output specified
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {args.output}")


if __name__ == "__main__":
    main()

"""Generate Opik datasets from scenario files."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from opik import Opik

from evals.datasets.api_client import FiscalGuardAPIClient
from evals.datasets.auth import AuthClient
from evals.scenarios.schema import Scenario, ScenarioCollection


class DatasetGenerator:
    """Generate Opik datasets from test scenarios."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        opik_workspace: Optional[str] = None,
    ):
        """Initialize dataset generator.

        Args:
            api_url: Base URL for Fiscal Guard API
            opik_workspace: Opik workspace name (optional)
        """
        self.api_client = FiscalGuardAPIClient(api_url)
        self.auth_client = AuthClient(api_url)
        self.opik_client = Opik(workspace=opik_workspace)

        # Verify API is healthy
        if not self.api_client.health_check():
            raise RuntimeError(
                f"API at {api_url} is not healthy. Make sure the API is running."
            )

    def load_scenario_file(self, scenario_path: Path) -> ScenarioCollection:
        """Load and validate a scenario file.

        Args:
            scenario_path: Path to scenario JSON file

        Returns:
            Validated scenario collection

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

        with open(scenario_path, "r") as f:
            data = json.load(f)

        return ScenarioCollection(**data)

    def run_scenario(self, scenario: Scenario, prompt_version: str) -> Dict[str, Any]:
        """Run a single scenario against the API.

        Args:
            scenario: Scenario to run
            prompt_version: Version of prompt being tested

        Returns:
            Dataset entry with input, expected, actual, and metadata
        """
        print(f"  Running scenario: {scenario.id}")

        # Login as persona
        token = self.auth_client.login_as_persona(scenario.persona)

        # Convert conversation history to API format
        conversation_history = [
            {"role": msg.role, "content": msg.content}
            for msg in scenario.input.conversation_history
        ]

        # Call the API
        try:
            response = self.api_client.send_chat_message(
                message=scenario.input.message,
                token=token,
                conversation_history=conversation_history,
            )

            actual_output = response
            error = None
        except Exception as e:
            actual_output = None
            error = str(e)

        # Build dataset entry
        entry = {
            "input": scenario.input.model_dump(),
            "context": {
                "persona": scenario.persona,
                "scenario_id": scenario.id,
                "scenario_tags": scenario.tags,
                "scenario_description": scenario.description,
                "month": scenario.context.month,
            },
            "expected_output": scenario.expected_output.model_dump(),
            "actual_output": actual_output,
            "error": error,
            "metadata": {
                "prompt_version": prompt_version,
                "scenario_file": scenario.id.split("_")[
                    0
                ],  # e.g., "sarah" from "sarah_watch_over_budget"
            },
        }

        return entry

    def generate_dataset(
        self,
        scenario_path: Path,
        dataset_name: str,
        prompt_version: str = "v1.0",
    ) -> str:
        """Generate an Opik dataset from a scenario file.

        Note: Opik automatically creates a new version each time insert() is called,
        so running this multiple times on the same dataset will create v1, v2, v3, etc.

        Args:
            scenario_path: Path to scenario JSON file
            dataset_name: Name for the Opik dataset
            prompt_version: Version of prompt being tested

        Returns:
            Dataset name

        Raises:
            FileNotFoundError: If scenario file doesn't exist
            RuntimeError: If API is not healthy
        """
        print(f"\n📊 Generating dataset: {dataset_name}")
        print(f"   Scenario file: {scenario_path}")
        print(f"   Prompt version: {prompt_version}")

        # Load scenarios
        collection = self.load_scenario_file(scenario_path)
        print(f"   Loaded {len(collection.scenarios)} scenarios")

        # Get or create dataset
        # Note: Opik will auto-version on insert()
        dataset = self.opik_client.get_or_create_dataset(name=dataset_name)

        # Clear existing entries to create a clean new version
        print(f"   Clearing existing entries...")
        dataset.clear()

        # Run each scenario
        entries = []
        for i, scenario in enumerate(collection.scenarios, 1):
            print(f"   [{i}/{len(collection.scenarios)}]", end=" ")
            entry = self.run_scenario(scenario, prompt_version)
            entries.append(entry)

        # Insert into Opik dataset
        # This automatically creates a new version (v1, v2, v3, etc.)
        print(f"\n   Inserting {len(entries)} entries into Opik dataset...")
        print(f"   Note: Opik will automatically create a new version")
        dataset.insert(entries)

        print(f"✅ Dataset generated: {dataset_name}")
        print(f"   Total entries: {len(entries)}")
        print(f"   Failures: {sum(1 for e in entries if e['error'] is not None)}")

        return dataset_name


def main():
    """CLI entry point for dataset generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Opik datasets from scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        required=True,
        help="Path to scenario JSON file",
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        help="Name for Opik dataset (default: derived from scenario file)",
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--prompt-version",
        type=str,
        default="v1.0",
        help="Prompt version being tested (default: v1.0)",
    )
    parser.add_argument(
        "--opik-workspace",
        type=str,
        help="Opik workspace name (optional)",
    )

    args = parser.parse_args()

    # Derive dataset name from scenario file if not provided
    dataset_name = args.dataset_name
    if not dataset_name:
        # e.g., scenarios/purchase_decisions/sarah_basic.json -> fiscal-guard-sarah-basic
        dataset_name = f"fiscal-guard-{args.scenario.stem}"

    # Generate dataset
    generator = DatasetGenerator(
        api_url=args.api_url,
        opik_workspace=args.opik_workspace,
    )

    try:
        generator.generate_dataset(
            scenario_path=args.scenario,
            dataset_name=dataset_name,
            prompt_version=args.prompt_version,
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

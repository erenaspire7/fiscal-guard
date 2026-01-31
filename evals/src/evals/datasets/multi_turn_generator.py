"""Generate Opik datasets from multi-turn scenario files."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.config import settings
from core.database.session import DatabaseManager
from opik import Opik
from sqlalchemy.orm import Session

from evals.datasets.api_client import FiscalGuardAPIClient
from evals.datasets.auth import AuthClient
from evals.scenarios.schema import MultiTurnScenario, ScenarioCollection, Turn


class MultiTurnDatasetGenerator:
    """Generate Opik datasets from multi-turn test scenarios.

    Connects to the same PostgreSQL database as the API to track state changes.
    """

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        opik_workspace: Optional[str] = None,
        prompt_override: Optional[Dict[str, str]] = None,
    ):
        """Initialize multi-turn dataset generator.

        Args:
            api_url: Base URL for Fiscal Guard API
            opik_workspace: Opik workspace name (optional)
            prompt_override: Optional dict with agent_type and prompt for testing
        """
        self.api_client = FiscalGuardAPIClient(api_url)
        self.opik_client = Opik(workspace=opik_workspace)
        self.prompt_override = prompt_override
        self.session_id = None

        # Initialize database connection (same as API uses)
        database_url = os.getenv("DATABASE_URL") or settings.database_url
        self.db_manager = DatabaseManager(database_url)

        # Verify API is healthy
        if not self.api_client.health_check():
            raise RuntimeError(
                f"API at {api_url} is not healthy. Make sure the API is running."
            )

    def load_scenario_file(self, scenario_path: Path) -> ScenarioCollection:
        """Load and validate a multi-turn scenario file.

        Args:
            scenario_path: Path to scenario JSON file

        Returns:
            Validated scenario collection

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid or not multi_turn type
        """
        if not scenario_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {scenario_path}")

        with open(scenario_path, "r") as f:
            data = json.load(f)

        collection = ScenarioCollection(**data)

        if collection.type != "multi_turn":
            raise ValueError(
                f"Expected multi_turn scenarios, got: {collection.type}. "
                "Use the standard generator for single_turn scenarios."
            )

        return collection

    def run_multi_turn_scenario(
        self,
        scenario: MultiTurnScenario,
        prompt_version: str,
        internal_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a multi-turn scenario against the API.

        Args:
            scenario: Multi-turn scenario to run
            prompt_version: Version of prompt being tested
            internal_token: Optional internal API token for prompt override

        Returns:
            Dataset entry with all turns and state changes
        """
        print(f"  Running multi-turn scenario: {scenario.id}")
        print(f"    Turns: {len(scenario.turns)}")

        # Set up prompt override if specified
        if self.prompt_override and internal_token:
            from uuid import uuid4

            self.session_id = str(uuid4())

            try:
                self.api_client.set_prompt_override(
                    agent_type=self.prompt_override["agent_type"],
                    prompt=self.prompt_override["prompt"],
                    session_id=self.session_id,
                    internal_token=internal_token,
                )
                print(f"    ✓ Prompt override set (session: {self.session_id})")
            except Exception as e:
                print(f"    ⚠️  Failed to set prompt override: {e}")
                self.session_id = None

        # Login as persona
        token = self.auth_client.login_as_persona(scenario.persona)

        # Track conversation history across turns
        conversation_history = []

        # Track all turn results
        turn_results = []

        # Run each turn sequentially
        for turn in scenario.turns:
            print(
                f"    Turn {turn.turn}/{len(scenario.turns)}: {turn.description or turn.input.message[:50]}"
            )

            # Get initial state before turn (for validation)
            initial_state = self._capture_state(scenario.persona)

            # Call the API (with session_id for prompt override)
            try:
                response = self.api_client.send_chat_message(
                    message=turn.input.message,
                    token=token,
                    conversation_history=conversation_history,
                    session_id=self.session_id,
                )

                # Get state after turn
                final_state = self._capture_state(scenario.persona)

                # Validate state changes
                state_validation = self._validate_state_changes(
                    initial_state=initial_state,
                    final_state=final_state,
                    expected_changes=turn.expected_output.state_changes,
                )

                turn_result = {
                    "turn": turn.turn,
                    "input": turn.input.model_dump(),
                    "expected_output": turn.expected_output.model_dump(),
                    "actual_output": response,
                    "state_validation": state_validation,
                    "error": None,
                }

                # Update conversation history for next turn
                conversation_history.append(
                    {
                        "role": "user",
                        "content": turn.input.message,
                    }
                )
                conversation_history.append(
                    {
                        "role": "assistant",
                        "content": response.get("message", ""),
                    }
                )

            except Exception as e:
                turn_result = {
                    "turn": turn.turn,
                    "input": turn.input.model_dump(),
                    "expected_output": turn.expected_output.model_dump(),
                    "actual_output": None,
                    "state_validation": {"valid": False, "errors": [str(e)]},
                    "error": str(e),
                }

            turn_results.append(turn_result)

        # Build dataset entry
        entry = {
            "input": {
                "scenario_id": scenario.id,
                "persona": scenario.persona,
                "total_turns": len(scenario.turns),
            },
            "context": {
                "scenario_id": scenario.id,
                "persona": scenario.persona,
                "scenario_tags": scenario.tags,
                "scenario_description": scenario.description,
                "month": scenario.context.month,
            },
            "turns": turn_results,
            "metadata": {
                "prompt_version": prompt_version,
                "scenario_file": scenario.id.split("_")[0],
                "total_turns": len(scenario.turns),
                "successful_turns": sum(1 for t in turn_results if not t["error"]),
            },
        }

        return entry

    def _capture_state(self, persona: str) -> Dict[str, Any]:
        """Capture current database state for a persona.

        Args:
            persona: Persona name

        Returns:
            Dict with budget categories and goals
        """
        db = next(self.db_manager.get_session())
        try:
            from core.database.models import Budget, Goal, User

            # Get user
            email = f"demo+{persona}@fiscalguard.app"
            user = db.query(User).filter(User.email == email).first()
            if not user:
                return {"error": f"User not found: {email}"}

            # Get current budget
            budget = (
                db.query(Budget)
                .filter(Budget.user_id == user.user_id)
                .order_by(Budget.created_at.desc())
                .first()
            )

            budget_state = {}
            if budget:
                budget_state = {
                    "categories": budget.categories.copy() if budget.categories else {}
                }

            # Get goals
            goals = db.query(Goal).filter(Goal.user_id == user.user_id).all()
            goals_state = {
                goal.goal_name: {
                    "current_amount": float(goal.current_amount),
                    "target_amount": float(goal.target_amount),
                }
                for goal in goals
            }

            return {
                "budget": budget_state,
                "goals": goals_state,
            }
        finally:
            db.close()

    def _validate_state_changes(
        self,
        initial_state: Dict[str, Any],
        final_state: Dict[str, Any],
        expected_changes: List[Any],
    ) -> Dict[str, Any]:
        """Validate that expected state changes occurred.

        Args:
            initial_state: State before turn
            final_state: State after turn
            expected_changes: List of expected StateChange objects

        Returns:
            Validation result with errors if any
        """
        if not expected_changes:
            return {"valid": True, "checked": 0}

        errors = []

        for change in expected_changes:
            # Parse field path (e.g., "budget_categories.groceries.spent")
            parts = change.field.split(".")

            try:
                # Navigate to the field in both states
                initial_value = self._get_nested_value(initial_state, parts)
                final_value = self._get_nested_value(final_state, parts)

                # Calculate expected final value
                if change.operation == "+":
                    expected = initial_value + change.value
                elif change.operation == "-":
                    expected = initial_value - change.value
                elif change.operation == "=":
                    expected = change.value
                else:
                    errors.append(f"Unknown operation: {change.operation}")
                    continue

                # Validate (with small tolerance for floating point)
                if abs(final_value - expected) > 0.01:
                    errors.append(
                        f"{change.field}: expected {expected}, got {final_value} "
                        f"(initial: {initial_value}, operation: {change.operation}{change.value})"
                    )

            except Exception as e:
                errors.append(f"{change.field}: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "checked": len(expected_changes),
            "errors": errors,
        }

    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> float:
        """Get a nested value from a dict using a path.

        Args:
            data: Dictionary to navigate
            path: List of keys (e.g., ["budget_categories", "groceries", "spent"])
                  Will be mapped to actual state structure

        Returns:
            Value at the path

        Raises:
            KeyError: If path doesn't exist
        """
        # Map scenario field paths to actual state structure
        # Scenarios use "budget_categories" but state has "budget.categories"
        # Scenarios use "goals" which maps to "goals" directly
        mapped_path = list(path)  # Make a copy

        if len(mapped_path) > 0:
            if mapped_path[0] == "budget_categories":
                # Transform "budget_categories.X.Y" -> "budget.categories.X.Y"
                mapped_path = ["budget", "categories"] + mapped_path[1:]
            elif mapped_path[0] == "goals":
                # "goals.Emergency Fund.current_amount" stays as-is
                pass

        current = data
        for key in mapped_path:
            if isinstance(current, dict):
                current = current[key]
            else:
                raise KeyError(f"Cannot navigate to {key} in {type(current)}")

        return float(current)

    def generate_dataset(
        self,
        scenario_path: Path,
        dataset_name: str,
        prompt_version: str = "v1.0",
        internal_token: Optional[str] = None,
    ) -> str:
        """Generate an Opik dataset from a multi-turn scenario file.

        Args:
            scenario_path: Path to scenario JSON file
            dataset_name: Name for the Opik dataset
            prompt_version: Version of prompt being tested
            internal_token: Optional internal API token for prompt override

        Returns:
            Dataset name

        Raises:
            FileNotFoundError: If scenario file doesn't exist
            RuntimeError: If API is not healthy
        """
        print(f"\n📊 Generating multi-turn dataset: {dataset_name}")
        print(f"   Scenario file: {scenario_path}")
        print(f"   Prompt version: {prompt_version}")

        # Load scenarios
        collection = self.load_scenario_file(scenario_path)
        print(f"   Loaded {len(collection.scenarios)} multi-turn scenarios")

        # Get or create dataset
        # Note: Opik will auto-version on insert()
        dataset = self.opik_client.get_or_create_dataset(name=dataset_name)

        # Clear existing entries to create a clean new version
        print(f"   Clearing existing entries...")
        dataset.clear()

        # Create auth client
        self.auth_client = AuthClient(self.api_client.api_url)

        # Run each scenario
        entries = []
        for i, scenario in enumerate(collection.scenarios, 1):
            print(f"\n   [{i}/{len(collection.scenarios)}]")
            entry = self.run_multi_turn_scenario(
                scenario, prompt_version, internal_token
            )
            entries.append(entry)

        # Insert into Opik dataset
        print(f"\n   Inserting {len(entries)} entries into Opik dataset...")
        dataset.insert(entries)

        print(f"✅ Multi-turn dataset generated: {dataset_name}")
        print(f"   Total scenarios: {len(entries)}")
        print(f"   Total turns: {sum(e['metadata']['total_turns'] for e in entries)}")
        print(
            f"   Failed turns: {sum(e['metadata']['total_turns'] - e['metadata']['successful_turns'] for e in entries)}"
        )

        return dataset_name


def main():
    """CLI entry point for multi-turn dataset generation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate Opik datasets from multi-turn scenarios"
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        required=True,
        help="Path to multi-turn scenario JSON file",
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
    parser.add_argument(
        "--prompt-file",
        type=Path,
        help="Path to prompt file for override testing (optional)",
    )
    parser.add_argument(
        "--agent-type",
        type=str,
        choices=["decision_agent", "intent_classifier"],
        help="Agent type for prompt override (required if --prompt-file is used)",
    )
    parser.add_argument(
        "--internal-token",
        type=str,
        help="Internal API token (from INTERNAL_API_TOKEN env var)",
    )

    args = parser.parse_args()

    # Derive dataset name from scenario file if not provided
    dataset_name = args.dataset_name
    if not dataset_name:
        dataset_name = f"fiscal-guard-{args.scenario.stem}-mt"

    # Load prompt override if specified
    prompt_override = None
    if args.prompt_file:
        if not args.agent_type:
            print("❌ Error: --agent-type required when using --prompt-file")
            sys.exit(1)

        with open(args.prompt_file, "r") as f:
            prompt_override = {
                "agent_type": args.agent_type,
                "prompt": f.read(),
            }
        print(f"✓ Loaded prompt override from {args.prompt_file}")

    # Generate dataset
    generator = MultiTurnDatasetGenerator(
        api_url=args.api_url,
        opik_workspace=args.opik_workspace,
        prompt_override=prompt_override,
    )

    try:
        generator.generate_dataset(
            scenario_path=args.scenario,
            dataset_name=dataset_name,
            prompt_version=args.prompt_version,
            internal_token=args.internal_token,
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

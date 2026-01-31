"""Pydantic schemas for test scenarios."""

from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    """A message in conversation history."""

    role: str = Field(..., description="Role: user or assistant")
    content: str = Field(..., description="Message content")


class ScenarioInput(BaseModel):
    """Input to the agent being tested."""

    message: str = Field(..., description="User's message")
    conversation_history: List[ConversationMessage] = Field(
        default_factory=list, description="Previous conversation context"
    )


class BudgetAnalysisExpected(BaseModel):
    """Expected budget analysis output."""

    category: str = Field(..., description="Budget category")
    would_exceed: bool = Field(..., description="Whether purchase would exceed budget")
    percentage_used: Optional[float] = Field(
        None, description="Expected percentage of budget used (tolerance: ±5%)"
    )


class ExpectedOutput(BaseModel):
    """Expected output from the agent."""

    intent: Optional[str] = Field(None, description="Expected intent classification")
    score: Optional[int] = Field(None, description="Expected decision score (1-10)")
    decision_category: Optional[str] = Field(
        None, description="Expected decision category"
    )
    reasoning_must_contain: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that must appear in reasoning",
    )
    reasoning_must_not_contain: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that must NOT appear in reasoning",
    )
    must_have_alternatives: Optional[bool] = Field(
        None, description="Whether alternatives must be provided"
    )
    must_have_conditions: Optional[bool] = Field(
        None, description="Whether conditions must be provided"
    )
    budget_analysis: Optional[BudgetAnalysisExpected] = Field(
        None, description="Expected budget analysis"
    )
    extracted_entities: Optional[Dict[str, Any]] = Field(
        None, description="Expected extracted entities (for intent classification)"
    )
    confidence: Optional[float] = Field(
        None, description="Minimum expected confidence (for intent classification)"
    )


class ScenarioContext(BaseModel):
    """Context for running the scenario."""

    month: str = Field(
        "current", description="Which month's budget to use (current, or YYYY-MM)"
    )
    additional_context: Optional[str] = Field(
        None, description="Additional context to provide"
    )


class Scenario(BaseModel):
    """A single test scenario."""

    id: str = Field(..., description="Unique scenario identifier")
    persona: str = Field(..., description="Persona to test as (sarah, alex, marcus)")
    context: ScenarioContext = Field(
        default_factory=ScenarioContext, description="Scenario context"
    )
    input: ScenarioInput = Field(..., description="Input to the agent")
    expected_output: ExpectedOutput = Field(..., description="Expected agent output")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    description: Optional[str] = Field(
        None, description="Human-readable description of what this tests"
    )


class StateChange(BaseModel):
    """Expected state change in the database."""

    field: str = Field(..., description="Field path (e.g., 'budget_categories.groceries.spent')")
    operation: Literal["+", "-", "="] = Field(..., description="Operation: + (add), - (subtract), = (set)")
    value: float = Field(..., description="Value for the operation")


class TurnExpectedOutput(BaseModel):
    """Expected output for a single turn in a multi-turn scenario."""

    intent: Optional[str] = Field(None, description="Expected intent classification")
    response_contains: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that must appear in response",
    )
    response_must_not_contain: List[str] = Field(
        default_factory=list,
        description="Keywords/phrases that must NOT appear in response",
    )
    state_changes: List[StateChange] = Field(
        default_factory=list,
        description="Expected database state changes",
    )
    metadata_checks: Optional[Dict[str, Any]] = Field(
        None,
        description="Expected metadata fields (e.g., {'decision_id': 'not_null'})",
    )


class Turn(BaseModel):
    """A single turn in a multi-turn scenario."""

    turn: int = Field(..., description="Turn number (1-indexed)")
    input: ScenarioInput = Field(..., description="Input for this turn")
    expected_output: TurnExpectedOutput = Field(..., description="Expected output")
    description: Optional[str] = Field(None, description="Description of this turn")


class MultiTurnScenario(BaseModel):
    """A multi-turn conversation scenario."""

    id: str = Field(..., description="Unique scenario identifier")
    persona: str = Field(..., description="Persona to test as (sarah, alex, marcus)")
    description: str = Field(..., description="Overall scenario description")
    context: ScenarioContext = Field(
        default_factory=ScenarioContext,
        description="Scenario context",
    )
    turns: List[Turn] = Field(..., description="List of conversation turns")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ScenarioCollection(BaseModel):
    """A collection of related scenarios."""

    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection description")
    version: str = Field(..., description="Schema version")
    type: Literal["single_turn", "multi_turn"] = Field(
        "single_turn",
        description="Scenario type",
    )
    scenarios: List[Union[Scenario, MultiTurnScenario]] = Field(
        ..., description="List of scenarios"
    )

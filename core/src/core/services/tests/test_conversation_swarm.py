"""Tests for conversation swarm orchestrator."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from core.ai.agents.conversation_swarm import SwarmOrchestrator
from core.models.context import UserFinancialContext
from core.models.conversation import ConversationMessage


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def user_id():
    """Create a test user ID."""
    return uuid4()


@pytest.fixture
def orchestrator(mock_db_session, user_id):
    """Create a swarm orchestrator."""
    return SwarmOrchestrator(mock_db_session, user_id)


def test_orchestrator_initialization(orchestrator, user_id):
    """Test that orchestrator initializes correctly."""
    assert orchestrator.user_id == str(user_id)
    assert orchestrator.conversation_state["user_id"] == str(user_id)
    assert orchestrator.conversation_state["turn_count"] == 0
    assert len(orchestrator.conversation_state["conversation_history"]) == 0

    # Agents and swarm are None until first message triggers creation
    assert orchestrator.router_agent is None
    assert orchestrator.swarm is None


def test_agents_created_with_tools(orchestrator):
    """Test that agents are created with correct tools after _create_agents_with_tools."""
    orchestrator._create_agents_with_tools(financial_context=None)

    # All agents should exist
    assert orchestrator.router_agent is not None
    assert orchestrator.router_agent.name == "router"
    assert orchestrator.purchase_decision_agent is not None
    assert orchestrator.budget_query_agent is not None
    assert orchestrator.log_expense_agent is not None
    assert orchestrator.small_talk_agent is not None


def test_swarm_initialization(orchestrator):
    """Test that swarm is initialized correctly after agents are created."""
    orchestrator._create_agents_with_tools(None)
    orchestrator._initialize_swarm()

    assert orchestrator.swarm is not None


def test_router_context_building(orchestrator):
    """Test that router builds correct context from conversation history."""
    conversation_history = [
        ConversationMessage(role="user", content="Hi there!"),
        ConversationMessage(role="assistant", content="Hello! How can I help?"),
        ConversationMessage(role="user", content="I spent $100 on groceries"),
    ]

    financial_context = MagicMock(spec=UserFinancialContext)
    financial_context.has_budget = True
    financial_context.get_category_names.return_value = [
        "groceries",
        "dining",
        "entertainment",
    ]
    financial_context.has_goals = False
    financial_context.recent_decisions = []

    context = orchestrator._build_context_for_router(
        conversation_history, financial_context
    )

    # Should include conversation history
    assert "User: Hi there!" in context
    assert "User: I spent $100 on groceries" in context

    # Should include budget categories
    assert "groceries" in context
    assert "dining" in context


def test_conversation_state_persistence(orchestrator):
    """Test that conversation state persists across turns."""
    initial_turn = orchestrator.conversation_state["turn_count"]

    # Simulate processing a message
    orchestrator.conversation_state["turn_count"] += 1
    orchestrator.conversation_state["last_intent"] = "budget_query"
    orchestrator.conversation_state["active_category"] = "groceries"

    # State should persist
    assert orchestrator.conversation_state["turn_count"] == initial_turn + 1
    assert orchestrator.conversation_state["last_intent"] == "budget_query"
    assert orchestrator.conversation_state["active_category"] == "groceries"


def test_empty_response_handling(orchestrator):
    """Test that empty responses are handled gracefully."""
    conversation_history = []

    with patch.object(orchestrator, "_create_agents_with_tools"):
        with patch.object(orchestrator, "_initialize_swarm"):
            # Mock swarm to return result with no agents and no message
            mock_swarm = MagicMock()
            mock_result = MagicMock()
            mock_result.node_history = []
            mock_result.results = {}
            mock_result.status = "COMPLETED"
            # Ensure .message fallback also returns empty
            mock_result.message = None
            mock_swarm.return_value = mock_result
            orchestrator.swarm = mock_swarm

            response = orchestrator.process_message(
                user_message="How much do I have left in groceries?",
                conversation_history=conversation_history,
                financial_context=None,
            )

            assert response is not None
            assert isinstance(response, str)
            assert "couldn't generate a response" in response.lower()


def test_none_result_handling(orchestrator):
    """Test that None results are handled gracefully."""
    conversation_history = []

    with patch.object(orchestrator, "_create_agents_with_tools"):
        with patch.object(orchestrator, "_initialize_swarm"):
            mock_swarm = MagicMock()
            mock_swarm.return_value = None
            orchestrator.swarm = mock_swarm

            response = orchestrator.process_message(
                user_message="How much do I have left in groceries?",
                conversation_history=conversation_history,
                financial_context=None,
            )

            assert response is not None
            assert isinstance(response, str)
            assert "encountered an issue" in response.lower()


def test_exception_handling(orchestrator):
    """Test that exceptions during swarm execution are handled gracefully."""
    conversation_history = []

    with patch.object(orchestrator, "_create_agents_with_tools"):
        with patch.object(orchestrator, "_initialize_swarm"):
            mock_swarm = MagicMock()
            mock_swarm.side_effect = Exception("Test exception")
            orchestrator.swarm = mock_swarm

            response = orchestrator.process_message(
                user_message="How much do I have left in groceries?",
                conversation_history=conversation_history,
                financial_context=None,
            )

            assert response is not None
            assert isinstance(response, str)
            assert "encountered an error" in response.lower()


def test_extract_final_response(orchestrator):
    """Test that _extract_final_response gets text from the last agent only."""
    # Build a mock SwarmResult with multiple agent results
    mock_result = MagicMock()

    # Simulate: router -> budget_modification -> log_expense
    router_node = MagicMock()
    router_node.node_id = "router"
    budget_mod_node = MagicMock()
    budget_mod_node.node_id = "budget_modification"
    log_expense_node = MagicMock()
    log_expense_node.node_id = "log_expense"

    mock_result.node_history = [router_node, budget_mod_node, log_expense_node]

    # Router result has handoff narration
    router_agent_result = MagicMock()
    router_agent_result.__str__ = lambda self: (
        "Handing off to budget_modification: user wants to create a category"
    )
    router_node_result = MagicMock()
    router_node_result.result = router_agent_result

    # Budget mod result has handoff narration
    budget_agent_result = MagicMock()
    budget_agent_result.__str__ = lambda self: (
        "Created category. Handing off to log_expense."
    )
    budget_node_result = MagicMock()
    budget_node_result.result = budget_agent_result

    # Log expense result is the user-facing response
    expense_agent_result = MagicMock()
    expense_agent_result.__str__ = lambda self: (
        "I've logged $500 for rent under your general category."
    )
    expense_node_result = MagicMock()
    expense_node_result.result = expense_agent_result

    mock_result.results = {
        "router": router_node_result,
        "budget_modification": budget_node_result,
        "log_expense": expense_node_result,
    }

    response = orchestrator._extract_final_response(mock_result)
    assert response == "I've logged $500 for rent under your general category."


def test_context_building_with_active_state(orchestrator):
    """Test context building includes active state information."""
    conversation_history = []

    # Set active state
    orchestrator.conversation_state["active_decision_id"] = "decision-123"
    orchestrator.conversation_state["active_goal_name"] = "Emergency Fund"
    orchestrator.conversation_state["active_category"] = "groceries"
    orchestrator.conversation_state["last_intent"] = "budget_query"

    context = orchestrator._build_context_for_router(conversation_history, None)

    # Should include all active state
    assert "decision-123" in context
    assert "Emergency Fund" in context
    assert "groceries" in context
    assert "budget_query" in context


def test_turn_count_increments(orchestrator):
    """Test that turn count increments on each message."""
    conversation_history = []
    initial_turn = orchestrator.conversation_state["turn_count"]

    with patch.object(orchestrator, "_create_agents_with_tools"):
        with patch.object(orchestrator, "_initialize_swarm"):
            # Mock swarm with a valid final agent response
            mock_swarm = MagicMock()
            mock_result = MagicMock()

            final_node = MagicMock()
            final_node.node_id = "small_talk"
            mock_result.node_history = [final_node]

            agent_result = MagicMock()
            agent_result.__str__ = lambda self: "Test response"
            node_result = MagicMock()
            node_result.result = agent_result
            mock_result.results = {"small_talk": node_result}

            mock_swarm.return_value = mock_result
            orchestrator.swarm = mock_swarm

            orchestrator.process_message(
                user_message="Test message",
                conversation_history=conversation_history,
                financial_context=None,
            )

            assert orchestrator.conversation_state["turn_count"] == initial_turn + 1


def test_update_conversation_state(orchestrator):
    """Test that conversation state is updated after swarm execution."""
    mock_result = MagicMock()

    budget_node = MagicMock()
    budget_node.node_id = "budget_query"
    mock_result.node_history = [budget_node]
    mock_result.message = "You have $350 remaining in groceries."

    orchestrator._update_conversation_state(mock_result, "how much left in groceries?")

    assert orchestrator.conversation_state["last_intent"] == "budget_query"
    assert orchestrator.conversation_state["active_category"] == "groceries"


@pytest.mark.skip(reason="Integration test - requires live LLM and database")
def test_process_message_integration(orchestrator):
    """Integration test for processing a real message."""
    conversation_history = []

    response = orchestrator.process_message(
        user_message="How much do I have left in groceries?",
        conversation_history=conversation_history,
        financial_context=None,
    )

    assert response is not None
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.skip(reason="Integration test - requires live LLM and database")
async def test_stream_message_integration(orchestrator):
    """Integration test for streaming a real message."""
    conversation_history = []

    chunks = []
    async for chunk in orchestrator.stream_message(
        user_message="How much do I have left in groceries?",
        conversation_history=conversation_history,
        financial_context=None,
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert all("data" in chunk for chunk in chunks)


@pytest.mark.skip(reason="Integration test - requires live LLM and database")
async def test_streaming_handoff_events(orchestrator):
    """Integration test for handoff events during streaming."""
    conversation_history = []

    events = []
    async for event in orchestrator.stream_message(
        user_message="Should I buy a $100 headset?",
        conversation_history=conversation_history,
        financial_context=None,
    ):
        events.append(event)

    # Should have streamed text chunks
    assert len(events) > 0
    # All events should have 'data' field
    assert all("data" in event for event in events)

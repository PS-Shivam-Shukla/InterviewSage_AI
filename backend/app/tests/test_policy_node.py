"""
Model-Mediated PolicyNode & Tool Loop Unit/Integration Tests (Phase 11).

Verifies:
1. Structured PolicyDecision schemas (ToolCallDecision vs FinishDecision).
2. Model tool selection over exposed MCP tool schemas.
3. ToolExecutor execution boundary & Observation capture.
4. Bounded loop iteration limit (MAX_POLICY_ITERATIONS = 5).
5. Complete loop sequence (Policy -> tool_call -> Observation -> Policy -> finish).
"""

from app.core.llm_client import FakeLLMClient
from app.graph.policy_node import (
    MAX_POLICY_ITERATIONS,
    FinishDecision,
    PolicyDecision,
    PolicyNode,
    ToolCallDecision,
)
from app.tools.executor import Observation, ToolExecutor


def test_policy_decision_schemas():
    """Verify PolicyDecision structured schemas enforce action payloads."""
    tool_dec = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(tool="score_answer_rubric", arguments={"question_type": "technical"}),
        reasoning="Evaluating technical correctness."
    )
    assert tool_dec.action == "tool_call"
    assert tool_dec.tool_call.tool == "score_answer_rubric"

    finish_dec = PolicyDecision(
        action="finish",
        finish=FinishDecision(reasoning="Evaluation turn completed."),
        reasoning="Evaluation turn completed."
    )
    assert finish_dec.action == "finish"
    assert finish_dec.finish.reasoning == "Evaluation turn completed."


def test_tool_executor_execution():
    """Verify ToolExecutor validates tool registration and returns structured Observation."""
    executor = ToolExecutor()
    obs = executor.execute_tool(
        "score_answer_rubric",
        {"question_type": "technical", "seniority_level": "MID"}
    )
    assert isinstance(obs, Observation)
    assert obs.tool_name == "score_answer_rubric"
    assert obs.success is True
    assert obs.latency_ms >= 0


def test_policy_node_iteration_boundary():
    """Verify PolicyNode safely terminates when policy_iteration_count exceeds MAX_POLICY_ITERATIONS."""
    policy = PolicyNode()
    state = {
        "interview_id": "test-123",
        "policy_iteration_count": MAX_POLICY_ITERATIONS,  # iteration 5 -> next is 6 > 5
    }
    result = policy(state)
    assert result["next_node"] == "report_generator_agent"
    assert result["policy_decisions"][0]["action"] == "finish"
    assert "Max policy iteration limit" in result["policy_decisions"][0]["reasoning"]


def test_policy_node_model_mediated_tool_loop():
    """
    Verify complete model-mediated loop:
    PolicyNode -> tool_call -> ToolExecutor -> Observation -> PolicyNode -> finish.
    """
    # 1. First fake model response: choose tool 'score_answer_rubric'
    fake_dec1 = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(
            tool="score_answer_rubric",
            arguments={"question_type": "technical", "seniority_level": "MID"},
            reasoning="Selecting rubric tool for answer scoring."
        )
    )

    # 2. Second fake model response: emit finish decision
    fake_dec2 = PolicyDecision(
        action="finish",
        finish=FinishDecision(reasoning="Turn processing finished."),
        reasoning="Turn processing finished."
    )

    fake_llm = FakeLLMClient(responses=[fake_dec1, fake_dec2])
    policy = PolicyNode(llm_client=fake_llm)

    # Turn 1: PolicyNode perceives state and selects tool
    initial_state = {
        "interview_id": "test-loop-123",
        "policy_iteration_count": 0,
        "current_question": {"question_text": "Explain Python GIL."},
        "answers": [{"answer_text": "GIL is Global Interpreter Lock."}],
    }
    step1_out = policy(initial_state)

    assert step1_out["next_node"] == "tool_executor_node"
    assert step1_out["policy_decisions"][0]["action"] == "tool_call"
    assert step1_out["policy_decisions"][0]["tool"] == "score_answer_rubric"

    # Step 2: ToolExecutor executes chosen tool and captures Observation
    executor = ToolExecutor()
    obs = executor.execute_tool(
        step1_out["policy_decisions"][0]["tool"],
        step1_out["policy_decisions"][0]["arguments"]
    )
    assert obs.success is True

    # Turn 2: PolicyNode receives observation and decides finish
    state_turn2 = {
        **initial_state,
        "policy_iteration_count": step1_out["policy_iteration_count"],
        "observations": [obs.to_dict()],
    }
    step2_out = policy(state_turn2)

    assert step2_out["next_node"] == "report_generator_agent"
    assert step2_out["policy_decisions"][0]["action"] == "finish"

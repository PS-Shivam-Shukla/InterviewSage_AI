"""
Comprehensive Policy Node & Model-Mediated Tool Loop Test Suite.
Verifies all 9 policy loop test requirements (Tests A through I).
"""

from app.core.llm_client import FakeLLMClient
from app.graph.policy_node import (
    MAX_POLICY_ITERATIONS,
    FinishDecision,
    PolicyDecision,
    PolicyNode,
    ToolCallDecision,
)
from app.mcp.server import mcp_server
from app.tools.executor import tool_executor


def make_test_state(observations=None, iteration=0):
    return {
        "interview_id": "test-int-100",
        "current_question": {"question_text": "What is Python GIL?"},
        "answers": [{"answer_text": "GIL is Global Interpreter Lock in CPython."}],
        "observations": observations or [],
        "policy_iteration_count": iteration,
        "available_tools": mcp_server.list_tools(),
    }


def test_a_tool_discovery():
    """Test A: Policy receives discovered tool schemas from registry."""
    tools = mcp_server.list_tools()
    tool_names = [t["name"] for t in tools]
    assert "map_skills" in tool_names
    assert "compute_ats_score" in tool_names
    assert "score_answer_rubric" in tool_names
    assert len(tools) >= 5


def test_b_model_selected_tool_execution():
    """Test B: Fake LLM returns tool_call for map_skills, and runtime executes map_skills."""
    class FakePolicyLLM(FakeLLMClient):
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            return PolicyDecision(
                action="tool_call",
                tool_call=ToolCallDecision(
                    tool="map_skills",
                    arguments={"resume_skills": ["Python", "SQL"], "jd_required_skills": ["Python", "SQL", "Docker"]},
                    reasoning="Mapping candidate skills to job description."
                )
            )

    node = PolicyNode(llm_client=FakePolicyLLM())
    state = make_test_state()
    res = node(state)

    assert res["next_node"] == "tool_executor_node"
    assert res["policy_decisions"][0]["tool"] == "map_skills"
    assert res["policy_decisions"][0]["arguments"] == {"resume_skills": ["Python", "SQL"], "jd_required_skills": ["Python", "SQL", "Docker"]}


def test_c_observation_propagation():
    """Test C: Tool result is packaged into Observation and passed into next Policy call."""
    obs = tool_executor.execute_tool(
        "map_skills",
        {"resume_skills": ["Python"], "jd_required_skills": ["Python", "FastAPI"]}
    )
    assert obs.success is True
    assert obs.tool_name == "map_skills"

    captured_prompt = ""
    class CapturingLLM(FakeLLMClient):
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            nonlocal captured_prompt
            captured_prompt = " ".join([getattr(m, "content", str(m)) for m in messages])
            return PolicyDecision(action="finish", finish=FinishDecision(reasoning="Complete"))

    node = PolicyNode(llm_client=CapturingLLM())
    state = make_test_state(observations=[obs.to_dict()], iteration=1)
    res = node(state)

    assert "Turn 1: Tool 'map_skills'" in captured_prompt
    assert "Success: True" in captured_prompt


def test_d_multi_step_model_selected_tool_sequence():
    """Test D: Fake LLM simulates tool_call(map_skills) -> tool_call(compute_ats_score) -> finish."""
    class SequenceLLM(FakeLLMClient):
        def __init__(self):
            super().__init__()
            self.call_count = 0

        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            self.call_count += 1
            if self.call_count == 1:
                return PolicyDecision(
                    action="tool_call",
                    tool_call=ToolCallDecision(
                        tool="map_skills",
                        arguments={"resume_skills": ["Python"], "jd_required_skills": ["Python"]},
                        reasoning="Map skills first."
                    )
                )
            elif self.call_count == 2:
                return PolicyDecision(
                    action="tool_call",
                    tool_call=ToolCallDecision(
                        tool="compute_ats_score",
                        arguments={"resume_skills": ["Python"], "jd_skills": ["Python"], "experience_years": 3},
                        reasoning="Compute ATS score second."
                    )
                )
            else:
                return PolicyDecision(
                    action="finish",
                    finish=FinishDecision(reasoning="Sufficient evidence collected.")
                )

    seq_llm = SequenceLLM()
    node = PolicyNode(llm_client=seq_llm)
    state = make_test_state()

    # Step 1: Policy decision -> map_skills
    res1 = node(state)
    assert res1["policy_decisions"][0]["tool"] == "map_skills"
    obs1 = tool_executor.execute_tool("map_skills", res1["policy_decisions"][0]["arguments"])
    state["observations"].append(obs1.to_dict())
    state["policy_iteration_count"] = 1

    # Step 2: Policy decision -> compute_ats_score
    res2 = node(state)
    assert res2["policy_decisions"][0]["tool"] == "compute_ats_score"
    obs2 = tool_executor.execute_tool("compute_ats_score", res2["policy_decisions"][0]["arguments"])
    state["observations"].append(obs2.to_dict())
    state["policy_iteration_count"] = 2

    # Step 3: Policy decision -> finish
    res3 = node(state)
    assert res3["policy_decisions"][0]["action"] == "finish"
    assert res3["next_node"] == "report_generator_agent"


def test_e_finish_decision():
    """Test E: Policy returns finish decision and terminates loop without tool execution."""
    class FinishLLM(FakeLLMClient):
        def invoke_structured(self, messages, output_schema, retry_feedback=None):
            return PolicyDecision(
                action="finish",
                finish=FinishDecision(reasoning="Execution complete.")
            )

    node = PolicyNode(llm_client=FinishLLM())
    state = make_test_state()
    res = node(state)

    assert res["policy_decisions"][0]["action"] == "finish"
    assert res["next_node"] == "report_generator_agent"


def test_f_unknown_tool_rejection():
    """Test F: If requested tool is not in registry, tool execution handles error safely."""
    obs = tool_executor.execute_tool("nonexistent_tool", {"foo": "bar"})
    assert obs.success is False
    assert "Unknown tool" in obs.error or "nonexistent_tool" in obs.error


def test_g_invalid_arguments():
    """Test G: Missing required parameters returns unsuccessful observation."""
    obs = tool_executor.execute_tool("compute_ats_score", {})
    assert obs.success is False
    assert "Missing required parameters" in obs.error or "required" in obs.error.lower()


def test_h_maximum_iterations_boundary():
    """Test H: Iterations beyond MAX_POLICY_ITERATIONS are safely terminated."""
    node = PolicyNode()
    state = make_test_state(iteration=MAX_POLICY_ITERATIONS + 1)
    res = node(state)

    assert res["policy_decisions"][0]["action"] == "finish"
    assert "Max policy iteration limit" in res["policy_decisions"][0]["reasoning"]
    assert res["next_node"] == "report_generator_agent"


def test_i_tool_execution_failure_handled():
    """Test I: Tool handler exception returns structured Observation with success=False."""
    def failing_handler(**kwargs):
        raise RuntimeError("Database connection timeout")

    mcp_server.register_tool(
        name="failing_test_tool",
        description="Fails intentionally",
        parameters={},
        handler=failing_handler
    )

    obs = tool_executor.execute_tool("failing_test_tool", {})
    assert obs.success is False
    assert "Database connection timeout" in obs.error

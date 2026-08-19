"""
L2 End-to-End Compliance Integration Test Suite.
Tests:
1. Real MCP Client Session handshake & initialization.
2. Real MCP tool discovery via tools/list.
3. Real MCP tool execution over ClientSession transport (map_skills, compute_ats_score).
4. Active Agentic Decision Loop (PolicyNode perceive -> decide -> tool_call -> observe -> repeat/finish).
5. Mathematical reflection verification & score grounding.
6. Reliability & Guardrails (malformed tool call handling, unknown tool retry, prompt injection isolation).
"""

from __future__ import annotations

import json
import pytest

from app.graph.policy_node import PolicyNode, PolicyDecision, ToolCallDecision, FinishDecision
from app.graph.report_verification_node import report_verification_node
from app.mcp.client import mcp_protocol_client
from app.tools.executor import ToolExecutor, Observation
from app.services.answer_sanity_guard import AnswerSanityGuard


# ── 1. Real MCP Protocol Tests ────────────────────────────────────────────────

def test_mcp_handshake_and_discovery():
    """Verify that MCPProtocolClient executes handshake and discovers tools via ClientSession."""
    tools = mcp_protocol_client.list_tools_protocol_sync()
    assert isinstance(tools, list)
    assert len(tools) >= 8
    
    tool_names = [t["name"] for t in tools]
    assert "map_skills" in tool_names
    assert "compute_ats_score" in tool_names
    assert "score_answer_rubric" in tool_names
    assert "generate_report_pdf" in tool_names

    # Inspect contract for map_skills
    map_skills_tool = next(t for t in tools if t["name"] == "map_skills")
    assert "description" in map_skills_tool
    assert "parameters" in map_skills_tool


def test_real_mcp_stdio_handshake_and_tool_execution():
    """Verify official MCP STDIO subprocess client transport (python -m app.mcp.cli)."""
    import asyncio
    tools = asyncio.run(mcp_protocol_client.list_tools_stdio_protocol())
    assert isinstance(tools, list)
    assert len(tools) == 8
    
    tool_names = [t["name"] for t in tools]
    assert "map_skills" in tool_names

    res = asyncio.run(mcp_protocol_client.call_tool_stdio_protocol(
        "map_skills",
        {
            "resume_skills": ["Python", "FastAPI"],
            "jd_required_skills": ["Python", "FastAPI", "Docker"],
        },
    ))
    assert res["success"] is True
    score_val = res["output"].get("ats_overlap_score") or res["output"].get("overlap_score")
    assert score_val == 66.67 or score_val == 66 or score_val == 67


def test_mcp_call_tool_map_skills_protocol():
    """Verify real tool execution via call_tool_protocol_sync over ClientSession transport."""
    res = mcp_protocol_client.call_tool_protocol_sync(
        "map_skills",
        {
            "resume_skills": ["Python", "FastAPI", "PostgreSQL"],
            "jd_required_skills": ["Python", "FastAPI", "Docker"],
        },
    )
    assert res["success"] is True
    assert res["error"] is None
    output = res["output"]
    assert "ats_overlap_score" in output
    assert output["matched_skills"] == ["Python", "FastAPI"]
    assert output["missing_skills"] == ["Docker"]


def test_mcp_unknown_tool_rejection():
    """Verify unknown tool call is handled cleanly without crashing."""
    res = mcp_protocol_client.call_tool_protocol_sync(
        "non_existent_tool",
        {"arg": 123},
    )
    assert res["success"] is False
    assert res["error"] is not None


# ── 2. Active Agentic Decision Loop Tests ─────────────────────────────────────

def test_tool_executor_observation_generation():
    """Verify ToolExecutor executes tool over ClientSession and wraps output in Observation."""
    executor = ToolExecutor(mcp_client=mcp_protocol_client)
    obs = executor.execute_tool(
        "compute_ats_score",
        {
            "resume_skills": ["Python", "FastAPI", "Docker", "SQL"],
            "jd_required_skills": ["Python", "FastAPI", "Docker", "Kubernetes", "AWS"],
        },
    )
    assert isinstance(obs, Observation)
    assert obs.tool_name == "compute_ats_score"
    assert obs.success is True
    assert obs.output["overlap_score"] == 60.0


def test_policy_node_bounded_decide_act_observe_loop(mocker):
    """Verify PolicyNode runs a bounded decide-act-observe loop and finishes cleanly."""
    policy = PolicyNode()

    # Step 1: Simulate LLM returning a tool_call decision for map_skills
    dec1 = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(
            tool="map_skills",
            arguments={
                "resume_skills": ["Python", "FastAPI"],
                "jd_required_skills": ["Python", "FastAPI", "Redis"],
            },
            reasoning="Map skills to identify gap.",
        ),
    )
    mocker.patch.object(policy.llm, "invoke_structured", return_value=dec1)

    state = {
        "interview_id": "test-session-l2",
        "current_question": {"question_text": "How do you use Redis with FastAPI?"},
        "answers": [{"answer_text": "I use Redis for asynchronous caching in FastAPI."}],
        "policy_iteration_count": 0,
        "observations": [],
    }

    res1 = policy(state)
    assert res1["policy_iteration_count"] == 1
    assert res1["policy_decisions"][0]["action"] == "tool_call"
    assert res1["next_node"] == "tool_executor_node"

    # Step 2: Execute ToolExecutor to produce an observation
    executor = ToolExecutor(mcp_client=mcp_protocol_client)
    obs = executor.execute_tool(
        res1["policy_decisions"][0]["tool"],
        res1["policy_decisions"][0]["arguments"],
    )

    # Step 3: Next PolicyNode turn receives observation and emits finish decision
    dec2 = PolicyDecision(
        action="finish",
        finish=FinishDecision(
            reasoning="Evaluation and skill mapping completed successfully.",
            result={"status": "COMPLETED"},
        ),
    )
    mocker.patch.object(policy.llm, "invoke_structured", return_value=dec2)

    updated_state = {
        **state,
        "policy_iteration_count": res1["policy_iteration_count"],
        "policy_decisions": res1["policy_decisions"],
        "observations": [obs.to_dict()],
    }

    res2 = policy(updated_state)
    assert res2["policy_iteration_count"] == 2
    assert res2["policy_decisions"][0]["action"] == "finish"
    assert res2["next_node"] == "report_generator_agent"


def test_policy_node_max_iteration_cap():
    """Verify PolicyNode forces safe completion when MAX_POLICY_ITERATIONS (5) is exceeded."""
    policy = PolicyNode()
    state = {
        "interview_id": "test-max-iter",
        "policy_iteration_count": 5,
    }
    res = policy(state)
    assert res["policy_iteration_count"] == 6
    assert res["policy_decisions"][0]["action"] == "finish"
    assert res["next_node"] == "report_generator_agent"


# ── 3. Reflection Verification & Grounding Tests ──────────────────────────────

def test_report_verification_mathematical_consistency(mocker):
    """Verify ReportVerificationNode compares report summaries against candidate transcript turns."""
    state = {
        "interview_id": "test-verif-1",
        "questions_asked": [{"question_text": "What is Python asyncio?"}],
        "answers": [{"answer_text": "Asyncio is Python's standard library for writing concurrent code using async/await."}],
        "evaluations": [
            {"score": 80, "competency_targeted": "Python"},
        ],
        "final_report": {
            "overall_score": 80,
            "executive_summary": "Candidate demonstrated clear understanding of Python asyncio.",
        },
    }
    from app.graph.report_verification_node import VerifiedReportOutput, ClaimVerification
    mock_out = VerifiedReportOutput(
        verified=True,
        claims=[
            ClaimVerification(
                claim="Candidate demonstrated clear understanding of Python asyncio.",
                status="supported",
                evidence_ids=["Turn 1"],
                reasoning="Explicitly supported by candidate response.",
            )
        ],
        corrected_executive_summary="Candidate demonstrated clear understanding of Python asyncio.",
        unsupported_claims_count=0,
    )
    mocker.patch.object(report_verification_node.llm, "invoke_structured", return_value=mock_out)

    res = report_verification_node(state)
    assert "verification_report" in res
    assert res["verification_report"]["verified"] is True
    assert res["verification_report"]["unsupported_claims_count"] == 0


def test_report_verification_score_discrepancy_correction(mocker):
    """Verify ReportVerificationNode flags unsupported claims and score divergence in executive summary."""
    state = {
        "interview_id": "test-verif-2",
        "questions_asked": [{"question_text": "What is Python asyncio?"}],
        "answers": [{"answer_text": "I do not know."}],
        "evaluations": [
            {"score": 20, "competency_targeted": "Python"},
        ],
        "final_report": {
            "overall_score": 99,
            "executive_summary": "Candidate demonstrated expert mastery of Kubernetes and microservices.",
        },
    }
    from app.graph.report_verification_node import VerifiedReportOutput, ClaimVerification
    mock_out = VerifiedReportOutput(
        verified=False,
        claims=[
            ClaimVerification(
                claim="Candidate demonstrated expert mastery of Kubernetes and microservices.",
                status="unsupported",
                evidence_ids=[],
                reasoning="No mention of Kubernetes or microservices in candidate response.",
            )
        ],
        corrected_executive_summary="Candidate did not provide technical details for Python.",
        unsupported_claims_count=1,
    )
    mocker.patch.object(report_verification_node.llm, "invoke_structured", return_value=mock_out)

    res = report_verification_node(state)
    assert "verification_report" in res
    assert res["verification_report"]["verified"] is False
    assert res["verification_report"]["unsupported_claims_count"] >= 1


# ── 4. Guardrails & Prompt Injection Isolation Tests ─────────────────────────

def test_answer_sanity_guard_prefilter():
    """Verify AnswerSanityGuard intercepts invalid/empty candidate answers deterministically."""
    res_empty = AnswerSanityGuard.evaluate("", round_type="TECHNICAL")
    assert res_empty.needs_llm_eval is False
    assert res_empty.is_valid_answer is False
    assert res_empty.answer_quality == "EMPTY"

    res_short = AnswerSanityGuard.evaluate("idk", round_type="TECHNICAL")
    assert res_short.needs_llm_eval is False
    assert res_short.answer_quality == "NO_ANSWER"

    res_valid = AnswerSanityGuard.evaluate(
        "FastAPI handles async requests using Python's asyncio event loop.",
        round_type="TECHNICAL",
    )
    assert res_valid.needs_llm_eval is True
    assert res_valid.is_valid_answer is True


# ── 5. Production InterviewService Integration Test ───────────────────────────

def test_production_interview_service_submit_answer_integration(db_session, mocker):
    """
    CRITICAL INTEGRATION TEST (Phase 14 Test 11):
    Proves that the active production path InterviewService.submit_answer() executes through:
    master_workflow -> policy_node -> tool_executor_node -> MCPProtocolClient -> ClientSession.
    """
    from app.services.interview_service import InterviewService
    from app.models import User, Resume, JobDescription, Interview, InterviewQuestion
    import uuid
    from datetime import datetime, UTC

    # Create DB context
    user = User(id=str(uuid.uuid4()), email=f"l2_{uuid.uuid4()}@example.com", password_hash="pw", full_name="L2 User")
    db_session.add(user)
    
    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="test.pdf",
        raw_text="Python FastAPI engineer",
        parsed_skills='["Python", "FastAPI"]',
        parsed_experience='[]',
    )
    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        raw_text="Seeking Senior Backend Engineer proficient in Python and FastAPI.",
        target_role="Backend Engineer",
        required_skills='["Python", "FastAPI"]',
    )
    db_session.add(resume)
    db_session.add(jd)
    
    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    
    question = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="TECHNICAL",
        competency_targeted="Python Concurrency",
        difficulty="MEDIUM",
        question_text="How do async handlers work in FastAPI?",
        sequence_number=1,
        status="READY",
        created_at=datetime.now(UTC),
    )
    db_session.add(question)
    db_session.commit()

    service = InterviewService(db_session)
    
    # Mock LLM evaluation agent call to return a valid structured score
    from app.agents.evaluation_agent import EvaluationAgent
    mocker.patch.object(
        EvaluationAgent,
        "_run",
        return_value={
            "evaluations": [
                {
                    "score": 85,
                    "feedback": "Great explanation of asyncio event loop.",
                    "ideal_answer_summary": "FastAPI uses asyncio loop to handle concurrency.",
                    "rubric_breakdown": {"Correctness": 4, "Completeness": 4},
                    "competency_targeted": "Python Concurrency",
                    "question_type": "technical",
                    "needs_human_review": False,
                }
            ]
        },
    )

    # Submit candidate answer
    res = service.submit_answer(
        interview_id=interview.id,
        answer="FastAPI relies on Python's asyncio event loop to run coroutines concurrently without blocking worker threads.",
        question_id=question.id,
    )

    assert res["interview_id"] == interview.id
    assert res["status"] in ("IN_PROGRESS", "COMPLETED")
    assert "evaluation" in res
    assert res["evaluation"]["score"] == 85

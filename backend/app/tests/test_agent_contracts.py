"""
Unit Tests for Agent Contracts & Pydantic Schemas (Phase 4B).
Verifies validation rules, serialization, error envelope behavior, and schema generation.
"""

import json
import pytest
from pydantic import ValidationError

from app.schemas.agent_contracts import (
    AgentError,
    AgentErrorCode,
    AgentResult,
    AnswerEvaluation,
    AnswerEvaluationInput,
    GeneratedQuestion,
    InterviewContext,
    InterviewPlan,
    InterviewReport,
    JDAnalysis,
    QuestionGenerationInput,
    ResumeAgentInput,
    ResumeAnalysis,
)


def test_resume_agent_input_valid():
    inp = ResumeAgentInput(resume_raw_text="Experienced Python Engineer with 5 years in FastAPI")
    assert inp.resume_raw_text.startswith("Experienced")


def test_resume_agent_input_missing_required():
    with pytest.raises(ValidationError):
        ResumeAgentInput()


def test_resume_analysis_serialization():
    analysis = ResumeAnalysis(
        summary="Senior Backend Engineer",
        technical_skills=["Python", "FastAPI", "PostgreSQL"],
        career_level="senior",
        resume_quality_score=92,
    )
    assert analysis.career_level == "SENIOR"  # Validator capitalizes
    data_dict = analysis.model_dump()
    assert data_dict["resume_quality_score"] == 92
    json_str = analysis.model_dump_json()
    parsed = json.loads(json_str)
    assert parsed["career_level"] == "SENIOR"


def test_jd_analysis_validation():
    jd = JDAnalysis(
        target_role="Lead Architect",
        seniority_required="staff",
        required_skills=["Python", "LangGraph", "System Design"],
    )
    assert jd.seniority_required == "STAFF"


def test_answer_evaluation_rubric_validation():
    # Sub-scores must be between 1 and 5
    with pytest.raises(ValidationError):
        AnswerEvaluation(
            score=8,
            rubric_breakdown={"technical": 6, "communication": 4},  # 6 is > 5
            feedback="Good",
        )

    valid_eval = AnswerEvaluation(
        score=8,
        rubric_breakdown={"technical": 4, "communication": 5},
        feedback="Excellent response",
    )
    assert valid_eval.score == 8


def test_agent_result_envelope_success():
    res = AgentResult[GeneratedQuestion](
        success=True,
        agent_name="QuestionGeneratorAgent",
        data=GeneratedQuestion(
            question_text="Explain async/await in Python.",
            competency_targeted="Concurrency",
            difficulty="MEDIUM",
        ),
        execution_time_ms=120,
    )
    assert res.success is True
    assert res.data.competency_targeted == "Concurrency"
    assert res.error is None


def test_agent_result_envelope_failure():
    err = AgentError(
        code=AgentErrorCode.LLM_TIMEOUT,
        message="Ollama request timed out after 30 seconds",
        retryable=True,
        agent_name="QuestionGeneratorAgent",
    )
    res = AgentResult[GeneratedQuestion](
        success=False,
        agent_name="QuestionGeneratorAgent",
        error=err,
        execution_time_ms=30000,
    )
    assert res.success is False
    assert res.error.code == AgentErrorCode.LLM_TIMEOUT
    assert res.data is None


def test_interview_context_structure():
    ctx = InterviewContext(
        interview_id="int-101",
        candidate_id="usr-202",
        raw_resume_text="Sample resume text",
        total_questions=3,
    )
    assert ctx.interview_id == "int-101"
    assert ctx.total_questions == 3
    assert ctx.resume_analysis is None
    assert ctx.questions_asked == []


def test_json_schema_generation():
    schema = ResumeAnalysis.model_json_schema()
    assert "properties" in schema
    assert "career_level" in schema["properties"]

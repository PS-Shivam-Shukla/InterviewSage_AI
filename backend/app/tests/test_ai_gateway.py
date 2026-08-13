"""
Unit and Integration Tests for AI Gateway Subsystem.
Verifies single entry point execution, structured responses, token accounting, and DB audit logging.
"""

import pytest
from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway
from app.ai.request import AIGatewayRequest
from app.ai.response import AIGatewayResponse
from app.models.llm_audit import LLMRequest, LLMResponse, TokenUsage


def test_ai_gateway_successful_execution(db_session: Session):
    """Verify AIGateway executes request, parses JSON, and records DB audit logs."""
    gateway = AIGateway()
    request = AIGatewayRequest(
        task_type="personalize_question",
        prompt_key="prompt:question_personalizer",
        prompt_version="v1",
        variables={
            "seniority_level": "Senior",
            "target_competency": "System Design",
            "project_context": "Distributed microservices",
            "baseline_question": "Discuss scaling DB connection pools.",
        },
        interview_id="int-test-101",
        user_id="usr-test-101",
    )

    response: AIGatewayResponse = gateway.execute(request, db=db_session)

    assert response.success is True
    assert response.provider == "ollama"
    assert response.model_name is not None
    assert response.parsed_json is not None
    assert response.total_tokens > 0
    assert response.latency_ms >= 0

    # Verify DB persistence
    audit_req = db_session.query(LLMRequest).filter(LLMRequest.interview_id == "int-test-101").first()
    assert audit_req is not None
    assert audit_req.task_type == "personalize_question"

    audit_res = db_session.query(LLMResponse).filter(LLMResponse.llm_request_id == audit_req.id).first()
    assert audit_res is not None
    assert audit_res.raw_output is not None

    token_rec = db_session.query(TokenUsage).filter(TokenUsage.interview_id == "int-test-101").first()
    assert token_rec is not None
    assert token_rec.total_tokens > 0


def test_ai_gateway_provider_override():
    """Verify provider and model overrides propagate cleanly."""
    gateway = AIGateway()
    request = AIGatewayRequest(
        task_type="evaluate_answer",
        prompt_key="prompt:answer_evaluator",
        provider_override="openai",
        model_override="gpt-4o",
        variables={"question_text": "Q", "target_concepts": "C", "candidate_answer": "A"},
    )

    response = gateway.execute(request)
    assert response.provider == "openai"
    assert response.model_name == "gpt-4o"

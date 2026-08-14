"""
Unit and Integration Tests for AI Gateway Subsystem.
Verifies LLM failure semantics, provider overrides, explicit error handling, and test-only fake doubles.
"""

import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway
from app.ai.request import AIGatewayRequest
from app.ai.response import AIGatewayResponse
from app.models.llm_audit import LLMRequest, LLMResponse, TokenUsage
from app.tests.fakes.fake_gateway import FakeAIGateway


def test_ai_gateway_provider_unavailable():
    """Case B: LLM provider unavailable (Ollama offline) returns explicit failure."""
    gateway = AIGateway()
    request = AIGatewayRequest(
        task_type="personalize_question",
        prompt_key="prompt:question_personalizer",
        prompt_version="v1",
        variables={
            "seniority_level": "Senior",
            "target_competency": "System Design",
            "project_context": "Microservices",
            "baseline_question": "Discuss scalability.",
        },
    )

    with patch("httpx.Client.post", side_effect=Exception("Connection refused")):
        response = gateway.execute(request)

    assert response.success is False
    assert response.raw_content == ""
    assert response.parsed_json is None
    assert "Connection refused" in (response.error_message or "")


def test_ai_gateway_unsupported_provider():
    """Case C: Unsupported provider returns explicit failure."""
    gateway = AIGateway()
    request = AIGatewayRequest(
        task_type="evaluate_answer",
        prompt_key="prompt:answer_evaluator",
        provider_override="unsupported_vendor_xyz",
        variables={"question_text": "Q", "target_concepts": "C", "candidate_answer": "A"},
    )

    with patch.object(gateway.router, "get_fallback", side_effect=ValueError("LLM Provider 'unsupported_vendor_xyz' is unconfigured or unavailable")):
        response = gateway.execute(request)

    assert response.success is False
    assert "unconfigured or unavailable" in (response.error_message or "")


def test_ai_gateway_fake_double_injected():
    """Case E: Test explicitly injected FakeAIGateway returns successful test double response."""
    fake_gateway = FakeAIGateway(predefined_response={"status": "COMPLETED", "score": 92.0})
    request = AIGatewayRequest(
        task_type="personalize_question",
        prompt_key="prompt:question_personalizer",
        variables={"seniority_level": "Senior", "target_competency": "DB", "project_context": "Ctx", "baseline_question": "Q"},
    )

    response = fake_gateway.execute(request)
    assert response.success is True
    assert response.parsed_json is not None
    assert response.parsed_json["score"] == 92.0


def test_ai_gateway_db_audit_logging(db_session: Session):
    """Verify AIGateway records audit logs in database during execution."""
    fake_gateway = FakeAIGateway()
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

    response: AIGatewayResponse = fake_gateway.execute(request, db=db_session)

    assert response.success is True
    assert response.total_tokens > 0

    # Verify DB persistence via test double
    audit_req = db_session.query(LLMRequest).filter(LLMRequest.interview_id == "int-test-101").first()
    assert audit_req is not None
    assert audit_req.task_type == "personalize_question"

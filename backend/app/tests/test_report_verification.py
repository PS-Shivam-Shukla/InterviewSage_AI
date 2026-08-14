"""
Evidence-Grounded Report Verification Node Tests (Phase 14).

Verifies:
1. Supported claims with transcript evidence pass verification.
2. Unsupported claims without transcript evidence (e.g. hallucinated Kubernetes skills) are flagged as 'unsupported' and corrected/removed in corrected_executive_summary.
"""

from app.core.llm_client import FakeLLMClient
from app.graph.report_verification_node import (
    ClaimVerification,
    ReportVerificationNode,
    VerifiedReportOutput,
)


def test_report_verification_supported_claims():
    """Verify ReportVerificationNode approves report when all claims are backed by transcript evidence."""
    fake_out = VerifiedReportOutput(
        verified=True,
        claims=[
            ClaimVerification(
                claim="Candidate explained Python asyncio and event loops.",
                status="supported",
                evidence_ids=["turn_1"],
                reasoning="Candidate provided accurate asyncio code snippet in Turn 1.",
            )
        ],
        corrected_executive_summary="Candidate demonstrated solid understanding of Python asyncio concurrency.",
        unsupported_claims_count=0,
    )
    fake_llm = FakeLLMClient(responses=[fake_out])
    verifier = ReportVerificationNode(llm_client=fake_llm)

    state = {
        "final_report": {
            "executive_summary": "Candidate demonstrated solid understanding of Python asyncio concurrency."
        },
        "questions_asked": [{"question_text": "Explain asyncio in Python."}],
        "answers": [{"answer_text": "Asyncio is an event loop library for non-blocking I/O."}],
    }

    result = verifier(state)
    assert result["verification_report"]["verified"] is True
    assert result["verification_report"]["unsupported_claims_count"] == 0
    assert result["final_report"]["executive_summary"] == fake_out.corrected_executive_summary


def test_report_verification_unsupported_claims_corrected():
    """
    Verify ReportVerificationNode flags unsupported claims (e.g. Kubernetes expertise without evidence)
    and removes/corrects them in corrected_executive_summary.
    """
    fake_out = VerifiedReportOutput(
        verified=False,
        claims=[
            ClaimVerification(
                claim="Candidate demonstrated expert Kubernetes cluster administration.",
                status="unsupported",
                evidence_ids=[],
                reasoning="Transcript contains no mention or questions related to Kubernetes.",
            ),
            ClaimVerification(
                claim="Candidate demonstrated basic Python syntax skills.",
                status="supported",
                evidence_ids=["turn_1"],
                reasoning="Turn 1 answer covers Python functions.",
            ),
        ],
        corrected_executive_summary="Candidate demonstrated basic Python syntax skills.",
        unsupported_claims_count=1,
    )
    fake_llm = FakeLLMClient(responses=[fake_out])
    verifier = ReportVerificationNode(llm_client=fake_llm)

    state = {
        "final_report": {
            "executive_summary": "Candidate demonstrated expert Kubernetes cluster administration and basic Python syntax skills."
        },
        "questions_asked": [{"question_text": "Explain Python functions."}],
        "answers": [{"answer_text": "Python functions use the def keyword."}],
    }

    result = verifier(state)
    assert result["verification_report"]["unsupported_claims_count"] == 1
    assert "Kubernetes" not in result["final_report"]["executive_summary"]
    assert (
        result["final_report"]["executive_summary"]
        == "Candidate demonstrated basic Python syntax skills."
    )

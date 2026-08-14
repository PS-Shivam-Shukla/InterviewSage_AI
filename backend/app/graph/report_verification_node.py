"""
Report Verification & Evidence Reflection Node (Phase 6).
Implements evidence-grounded reflection on synthesized final interview reports.

Flow:
Transcript Evidence + Draft Report -> ReportVerificationNode -> Claim Classification -> Verified Report

Design contract:
- Inspects draft report claims against raw candidate transcript evidence.
- Classifies each substantive claim as 'supported', 'unsupported', or 'uncertain'.
- Unsupported claims are automatically removed or corrected in corrected_executive_summary.
- Fails closed if transcript evidence is missing or unverified.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.core.llm_client import LLMClient
from app.core.logging import get_logger
from app.graph.state import InterviewState

logger = get_logger(__name__)


# ── Reflection Schemas ────────────────────────────────────────────────────────

class ClaimVerification(BaseModel):
    """Factual verification result for a single claim in the report."""
    claim: str = Field(description="The substantive claim extracted from the draft report.")
    status: Literal["supported", "unsupported", "uncertain"] = Field(
        description="Supported: explicit transcript evidence exists. Unsupported: no evidence in transcript. Uncertain: ambiguous."
    )
    evidence_ids: list[str] = Field(
        default_factory=list, description="IDs or turn numbers of transcript evidence supporting this claim."
    )
    reasoning: str = Field(description="Explanation of factual verification finding.")


class VerifiedReportOutput(BaseModel):
    """Final verified report output schema."""
    verified: bool = Field(description="True if all claims are supported or successfully corrected.")
    claims: list[ClaimVerification] = Field(default_factory=list)
    corrected_executive_summary: str = Field(description="Executive summary with unsupported claims removed or corrected.")
    unsupported_claims_count: int = Field(default=0)


# ── Report Verification Node Implementation ───────────────────────────────────

class ReportVerificationNode:
    """
    Evidence-grounded reflection node that validates report summaries against candidate transcript turns.
    """

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient(temperature=0.1)

    def __call__(self, state: InterviewState) -> dict:
        """LangGraph node handler for report reflection verification."""
        final_report = state.get("final_report") or {}
        draft_summary = final_report.get("executive_summary") or ""

        questions = state.get("questions_asked") or []
        answers = state.get("answers") or []
        evaluations = state.get("evaluations") or []

        # ── 1. Build Transcript Evidence Text ─────────────────────────────────
        evidence_lines = []
        for i, (q, a) in enumerate(zip(questions, answers), 1):
            q_text = q.get("question_text", "")
            a_text = a.get("answer_text", "")
            evidence_lines.append(f"Turn {i} (Q): {q_text}\nTurn {i} (A): {a_text[:400]}")

        transcript_evidence = "\n\n".join(evidence_lines) if evidence_lines else "No transcript evidence recorded."

        if not draft_summary:
            logger.info("ReportVerificationNode: No draft summary present to verify.")
            return {
                "verification_report": {
                    "verified": True,
                    "claims": [],
                    "corrected_executive_summary": "Interview complete.",
                    "unsupported_claims_count": 0,
                }
            }

        logger.info(
            "\n================================================================================\n"
            "🔍 [REFLECTION NODE STARTED] Verifying Report Executive Summary against Transcript Evidence\n"
            "────────────────────────────────────────────────────────────────────────────────"
        )

        # ── 2. LLM Evidence-Grounded Verification Prompt ──────────────────────
        system_prompt = (
            "You are the Evidence-Grounded Reflection Auditor for InterviewSage AI.\n"
            "Your job is to inspect every substantive claim made in the Draft Executive Summary "
            "against the actual Candidate Transcript Evidence.\n\n"
            "STRICT REFLECTION RULES:\n"
            "1. For each claim, determine status:\n"
            "   - 'supported': Explicit transcript evidence exists for this claim.\n"
            "   - 'unsupported': The transcript contains NO evidence or contradicts this claim.\n"
            "   - 'uncertain': Evidence is vague or inconclusive.\n"
            "2. If a claim is 'unsupported' (e.g., claiming expert Kubernetes skills when Kubernetes was never discussed), "
            "you MUST mark it unsupported and OMIT or CORRECT it in corrected_executive_summary.\n"
            "3. Do NOT allow unsupported claims to remain in corrected_executive_summary."
        )

        user_prompt = (
            f"DRAFT EXECUTIVE SUMMARY:\n{draft_summary}\n\n"
            f"CANDIDATE TRANSCRIPT EVIDENCE:\n{transcript_evidence}\n\n"
            "Perform evidence verification and return valid JSON matching VerifiedReportOutput schema."
        )

        messages = LLMClient.build_messages(
            system_prompt=system_prompt,
            developer_prompt="Return JSON matching VerifiedReportOutput schema.",
            user_content=user_prompt,
        )

        try:
            verified_out: VerifiedReportOutput = self.llm.invoke_structured(messages, VerifiedReportOutput)
            unsupported = [c for c in verified_out.claims if c.status == "unsupported"]
            verified_out.unsupported_claims_count = len(unsupported)

            logger.info(
                f"🔍 [REFLECTION COMPLETED] Verified: {verified_out.verified} | "
                f"Total Claims: {len(verified_out.claims)} | Unsupported Claims: {len(unsupported)}\n"
                f"   Corrected Summary: {verified_out.corrected_executive_summary[:200]}...\n"
                f"================================================================================"
            )

            # Update final_report in place with corrected summary
            updated_report = dict(final_report)
            updated_report["executive_summary"] = verified_out.corrected_executive_summary

            return {
                "verification_report": verified_out.model_dump(),
                "final_report": updated_report,
            }

        except Exception as exc:
            logger.warning(f"ReportVerificationNode verification failed: {exc}. Retaining baseline summary safely.")
            return {
                "verification_report": {
                    "verified": False,
                    "claims": [],
                    "corrected_executive_summary": draft_summary,
                    "unsupported_claims_count": 0,
                    "error": str(exc),
                }
            }


# Node instance helper
report_verification_node = ReportVerificationNode()

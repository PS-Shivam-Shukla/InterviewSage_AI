"""
Report Generator Agent (Section 10.13)
Compiles everything into the final structured report and triggers PDF export.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class CompetencyScore(BaseModel):
    competency: str
    score: float
    max_score: float = 100.0
    percentage: float


class TranscriptTurn(BaseModel):
    sequence_number: int
    round_type: str
    question_text: str
    answer_text: str
    score: int
    feedback: str


class ReportOutput(BaseModel):
    overall_score: float = Field(ge=0.0, le=100.0)
    competency_scorecard: list[CompetencyScore]
    improvement_plan: list[dict]
    transcript_snapshot: list[TranscriptTurn]
    executive_summary: str
    generated_at: str


# ── Helpers ───────────────────────────────────────────────────


def _build_scorecard(
    evaluations: list[dict], matrix: list[dict]
) -> tuple[list[CompetencyScore], float]:
    """Compute per-competency weighted scores and overall score on 0-100 canonical scale."""
    comp_scores: dict[str, list[float]] = defaultdict(list)
    for e in evaluations:
        raw_s = float(e.get("score", 0))
        pct_s = raw_s * 10.0 if (0 < raw_s <= 10) else raw_s
        comp_scores[e.get("competency_targeted", "General")].append(pct_s)

    scorecard = []
    total_weight = 0.0
    weighted_sum = 0.0

    for comp in matrix:
        name = comp["name"]
        weight = comp.get("weight", 10) / 100.0
        scores = comp_scores.get(name, [])
        avg = sum(scores) / len(scores) if scores else 0.0
        scorecard.append(
            CompetencyScore(
                competency=name,
                score=round(avg, 1),
                max_score=100.0,
                percentage=round(avg, 1),
            )
        )
        weighted_sum += avg * weight
        total_weight += weight

    overall = round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0
    return scorecard, overall


# ── Agent ─────────────────────────────────────────────────────


class ReportGeneratorAgent(BaseAgent):
    agent_name = "ReportGeneratorAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.3

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        evaluations = state.get("evaluations") or []
        questions = state.get("questions_asked") or []
        answers = state.get("answers") or []
        matrix = state.get("competency_matrix") or []
        coaching_plan = state.get("coaching_plan") or {}
        interview_id = state.get("interview_id", "")

        # ── Deterministic aggregation (no LLM needed) ─────────
        scorecard, overall_score = _build_scorecard(evaluations, matrix)

        transcript = []
        for i, (q, a, e) in enumerate(zip(questions, answers, evaluations), 1):
            raw_s = float(e.get("score", 0))
            score_val = int(raw_s * 10) if (0 < raw_s <= 10) else int(raw_s)
            transcript.append(
                TranscriptTurn(
                    sequence_number=i,
                    round_type=q.get("round_type", ""),
                    question_text=q.get("question_text", ""),
                    answer_text=a.get("answer_text", "")[:500],
                    score=score_val,
                    feedback=e.get("feedback", ""),
                )
            )

        improvement_plan = coaching_plan.get("items", [])

        # ── LLM only for 2-sentence executive summary ─────────
        summary_prompt = (
            f"Overall score: {overall_score}/100\n"
            f"Top competency: {scorecard[0].competency if scorecard else 'N/A'}\n"
            f"Weakest competency: {scorecard[-1].competency if scorecard else 'N/A'}\n"
            "Write a 2-3 sentence executive summary of this interview performance."
        )

        class SummaryOut(BaseModel):
            executive_summary: str

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("report_generator_agent", self.prompt_version),
            developer_prompt='Return JSON: {"executive_summary": "..."}',
            user_content=summary_prompt,
        )
        try:
            summary_out: SummaryOut = self._invoke_structured(messages, SummaryOut, retry_feedback)
            exec_summary = summary_out.executive_summary
        except Exception:
            exec_summary = f"Interview completed with an overall score of {overall_score}/100."

        report = ReportOutput(
            overall_score=overall_score,
            competency_scorecard=scorecard,
            improvement_plan=improvement_plan,
            transcript_snapshot=transcript,
            executive_summary=exec_summary,
            generated_at=datetime.utcnow().isoformat(),
        )

        # ── PDF generation via MCP tool ───────────────────────
        pdf_data = {
            "interview_id": interview_id,
            "overall_score": overall_score,
            "competency_scorecard": [c.model_dump() for c in scorecard],
            "improvement_plan": improvement_plan,
        }
        mcp_server.call_tool("generate_report_pdf", report_data=pdf_data)

        return {
            "final_report": report.model_dump(),
            "current_round": "COMPLETE",
        }

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        evaluations = state.get("evaluations") or []
        matrix = state.get("competency_matrix") or []
        scorecard, overall = _build_scorecard(evaluations, matrix)
        return {
            "final_report": {
                "overall_score": overall,
                "competency_scorecard": [c.model_dump() for c in scorecard],
                "improvement_plan": [],
                "transcript_snapshot": [],
                "executive_summary": "Report generation partially failed.",
                "generated_at": datetime.utcnow().isoformat(),
            },
            "error_log": [{"agent": self.agent_name, "error": error}],
        }

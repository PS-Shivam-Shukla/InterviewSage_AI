"""
Career Coach Agent (Section 10.12)
Synthesises all evaluations → prioritised improvement plan.
Every recommendation MUST cite the specific question/answer that exposed the gap.
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_system_prompt, get_developer_prompt


# ── Output schema ─────────────────────────────────────────────

class CoachingItem(BaseModel):
    competency: str
    current_score: float = Field(ge=0.0, le=10.0)
    specific_gap_description: str
    recommended_action: str
    priority: int = Field(ge=1)


class CoachingPlanOutput(BaseModel):
    items: List[CoachingItem]
    partial_data: bool = False

    @model_validator(mode="after")
    def has_specific_citations(self) -> "CoachingPlanOutput":
        for item in self.items:
            if len(item.specific_gap_description) < 20:
                raise ValueError(
                    f"Gap description for '{item.competency}' is too generic "
                    f"(must cite a specific answer). Got: '{item.specific_gap_description}'"
                )
        return self


# ── Helper ────────────────────────────────────────────────────

def _compute_competency_averages(
    evaluations: list[dict], questions_asked: list[dict]
) -> dict[str, float]:
    """Return {competency_name: avg_score} across all evaluations."""
    scores: dict[str, list[int]] = defaultdict(list)
    for e in evaluations:
        comp = e.get("competency_targeted", "General")
        scores[comp].append(e.get("score", 5))
    return {c: sum(s) / len(s) for c, s in scores.items()}


# ── Agent ─────────────────────────────────────────────────────

class CareerCoachAgent(BaseAgent):
    agent_name = "CareerCoachAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.4

    def _run(self, state: InterviewState, retry_feedback: Optional[str] = None) -> dict:
        evaluations    = state.get("evaluations") or []
        questions      = state.get("questions_asked") or []
        answers        = state.get("answers") or []
        matrix         = state.get("competency_matrix") or []

        if len(evaluations) < 1:
            return {
                "coaching_plan": CoachingPlanOutput(items=[], partial_data=True).model_dump()
            }

        averages = _compute_competency_averages(evaluations, questions)

        # Build a detailed transcript for the LLM
        qa_pairs = []
        for i, (q, a, e) in enumerate(zip(questions, answers, evaluations), 1):
            qa_pairs.append(
                f"Q{i} [{q.get('competency_targeted','')} | "
                f"{q.get('question_type','').upper()}]: {q.get('question_text','')}\n"
                f"Answer: {a.get('answer_text','')[:300]}\n"
                f"Score: {e.get('score',0)}/10 | Feedback: {e.get('feedback','')}"
            )
        transcript = "\n\n".join(qa_pairs)

        developer = get_developer_prompt("career_coach_agent", self.prompt_version)
        user_content = (
            f"Competency averages: {averages}\n"
            f"Competency matrix (for context): {matrix}\n\n"
            f"Full Q&A transcript:\n{transcript}\n\n"
            "Return JSON: {\"items\": [{\"competency\": ..., \"current_score\": ..., "
            "\"specific_gap_description\": ..., \"recommended_action\": ..., \"priority\": ...}], "
            "\"partial_data\": false}"
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("career_coach_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        plan: CoachingPlanOutput = self._invoke_structured(messages, CoachingPlanOutput, retry_feedback)
        return {"coaching_plan": plan.model_dump()}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        evaluations = state.get("evaluations") or []
        averages = _compute_competency_averages(evaluations, state.get("questions_asked") or [])
        fallback_items = [
            CoachingItem(
                competency=comp,
                current_score=round(avg, 1),
                specific_gap_description=f"Score of {avg:.1f}/10 indicates improvement needed.",
                recommended_action="Review fundamentals and practice targeted questions.",
                priority=i + 1,
            )
            for i, (comp, avg) in enumerate(sorted(averages.items(), key=lambda x: x[1]))
        ]
        return {
            "coaching_plan": CoachingPlanOutput(items=fallback_items, partial_data=True).model_dump(),
            "error_log": [{"agent": self.agent_name, "error": error}],
        }

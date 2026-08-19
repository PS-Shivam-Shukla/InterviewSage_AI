"""
HR Interview Agent (Section 10.9)
Conducts the behavioral round — presents the current question, receives
the candidate's answer, and optionally generates one follow-up question.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class HRTurn(BaseModel):
    question_text: str
    candidate_answer: str
    follow_up_question: str | None = None
    follow_up_rationale: str | None = None


# ── Agent ─────────────────────────────────────────────────────


class HRInterviewAgent(BaseAgent):
    agent_name = "HRInterviewAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.5  # warm, natural tone

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        current_q = state.get("current_question") or {}
        candidate_answer = state.get("pending_answer", "")

        # Empty / timed-out answer → gentle re-prompt, not a zero score
        if not candidate_answer or not candidate_answer.strip():
            return {
                "current_question": {
                    **current_q,
                    "re_prompt": "Take your time — feel free to share whatever comes to mind.",
                },
            }

        resume_data = state.get("resume_data") or {}
        asked_in_round = [
            q for q in (state.get("questions_asked") or []) if q.get("round_type") == "HR"
        ]
        follow_up_count = sum(1 for q in asked_in_round if q.get("is_follow_up"))

        developer = get_developer_prompt("hr_interview_agent", self.prompt_version) or (
            "You are a warm, professional HR interviewer. "
            "Decide whether ONE follow-up question would deepen understanding. "
            'Return JSON: {"question_text": "...", "candidate_answer": "...", '
            '"follow_up_question": "..." or null, "follow_up_rationale": "..." or null}'
        )

        can_follow_up = follow_up_count < 1  # max 1 follow-up per question

        user_content = (
            f"Question asked: {current_q.get('question_text','')}\n"
            f"Candidate answer: {candidate_answer}\n"
            f"Candidate's resume context: {resume_data.get('experience', [])[:2]}\n\n"
            f"{'Generate a follow-up question if it would meaningfully deepen understanding.' if can_follow_up else 'Do NOT generate a follow-up (max 1 already reached).'}"
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("hr_interview_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        turn: HRTurn = self._invoke_structured(messages, HRTurn, retry_feedback)

        answer_record = {
            "question_id": current_q.get("sequence_number"),
            "question_text": current_q.get("question_text"),
            "answer_text": candidate_answer,
            "round_type": "HR",
            "competency_targeted": current_q.get("competency_targeted", ""),
        }

        update: dict = {
            "questions_asked": [current_q],
            "answers": [answer_record],
            # Clear pending_answer: this agent has consumed it.
            # Prevents the HR graph loop from re-entering hr_interview_agent
            # if EvaluationAgent's pending_answer=None update is not applied.
            "pending_answer": None,
        }

        if turn.follow_up_question and can_follow_up:
            update["current_question"] = {
                **current_q,
                "question_text": turn.follow_up_question,
                "is_follow_up": True,
                "sequence_number": current_q.get("sequence_number"),
            }

        return update

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        """Failure path: clear pending_answer to prevent infinite graph loop."""
        current_q = state.get("current_question") or {}
        candidate_answer = state.get("pending_answer", "") or ""
        answer_record = {
            "question_id": current_q.get("sequence_number"),
            "question_text": current_q.get("question_text"),
            "answer_text": candidate_answer,
            "round_type": "HR",
            "competency_targeted": current_q.get("competency_targeted", ""),
        }
        return {
            "answers": [answer_record],
            # Must clear pending_answer to terminate the HR graph loop.
            "pending_answer": None,
            "error_log": [{"agent": self.agent_name, "error": error}],
        }

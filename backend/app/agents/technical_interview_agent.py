"""
Technical Interview Agent (Section 10.10)
Conducts the technical round — presents the question, receives the answer,
and optionally generates one probing follow-up (e.g. time complexity,
scalability, edge cases).
"""

from __future__ import annotations

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────

class TechnicalTurn(BaseModel):
    question_text: str
    candidate_answer: str
    follow_up_question: str | None = None
    follow_up_rationale: str | None = None


# ── Agent ─────────────────────────────────────────────────────

class TechnicalInterviewAgent(BaseAgent):
    agent_name = "TechnicalInterviewAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.4

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        current_q        = state.get("current_question") or {}
        candidate_answer = state.get("pending_answer", "")

        if not candidate_answer or not candidate_answer.strip():
            return {
                "current_question": {
                    **current_q,
                    "re_prompt": "Take your time — walk me through your thinking.",
                }
            }

        competency = current_q.get("competency_targeted", "")
        difficulty = current_q.get("difficulty", "MEDIUM")
        asked_tech = [
            q for q in (state.get("questions_asked") or [])
            if q.get("round_type") == "TECHNICAL"
        ]
        follow_up_count = sum(1 for q in asked_tech if q.get("is_follow_up"))
        can_follow_up   = follow_up_count < 1

        developer = (
            get_developer_prompt("technical_interview_agent", self.prompt_version)
            or (
                "You are a rigorous, fair technical interviewer. "
                "Probe for depth: time/space complexity, scalability, edge cases, trade-offs. "
                "Return JSON: {\"question_text\": \"...\", \"candidate_answer\": \"...\", "
                "\"follow_up_question\": \"...\" or null, \"follow_up_rationale\": \"...\" or null}"
            )
        )

        user_content = (
            f"Question: {current_q.get('question_text', '')}\n"
            f"Competency: {competency} | Difficulty: {difficulty}\n"
            f"Candidate answer: {candidate_answer}\n\n"
            f"{'Suggest ONE probing follow-up that tests deeper understanding.' if can_follow_up else 'No follow-up needed.'}"
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("technical_interview_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        turn: TechnicalTurn = self._invoke_structured(messages, TechnicalTurn, retry_feedback)

        answer_record = {
            "question_id": current_q.get("sequence_number"),
            "question_text": current_q.get("question_text"),
            "answer_text": candidate_answer,
            "round_type": "TECHNICAL",
            "competency_targeted": competency,
        }

        update: dict = {
            "questions_asked": [current_q],
            "answers": [answer_record],
        }

        if turn.follow_up_question and can_follow_up:
            update["current_question"] = {
                **current_q,
                "question_text": turn.follow_up_question,
                "is_follow_up": True,
            }

        return update

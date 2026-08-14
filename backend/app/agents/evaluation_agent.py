"""
Evaluation Agent (Section 10.11)
Scores EVERY answer immediately — competency-weighted rubric, per-dimension
breakdown, feedback, and ideal-answer summary.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, model_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_developer_prompt, get_system_prompt

# ── Output schema ─────────────────────────────────────────────


class EvaluationOutput(BaseModel):
    score: int = Field(ge=1, le=10)
    rubric_breakdown: dict[str, int] = Field(default_factory=dict)
    feedback: str = ""
    ideal_answer_summary: str = ""
    needs_human_review: bool = False

    @model_validator(mode="after")
    def sub_scores_in_range(self) -> EvaluationOutput:
        for dim, val in self.rubric_breakdown.items():
            if not (1 <= val <= 5):
                raise ValueError(f"Sub-score for '{dim}' is {val} — must be 1–5.")
        return self


# ── Agent ─────────────────────────────────────────────────────


class EvaluationAgent(BaseAgent):
    agent_name = "EvaluationAgent"
    prompt_version = "v1"

    def _temperature(self) -> float:
        return 0.1  # maximum consistency

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        current_q = state.get("current_question") or {}
        answers = state.get("answers") or []
        matrix = state.get("competency_matrix") or []
        profile = state.get("profile_summary") or {}
        # Full resume and JD context so the LLM can evaluate against actual role requirements
        resume_data = state.get("resume_data") or {}
        jd_data = state.get("jd_data") or {}

        # Always evaluate the most recent answer
        if not answers:
            return {}

        latest_answer = answers[-1]
        answer_text = latest_answer.get("answer_text", "")
        competency = (
            current_q.get("competency_targeted")
            or latest_answer.get("competency_targeted")
            or "General"
        )
        q_type = (
            current_q.get("question_type") or latest_answer.get("question_type") or "fundamentals"
        )
        round_type = (current_q.get("round_type") or latest_answer.get("round_type") or "").upper()

        # ── Deterministic Answer Sanity Guard ─────────────────────────
        from app.services.answer_sanity_guard import AnswerSanityGuard

        sanity_res = AnswerSanityGuard.evaluate(answer_text, round_type=round_type)
        if not sanity_res.needs_llm_eval:
            # Bypass LLM evaluation for EMPTY, NO_ANSWER, or GIBBERISH
            eval_record = {
                "score": 0,  # 0/10 raw score -> 0%
                "rubric_breakdown": {
                    "Correctness": 1,
                    "Communication": 1,
                    "Confidence": 1,
                },
                "feedback": sanity_res.reason,
                "ideal_answer_summary": "Candidate did not provide a valid answer.",
                "needs_human_review": False,
                "question_id": current_q.get("sequence_number"),
                "competency_targeted": competency,
                "question_type": q_type,
                "answer_quality": sanity_res.answer_quality,
            }
            return {"evaluations": [eval_record]}

        # ── Deterministic Aptitude Evaluation ─────────────────────────
        if round_type == "APTITUDE":
            from app.strategy.aptitude_bank import APTITUDE_20_BANK

            q_text_clean = re.sub(
                r"[^\w\s]", "", (current_q.get("question_text") or "").lower()
            ).strip()

            def _q_match(bank_item: dict) -> bool:
                b_clean = re.sub(r"[^\w\s]", "", bank_item["question_text"].lower()).strip()
                return bool(b_clean and (b_clean in q_text_clean or q_text_clean in b_clean))

            matched_apt = next((item for item in APTITUDE_20_BANK if _q_match(item)), None)
            expected_raw = matched_apt.get("correct_answer", "") if matched_apt else ""

            def _norm(s: str) -> str:
                return (
                    s.lower()
                    .replace(" ", "")
                    .replace("$", "")
                    .replace("₹", "")
                    .replace("€", "")
                    .replace("£", "")
                    .replace("rupees", "")
                    .replace("dollars", "")
                    .replace("km", "")
                    .replace("days", "")
                    .replace("%", "")
                )

            ans_norm = _norm(answer_text)
            exp_norm = _norm(expected_raw)

            is_correct = bool(
                exp_norm and ((ans_norm == exp_norm) or (ans_norm != "" and ans_norm in exp_norm))
            )
            score_val = 10 if is_correct else 0
            feedback_str = (
                f"Correct answer. Candidate provided '{answer_text}' which matches expected answer '{expected_raw}'."
                if is_correct
                else f"Incorrect answer. Candidate provided '{answer_text}'. Expected answer: '{expected_raw}'."
            )

            eval_record = {
                "score": score_val,
                "rubric_breakdown": {
                    "Correctness": 5 if is_correct else 1,
                    "Communication": 5 if is_correct else 1,
                    "Confidence": 5 if is_correct else 1,
                },
                "feedback": feedback_str,
                "ideal_answer_summary": (
                    f"The correct answer is {expected_raw}."
                    if expected_raw
                    else "Quantitative / logical problem solving."
                ),
                "needs_human_review": False,
                "question_id": current_q.get("sequence_number"),
                "competency_targeted": competency,
                "question_type": "aptitude",
                "answer_quality": "VALID_ANSWER",
            }
            return {"evaluations": [eval_record]}

        # Role and skill context for the LLM prompt
        role = jd_data.get("target_role", "") or ""
        seniority = profile.get("calibrated_seniority") or "MID"
        jd_skills_str = ", ".join((jd_data.get("required_skills") or [])[:8])
        resume_skills_str = ", ".join((resume_data.get("skills") or [])[:8])

        # Fetch rubric template via MCP tool (no answer_text — template only)
        rubric_result = mcp_server.call_tool(
            "score_answer_rubric",
            question_type=q_type,
            seniority_level=seniority,
        )
        rubric = rubric_result.output if rubric_result.success else {}

        # Competency weight for this competency
        weight = next((c.get("weight", 10) for c in matrix if c.get("name") == competency), 10)

        developer = get_developer_prompt("evaluation_agent", self.prompt_version)
        user_content = (
            f"Role being interviewed for: {role}\n"
            f"JD required skills: {jd_skills_str}\n"
            f"Candidate skills from resume: {resume_skills_str}\n"
            f"Question: {current_q.get('question_text', '')}\n"
            f"Competency being tested: {competency} (weight: {weight}%)\n"
            f"Question type: {q_type} | Round type: {round_type} | Seniority: {seniority}\n"
            f"Candidate answer:\n{answer_text}\n\n"
            f"Scoring rubric:\n{rubric}\n\n"
            "EVALUATION INSTRUCTIONS: Evaluate three independent dimensions in rubric_breakdown (each 1-5):\n"
            "1. Correctness (core technical/behavioral correctness & depth)\n"
            "2. Communication (clarity, logical structure, explanation quality)\n"
            "3. Confidence (assertiveness vs hedging phrases like 'maybe', 'I think', 'probably', 'I guess')\n"
            "Evaluate candidates of all seniority levels (including Fresher/Junior) on all three dimensions, calibrating expectations to their experience level.\n"
            "CRITICAL SCORING RULE: If the answer is semantically irrelevant to the question "
            "(e.g., random characters, celebrity names, gibberish, unrelated personal statements, "
            "or content completely unrelated to the topic), you MUST assign score=1 and all sub-scores=1.\n"
            "Return ONLY JSON matching the schema."
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("evaluation_agent", self.prompt_version),
            developer_prompt=developer,
            user_content=user_content,
        )

        evaluation: EvaluationOutput = self._invoke_structured(
            messages, EvaluationOutput, retry_feedback
        )

        eval_record = {
            **evaluation.model_dump(),
            "question_id": current_q.get("sequence_number"),
            "competency_targeted": competency,
            "question_type": q_type,
            "answer_quality": "VALID_ANSWER",
        }
        return {"evaluations": [eval_record]}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        current_q = state.get("current_question") or {}
        return {
            "evaluations": [
                {
                    "score": 0,
                    "rubric_breakdown": {
                        "Correctness": 1,
                        "Communication": 1,
                        "Confidence": 1,
                    },
                    "feedback": f"Evaluation system unavailable: {error[:120]}",
                    "ideal_answer_summary": "Evaluation requires human review or system retry.",
                    "needs_human_review": True,
                    "question_id": current_q.get("sequence_number"),
                    "competency_targeted": current_q.get("competency_targeted", ""),
                    "question_type": current_q.get("question_type", ""),
                    "answer_quality": "EVALUATION_UNAVAILABLE",
                }
            ],
            "error_log": [{"agent": self.agent_name, "error": error}],
        }

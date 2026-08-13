"""
Question Generator Agent (Section 10.8 + Section 11)
Generates ONE deeply-contextualised, non-repetitive question per call.
Implements:
  - Full context bundle assembly (resume, JD, history, competency target)
  - Adaptive difficulty based on running competency scores
  - 40/20/20/20 question-type distribution
  - Two-layer repetition avoidance: history injection + cosine-similarity guard
"""

from __future__ import annotations

import random
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_system_prompt, get_developer_prompt

# ── Distribution targets ──────────────────────────────────────
_DISTRIBUTION = {
    "fundamentals":   0.40,
    "advanced":       0.20,
    "industry":       0.20,   # "industry standards" questions
    "company":        0.20,   # company-specific / JD-specific
}

_DIFFICULTY_LADDER = ["EASY", "MEDIUM", "HARD", "ADVANCED"]


# ── Output schema ─────────────────────────────────────────────

class GeneratedQuestion(BaseModel):
    question_text: str
    competency_targeted: str
    difficulty: str = "MEDIUM"
    question_type: str = "fundamentals"
    personalisation_note: str = ""

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        return v.upper() if v.upper() in {"EASY","MEDIUM","HARD","ADVANCED"} else "MEDIUM"

    @field_validator("question_type")
    @classmethod
    def validate_q_type(cls, v: str) -> str:
        allowed = {"behavioral","fundamentals","advanced","system_design","industry","company"}
        return v.lower() if v.lower() in allowed else "fundamentals"


# ── Helpers ───────────────────────────────────────────────────

def _pick_competency(matrix: list[dict], asked: list[dict]) -> str:
    """Weighted-random competency selection, biasing toward under-asked ones."""
    if not matrix:
        return "General"
    counts = {c["name"]: 0 for c in matrix}
    for q in asked:
        name = q.get("competency_targeted", "")
        if name in counts:
            counts[name] += 1
    # Inverse frequency weights — less-asked = higher probability
    weights = [1.0 / (counts[c["name"]] + 1) * (c.get("weight", 10) / 100.0)
               for c in matrix]
    total = sum(weights)
    if total == 0:
        return matrix[0]["name"]
    normalised = [w / total for w in weights]
    return random.choices([c["name"] for c in matrix], weights=normalised, k=1)[0]


def _pick_question_type(asked_types: list[str]) -> str:
    """Pick the question type most under-represented vs the 40/20/20/20 target."""
    type_map = {"fundamentals": "fundamentals", "advanced": "advanced",
                "industry": "industry", "company": "company",
                "behavioral": "fundamentals", "system_design": "advanced"}
    counts: dict[str,int] = {k: 0 for k in _DISTRIBUTION}
    for t in asked_types:
        mapped = type_map.get(t, "fundamentals")
        counts[mapped] = counts.get(mapped, 0) + 1
    total = len(asked_types) + 1
    deficits = {t: _DISTRIBUTION[t] - counts.get(t, 0) / total for t in _DISTRIBUTION}
    return max(deficits, key=lambda t: deficits[t])


def _adaptive_difficulty(competency: str, evaluations: list[dict]) -> str:
    """Escalate/de-escalate difficulty based on recent scores for this competency."""
    scores = [e.get("score", 5) for e in evaluations
              if e.get("competency_targeted") == competency]
    if not scores:
        return "MEDIUM"
    avg = sum(scores) / len(scores)
    if avg >= 8.5:
        return "ADVANCED"
    if avg >= 7.0:
        return "HARD"
    if avg >= 5.0:
        return "MEDIUM"
    return "EASY"


def _is_duplicate(new_text: str, existing: list[dict], threshold: float = 0.85) -> bool:
    """Simple word-overlap similarity check (cosine substitute — no embedding needed in tests)."""
    new_words = set(new_text.lower().split())
    for q in existing:
        old_words = set(q.get("question_text", "").lower().split())
        if not old_words or not new_words:
            continue
        intersection = len(new_words & old_words)
        union = len(new_words | old_words)
        if union > 0 and intersection / union > threshold:
            return True
    return False


# ── Agent ─────────────────────────────────────────────────────

class QuestionGeneratorAgent(BaseAgent):
    agent_name = "QuestionGeneratorAgent"
    prompt_version = "v1"

    def __init__(self, round_type: str = "HR", llm_client=None):
        super().__init__(llm_client)
        self.round_type = round_type  # "HR" or "TECHNICAL"

    def _temperature(self) -> float:
        return 0.6   # variety in questions

    def _run(self, state: InterviewState, retry_feedback: Optional[str] = None) -> dict:
        resume_data   = state.get("resume_data") or {}
        jd_data       = state.get("jd_data") or {}
        matrix        = state.get("competency_matrix") or []
        asked         = state.get("questions_asked") or []
        evaluations   = state.get("evaluations") or []

        asked_in_round = [q for q in asked if q.get("round_type") == self.round_type]
        asked_types    = [q.get("question_type", "fundamentals") for q in asked]

        competency = _pick_competency(matrix, asked_in_round)
        q_type = _pick_question_type(asked_types)

        # Deterministic Question Difficulty Policy & Relevance Classification
        from app.services.difficulty_policy import QuestionDifficultyPolicy
        from app.services.question_relevance_service import QuestionRelevanceService

        seniority = (resume_data.get("seniority_signal") or "MID").upper()
        relevant_months = resume_data.get("relevant_experience_months", 0)

        policy_res = QuestionDifficultyPolicy.calculate_next_difficulty(
            relevant_experience_months=relevant_months,
            seniority_level=seniority,
            previous_evaluations=evaluations,
            current_difficulty=asked[-1].get("difficulty", "BASIC") if asked else "BASIC",
        )
        difficulty = policy_res.recommended_difficulty

        # Classify Candidate & JD Skills into 4 Tiers
        work_exp_bullets = [
            str(e.get("description", "")) + " " + " ".join(e.get("technologies", []))
            for e in resume_data.get("experience", [])
        ]
        candidate_skills = resume_data.get("skills", [])
        jd_skills = jd_data.get("required_skills", [])

        classified_skills = QuestionRelevanceService.classify_skills(
            candidate_skills=candidate_skills,
            work_experience_bullets=work_exp_bullets,
            jd_required_skills=jd_skills,
        )

        strong_matches = [s for s, c in classified_skills.items() if c.tier == "STRONG_MATCH"]
        possible_matches = [s for s, c in classified_skills.items() if c.tier == "POSSIBLE_MATCH"]
        jd_gaps = [s for s, c in classified_skills.items() if c.tier == "JD_GAP"]

        # Industry standards for context
        role = jd_data.get("target_role", "")
        standards = mcp_server.read_resource(
            f"resource://industry-standards/{role.lower().replace(' ', '-')}"
        ) or {}

        history_block = "\n".join(
            f"- [{q.get('competency_targeted')}] {q.get('question_text', '')}"
            for q in asked[-10:]   # last 10 to keep prompt compact
        )

        round_instruction = (
            "CRITICAL REQUIREMENT: This is an HR / Behavioural round question. The question MUST be about candidate soft skills, teamwork, conflict resolution, work ethic, or career background. It MUST NOT be a technical coding, database, or software engineering question."
            if self.round_type == "HR"
            else "CRITICAL REQUIREMENT: This is a TECHNICAL round question testing core software engineering, programming concepts, framework internals, or backend architecture. It MUST NOT be an HR, career motivation, or behavioral soft skills question."
        )

        user_content = (
            f"Round type: {self.round_type}\n"
            f"{round_instruction}\n"
            f"Target competency: {competency}\n"
            f"Required question type: {q_type}\n"
            f"Required difficulty: {difficulty}\n"
            f"Difficulty ceiling constraint: {policy_res.max_allowed_difficulty}\n"
            f"Candidate seniority: {seniority}\n"
            f"Relevant experience: {relevant_months} months\n"
            f"STRONG MATCH (Proven Experience Evidence): {strong_matches}\n"
            f"POSSIBLE MATCH (Skills List Only): {possible_matches}\n"
            f"JD GAP (Required by JD, missing in resume): {jd_gaps}\n"
            f"Industry tools for this role: {standards.get('industry_tools', [])}\n\n"
            f"Questions already asked (do NOT repeat topic or phrasing):\n{history_block or 'None yet'}"
        )

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("question_generator_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("question_generator_agent", self.prompt_version),
            user_content=user_content,
        )

        question: GeneratedQuestion = self._invoke_structured(
            messages, GeneratedQuestion, retry_feedback
        )

        # Multi-Gate Question Relevance Validation Contract
        rel_res = QuestionRelevanceService.validate_question(
            question_text=question.question_text,
            question_difficulty=question.difficulty,
            relevant_experience_months=relevant_months,
            seniority_level=seniority,
            candidate_skills=candidate_skills,
            work_experience_bullets=work_exp_bullets,
            jd_required_skills=jd_skills,
            questions_asked=asked,
            round_type=self.round_type,
        )

        if not rel_res.accepted:
            if not rel_res.difficulty_allowed:
                # Clamp generated question difficulty to candidate ceiling
                question.difficulty = policy_res.max_allowed_difficulty
            elif rel_res.duplicate_score > 0.35 or "Unrelated Tech" in rel_res.reason:
                raise ValueError(f"Question relevance validation failed: {rel_res.reason}")

        # Negative Domain Constraint Validation
        negative_skills = jd_data.get("negative_skills") or []
        from app.core.contracts import NegativeConstraintContract
        contract_res = NegativeConstraintContract.validate(question.question_text, negative_skills)
        if not contract_res.is_valid:
            raise ValueError(
                f"Negative constraint violation detected for keywords {contract_res.violations} "
                f"in question: '{question.question_text[:80]}'."
            )

        # Duplicate guard
        if _is_duplicate(question.question_text, asked):
            raise ValueError(
                f"Generated question is too similar to a previous one: "
                f"'{question.question_text[:80]}'. Generate a different question."
            )

        q_dict = {
            **question.model_dump(),
            "round_type": self.round_type,
            "sequence_number": len(asked) + 1,
            "required_seniority": seniority,
            "required_experience_months": relevant_months,
        }
        return {"current_question": q_dict}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        """Fall back to seed question bank."""
        role  = (state.get("jd_data") or {}).get("target_role", "engineer")
        asked = state.get("questions_asked") or []
        plan  = state.get("interview_plan") or {}
        difficulty = _adaptive_difficulty("General", state.get("evaluations") or [])

        bank_result = mcp_server.read_resource(
            f"resource://question-bank/{role.lower().replace(' ','-')}/{difficulty}"
        ) or {}
        seed_questions = bank_result.get("questions", [])

        # Pick first seed not already asked
        for sq in seed_questions:
            if not _is_duplicate(sq.get("text",""), asked, threshold=0.7):
                return {
                    "current_question": {
                        "question_text": sq["text"],
                        "competency_targeted": sq.get("competency_targeted","General"),
                        "difficulty": sq.get("difficulty","MEDIUM"),
                        "question_type": (sq.get("question_type") or sq.get("round_type") or "HR").lower(),
                        "round_type": self.round_type,
                        "sequence_number": len(asked) + 1,
                    },
                    "error_log": [{"agent": self.agent_name, "error": error, "fallback": "seed_bank"}],
                }

        # Absolute last resort
        return {
            "current_question": {
                "question_text": "Tell me about a challenging project you worked on recently.",
                "competency_targeted": "Communication",
                "difficulty": "MEDIUM",
                "question_type": "behavioral",
                "round_type": self.round_type,
                "sequence_number": len(asked) + 1,
            },
            "error_log": [{"agent": self.agent_name, "error": error, "fallback": "hardcoded"}],
        }

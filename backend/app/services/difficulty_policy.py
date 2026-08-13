"""
Question Difficulty Policy (Section 10.4)
Deterministic Python policy enforcing maximum question difficulty ceilings based on
candidate seniority level and relevant experience months.

Rules:
- 0–3 months: BASIC ceiling only
- 3–12 months: INTERMEDIATE max ceiling
- 12–36 months: INTERMEDIATE max ceiling
- 36–60 months: ADVANCED max ceiling
- 60+ months: ADVANCED / SYSTEM_DESIGN max ceiling (if SENIOR or STAFF)

Seniority level acts as a strict guardrail.
High previous evaluation scores can escalate difficulty up to the ceiling, but can NEVER exceed it.
"""

from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

# Difficulty values ordered by ascending complexity
DIFFICULTY_RANK = {
    "BASIC": 1,
    "EASY": 1,
    "INTERMEDIATE": 2,
    "MEDIUM": 2,
    "ADVANCED": 3,
    "HARD": 3,
    "SYSTEM_DESIGN": 4,
}

DIFFICULTY_NAMES = {
    1: "BASIC",
    2: "INTERMEDIATE",
    3: "ADVANCED",
    4: "SYSTEM_DESIGN",
}


class DifficultyPolicyResult(BaseModel):
    max_allowed_difficulty: str
    recommended_difficulty: str
    policy_reason: str
    is_escalation_capped: bool = False


class QuestionDifficultyPolicy:

    @classmethod
    def get_max_allowed_difficulty(
        cls,
        relevant_experience_months: int,
        seniority_level: str = "MID",
    ) -> str:
        """
        Determines the strict upper bound difficulty ceiling for a candidate.
        """
        seniority = (seniority_level or "MID").upper()
        months = max(0, relevant_experience_months)

        # Experience-based primary ceiling
        if months <= 3:
            exp_ceiling = "BASIC"
        elif months <= 36:
            exp_ceiling = "INTERMEDIATE"
        elif months <= 60:
            exp_ceiling = "ADVANCED"
        else:
            exp_ceiling = "SYSTEM_DESIGN" if seniority in ("SENIOR", "STAFF") else "ADVANCED"

        # Seniority level secondary ceiling guardrail
        seniority_ceilings = {
            "INTERN": "BASIC",
            "JUNIOR": "INTERMEDIATE",
            "MID": "ADVANCED",
            "SENIOR": "SYSTEM_DESIGN",
            "STAFF": "SYSTEM_DESIGN",
        }
        level_ceiling = seniority_ceilings.get(seniority, "INTERMEDIATE")

        # Pick the most restrictive of experience ceiling vs level ceiling
        exp_rank = DIFFICULTY_RANK.get(exp_ceiling, 2)
        level_rank = DIFFICULTY_RANK.get(level_ceiling, 2)
        final_rank = min(exp_rank, level_rank)

        return DIFFICULTY_NAMES.get(final_rank, "BASIC")

    @classmethod
    def calculate_next_difficulty(
        cls,
        relevant_experience_months: int,
        seniority_level: str = "MID",
        previous_evaluations: Optional[List[Dict[str, Any]]] = None,
        current_difficulty: str = "BASIC",
    ) -> DifficultyPolicyResult:
        """
        Calculates recommended next question difficulty while strictly enforcing the candidate's ceiling.
        """
        ceiling = cls.get_max_allowed_difficulty(relevant_experience_months, seniority_level)
        ceiling_rank = DIFFICULTY_RANK.get(ceiling, 1)

        evals = previous_evaluations or []
        if not evals:
            # First question: start at candidate's entry level
            recommended_rank = 1 if ceiling == "BASIC" else min(2, ceiling_rank)
            return DifficultyPolicyResult(
                max_allowed_difficulty=ceiling,
                recommended_difficulty=DIFFICULTY_NAMES.get(recommended_rank, "BASIC"),
                policy_reason=f"Initial question starting at {DIFFICULTY_NAMES.get(recommended_rank, 'BASIC')} for {seniority_level} ({relevant_experience_months} mos exp). Ceiling: {ceiling}.",
                is_escalation_capped=False,
            )

        # Evaluate performance from previous question scores (scale 1-10 or 0-100)
        recent_scores = []
        for e in evals:
            sc = e.get("score", 0)
            if sc > 10:
                sc = sc / 10.0  # normalize 0-100 -> 0-10
            recent_scores.append(sc)

        avg_score = sum(recent_scores) / len(recent_scores) if recent_scores else 5.0
        curr_rank = DIFFICULTY_RANK.get(current_difficulty.upper(), 1)

        if avg_score >= 8.0:
            target_rank = curr_rank + 1
            reason = f"Strong performance (avg {avg_score:.1f}/10) recommends difficulty escalation."
        elif avg_score < 4.0:
            target_rank = max(1, curr_rank - 1)
            reason = f"Weak performance (avg {avg_score:.1f}/10) de-escalates difficulty."
        else:
            target_rank = curr_rank
            reason = f"Steady performance (avg {avg_score:.1f}/10) maintains current difficulty."

        # Cap target difficulty by deterministic policy ceiling
        capped_rank = min(target_rank, ceiling_rank)
        is_capped = target_rank > ceiling_rank

        if is_capped:
            reason += f" Escalation to {DIFFICULTY_NAMES.get(target_rank, 'ADVANCED')} capped by deterministic ceiling ({ceiling})."

        return DifficultyPolicyResult(
            max_allowed_difficulty=ceiling,
            recommended_difficulty=DIFFICULTY_NAMES.get(capped_rank, "BASIC"),
            policy_reason=reason,
            is_escalation_capped=is_capped,
        )

    @classmethod
    def validate_question_difficulty(
        cls,
        question_difficulty: str,
        relevant_experience_months: int,
        seniority_level: str = "MID",
    ) -> Tuple[bool, str]:
        """
        Validates if a generated question's difficulty exceeds candidate ceiling.
        Returns (is_valid, reason).
        """
        ceiling = cls.get_max_allowed_difficulty(relevant_experience_months, seniority_level)
        q_rank = DIFFICULTY_RANK.get((question_difficulty or "BASIC").upper(), 1)
        c_rank = DIFFICULTY_RANK.get(ceiling, 1)

        if q_rank > c_rank:
            return False, f"Question difficulty '{question_difficulty}' exceeds candidate ceiling '{ceiling}' for {seniority_level} ({relevant_experience_months} mos exp)."
        return True, f"Question difficulty '{question_difficulty}' is within allowed ceiling '{ceiling}'."

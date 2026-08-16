"""
Question Generator Agent (Section 10.8 + Section 11)
Generates ONE deeply-contextualised, non-repetitive question per call.
Implements:
  - Full context bundle assembly (resume, JD, history, competency target)
  - Adaptive difficulty based on running competency scores
  - 40/20/20/20 question-type distribution
  - Multi-angle same-competency retries (5 preferred cognitive angles)
  - Layered duplicate detection (GATE 5) against accepted history only
  - Seed-bank fallback recovery with preserved competency & round type
  - Sanitized domain-level retry feedback (no infrastructure leak)
"""

from __future__ import annotations

import random
import re
import time
from typing import Any

from pydantic import BaseModel, field_validator

from app.agents.base import BaseAgent
from app.core.llm_client import LLMClient
from app.core.logging import get_logger
from app.graph.state import InterviewState
from app.mcp import mcp_server
from app.prompts.loader import get_developer_prompt, get_system_prompt

logger = get_logger(__name__)

# ── Distribution targets ──────────────────────────────────────
_DISTRIBUTION = {
    "fundamentals": 0.40,
    "advanced": 0.20,
    "industry": 0.20,
    "company": 0.20,
}

_DIFFICULTY_LADDER = ["EASY", "MEDIUM", "HARD", "ADVANCED"]

PRIMARY_COGNITIVE_ANGLES = [
    "fundamentals_and_concepts",
    "implementation_and_usage",
    "debugging_and_failure_investigation",
    "architecture_and_design_tradeoffs",
    "performance_and_optimization",
]

COGNITIVE_ANGLES = [
    "fundamentals_and_concepts",
    "implementation_and_usage",
    "debugging_and_failure_investigation",
    "architecture_and_design_tradeoffs",
    "performance_and_optimization",
    "production_scalability",
    "security_and_reliability",
    "real_world_scenario",
]

ANGLE_FRAMING_INSTRUCTIONS = {
    "fundamentals_and_concepts": "Focus on core mechanics, principles, and underlying definitions (e.g., 'Explain the core mechanism of...').",
    "implementation_and_usage": "Focus on practical code patterns, API usage, and standard library constructs (e.g., 'How would you implement...').",
    "debugging_and_failure_investigation": "Focus on diagnosing production errors, stack traces, and failure modes (e.g., 'A production system experiences X... How would you diagnose...').",
    "architecture_and_design_tradeoffs": "Focus on design patterns, component interactions, and structural trade-offs (e.g., 'Compare two approaches and explain when you would choose each...').",
    "performance_and_optimization": "Focus on memory/CPU profiling, query planning, indexing, and bottleneck elimination (e.g., 'A system experiences a bottleneck... How would you optimize...').",
    "production_scalability": "Focus on high-concurrency, connection pooling, caching, and horizontal scale (e.g., 'Design an architecture for high-volume scale...').",
    "security_and_reliability": "Focus on fault tolerance, hardening, input sanitization, and graceful degradation (e.g., 'What security/reliability risks would you consider...').",
    "real_world_scenario": "Focus on operational decision making, operational trade-offs, and incident response (e.g., 'You are operating this system in production and... What would you do?').",
}


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
        allowed = {"EASY", "MEDIUM", "HARD", "ADVANCED", "BASIC", "INTERMEDIATE", "SYSTEM_DESIGN"}
        return v.upper() if v.upper() in allowed else "MEDIUM"

    @field_validator("question_type")
    @classmethod
    def validate_q_type(cls, v: str) -> str:
        allowed = {"behavioral", "fundamentals", "advanced", "system_design", "industry", "company"}
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
    weights = [1.0 / (counts[c["name"]] + 1) * (c.get("weight", 10) / 100.0) for c in matrix]
    total = sum(weights)
    if total == 0:
        return matrix[0]["name"]
    normalised = [w / total for w in weights]
    return random.choices([c["name"] for c in matrix], weights=normalised, k=1)[0]


def _pick_question_type(asked_types: list[str]) -> str:
    """Pick the question type most under-represented vs the 40/20/20/20 target."""
    type_map = {
        "fundamentals": "fundamentals",
        "advanced": "advanced",
        "industry": "industry",
        "company": "company",
        "behavioral": "fundamentals",
        "system_design": "advanced",
    }
    counts: dict[str, int] = {k: 0 for k in _DISTRIBUTION}
    for t in asked_types:
        mapped = type_map.get(t, "fundamentals")
        counts[mapped] = counts.get(mapped, 0) + 1
    total = len(asked_types) + 1
    deficits = {t: _DISTRIBUTION[t] - counts.get(t, 0) / total for t in _DISTRIBUTION}
    return max(deficits, key=lambda t: deficits[t])


def _adaptive_difficulty(competency: str, evaluations: list[dict]) -> str:
    """Escalate/de-escalate difficulty based on recent scores for this competency."""
    scores = [e.get("score", 5) for e in evaluations if e.get("competency_targeted") == competency]
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


def _is_duplicate(new_text: str, existing: list[dict], threshold: float = 0.75) -> bool:
    """Word overlap duplicate check against existing questions."""
    new_words = set(new_text.lower().split())
    for q in existing:
        if not isinstance(q, dict):
            continue
        old_words = set(q.get("question_text", "").lower().split())
        if not old_words or not new_words:
            continue
        intersection = len(new_words & old_words)
        union = len(new_words | old_words)
        if union > 0 and intersection / union > threshold:
            return True
    return False


def _pick_fallback_competency(
    matrix: list[dict], asked: list[dict], failed_competencies: set[str]
) -> str:
    """Selects the next eligible competency from competency_matrix that has not failed in current turn retries."""
    eligible = [c for c in matrix if c.get("name") not in failed_competencies]
    if not eligible:
        return matrix[0]["name"] if matrix else "General"
    return _pick_competency(eligible, asked)


def _pick_alternative_q_type(asked_types: list[str], current_type: str) -> str:
    """Pick an alternative question type different from current_type."""
    candidates = [t for t in _DISTRIBUTION if t != current_type]
    if not candidates:
        return current_type
    return random.choice(candidates)


# ── Agent ─────────────────────────────────────────────────────


class QuestionGeneratorAgent(BaseAgent):
    agent_name = "QuestionGeneratorAgent"
    prompt_version = "v1"

    def __init__(self, round_type: str = "HR", llm_client=None):
        super().__init__(llm_client)
        self.round_type = round_type
        self.max_retries = 1

    def _temperature(self) -> float:
        return 0.6

    def _run(self, state: InterviewState, retry_feedback: str | None = None) -> dict:
        t_attempt_start = time.monotonic()
        resume_data = state.get("resume_data") or {}
        jd_data = state.get("jd_data") or {}
        matrix = state.get("competency_matrix") or []
        asked = state.get("questions_asked") or []
        evaluations = state.get("evaluations") or []

        asked_in_round = [q for q in asked if q.get("round_type") == self.round_type]
        asked_types = [q.get("question_type", "fundamentals") for q in asked]

        round_type_upper = (self.round_type or "").strip().upper()
        is_hr_round = round_type_upper == "HR"
        is_aptitude_round = round_type_upper == "APTITUDE"

        if is_hr_round:
            target_matrix = [
                {
                    "name": "Leadership & Team Collaboration",
                    "weight": 25,
                    "description": "Teamwork, cross-functional collaboration, and communication",
                },
                {
                    "name": "Conflict Resolution & Adaptability",
                    "weight": 25,
                    "description": "Handling workplace conflict, ambiguity, and changing priorities",
                },
                {
                    "name": "Work Ethic & Ownership",
                    "weight": 25,
                    "description": "Personal accountability, initiative, and work-life balance",
                },
                {
                    "name": "Culture Fit & Career Growth",
                    "weight": 25,
                    "description": "Alignment with company values, growth mindset, and motivations",
                },
            ]
        elif is_aptitude_round:
            target_matrix = [
                {
                    "name": "Quantitative Aptitude",
                    "weight": 25,
                    "description": "Numerical reasoning and math problem solving",
                },
                {
                    "name": "Logical Reasoning",
                    "weight": 25,
                    "description": "Deductive logic and pattern recognition",
                },
                {
                    "name": "Verbal Ability",
                    "weight": 25,
                    "description": "Comprehension and analytical reasoning",
                },
                {
                    "name": "Data Interpretation",
                    "weight": 25,
                    "description": "Chart and data analysis reasoning",
                },
            ]
        else:
            target_matrix = matrix

        t_prompt_start = time.monotonic()
        target_competency = state.get("target_competency") or _pick_competency(target_matrix, asked_in_round)
        q_type = _pick_question_type(asked_types)

        # ── Bounded Multi-Angle Generation Strategy State Machine ─────────────
        # Rotate through cognitive angles against the SAME competency before switching.
        attempt_num = 1
        if retry_feedback:
            match_att = re.search(r"\[ATTEMPT\s+(\d+)\s+FAILED\]", retry_feedback)
            if match_att:
                attempt_num = int(match_att.group(1)) + 1
            else:
                attempt_num = 2

        selected_competency = target_competency
        if attempt_num == 1:
            generation_strategy = "PRIMARY"
        elif attempt_num <= len(PRIMARY_COGNITIVE_ANGLES):
            generation_strategy = "ALTERNATIVE_ANGLE"
        else:
            # Exhausted all 5 cognitive angles for target_competency
            failed_competencies = {target_competency}
            fallback_comp = _pick_fallback_competency(
                target_matrix, asked_in_round, failed_competencies
            )
            if fallback_comp != target_competency:
                generation_strategy = "FALLBACK_COMPETENCY"
                selected_competency = fallback_comp
            else:
                generation_strategy = "ALTERNATIVE_QUESTION_TYPE"
                selected_competency = target_competency
                q_type = _pick_alternative_q_type(asked_types, q_type)

        # Select cognitive angle for selected_competency
        used_angles_for_comp = [
            q.get("cognitive_angle")
            for q in asked
            if q.get("competency_targeted") == selected_competency and q.get("cognitive_angle")
        ]
        unused_angles = [a for a in PRIMARY_COGNITIVE_ANGLES if a not in used_angles_for_comp]
        if unused_angles:
            cognitive_angle = unused_angles[(attempt_num - 1) % len(unused_angles)]
        else:
            all_unused = [a for a in COGNITIVE_ANGLES if a not in used_angles_for_comp]
            if all_unused:
                cognitive_angle = all_unused[(attempt_num - 1) % len(all_unused)]
            else:
                angle_idx = (len(asked) + abs(hash(selected_competency)) + (attempt_num - 1)) % len(
                    PRIMARY_COGNITIVE_ANGLES
                )
                cognitive_angle = PRIMARY_COGNITIVE_ANGLES[angle_idx]

        # Deterministic Question Difficulty Policy & Relevance Classification
        from app.services.difficulty_policy import QuestionDifficultyPolicy
        from app.services.question_relevance_service import QuestionRelevanceService

        seniority = (resume_data.get("seniority_signal") or "MID").upper()
        relevant_months = resume_data.get("relevant_experience_months", 0)
        if not relevant_months:
            seniority_months_map = {
                "SENIOR": 60,
                "STAFF": 72,
                "MID": 36,
                "JUNIOR": 12,
                "FRESHER": 0,
            }
            relevant_months = seniority_months_map.get(seniority, 24)

        policy_res = QuestionDifficultyPolicy.calculate_next_difficulty(
            relevant_experience_months=relevant_months,
            seniority_level=seniority,
            previous_evaluations=evaluations,
            current_difficulty=asked[-1].get("difficulty", "BASIC") if asked else "BASIC",
        )
        difficulty = policy_res.recommended_difficulty

        # Classify Candidate & JD Skills into 4 Tiers
        raw_exp = resume_data.get("experience", [])
        if isinstance(raw_exp, dict):
            raw_exp = raw_exp.get("work_experience") or raw_exp.get("experience") or []
        work_exp_bullets = [
            str(e.get("description", "")) + " " + " ".join(e.get("technologies", []))
            for e in raw_exp
            if isinstance(e, dict)
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
        standards = (
            mcp_server.read_resource(
                f"resource://industry-standards/{role.lower().replace(' ', '-')}"
            )
            or {}
        )

        # Compact History Block (Top relevant questions + recent general questions, max 5)
        relevant_history = [q for q in asked if q.get("competency_targeted") == selected_competency]
        if len(relevant_history) < 5:
            other_recent = [q for q in asked if q not in relevant_history][
                -5 + len(relevant_history) :
            ]
            history_subset = relevant_history + other_recent
        else:
            history_subset = relevant_history[-5:]

        history_lines = []
        for i, q in enumerate(history_subset, 1):
            comp_tag = q.get("competency_targeted", "General")
            ang_tag = q.get("cognitive_angle", "fundamentals")
            q_text = q.get("question_text", "")
            history_lines.append(
                f'{i}. competency={comp_tag} | angle={ang_tag} | question="{q_text[:160]}"'
            )

        history_block = "\n".join(history_lines)

        if round_type_upper == "HR":
            round_instruction = (
                "CRITICAL REQUIREMENT: This is an HR / Behavioural round question. The question MUST be about candidate soft skills, teamwork, conflict resolution, work ethic, or career background. It MUST NOT be a technical coding, database, or software engineering question."
            )
        elif round_type_upper == "APTITUDE":
            round_instruction = (
                "CRITICAL REQUIREMENT: This is an APTITUDE round question testing quantitative math, logical reasoning, verbal ability, or data interpretation. It MUST NOT be a software engineering, coding, framework, or technical question."
            )
        else:
            round_instruction = (
                "CRITICAL REQUIREMENT: This is a TECHNICAL round question testing core software engineering, programming concepts, framework internals, or backend architecture. It MUST NOT be an HR, career motivation, or behavioral soft skills question."
            )

        framing_guidance = ANGLE_FRAMING_INSTRUCTIONS.get(cognitive_angle, "")

        user_content = (
            f"Round type: {self.round_type}\n"
            f"{round_instruction}\n"
            f"Target competency: {selected_competency}\n"
            f"Required cognitive angle: {cognitive_angle.replace('_', ' ').title()}\n"
            f"Angle framing guidance: {framing_guidance}\n"
            f"Required question type: {q_type}\n"
            f"Required difficulty: {difficulty}\n"
            f"Difficulty ceiling constraint: {policy_res.max_allowed_difficulty}\n"
            f"Candidate seniority: {seniority}\n"
            f"Relevant experience: {relevant_months} months\n"
            f"STRONG MATCH (Proven Experience Evidence): {strong_matches}\n"
            f"POSSIBLE MATCH (Skills List Only): {possible_matches}\n"
            f"JD GAP (Required by JD, missing in resume): {jd_gaps}\n"
            f"Industry tools for this role: {standards.get('industry_tools', [])}\n\n"
            f"RECENT QUESTIONS (do NOT repeat topic, angle, or phrasing):\n{history_block or 'None yet'}"
        )

        # Apply Bounded Generation Strategy Prompt Augmentations
        if generation_strategy == "ALTERNATIVE_ANGLE":
            user_content += (
                f"\n\nSTRATEGY: ALTERNATIVE ANGLE (Attempt {attempt_num})\n"
                f"The previous generated question was rejected because it was too similar or lacked angle distinction.\n"
                f"You MUST preserve the target competency strictly as '{selected_competency}'.\n"
                f"You MUST NOT ask about the same conceptual dimension.\n"
                f"Use this cognitive angle: '{cognitive_angle.upper()}'.\n"
                f"Framing instruction: {framing_guidance}\n"
                f"The new question must test a materially different reasoning dimension.\n"
                f"Do NOT paraphrase the previous question.\n"
                f"Do NOT reuse the same scenario.\n"
                f"Do NOT merely replace nouns or frameworks.\n"
                f"Prefer a fundamentally different question structure."
            )
        elif generation_strategy == "FALLBACK_COMPETENCY":
            user_content += (
                f"\n\nSTRATEGY: FALLBACK COMPETENCY (Attempt {attempt_num})\n"
                f"Bounded attempts for competency '{target_competency}' reached limits.\n"
                f"Switching deterministically to alternative eligible competency '{selected_competency}' from candidate interview plan.\n"
                f"Generate a high-quality question for '{selected_competency}' testing cognitive angle '{cognitive_angle.replace('_', ' ').upper()}'."
            )

        # Clean domain-level feedback (Never inject stack traces, SQLAlchemy logs, WebSocket errors, URLs, or JWTs)
        if retry_feedback:
            fb_lower = retry_feedback.lower()
            if "placeholder" in fb_lower or "gate 0" in fb_lower:
                cat_feedback = "Previous attempt contained unresolved placeholders. Generate a complete question with no placeholders."
            elif (
                "duplicate" in fb_lower
                or "paraphrase" in fb_lower
                or "gate 5" in fb_lower
                or "too similar" in fb_lower
            ):
                cat_feedback = (
                    f"Previous attempt was too similar to an existing question. "
                    f"Generate a distinctly different question for target competency '{selected_competency}' "
                    f"using the '{cognitive_angle.replace('_', ' ')}' angle."
                )
            elif "competency" in fb_lower or "mismatch" in fb_lower or "gate 6" in fb_lower:
                cat_feedback = f"Previous attempt tested a different topic. Stay strictly focused on '{selected_competency}'."
            elif "relevance" in fb_lower or "gate 2" in fb_lower or "unrelated tech" in fb_lower:
                cat_feedback = f"Previous attempt introduced technologies outside the candidate's verified background. Focus strictly on '{selected_competency}'."
            elif "difficulty" in fb_lower or "gate 1" in fb_lower:
                cat_feedback = f"Previous attempt exceeded candidate seniority ceiling. Provide an appropriately calibrated question for '{selected_competency}'."
            else:
                cat_feedback = f"Previous attempt failed validation. Generate a clear, concise question focused strictly on '{selected_competency}'."

            rej_match = re.search(r"['\"]([^'\"]{10,120})['\"]", retry_feedback)
            rej_text_snippet = (
                f'\nPrevious attempt snippet: "{rej_match.group(1)}"'
                if rej_match
                and not any(
                    k in rej_match.group(1).lower()
                    for k in ["traceback", "websocket", "select ", "insert ", "token", "http", "psycopg"]
                )
                else ""
            )
            user_content += f'\n\nPREVIOUS ATTEMPT FEEDBACK:\n"{cat_feedback}"{rej_text_snippet}'

        messages = LLMClient.build_messages(
            system_prompt=get_system_prompt("question_generator_agent", self.prompt_version),
            developer_prompt=get_developer_prompt("question_generator_agent", self.prompt_version),
            user_content=user_content,
        )
        t_prompt_end = time.monotonic()
        prompt_build_ms = int((t_prompt_end - t_prompt_start) * 1000)
        prompt_chars = len(user_content)

        t_llm_start = time.monotonic()
        question: GeneratedQuestion = self._invoke_structured(
            messages, GeneratedQuestion, retry_feedback
        )
        t_llm_end = time.monotonic()
        llm_gen_ms = int((t_llm_end - t_llm_start) * 1000)

        # Clean mechanical experience strings immediately
        clean_text = re.sub(
            r"\s*,?\s*while connecting the candidate's \d+\s*(?:-|\s+)?months?(?:\s+of)?\s+experience.*?(?=\?|\.|$)",
            "",
            question.question_text,
            flags=re.IGNORECASE,
        )
        clean_text = re.sub(
            r"\s*,?\s*with \d+\s*(?:-|\s+)?months?(?:\s+of)?\s+experience.*?(?=\?|\.|$)",
            "",
            clean_text,
            flags=re.IGNORECASE,
        )
        clean_text = re.sub(
            r"\s*,?\s*in a backend with \d+\s*(?:-|\s+)?months?.*?(?=\?|\.|$)",
            "",
            clean_text,
            flags=re.IGNORECASE,
        )
        question.question_text = clean_text.strip()

        # Multi-Gate Question Relevance Validation Contract
        t_val_start = time.monotonic()

        # Placeholder Protection Rejection (Gate 0)
        t_g0_start = time.monotonic()
        if re.search(
            r"\[[A-Za-z0-9_\-\s]+\]|\{[A-Za-z0-9_\-\s]+\}|<[A-Za-z0-9_\-\s]+>",
            question.question_text,
        ):
            t_g0_end = time.monotonic()
            gate0_ms = int((t_g0_end - t_g0_start) * 1000)
            val_ms = int((t_g0_end - t_val_start) * 1000)
            total_att_ms = int((t_g0_end - t_attempt_start) * 1000)
            logger.info(
                f"\nQUESTION_GENERATOR_TIMING\n"
                f"  attempt={attempt_num}\n"
                f"  generation_strategy={generation_strategy}\n"
                f"  target_competency={target_competency}\n"
                f"  selected_competency={selected_competency}\n"
                f"  cognitive_angle={cognitive_angle}\n"
                f"  difficulty={difficulty}\n"
                f"  question_type={q_type}\n"
                f"  similarity_score=0.0000\n"
                f"  prompt_chars={prompt_chars}\n"
                f"  history_count={len(asked)}\n"
                f"  prompt_build_ms={prompt_build_ms}\n"
                f"  llm_generation_ms={llm_gen_ms}\n"
                f"  parsing_ms=1\n"
                f"  gate0_ms={gate0_ms}\n"
                f"  competency_gate_ms=0\n"
                f"  gate5_ms=0\n"
                f"  total_validation_ms={val_ms}\n"
                f"  result=REJECTED\n"
                f"  rejection_gate=GATE_0\n"
                f"  fallback_used=False\n"
                f"  fallback_type=None\n"
                f"  total_attempt_ms={total_att_ms}"
            )
            raise ValueError(
                f"[ATTEMPT {attempt_num} FAILED] [strategy={generation_strategy}] "
                f"Generated question contains unresolved bracketed placeholders: "
                f"'{question.question_text[:80]}'. Regenerate without placeholders."
            )
        t_g0_end = time.monotonic()
        gate0_ms = int((t_g0_end - t_g0_start) * 1000)

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
            competency_targeted=selected_competency,
        )

        t_val_end = time.monotonic()
        val_ms = int((t_val_end - t_val_start) * 1000)
        total_att_ms = int((t_val_end - t_attempt_start) * 1000)

        rej_gate = "NONE"
        if not rel_res.accepted:
            if "GATE 5" in rel_res.reason or rel_res.duplicate_score > 0.45:
                rej_gate = "GATE_5"
            elif "GATE 6" in rel_res.reason or "Competency Mismatch" in rel_res.reason:
                rej_gate = "GATE_6"
            elif "GATE 2" in rel_res.reason or "Unrelated Tech" in rel_res.reason:
                rej_gate = "GATE_2"
            elif "GATE 1" in rel_res.reason or "Difficulty Ceiling" in rel_res.reason:
                rej_gate = "GATE_1"
            else:
                rej_gate = "RELEVANCE_GATE"

            logger.info(
                f"\nQUESTION_GENERATOR_TIMING\n"
                f"  attempt={attempt_num}\n"
                f"  generation_strategy={generation_strategy}\n"
                f"  target_competency={target_competency}\n"
                f"  selected_competency={selected_competency}\n"
                f"  cognitive_angle={cognitive_angle}\n"
                f"  difficulty={difficulty}\n"
                f"  question_type={q_type}\n"
                f"  similarity_score={rel_res.duplicate_score:.4f}\n"
                f"  prompt_chars={prompt_chars}\n"
                f"  history_count={len(asked)}\n"
                f"  prompt_build_ms={prompt_build_ms}\n"
                f"  llm_generation_ms={llm_gen_ms}\n"
                f"  parsing_ms=1\n"
                f"  gate0_ms={gate0_ms}\n"
                f"  competency_gate_ms=0\n"
                f"  gate5_ms={val_ms}\n"
                f"  total_validation_ms={val_ms}\n"
                f"  result=REJECTED\n"
                f"  rejection_gate={rej_gate}\n"
                f"  fallback_used=False\n"
                f"  fallback_type=None\n"
                f"  total_attempt_ms={total_att_ms}"
            )

            if not rel_res.difficulty_allowed:
                question.difficulty = policy_res.max_allowed_difficulty
            elif (
                rel_res.duplicate_score > 0.45
                or "Unrelated Tech" in rel_res.reason
                or "Competency Mismatch" in rel_res.reason
                or "GATE 2" in rel_res.reason
                or "GATE 4" in rel_res.reason
            ):
                raise ValueError(
                    f"[ATTEMPT {attempt_num} FAILED] [strategy={generation_strategy}] "
                    f"Question relevance validation failed: {rel_res.reason} | Rejected question: '{question.question_text[:80]}'"
                )

        # Negative Domain Constraint Validation
        negative_skills = jd_data.get("negative_skills") or []
        from app.core.contracts import NegativeConstraintContract

        contract_res = NegativeConstraintContract.validate(question.question_text, negative_skills)
        if not contract_res.is_valid:
            logger.info(
                f"\nQUESTION_GENERATOR_TIMING\n"
                f"  attempt={attempt_num}\n"
                f"  generation_strategy={generation_strategy}\n"
                f"  target_competency={target_competency}\n"
                f"  selected_competency={selected_competency}\n"
                f"  cognitive_angle={cognitive_angle}\n"
                f"  difficulty={difficulty}\n"
                f"  question_type={q_type}\n"
                f"  similarity_score={rel_res.duplicate_score:.4f}\n"
                f"  prompt_chars={prompt_chars}\n"
                f"  history_count={len(asked)}\n"
                f"  prompt_build_ms={prompt_build_ms}\n"
                f"  llm_generation_ms={llm_gen_ms}\n"
                f"  parsing_ms=1\n"
                f"  gate0_ms={gate0_ms}\n"
                f"  competency_gate_ms=0\n"
                f"  gate5_ms={val_ms}\n"
                f"  total_validation_ms={val_ms}\n"
                f"  result=REJECTED\n"
                f"  rejection_gate=NEGATIVE_CONSTRAINT\n"
                f"  fallback_used=False\n"
                f"  fallback_type=None\n"
                f"  total_attempt_ms={total_att_ms}"
            )
            raise ValueError(
                f"[ATTEMPT {attempt_num} FAILED] [strategy={generation_strategy}] "
                f"Negative constraint violation detected for keywords {contract_res.violations} "
                f"in question: '{question.question_text[:80]}'."
            )

        logger.info(
            f"\nQUESTION_GENERATOR_TIMING\n"
            f"  attempt={attempt_num}\n"
            f"  generation_strategy={generation_strategy}\n"
            f"  target_competency={target_competency}\n"
            f"  selected_competency={selected_competency}\n"
            f"  cognitive_angle={cognitive_angle}\n"
            f"  difficulty={difficulty}\n"
            f"  question_type={q_type}\n"
            f"  similarity_score={rel_res.duplicate_score:.4f}\n"
            f"  prompt_chars={prompt_chars}\n"
            f"  history_count={len(asked)}\n"
            f"  prompt_build_ms={prompt_build_ms}\n"
            f"  llm_generation_ms={llm_gen_ms}\n"
            f"  parsing_ms=1\n"
            f"  gate0_ms={gate0_ms}\n"
            f"  competency_gate_ms=0\n"
            f"  gate5_ms={val_ms}\n"
            f"  total_validation_ms={val_ms}\n"
            f"  result=ACCEPTED\n"
            f"  rejection_gate=NONE\n"
            f"  fallback_used=False\n"
            f"  fallback_type=None\n"
            f"  total_attempt_ms={total_att_ms}"
        )

        # Clean mechanical experience strings if present
        clean_text = re.sub(
            r"\s*,?\s*with \d+\s*(?:-|\s+)?months?(?:\s+of)?\s+experience.*?(?=\?|\.|$)",
            "",
            question.question_text,
            flags=re.IGNORECASE,
        )
        clean_text = re.sub(
            r"\s*,?\s*in a backend with \d+\s*(?:-|\s+)?months?.*?(?=\?|\.|$)",
            "",
            clean_text,
            flags=re.IGNORECASE,
        )
        question.question_text = clean_text.strip()

        q_dict = {
            **question.model_dump(),
            "competency_targeted": selected_competency,
            "cognitive_angle": cognitive_angle,
            "round_type": self.round_type,
            "sequence_number": len(asked) + 1,
            "required_seniority": seniority,
            "required_experience_months": relevant_months,
            "fallback_used": False,
            "fallback_type": None,
        }
        return {"current_question": q_dict}

    def _on_failure(self, state: InterviewState, error: str) -> dict:
        """
        Fall back to seed question bank when all LLM attempts are exhausted.
        Preserves requested competency, round type, and difficulty.
        """
        asked = state.get("questions_asked") or []
        matrix = state.get("competency_matrix") or []

        # Determine target competency and difficulty
        target_comp = state.get("target_competency")
        if not target_comp and matrix:
            target_comp = matrix[0].get("name")
        if not target_comp:
            target_comp = "Technical" if self.round_type.upper() == "TECHNICAL" else "Communication"

        difficulty = _adaptive_difficulty(target_comp, state.get("evaluations") or [])

        from app.strategy.seed_question_bank import get_seed_question
        seed_q = get_seed_question(
            round_type=self.round_type,
            competency=target_comp,
            difficulty=difficulty,
            asked_questions=asked,
        )

        return {
            "current_question": {
                "question_text": seed_q["question_text"],
                "competency_targeted": seed_q["competency_targeted"],
                "difficulty": seed_q["difficulty"],
                "question_type": seed_q["question_type"],
                "round_type": self.round_type,
                "sequence_number": len(asked) + 1,
                "fallback_used": True,
                "fallback_type": "seed_bank",
            },
            "error_log": [
                {
                    "agent": self.agent_name,
                    "error": error[:120] if error else "LLM validation retries exhausted",
                    "fallback": "seed_bank",
                }
            ],
        }

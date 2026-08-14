"""
Interview service implementation.
Manages state machine execution, database persistence, MCP tools integration, and metrics tracing.
100% Stateless & Durable LangGraph State with Production Observability (Sprint 7).
Phase 5.5+: Dynamic LLM question generation, 20-question Aptitude bank, adaptive difficulty,
and genuine EvaluationAgent LLM scoring — NO hardcoded fallbacks for Technical/HR questions.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.metrics import (
    ACTIVE_INTERVIEWS_GAUGE,
    INTERVIEW_REQUESTS_TOTAL,
    MCP_TOOL_CALLS_TOTAL,
)
from app.core.request_context import set_request_context
from app.graph.workflow_master import build_master_workflow, get_checkpointer
from app.agents.evaluation_agent import EvaluationAgent
from app.agents.question_generator_agent import QuestionGeneratorAgent
from app.strategy.aptitude_bank import select_aptitude_questions
from app.strategy.difficulty_engine import DifficultyEngine
from app.models import (
    AgentLog,
    Evaluation,
    Interview,
    InterviewAnswer,
    InterviewQuestion,
    JobDescription,
    Resume,
)
from app.repositories import (
    AgentLogRepository,
    EvaluationRepository,
    InterviewAnswerRepository,
    InterviewQuestionRepository,
    InterviewRepository,
)

logger = get_logger(__name__)

# Master LangGraph workflow instance compiled with persistent checkpointer
master_workflow = build_master_workflow(checkpointer=get_checkpointer())
difficulty_engine = DifficultyEngine()


# ── Module-level helpers ──────────────────────────────────────────────────────

def _parse_json_field(value: Optional[str], default=None) -> Any:
    """Safely parse a JSON string field from a database model."""
    if not value:
        return default if default is not None else []
    try:
        result = json.loads(value)
        return result if result is not None else (default if default is not None else [])
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else []


def _build_resume_data(resume_obj) -> dict:
    """
    Build the resume_data dict consumed by QuestionGeneratorAgent and EvaluationAgent.
    Keys: skills (list), experience (list), seniority_signal (str).
    """
    if not resume_obj:
        return {}
    skills = _parse_json_field(resume_obj.parsed_skills, [])
    experience = _parse_json_field(resume_obj.parsed_experience, [])
    return {
        "skills": skills if isinstance(skills, list) else [],
        "experience": experience if isinstance(experience, list) else [],
        "seniority_signal": (resume_obj.seniority_signal or "MID").upper(),
    }


def _build_jd_data(jd_obj) -> dict:
    """
    Build the jd_data dict consumed by QuestionGeneratorAgent and EvaluationAgent.
    Keys: target_role (str), required_skills (list), seniority_level (str).
    """
    if not jd_obj:
        return {}
    required_skills = _parse_json_field(jd_obj.required_skills, [])
    return {
        "target_role": jd_obj.target_role or "",
        "required_skills": required_skills if isinstance(required_skills, list) else [],
        "seniority_level": (jd_obj.seniority_level or "MID").upper(),
    }


def _build_competency_matrix(role: str, jd_skills: list, resume_skills: list) -> list:
    """
    Build a competency matrix from role, JD skills, and resume skills.
    Returns a list of {name, weight, description} dicts with weights summing to ~100.
    JD skills get higher priority; resume-only skills supplement.
    """
    competencies: List[dict] = []
    seen: set = set()

    # JD skills: primary competencies (descending weight)
    for i, skill in enumerate(jd_skills[:8]):
        if not skill or not isinstance(skill, str):
            continue
        norm = skill.lower().strip()
        if norm not in seen:
            seen.add(norm)
            weight = max(8, 22 - i * 2)
            competencies.append({
                "name": skill,
                "weight": weight,
                "description": f"{skill} proficiency required for {role or 'this role'}",
            })

    # Resume skills: supplemental competencies
    for skill in resume_skills[:4]:
        if not skill or not isinstance(skill, str):
            continue
        norm = skill.lower().strip()
        if norm not in seen:
            seen.add(norm)
            competencies.append({
                "name": skill,
                "weight": 6,
                "description": f"{skill} from candidate background",
            })

    if not competencies:
        return [{"name": "General", "weight": 100, "description": f"General {role or 'Software Engineering'} knowledge"}]

    # Normalize weights to ~100
    total = sum(c["weight"] for c in competencies)
    for c in competencies:
        c["weight"] = round(c["weight"] * 100 / total)

    return competencies


def _difficulty_str_to_int(difficulty: str) -> int:
    """Convert EASY/MEDIUM/HARD/ADVANCED string to 1-5 int."""
    return {"EASY": 1, "MEDIUM": 2, "HARD": 3, "ADVANCED": 4}.get(
        (difficulty or "MEDIUM").upper(), 2
    )


def _difficulty_int_to_str(level: int) -> str:
    """Convert 1-5 int back to difficulty string."""
    return {1: "BASIC", 2: "INTERMEDIATE", 3: "HARD", 4: "ADVANCED", 5: "ADVANCED"}.get(
        max(1, min(5, level)), "INTERMEDIATE"
    )


def _is_fresher(seniority: str) -> bool:
    """Determine if a candidate is Fresher/Junior tier based on seniority signal."""
    return (seniority or "").strip().upper() in {
        "FRESHER", "JUNIOR", "0-1", "ENTRY", "INTERN", "1",
    }


def _determine_next_round_type(next_seq: int, is_fresher_candidate: bool) -> str:
    """Determine round type for the next dynamically generated question."""
    if is_fresher_candidate:
        if next_seq <= 4:
            return "APTITUDE"
        elif next_seq <= 7:
            return "TECHNICAL"
        else:
            return "HR"
    else:
        # Experienced: Q1-Q3 Technical, Q4-Q5 HR
        if next_seq <= 3:
            return "TECHNICAL"
        else:
            return "HR"


def _run_graph_in_worker_thread(initial_state: dict, config: dict) -> dict:
    """Execute LangGraph master_workflow.invoke in a dedicated worker thread."""
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")
    set_request_context(interview_id=thread_id)
    logger.info(f"LangGraph execution started for thread_id={thread_id}")
    try:
        output = master_workflow.invoke(initial_state, config=config)
        stage = output.get("workflow_stage", "COMPLETED")
        logger.info(f"LangGraph execution checkpointed for thread_id={thread_id}, stage={stage}")
        INTERVIEW_REQUESTS_TOTAL.labels(status="success", round_type="TECHNICAL").inc()
        return output
    except Exception as exc:
        logger.warning(
            f"LangGraph checkpointer warning for thread_id={thread_id}: {exc}. Executing in-memory."
        )
        output = master_workflow.invoke(initial_state, config=config)
        INTERVIEW_REQUESTS_TOTAL.labels(status="fallback", round_type="TECHNICAL").inc()
        return output


# ── InterviewService ──────────────────────────────────────────────────────────

class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.interview_repo = InterviewRepository(db)
        self.question_repo = InterviewQuestionRepository(db)
        self.answer_repo = InterviewAnswerRepository(db)
        self.eval_repo = EvaluationRepository(db)
        self.log_repo = AgentLogRepository(db)

    # ── Internal: LLM question generation ────────────────────────────────────

    def _generate_question_via_llm(
        self,
        round_type: str,
        resume_data: dict,
        jd_data: dict,
        competency_matrix: list,
        questions_asked: list,
        evaluations: list,
    ) -> Optional[dict]:
        """
        Generate one interview question via QuestionGeneratorAgent (LLM).
        Passes all required context via correct state keys.
        Returns the question dict (containing question_text, competency_targeted, difficulty,
        question_type) or None if the LLM fails.

        NOTE: This is the ONLY path for generating Technical and HR questions.
              If LLM is unavailable, callers must surface an HTTP 503 — no silent fallback.
        """
        q_gen = QuestionGeneratorAgent(round_type=round_type)

        # ── CORRECT STATE KEYS per QuestionGeneratorAgent._run() contract ─────
        state = {
            "resume_data": resume_data,          # ← was "resume_json" (WRONG)
            "jd_data": jd_data,                  # ← was "jd_json" (WRONG)
            "competency_matrix": competency_matrix,
            "questions_asked": questions_asked,
            "evaluations": evaluations,
        }
        output = q_gen(state)

        # Detect agent failure: _on_failure sets error_log
        if output.get("error_log"):
            logger.warning(
                f"QuestionGeneratorAgent failed for {round_type}: {output['error_log']}"
            )
            return None

        # ── CORRECT OUTPUT KEY per QuestionGeneratorAgent._run() contract ─────
        question = output.get("current_question")  # ← was "generated_question" (WRONG)
        if not question or not question.get("question_text"):
            logger.warning(
                f"QuestionGeneratorAgent returned empty current_question for {round_type}"
            )
            return None

        logger.info(
            f"QuestionGeneratorAgent[{round_type}]: role={jd_data.get('target_role')}, "
            f"competency={question.get('competency_targeted')}, "
            f"difficulty={question.get('difficulty')}"
        )
        return question

    # ── create_interview ──────────────────────────────────────────────────────

    def create_interview(
        self,
        user_id: str,
        resume_id: str,
        jd_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Interview:
        """
        Initialize a new interview session. Requires valid resume_id and jd_id.
        Removed demo-resume-101 and demo-jd-101 silent fallbacks.
        """
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required.")
        if not resume_id:
            raise HTTPException(
                status_code=422,
                detail="A valid resume_id is required to start an interview. Upload a resume first.",
            )
        if not jd_id:
            raise HTTPException(
                status_code=422,
                detail="A valid jd_id is required to start an interview. Create a Job Description first.",
            )

        # Verify Resume FK
        resume_db = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume_db:
            raise HTTPException(
                status_code=404,
                detail=f"Resume '{resume_id}' not found. Please upload a resume before starting.",
            )

        # Verify JobDescription FK
        jd_db = self.db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        if not jd_db:
            raise HTTPException(
                status_code=404,
                detail=f"JobDescription '{jd_id}' not found. Please create a Job Description first.",
            )

        # Deduplication Check: Return existing active interview for same (user, resume, jd) created within last 5 mins
        recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        existing_recent = (
            self.db.query(Interview)
            .filter(
                Interview.user_id == user_id,
                Interview.resume_id == resume_id,
                Interview.jd_id == jd_id,
                Interview.status.in_(["PLANNING", "READY", "IN_PROGRESS"]),
                Interview.started_at >= recent_cutoff,
            )
            .order_by(Interview.started_at.desc())
            .first()
        )
        if existing_recent:
            logger.info(
                f"Reusing existing interview session {existing_recent.id} for user {user_id} (resume={resume_id}, jd={jd_id})"
            )
            return existing_recent

        # Determine role_title and company_name from payload -> jd_db -> fallback
        role_title = (
            (payload and (payload.get("target_role") or payload.get("role")))
            or (jd_db and jd_db.target_role)
            or "Interview"
        )
        company_name = (
            (payload and (payload.get("target_company") or payload.get("company")))
            or (jd_db and jd_db.company_name)
            or ""
        )

        interview = Interview(
            user_id=user_id,
            resume_id=resume_id,
            jd_id=jd_id,
            target_role=role_title,
            target_company=company_name,
            status="PLANNING",
            current_round="TECHNICAL",
            overall_score=None,
            started_at=datetime.now(timezone.utc),
            completed_at=None,
        )
        created = self.interview_repo.create(interview)
        ACTIVE_INTERVIEWS_GAUGE.inc()
        return created

    def generate_plan_background(
        self,
        interview_id: str,
        context_override: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Background task to execute get_interview_plan asynchronously.
        Opens an isolated DB session, updates status to READY on success or FAILED on error.
        """
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            logger.info(f"Background plan generation started for interview {interview_id}")
            service = InterviewService(db)
            service.get_interview_plan(interview_id, context_override=context_override)
            logger.info(f"Background plan generation completed successfully for interview {interview_id}")
        except Exception as exc:
            logger.error(
                f"Background plan generation failed for interview {interview_id}: {exc}",
                exc_info=True,
            )
            try:
                interview_obj = db.query(Interview).filter(Interview.id == interview_id).first()
                if interview_obj:
                    interview_obj.status = "FAILED"
                    db.commit()
            except Exception as db_exc:
                logger.error(f"Failed to update interview status to FAILED: {db_exc}")
        finally:
            db.close()

    def get_interview(self, interview_id: str) -> Optional[Interview]:
        return self.interview_repo.get_by_id(interview_id)

    # ── get_interview_plan ────────────────────────────────────────────────────

    def get_interview_plan(
        self,
        interview_id: str,
        context_override: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Build or return the interview question plan.

        FRESHER:    Round 1 = 5 Aptitude (fixed bank, no LLM)
                    Round 2 = 1 Technical (LLM-generated)
                    Round 3 = 1 HR/Behavioural (LLM-generated)

        EXPERIENCED: Round 1 = 2 Technical (LLM-generated)
                     Round 2 = 1 HR/Behavioural (LLM-generated)

        If LLM is unavailable for Technical or HR questions → raises HTTP 503.
        """
        interview_obj = self.get_interview(interview_id)
        if not interview_obj:
            return None

        set_request_context(interview_id=interview_id, user_id=interview_obj.user_id)

        # ── Fetch Resume and JobDescription ───────────────────────────────────
        jd_obj = self.db.query(JobDescription).filter(
            JobDescription.id == interview_obj.jd_id
        ).first()
        resume_obj = self.db.query(Resume).filter(
            Resume.id == interview_obj.resume_id
        ).first()

        # ── Build authoritative interview context ─────────────────────────────
        resume_data = _build_resume_data(resume_obj)
        jd_data = _build_jd_data(jd_obj)

        # Role: from context_override → JD → never hardcode
        role_title = (
            (context_override and (
                context_override.get("role") or context_override.get("target_role")
            ))
            or jd_data.get("target_role")
            or "Interview"
        )
        jd_data["target_role"] = role_title

        # Seniority: from context_override → resume → JD
        seniority = (
            (context_override and context_override.get("experience_level"))
            or resume_data.get("seniority_signal")
            or jd_data.get("seniority_level")
            or "MID"
        ).upper()
        resume_data["seniority_signal"] = seniority

        jd_skills: List[str] = jd_data.get("required_skills", [])
        resume_skills: List[str] = resume_data.get("skills", [])
        is_fresher_candidate = _is_fresher(seniority)
        competency_matrix = _build_competency_matrix(role_title, jd_skills, resume_skills)

        logger.info(
            f"get_interview_plan: interview={interview_id}, role={role_title!r}, "
            f"seniority={seniority}, fresher={is_fresher_candidate}, "
            f"jd_skills={jd_skills[:5]}, resume_skills={resume_skills[:5]}"
        )

        target_q_count = 9 if is_fresher_candidate else 5
        existing_questions = self.question_repo.list_by_interview(interview_id)
        if len(existing_questions) >= target_q_count:
            first_q = existing_questions[0]
            blueprint_items = [
                {
                    "round_type": q.round_type,
                    "competency_targeted": q.competency_targeted,
                    "difficulty": q.difficulty,
                    "question_text": q.question_text,
                    "sequence_number": q.sequence_number,
                }
                for q in existing_questions
            ]
            return {
                "interview_id": interview_id,
                "plan": {
                    "interview_id": interview_id,
                    "role": role_title,
                    "classification": {
                        "tier": "Junior Engineer / Fresher" if is_fresher_candidate else "Senior Engineer",
                        "level": 1 if is_fresher_candidate else 3,
                        "vector_scores": {"tech_depth": 0.5 if is_fresher_candidate else 0.85},
                        "summary": f"Classified for {role_title} role.",
                    },
                    "blueprint_items": blueprint_items,
                    "first_question": {
                        "id": first_q.id,
                        "type": first_q.round_type,
                        "competency": first_q.competency_targeted,
                        "difficulty": first_q.difficulty,
                        "text": first_q.question_text,
                        "sequence_number": first_q.sequence_number,
                    },
                },
            }

        # ── Generate question plan ────────────────────────────────────────────
        db_questions_created: List[InterviewQuestion] = []

        if is_fresher_candidate:
            # FRESHER: 4 Aptitude (fixed bank) + 3 Technical (LLM) + 2 HR (LLM) = 9 Total
            aptitude_qs = select_aptitude_questions(4, session_seed=interview_id)
            history_so_far: List[dict] = []
            for idx, apt in enumerate(aptitude_qs, start=1):
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=interview_id,
                    round_type="APTITUDE",
                    competency_targeted=apt["competency_targeted"],
                    difficulty=apt["difficulty"],
                    question_text=apt["question_text"],
                    sequence_number=idx,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(db_q)
                db_questions_created.append(db_q)
                history_so_far.append({
                    "question_text": apt["question_text"],
                    "competency_targeted": apt["competency_targeted"],
                    "round_type": "APTITUDE",
                })

            # Q5, Q6, Q7: Technical — 3 LLM generated technical questions
            for seq_num in range(5, 8):
                t_q = self._generate_question_via_llm(
                    "TECHNICAL", resume_data, jd_data, competency_matrix, history_so_far, []
                )
                if not t_q:
                    raise HTTPException(
                        status_code=503,
                        detail=f"LLM question generation failed for Technical Q{seq_num} (role: {role_title!r}).",
                    )
                db_t = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=interview_id,
                    round_type="TECHNICAL",
                    competency_targeted=t_q.get("competency_targeted") or f"{role_title} Fundamentals",
                    difficulty=t_q.get("difficulty") or "EASY",
                    question_text=t_q["question_text"],
                    sequence_number=seq_num,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(db_t)
                db_questions_created.append(db_t)
                history_so_far.append({
                    "question_text": t_q["question_text"],
                    "competency_targeted": t_q.get("competency_targeted", "Technical"),
                    "round_type": "TECHNICAL",
                })

            # Q8, Q9: HR — 2 LLM generated HR questions
            for seq_num in range(8, 10):
                hr_q = self._generate_question_via_llm(
                    "HR", resume_data, jd_data, competency_matrix, history_so_far, []
                )
                if not hr_q:
                    raise HTTPException(
                        status_code=503,
                        detail=f"LLM question generation failed for HR Q{seq_num}.",
                    )
                db_hr = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=interview_id,
                    round_type="HR",
                    competency_targeted=hr_q.get("competency_targeted") or "Behavioural & Cultural Fit",
                    difficulty=hr_q.get("difficulty") or "EASY",
                    question_text=hr_q["question_text"],
                    sequence_number=seq_num,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(db_hr)
                db_questions_created.append(db_hr)
                history_so_far.append({
                    "question_text": hr_q["question_text"],
                    "competency_targeted": hr_q.get("competency_targeted", "HR"),
                    "round_type": "HR",
                })

        else:
            # EXPERIENCED: Q1, Q2, Q3 Technical + Q4, Q5 HR — all LLM generated
            # Q1: Technical (empty history)
            q1 = self._generate_question_via_llm(
                "TECHNICAL", resume_data, jd_data, competency_matrix, [], []
            )
            if not q1:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"LLM question generation failed for Technical Q1 "
                        f"(role: {role_title!r}). Ollama may be unavailable."
                    ),
                )
            db_q1 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=interview_id,
                round_type="TECHNICAL",
                competency_targeted=q1.get("competency_targeted") or (jd_skills[0] if jd_skills else role_title),
                difficulty=q1.get("difficulty") or "MEDIUM",
                question_text=q1["question_text"],
                sequence_number=1,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_q1)
            db_questions_created.append(db_q1)

            # Q2: Technical (Q1 in history)
            q2 = self._generate_question_via_llm(
                "TECHNICAL", resume_data, jd_data, competency_matrix, [q1], []
            )
            if not q2:
                raise HTTPException(
                    status_code=503,
                    detail="LLM question generation failed for Technical Q2. Ollama may be unavailable.",
                )
            db_q2 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=interview_id,
                round_type="TECHNICAL",
                competency_targeted=q2.get("competency_targeted") or (jd_skills[1] if len(jd_skills) > 1 else role_title),
                difficulty=q2.get("difficulty") or "MEDIUM",
                question_text=q2["question_text"],
                sequence_number=2,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_q2)
            db_questions_created.append(db_q2)

            # Q3: Technical (Q1+Q2 in history)
            q3 = self._generate_question_via_llm(
                "TECHNICAL", resume_data, jd_data, competency_matrix, [q1, q2], []
            )
            if not q3:
                raise HTTPException(
                    status_code=503,
                    detail="LLM question generation failed for Technical Q3. Ollama may be unavailable.",
                )
            db_q3 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=interview_id,
                round_type="TECHNICAL",
                competency_targeted=q3.get("competency_targeted") or (jd_skills[2] if len(jd_skills) > 2 else role_title),
                difficulty=q3.get("difficulty") or "MEDIUM",
                question_text=q3["question_text"],
                sequence_number=3,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_q3)
            db_questions_created.append(db_q3)

            # Q4: HR (Q1+Q2+Q3 in history)
            q4 = self._generate_question_via_llm(
                "HR", resume_data, jd_data, competency_matrix, [q1, q2, q3], []
            )
            if not q4:
                raise HTTPException(
                    status_code=503,
                    detail="LLM question generation failed for HR Q4. Ollama may be unavailable.",
                )
            db_q4 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=interview_id,
                round_type="HR",
                competency_targeted=q4.get("competency_targeted") or "Leadership & Collaboration",
                difficulty=q4.get("difficulty") or "MEDIUM",
                question_text=q4["question_text"],
                sequence_number=4,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_q4)
            db_questions_created.append(db_q4)

            # Q5: HR (Q1+Q2+Q3+Q4 in history)
            q5 = self._generate_question_via_llm(
                "HR", resume_data, jd_data, competency_matrix, [q1, q2, q3, q4], []
            )
            if not q5:
                raise HTTPException(
                    status_code=503,
                    detail="LLM question generation failed for HR Q5. Ollama may be unavailable.",
                )
            db_q5 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=interview_id,
                round_type="HR",
                competency_targeted=q5.get("competency_targeted") or "Culture & Conflict Resolution",
                difficulty=q5.get("difficulty") or "MEDIUM",
                question_text=q5["question_text"],
                sequence_number=5,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_q5)
            db_questions_created.append(db_q5)

        # ── Persist all questions atomically ──────────────────────────────────
        try:
            if interview_obj.status == "PLANNING":
                interview_obj.status = "READY"
                self.db.add(interview_obj)
            self.db.commit()
            for q in db_questions_created:
                self.db.refresh(q)
        except Exception as exc:
            self.db.rollback()
            logger.error(
                f"Failed to persist interview questions for {interview_id}: {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail="Failed to persist interview questions."
            )

        first_db_q = db_questions_created[0]
        blueprint_items = [
            {
                "round_type": q.round_type,
                "competency_targeted": q.competency_targeted,
                "difficulty": q.difficulty,
                "question_text": q.question_text,
                "sequence_number": q.sequence_number,
            }
            for q in db_questions_created
        ]

        return {
            "interview_id": interview_id,
            "plan": {
                "interview_id": interview_id,
                "role": role_title,
                "classification": {
                    "tier": "Junior Engineer / Fresher" if is_fresher_candidate else "Senior Engineer",
                    "level": 1 if is_fresher_candidate else 3,
                    "vector_scores": {"tech_depth": 0.5 if is_fresher_candidate else 0.85},
                    "summary": f"Classified for {role_title} role.",
                },
                "blueprint_items": blueprint_items,
                "first_question": {
                    "id": first_db_q.id,           # ← actual DB UUID (was "q-1" hardcoded)
                    "type": first_db_q.round_type,
                    "competency": first_db_q.competency_targeted,
                    "difficulty": first_db_q.difficulty,
                    "text": first_db_q.question_text,
                    "sequence_number": first_db_q.sequence_number,
                },
            },
        }

    async def get_interview_plan_async(
        self,
        interview_id: str,
        context_override: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Async variant that offloads to a worker thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self.get_interview_plan(interview_id, context_override)
        )

    def approve_blueprint(
        self,
        interview_id: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        plan_response = self.get_interview_plan(interview_id)
        if not plan_response:
            return {"error": f"Interview session {interview_id} not found."}
        plan = plan_response.get("plan", {})
        if overrides:
            if "blueprint_items" in overrides:
                plan["blueprint_items"] = overrides["blueprint_items"]
            if "role" in overrides:
                plan["role"] = overrides["role"]
        return {
            "interview_id": interview_id,
            "status": "APPROVED",
            "message": "Interview blueprint approved. Workflow ready to generate question sequence.",
            "plan": plan,
        }

    # ── submit_answer ─────────────────────────────────────────────────────────

    def submit_answer(
        self,
        interview_id: str,
        answer: str,
        question_id: str = "",
        question_text: str = "",
    ) -> Dict[str, Any]:
        """
        Evaluate candidate answer via EvaluationAgent (LLM PRIMARY), generate
        next question via QuestionGeneratorAgent (LLM), persist atomically.

        BUG FIXES APPLIED:
        1. Look up actual DB question by UUID — no q_text fallback to "Explain Python concurrency"
        2. Use actual question's competency_targeted — not hardcoded "Backend Architecture"
        3. EvaluationAgent is the PRIMARY scorer — score_answer_rubric heuristic removed
        4. EvaluationAgent state uses resume_data, jd_data (correct keys)
        5. EvaluationAgent output read from evaluations[0] — not agent_eval.get("score") (wrong)
        6. LLM score 1-10 converted to 0-100 percentage ONCE at this boundary
        7. QuestionGeneratorAgent state uses resume_data, jd_data (correct keys)
        8. QuestionGeneratorAgent output read from current_question (not "generated_question")
        9. HTTP 503 on LLM failure — no silent fallback to generic questions
        """
        set_request_context(interview_id=interview_id)

        # Parse answer text
        if isinstance(answer, dict):
            ans_str = str(answer.get("answer") or answer.get("answer_text") or "")
            if not question_text:
                question_text = answer.get("question_text", "")
        else:
            ans_str = str(answer)

        # Get interview
        interview_obj = self.get_interview(interview_id)
        if not interview_obj:
            raise HTTPException(status_code=404, detail=f"Interview '{interview_id}' not found.")

        # Idempotency guard: already completed
        if interview_obj.status == "COMPLETED":
            return {
                "interview_id": interview_id,
                "status": "COMPLETED",
                "evaluation": {
                    "score": interview_obj.overall_score or 0,
                    "reasoning": "Interview session is already completed.",
                    "rubric_breakdown": {},
                },
                "next_question": None,
                "report_id": interview_id,
                "message": "Interview session is already completed.",
            }

        # ── 1. Load previous answers and determine current sequence ───────────
        existing_answered = self.answer_repo.list_answers_with_evaluations_by_interview(interview_id)
        current_seq_from_count = len(existing_answered) + 1

        # ── 2. Resolve actual DB question ─────────────────────────────────────
        db_question: Optional[InterviewQuestion] = None
        question_needs_creating = False

        # Try by UUID (frontend sends actual DB ID now)
        if question_id and question_id not in ("q-1", ""):
            db_question = self.db.query(InterviewQuestion).filter(
                InterviewQuestion.id == question_id,
                InterviewQuestion.interview_id == interview_id,
            ).first()

        # Fall back to sequence-based lookup
        if not db_question:
            db_question = self.question_repo.get_by_interview_and_sequence(
                interview_id, current_seq_from_count
            )

        # Still not found — create ad-hoc from passed question_text
        if not db_question:
            if not question_text:
                raise HTTPException(
                    status_code=400,
                    detail="Question not found in DB and no question_text was provided.",
                )
            question_needs_creating = True

        # Extract question metadata (or prepare for ad-hoc creation)
        if not question_needs_creating:
            q_text = db_question.question_text
            competency = db_question.competency_targeted
            difficulty = db_question.difficulty
            round_type = db_question.round_type
            current_seq = db_question.sequence_number
        else:
            # Ad-hoc: derive from context
            jd_tmp = self.db.query(JobDescription).filter(
                JobDescription.id == interview_obj.jd_id
            ).first()
            q_text = question_text
            competency = (jd_tmp.target_role if jd_tmp else "General") + " Competency"
            difficulty = "MEDIUM"
            round_type = "TECHNICAL"
            current_seq = current_seq_from_count

        logger.info(
            f"submit_answer: interview={interview_id}, seq={current_seq}, "
            f"competency={competency!r}, difficulty={difficulty}, "
            f"round_type={round_type}, answer_len={len(ans_str)}"
        )

        # ── 3. Fetch Resume and JD context ────────────────────────────────────
        resume_obj = self.db.query(Resume).filter(
            Resume.id == interview_obj.resume_id
        ).first()
        jd_obj = self.db.query(JobDescription).filter(
            JobDescription.id == interview_obj.jd_id
        ).first()

        resume_data = _build_resume_data(resume_obj)
        jd_data = _build_jd_data(jd_obj)
        role_title = jd_data.get("target_role") or "Software Engineer"
        competency_matrix = _build_competency_matrix(
            role_title,
            jd_data.get("required_skills", []),
            resume_data.get("skills", []),
        )
        seniority = resume_data.get("seniority_signal", "MID")
        is_fresher_candidate = _is_fresher(seniority)
        all_configured_questions = self.question_repo.list_by_interview(interview_id)
        total_questions = len(all_configured_questions) if all_configured_questions else (7 if is_fresher_candidate else 5)

        # ── 4. Build previous evaluations list for adaptive difficulty ─────────
        previous_evaluations: List[dict] = []
        for item in existing_answered:
            eval_d = item.get("evaluation", {})
            if eval_d and isinstance(eval_d, dict):
                pct = eval_d.get("score", 0)
                # Store in 1-10 scale for the DifficultyEngine / QuestionGeneratorAgent
                previous_evaluations.append({
                    "score": round(pct / 10) if pct > 10 else pct,
                    "competency_targeted": eval_d.get("competency_targeted", ""),
                    "question_type": eval_d.get("question_type", ""),
                })

        # ── 5. EvaluationAgent — PRIMARY LLM evaluator ───────────────────────
        MCP_TOOL_CALLS_TOTAL.labels(tool_name="evaluation_agent", status="success").inc()

        eval_agent = EvaluationAgent()
        agent_eval = eval_agent({
            "interview_id": interview_id,
            "current_question": {
                "question_text": q_text,
                "competency_targeted": competency,   # ← actual competency (was "System Architecture")
                "question_type": round_type.lower() if round_type else "fundamentals",
                "round_type": round_type,
                "difficulty": difficulty,
            },
            "answers": [{"answer_text": ans_str}],
            "competency_matrix": competency_matrix,
            "profile_summary": {"calibrated_seniority": seniority},
            # Pass full resume/jd context so EvaluationAgent's LLM prompt is role-aware
            "resume_data": resume_data,
            "jd_data": jd_data,
            "evaluations": previous_evaluations,
        })

        # ── 6. Extract LLM evaluation — CORRECT KEY: "evaluations" list ──────
        evaluations_list = agent_eval.get("evaluations", [])
        if not evaluations_list:
            logger.error(f"EvaluationAgent returned no evaluations for {interview_id}")
            raise HTTPException(
                status_code=503,
                detail="LLM evaluation failed — EvaluationAgent returned no result.",
            )

        llm_eval = evaluations_list[0]

        # Detect hard failure (_on_failure: score=0 + needs_human_review=True)
        if llm_eval.get("needs_human_review") and int(llm_eval.get("score", 0)) == 0:
            logger.error(f"EvaluationAgent LLM failure for interview={interview_id}")
            raise HTTPException(
                status_code=503,
                detail="LLM evaluation failed. Ollama service may be unavailable.",
            )

        # ── 7. Convert 1-10 → 0-100 ONCE at service boundary ─────────────────
        raw_val = int(llm_eval.get("score", 0))
        if raw_val == 0:
            llm_score_1_10 = 0
            score_pct = 0
        else:
            llm_score_1_10 = max(1, min(10, raw_val))
            score_pct = llm_score_1_10 * 10  # Single authoritative conversion

        # Scale rubric sub-scores from 1-5 → 0-100
        rubric_raw: dict = llm_eval.get("rubric_breakdown", {})
        rubric_pct = {
            dim: min(100, max(0, int(sub * 20)))
            for dim, sub in rubric_raw.items()
            if isinstance(sub, (int, float))
        }

        # Build complete evaluation result with unambiguous canonical display score
        feedback_text = llm_eval.get("feedback", "")
        ideal_summary = llm_eval.get("ideal_answer_summary", "")
        display_str = f"{llm_score_1_10}/10 ({score_pct}%)"

        comm_val = (
            rubric_pct.get("Communication")
            if "Communication" in rubric_pct
            else rubric_pct.get("Clarity & Structure")
            if "Clarity & Structure" in rubric_pct
            else llm_eval.get("communication_score")
        )
        conf_val = (
            rubric_pct.get("Confidence")
            if "Confidence" in rubric_pct
            else llm_eval.get("confidence_score")
        )

        eval_result = {
            "score": score_pct,
            "score_1_10": llm_score_1_10,
            "display_score": display_str,
            "technical_score": score_pct,
            "communication_score": comm_val,
            "confidence_score": conf_val,
            "correctness": rubric_pct.get("Correctness", score_pct),
            "relevance": rubric_pct.get("Completeness", score_pct),
            "technical_quality": score_pct,
            "reasoning": feedback_text,
            "feedback": feedback_text,
            "ideal_answer_summary": ideal_summary,
            "rubric_breakdown": rubric_pct,
            "competency_targeted": competency,
            "question_type": round_type.lower() if round_type else "fundamentals",
            "round_type": round_type,
            "needs_human_review": llm_eval.get("needs_human_review", False),
            "answer_quality": llm_eval.get("answer_quality", "VALID_ANSWER"),
        }

        logger.info(
            f"EvaluationAgent: interview={interview_id}, seq={current_seq}, "
            f"score={display_str}, competency={competency!r}"
        )

        # ── 8. Adaptive difficulty decision ───────────────────────────────────
        adaptation = difficulty_engine.adapt_difficulty(
            current_difficulty=_difficulty_str_to_int(difficulty),
            latest_score=float(score_pct),
            candidate_answer=ans_str,
        )
        next_difficulty_str = _difficulty_int_to_str(adaptation.next_difficulty)
        logger.info(f"DifficultyEngine: {adaptation.adaptation_reason}")

        # ── 9. Atomic transaction: persist answer, evaluation, next question ──
        next_q_data = None
        is_completed = False

        try:
            if interview_obj.status == "PLANNING":
                interview_obj.status = "IN_PROGRESS"

            # Create ad-hoc question if needed
            if question_needs_creating:
                db_question = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=interview_id,
                    round_type=round_type,
                    competency_targeted=competency,
                    difficulty=difficulty,
                    question_text=q_text,
                    sequence_number=current_seq,
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(db_question)
                self.db.flush()

            # Persist answer
            db_answer = InterviewAnswer(
                id=str(uuid.uuid4()),
                question_id=db_question.id,
                answer_text=ans_str,
                response_time_seconds=30,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_answer)
            self.db.flush()

            # Persist evaluation (single authoritative record)
            db_eval_record = Evaluation(
                id=str(uuid.uuid4()),
                answer_id=db_answer.id,
                score=score_pct,                        # 0-100 persisted
                rubric_breakdown=json.dumps(eval_result),  # full eval dict
                feedback=feedback_text,
                ideal_answer_summary=ideal_summary,
            )
            self.db.add(db_eval_record)

            # Persist agent log
            db_log = AgentLog(
                id=str(uuid.uuid4()),
                interview_id=interview_obj.id,
                agent_name="EvaluationAgent",
                node_status="COMPLETED",
                input_snapshot=json.dumps({
                    "answer": ans_str[:200],
                    "question": q_text[:200],
                    "competency": competency,
                }),
                output_snapshot=json.dumps(eval_result),
                latency_ms=0,
                retry_count=0,
                prompt_version="1.0",
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(db_log)

            # ── Check completion ──────────────────────────────────────────────
            next_seq = current_seq + 1
            next_db_q = self.question_repo.get_by_interview_and_sequence(
                interview_id, next_seq
            )
            all_configured_questions = self.question_repo.list_by_interview(interview_id)

            is_last = (current_seq >= total_questions)

            if is_last:
                is_completed = True
                interview_obj.status = "COMPLETED"
                interview_obj.completed_at = datetime.now(timezone.utc)

                # Compute overall score from all evaluations + current
                all_scores = [
                    item.get("evaluation", {}).get("score", 0)
                    for item in existing_answered
                    if isinstance(item.get("evaluation"), dict)
                ]
                all_scores.append(score_pct)
                interview_obj.overall_score = int(round(
                    sum(all_scores) / max(1, len(all_scores))
                ))
                ACTIVE_INTERVIEWS_GAUGE.dec()

            else:
                # ── Dynamically generate/update next question adaptively ──────
                asked_history = [
                    {
                        "question_text": q.question_text,
                        "competency_targeted": q.competency_targeted,
                        "round_type": q.round_type,
                    }
                    for q in all_configured_questions
                    if q.sequence_number < next_seq
                ]
                gen_evaluations = previous_evaluations + [{
                    "score": llm_score_1_10,
                    "competency_targeted": competency,
                    "question_type": round_type.lower() if round_type else "fundamentals",
                }]

                if next_db_q:
                    # Regenerate pre-created question with real-time evaluation history & adaptive difficulty
                    next_q = self._generate_question_via_llm(
                        next_db_q.round_type,
                        resume_data,
                        jd_data,
                        competency_matrix,
                        asked_history,
                        gen_evaluations,
                    )
                    if next_q and next_q.get("question_text"):
                        next_db_q.question_text = next_q["question_text"]
                        next_db_q.competency_targeted = next_q.get("competency_targeted") or next_db_q.competency_targeted
                        next_db_q.difficulty = next_q.get("difficulty") or next_difficulty_str
                        self.db.add(next_db_q)
                        self.db.flush()
                else:
                    next_round_type = _determine_next_round_type(next_seq, is_fresher_candidate)
                    next_q = self._generate_question_via_llm(
                        next_round_type,
                        resume_data,
                        jd_data,
                        competency_matrix,
                        asked_history,
                        gen_evaluations,
                    )

                    if not next_q:
                        raise HTTPException(
                            status_code=503,
                            detail=(
                                f"Next question generation failed for round {next_round_type}. "
                                "LLM service may be unavailable."
                            ),
                        )

                    next_db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_obj.id,
                        round_type=next_round_type,
                        competency_targeted=next_q.get("competency_targeted") or "General",
                        difficulty=next_q.get("difficulty") or next_difficulty_str,
                        question_text=next_q["question_text"],
                        sequence_number=next_seq,
                        created_at=datetime.now(timezone.utc),
                    )
                    self.db.add(next_db_q)
                    self.db.flush()

                    logger.info(
                        f"QuestionGeneratorAgent[adaptive]: interview={interview_id}, "
                        f"seq={next_seq}, competency={next_db_q.competency_targeted!r}, "
                        f"difficulty={next_db_q.difficulty} ({adaptation.adaptation_reason})"
                    )

                next_q_data = {
                    "id": next_db_q.id,
                    "sequence_number": next_db_q.sequence_number,
                    "round_type": next_db_q.round_type,
                    "competency": next_db_q.competency_targeted,
                    "difficulty": next_db_q.difficulty,
                    "text": next_db_q.question_text,
                }

            # ── Atomic commit ─────────────────────────────────────────────────
            self.db.commit()

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as exc:
            self.db.rollback()
            logger.error(
                f"Atomic transaction failed in submit_answer for {interview_id}: {exc}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to process answer: {str(exc)[:120]}"
            )

        # Generate report on completion
        if is_completed:
            try:
                from app.services.report_service import ReportService
                report_service = ReportService(self.db)
                report_service.generate_report(interview_id)
            except Exception as exc:
                logger.warning(f"Report generation warning for {interview_id}: {exc}")

        status_str = "COMPLETED" if is_completed else "IN_PROGRESS"
        return {
            "interview_id": interview_id,
            "status": status_str,
            "evaluation": eval_result,
            "next_question": next_q_data,
            "report_id": interview_id if is_completed else None,
            "message": (
                "Interview completed successfully. Report generated."
                if is_completed
                else "Answer evaluated via EvaluationAgent LLM. Persisted to PostgreSQL."
            ),
        }

    # ── Lifecycle methods ─────────────────────────────────────────────────────

    def pause_interview(self, interview_id: str) -> Optional[Interview]:
        return self._update_status(interview_id, "PAUSED")

    def resume_interview(self, interview_id: str) -> Optional[Interview]:
        return self._update_status(interview_id, "IN_PROGRESS")

    def complete_interview(
        self, interview_id: str, overall_score: Optional[float] = None
    ) -> Optional[Interview]:
        interview = self.get_interview(interview_id)
        if not interview:
            return None

        if interview.status != "COMPLETED":
            interview.status = "COMPLETED"
            interview.completed_at = datetime.now(timezone.utc)

            if overall_score is not None:
                interview.overall_score = int(overall_score)
            else:
                existing_answers = self.answer_repo.list_answers_with_evaluations_by_interview(interview_id)
                all_scores = [
                    item.get("evaluation", {}).get("score", 0)
                    for item in existing_answers
                    if isinstance(item.get("evaluation"), dict) and item.get("evaluation", {}).get("score") is not None
                ]
                if all_scores:
                    interview.overall_score = int(round(sum(all_scores) / len(all_scores)))

            self.db.add(interview)
            self.db.commit()
            self.db.refresh(interview)
            ACTIVE_INTERVIEWS_GAUGE.dec()

            try:
                from app.services.report_service import ReportService
                report_service = ReportService(self.db)
                report_service.generate_report(interview_id)
            except Exception as exc:
                logger.warning(f"Report generation warning during explicit completion for {interview_id}: {exc}")

        return interview

    def _update_status(self, interview_id: str, status: str) -> Optional[Interview]:
        interview = self.get_interview(interview_id)
        if not interview:
            return None
        return self.interview_repo.update(interview_id, {"status": status})

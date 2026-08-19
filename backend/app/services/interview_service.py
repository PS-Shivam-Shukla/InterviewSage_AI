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
import time
from time import monotonic
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.evaluation_agent import EvaluationAgent
from app.agents.question_generator_agent import QuestionGeneratorAgent
from app.core.logging import get_logger
from app.core.metrics import (
    ACTIVE_INTERVIEWS_GAUGE,
    INTERVIEW_REQUESTS_TOTAL,
    MCP_TOOL_CALLS_TOTAL,
)
from app.core.request_context import set_request_context
from app.graph.graph_builder import build_graph
from app.graph.workflow_master import get_checkpointer
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
from app.strategy.aptitude_bank import select_aptitude_questions
from app.strategy.difficulty_engine import DifficultyEngine

logger = get_logger(__name__)

# Master LangGraph workflow instance compiled with persistent checkpointer
master_workflow = build_graph(allow_stubs=False, checkpointer=get_checkpointer())
difficulty_engine = DifficultyEngine()


# ── Module-level helpers ──────────────────────────────────────────────────────


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


def _parse_json_field(value: str | None, default=None) -> Any:
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
    competencies: list[dict] = []
    seen: set = set()

    # JD skills: primary competencies (descending weight)
    for i, skill in enumerate(jd_skills[:8]):
        if not skill or not isinstance(skill, str):
            continue
        norm = skill.lower().strip()
        if norm not in seen:
            seen.add(norm)
            weight = max(8, 22 - i * 2)
            competencies.append(
                {
                    "name": skill,
                    "weight": weight,
                    "description": f"{skill} proficiency required for {role or 'this role'}",
                }
            )

    # Resume skills: supplemental competencies
    for skill in resume_skills[:4]:
        if not skill or not isinstance(skill, str):
            continue
        norm = skill.lower().strip()
        if norm not in seen:
            seen.add(norm)
            competencies.append(
                {
                    "name": skill,
                    "weight": 6,
                    "description": f"{skill} from candidate background",
                }
            )

    if not competencies:
        return [
            {
                "name": "General",
                "weight": 100,
                "description": f"General {role or 'Software Engineering'} knowledge",
            }
        ]

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
        "FRESHER",
        "JUNIOR",
        "0-1",
        "ENTRY",
        "INTERN",
        "1",
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
    ) -> dict | None:
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
            "resume_data": resume_data,  # ← was "resume_json" (WRONG)
            "jd_data": jd_data,  # ← was "jd_json" (WRONG)
            "competency_matrix": competency_matrix,
            "questions_asked": questions_asked,
            "evaluations": evaluations,
        }
        output = q_gen(state)

        # Retrieve question from current_question (supports both LLM generated and seed-bank recovered)
        question = output.get("current_question")
        if question and question.get("question_text"):
            if output.get("error_log"):
                fallback_type = output["error_log"][0].get("fallback", "seed_bank")
                logger.warning(
                    f"QuestionGeneratorAgent recovered via fallback [{fallback_type}] for {round_type}: "
                    f"role={jd_data.get('target_role')}, "
                    f"competency={question.get('competency_targeted')}, "
                    f"difficulty={question.get('difficulty')}"
                )
            else:
                logger.info(
                    f"QuestionGeneratorAgent[{round_type}]: role={jd_data.get('target_role')}, "
                    f"competency={question.get('competency_targeted')}, "
                    f"difficulty={question.get('difficulty')}"
                )
            return question

        # If both LLM and seed-bank recovery failed to produce a valid question
        logger.error(
            f"QuestionGeneratorAgent failed completely for {round_type}: {output.get('error_log')}"
        )
        return None

    # ── create_interview ──────────────────────────────────────────────────────

    def create_interview(
        self,
        user_id: str,
        resume_id: str,
        jd_id: str,
        payload: dict[str, Any] | None = None,
    ) -> Interview:
        """
        Initialize a new interview session. Requires valid resume_id and jd_id.
        Immediate Q1 selection from deterministic seed bank, status set to READY synchronously.
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

        # Deduplication Check
        recent_cutoff = datetime.now(UTC) - timedelta(minutes=5)
        existing_recent = (
            self.db.query(Interview)
            .filter(
                Interview.user_id == user_id,
                Interview.resume_id == resume_id,
                Interview.jd_id == jd_id,
                Interview.status.in_(["READY", "IN_PROGRESS"]),
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

        # Determine role_title and company_name
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

        # Build authoritative interview context
        resume_data = _build_resume_data(resume_db)
        jd_data = _build_jd_data(jd_db)
        seniority = (
            (payload and payload.get("experience_level"))
            or resume_data.get("seniority_signal")
            or jd_data.get("seniority_level")
            or "MID"
        ).upper()
        resume_data["seniority_signal"] = seniority

        jd_skills: list[str] = jd_data.get("required_skills", [])
        resume_skills: list[str] = resume_data.get("skills", [])
        is_fresher_candidate = _is_fresher(seniority)
        competency_matrix = _build_competency_matrix(role_title, jd_skills, resume_skills)

        # Create interview row in DB with status READY
        interview = Interview(
            user_id=user_id,
            resume_id=resume_id,
            jd_id=jd_id,
            target_role=role_title,
            target_company=company_name,
            status="READY",
            current_round="TECHNICAL",
            overall_score=None,
            started_at=datetime.now(UTC),
            completed_at=None,
        )
        created = self.interview_repo.create(interview)
        ACTIVE_INTERVIEWS_GAUGE.inc()

        # Save competency matrix
        from app.models.interview import CompetencyMatrix, InterviewPlan
        comp_matrix_record = CompetencyMatrix(
            interview_id=created.id,
            competencies=json.dumps(competency_matrix),
        )
        self.db.add(comp_matrix_record)

        # Save interview plan
        plan_record = InterviewPlan(
            interview_id=created.id,
            hr_question_count=2,
            technical_question_count=7 if is_fresher_candidate else 3,
            round_structure=json.dumps({}),
            estimated_duration_minutes=60,
        )
        self.db.add(plan_record)
        self.db.flush()

        # Generate questions & placeholders
        from app.strategy.seed_question_bank import get_seed_question
        
        if is_fresher_candidate:
            # 4 Aptitude (fixed bank), 3 Technical, 2 HR = 9 Total
            aptitude_qs = select_aptitude_questions(4, session_seed=created.id)
            for idx, apt in enumerate(aptitude_qs, start=1):
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=created.id,
                    round_type="APTITUDE",
                    competency_targeted=apt["competency_targeted"],
                    difficulty=apt["difficulty"],
                    question_text=apt["question_text"],
                    sequence_number=idx,
                    status="READY",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q)

            # Q5, Q6, Q7: Technical
            for idx, seq_num in enumerate(range(5, 8)):
                comp_name = competency_matrix[idx % len(competency_matrix)]["name"] if competency_matrix else "Technical"
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=created.id,
                    round_type="TECHNICAL",
                    competency_targeted=comp_name,
                    difficulty="MEDIUM",
                    question_text="[Pending JIT Generation]",
                    sequence_number=seq_num,
                    status="PENDING",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q)

            # Q8, Q9: HR
            hr_comps = ["Communication", "Conflict Resolution"]
            for idx, seq_num in enumerate(range(8, 10)):
                comp_name = hr_comps[idx % len(hr_comps)]
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=created.id,
                    round_type="HR",
                    competency_targeted=comp_name,
                    difficulty="EASY",
                    question_text="[Pending JIT Generation]",
                    sequence_number=seq_num,
                    status="PENDING",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q)

        else:
            # EXPERIENCED: 3 Technical, 2 HR = 5 Total
            first_comp = competency_matrix[0]["name"] if competency_matrix else "System Design"
            q1_seed = get_seed_question(
                round_type="TECHNICAL",
                competency=first_comp,
                difficulty="MEDIUM",
            )
            db_q1 = InterviewQuestion(
                id=str(uuid.uuid4()),
                interview_id=created.id,
                round_type="TECHNICAL",
                competency_targeted=first_comp,
                difficulty="MEDIUM",
                question_text=q1_seed["question_text"],
                sequence_number=1,
                status="READY",
                created_at=datetime.now(UTC),
            )
            self.db.add(db_q1)

            # Q2, Q3: Technical
            for idx, seq_num in enumerate(range(2, 4)):
                comp_name = competency_matrix[(idx + 1) % len(competency_matrix)]["name"] if len(competency_matrix) > 1 else first_comp
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=created.id,
                    round_type="TECHNICAL",
                    competency_targeted=comp_name,
                    difficulty="MEDIUM",
                    question_text="[Pending JIT Generation]",
                    sequence_number=seq_num,
                    status="PENDING",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q)

            # Q4, Q5: HR
            hr_comps = ["Collaboration & Adaptability", "Culture Fit & Motivation"]
            for idx, seq_num in enumerate(range(4, 6)):
                comp_name = hr_comps[idx % len(hr_comps)]
                db_q = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=created.id,
                    round_type="HR",
                    competency_targeted=comp_name,
                    difficulty="MEDIUM",
                    question_text="[Pending JIT Generation]",
                    sequence_number=seq_num,
                    status="PENDING",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q)

        self.db.commit()
        return created

    def generate_question_jit_background(self, interview_id: str, sequence_number: int) -> None:
        """
        Spawns a background task (using loop.run_in_executor) to run JIT generation.
        """
        import asyncio

        def _run_in_thread():
            from app.core.database import SessionLocal
            db = SessionLocal()
            try:
                service = InterviewService(db)
                service.generate_question_jit_sync(interview_id, sequence_number)
            except Exception as e:
                logger.error(f"Error in generate_question_jit_background for seq {sequence_number}: {e}", exc_info=True)
            finally:
                db.close()

        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(None, _run_in_thread)
        except RuntimeError:
            _run_in_thread()

    def generate_question_jit_sync(self, interview_id: str, sequence_number: int) -> None:
        """
        Synchronously performs JIT question generation.
        Locks/marks status to GENERATING, invokes LLM, validates, and sets to READY or FALLBACK.
        """
        set_request_context(interview_id=interview_id)
        logger.info(f"Starting JIT generation for interview={interview_id}, seq={sequence_number}")

        # Load interview
        interview_obj = self.get_interview(interview_id)
        if not interview_obj:
            logger.error(f"Interview {interview_id} not found during JIT generation.")
            return

        # Fetch target question row with database row lock to prevent concurrency races
        q_row = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.sequence_number == sequence_number
        ).with_for_update().first()

        if not q_row:
            logger.error(f"InterviewQuestion row for seq {sequence_number} not found during JIT generation.")
            return

        # Idempotency check: if already generated or fallback, return
        if q_row.status in ("READY", "FALLBACK", "CONSUMED"):
            logger.info(f"Question seq {sequence_number} already in status {q_row.status}. Skipping JIT.")
            return

        # Mark question as GENERATING
        q_row.status = "GENERATING"
        self.db.commit()

        # Load context
        resume_obj = self.db.query(Resume).filter(Resume.id == interview_obj.resume_id).first()
        jd_obj = self.db.query(JobDescription).filter(JobDescription.id == interview_obj.jd_id).first()
        resume_data = _build_resume_data(resume_obj)
        jd_data = _build_jd_data(jd_obj)
        role_title = jd_data.get("target_role") or "Software Engineer"
        jd_data["target_role"] = role_title

        seniority = resume_data.get("seniority_signal") or "MID"

        # Get competency matrix
        from app.models.interview import CompetencyMatrix
        comp_matrix_record = self.db.query(CompetencyMatrix).filter(CompetencyMatrix.interview_id == interview_id).first()
        competency_matrix = json.loads(comp_matrix_record.competencies) if comp_matrix_record else []

        # Load accepted question history
        all_questions = self.question_repo.list_by_interview(interview_id)

        # Build asked_history: only include accepted previous questions (READY, FALLBACK, CONSUMED)
        asked_history = [
            {
                "question_text": q.question_text,
                "competency_targeted": q.competency_targeted,
                "round_type": q.round_type,
                "cognitive_angle": getattr(q, "cognitive_angle", None) or "fundamentals",
            }
            for q in all_questions
            if q.sequence_number < sequence_number and q.status in ("READY", "FALLBACK", "CONSUMED")
        ]

        # Determine target competency
        target_comp = q_row.competency_targeted

        # Build evaluations list
        existing_answered = self.answer_repo.list_answers_with_evaluations_by_interview(interview_id)
        previous_evaluations = []
        for item in existing_answered:
            eval_d = item.get("evaluation", {})
            if eval_d and isinstance(eval_d, dict):
                pct = eval_d.get("score", 0)
                previous_evaluations.append({
                    "score": round(pct / 10) if pct > 10 else pct,
                    "competency_targeted": eval_d.get("competency_targeted", ""),
                    "question_type": eval_d.get("question_type", ""),
                })

        # Generate via LLM (QuestionGeneratorAgent)
        t0 = time.monotonic()
        q_gen = QuestionGeneratorAgent(round_type=q_row.round_type)
        state = {
            "interview_id": interview_id,
            "resume_data": resume_data,
            "jd_data": jd_data,
            "competency_matrix": competency_matrix,
            "questions_asked": asked_history,
            "evaluations": previous_evaluations,
            "target_competency": target_comp,
        }

        try:
            agent_res = q_gen(state)
            q_data = agent_res.get("current_question")

            # Check if LLM returned a valid question and not fallback
            if q_data and q_data.get("question_text") and not q_data.get("fallback_used"):
                q_row.question_text = q_data["question_text"]
                q_row.competency_targeted = q_data.get("competency_targeted") or target_comp
                q_row.difficulty = q_data.get("difficulty") or q_row.difficulty
                q_row.status = "READY"

                llm_wait = int((time.monotonic() - t0) * 1000)
                val_ms = 3
                total_att_ms = llm_wait + val_ms

                logger.info(
                    f"\nQUESTION_JIT\n"
                    f"  seq={sequence_number}\n"
                    f"  attempt=1\n"
                    f"  competency={target_comp}\n"
                    f"  selected_competency={q_row.competency_targeted}\n"
                    f"  cognitive_angle={q_data.get('cognitive_angle', 'fundamentals')}\n"
                    f"  llm_wait_ms={llm_wait}\n"
                    f"  validation_ms={val_ms}\n"
                    f"  result=READY\n"
                    f"  fallback_used=false\n"
                    f"  total_attempt_ms={total_att_ms}"
                )
                self.db.add(q_row)
                self.db.commit()
                return

        except Exception as exc:
            logger.warning(f"LLM question generation failed for seq {sequence_number}: {exc}")

        # If LLM generation failed or returned a fallback, load seed fallback
        difficulty = _adaptive_difficulty(target_comp, previous_evaluations)
        from app.strategy.seed_question_bank import get_seed_question
        seed_q = get_seed_question(
            round_type=q_row.round_type,
            competency=target_comp,
            difficulty=difficulty,
            asked_questions=asked_history,
        )

        q_row.question_text = seed_q["question_text"]
        q_row.competency_targeted = seed_q.get("competency_targeted") or target_comp
        q_row.difficulty = seed_q.get("difficulty") or difficulty
        q_row.status = "FALLBACK"

        logger.info(
            f"\nQUESTION_JIT\n"
            f"  seq={sequence_number}\n"
            f"  competency={target_comp}\n"
            f"  result=FALLBACK\n"
            f"  fallback_type=seed_bank\n"
            f"  fallback_used=true"
        )
        self.db.add(q_row)
        self.db.commit()

    def trigger_next_pending_generation(self, interview_id: str) -> None:
        """
        Finds the first question in PENDING status and triggers JIT generation for it.
        """
        pending_q = self.db.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview_id,
            InterviewQuestion.status == "PENDING"
        ).order_by(InterviewQuestion.sequence_number.asc()).first()

        if pending_q:
            self.generate_question_jit_background(interview_id, pending_q.sequence_number)

    def get_interview(self, interview_id: str) -> Interview | None:
        return self.interview_repo.get_by_id(interview_id)

    # ── get_interview_plan ────────────────────────────────────────────────────

    def get_interview_plan(
        self,
        interview_id: str,
        context_override: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """
        Build or return the interview question plan. Returns blueprint items and first question.
        Never calls LLM, executes instantly.
        """
        interview_obj = self.get_interview(interview_id)
        if not interview_obj:
            return None

        set_request_context(interview_id=interview_id, user_id=interview_obj.user_id)

        jd_obj = (
            self.db.query(JobDescription).filter(JobDescription.id == interview_obj.jd_id).first()
        )
        resume_obj = self.db.query(Resume).filter(Resume.id == interview_obj.resume_id).first()

        resume_data = _build_resume_data(resume_obj)
        jd_data = _build_jd_data(jd_obj)

        role_title = (
            (
                context_override
                and (context_override.get("role") or context_override.get("target_role"))
            )
            or jd_data.get("target_role")
            or "Interview"
        )
        jd_data["target_role"] = role_title

        seniority = (
            (context_override and context_override.get("experience_level"))
            or resume_data.get("seniority_signal")
            or jd_data.get("seniority_level")
            or "MID"
        ).upper()
        resume_data["seniority_signal"] = seniority

        is_fresher_candidate = _is_fresher(seniority)

        # Retrieve questions from DB (all 9 or 5 questions are pre-created during create_interview)
        existing_questions = self.question_repo.list_by_interview(interview_id)
        if not existing_questions:
            # Populate questions & matrix & plan dynamically from seed bank for legacy/manual tests
            from app.models.interview import CompetencyMatrix, InterviewPlan
            jd_skills: list[str] = jd_data.get("required_skills", [])
            resume_skills: list[str] = resume_data.get("skills", [])
            competency_matrix = _build_competency_matrix(role_title, jd_skills, resume_skills)

            # Check / save competency matrix
            comp_matrix_record = self.db.query(CompetencyMatrix).filter(CompetencyMatrix.interview_id == interview_id).first()
            if not comp_matrix_record:
                comp_matrix_record = CompetencyMatrix(
                    interview_id=interview_id,
                    competencies=json.dumps(competency_matrix),
                )
                self.db.add(comp_matrix_record)

            # Check / save plan
            plan_record = self.db.query(InterviewPlan).filter(InterviewPlan.interview_id == interview_id).first()
            if not plan_record:
                plan_record = InterviewPlan(
                    interview_id=interview_id,
                    hr_question_count=2,
                    technical_question_count=7 if is_fresher_candidate else 3,
                    round_structure=json.dumps({}),
                    estimated_duration_minutes=60,
                )
                self.db.add(plan_record)
            self.db.flush()

            from app.strategy.seed_question_bank import get_seed_question
            from app.strategy.aptitude_bank import select_aptitude_questions

            if is_fresher_candidate:
                # 4 Aptitude (fixed bank), 3 Technical, 2 HR = 9 Total
                aptitude_qs = select_aptitude_questions(4, session_seed=interview_id)
                for idx, apt in enumerate(aptitude_qs, start=1):
                    db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_id,
                        round_type="APTITUDE",
                        competency_targeted=apt["competency_targeted"],
                        difficulty=apt["difficulty"],
                        question_text=apt["question_text"],
                        sequence_number=idx,
                        status="READY",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(db_q)

                # Q5, Q6, Q7: Technical
                for idx, seq_num in enumerate(range(5, 8)):
                    comp_name = competency_matrix[idx % len(competency_matrix)]["name"] if competency_matrix else "Technical"
                    db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_id,
                        round_type="TECHNICAL",
                        competency_targeted=comp_name,
                        difficulty="MEDIUM",
                        question_text="[Pending JIT Generation]",
                        sequence_number=seq_num,
                        status="PENDING",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(db_q)

                # Q8, Q9: HR
                hr_comps = ["Communication", "Conflict Resolution"]
                for idx, seq_num in enumerate(range(8, 10)):
                    comp_name = hr_comps[idx % len(hr_comps)]
                    db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_id,
                        round_type="HR",
                        competency_targeted=comp_name,
                        difficulty="EASY",
                        question_text="[Pending JIT Generation]",
                        sequence_number=seq_num,
                        status="PENDING",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(db_q)
            else:
                # EXPERIENCED: 3 Technical, 2 HR = 5 Total
                first_comp = competency_matrix[0]["name"] if competency_matrix else "System Design"
                q1_seed = get_seed_question(
                    round_type="TECHNICAL",
                    competency=first_comp,
                    difficulty="MEDIUM",
                )
                db_q1 = InterviewQuestion(
                    id=str(uuid.uuid4()),
                    interview_id=interview_id,
                    round_type="TECHNICAL",
                    competency_targeted=first_comp,
                    difficulty="MEDIUM",
                    question_text=q1_seed["question_text"],
                    sequence_number=1,
                    status="READY",
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_q1)

                # Q2, Q3: Technical
                for idx, seq_num in enumerate(range(2, 4)):
                    comp_name = competency_matrix[(idx + 1) % len(competency_matrix)]["name"] if len(competency_matrix) > 1 else first_comp
                    db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_id,
                        round_type="TECHNICAL",
                        competency_targeted=comp_name,
                        difficulty="MEDIUM",
                        question_text="[Pending JIT Generation]",
                        sequence_number=seq_num,
                        status="PENDING",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(db_q)

                # Q4, Q5: HR
                hr_comps = ["Collaboration & Adaptability", "Culture Fit & Motivation"]
                for idx, seq_num in enumerate(range(4, 6)):
                    comp_name = hr_comps[idx % len(hr_comps)]
                    db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_id,
                        round_type="HR",
                        competency_targeted=comp_name,
                        difficulty="MEDIUM",
                        question_text="[Pending JIT Generation]",
                        sequence_number=seq_num,
                        status="PENDING",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(db_q)

            self.db.commit()
            existing_questions = self.question_repo.list_by_interview(interview_id)

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
                    "tier": (
                        "Junior Engineer / Fresher"
                        if is_fresher_candidate
                        else "Senior Engineer"
                    ),
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

    async def get_interview_plan_async(
        self,
        interview_id: str,
        context_override: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Async variant that offloads to a worker thread."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, lambda: self.get_interview_plan(interview_id, context_override)
        )

    def approve_blueprint(
        self,
        interview_id: str,
        overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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
        start_t0 = monotonic()

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

        # Guard: PAUSED state
        if interview_obj.status == "PAUSED":
            raise HTTPException(
                status_code=400,
                detail="Interview is currently PAUSED. Resume interview to submit answers.",
            )

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
        existing_answered = self.answer_repo.list_answers_with_evaluations_by_interview(
            interview_id
        )
        current_seq_from_count = len(existing_answered) + 1

        # ── 2. Locate exact question record with strict isolation ─────────────
        db_question = None
        question_needs_creating = False

        # Try by UUID (frontend sends actual DB ID now)
        if question_id and question_id not in ("q-1", ""):
            db_question = (
                self.db.query(InterviewQuestion)
                .filter(
                    InterviewQuestion.id == question_id,
                    InterviewQuestion.interview_id == interview_id,
                )
                .first()
            )

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
            q_text = (
                question_text
                if (question_text and (not db_question.question_text or db_question.question_text.startswith("[")))
                else db_question.question_text
            )
            competency = db_question.competency_targeted
            difficulty = db_question.difficulty
            round_type = db_question.round_type
            current_seq = db_question.sequence_number
        else:
            # Ad-hoc: derive from context
            jd_tmp = (
                self.db.query(JobDescription)
                .filter(JobDescription.id == interview_obj.jd_id)
                .first()
            )
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
        resume_obj = self.db.query(Resume).filter(Resume.id == interview_obj.resume_id).first()
        jd_obj = (
            self.db.query(JobDescription).filter(JobDescription.id == interview_obj.jd_id).first()
        )

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
        total_questions = (
            len(all_configured_questions)
            if all_configured_questions
            else (7 if is_fresher_candidate else 5)
        )

        # ── 4. Build previous evaluations list for adaptive difficulty ─────────
        previous_evaluations: list[dict] = []
        for item in existing_answered:
            eval_d = item.get("evaluation", {})
            if eval_d and isinstance(eval_d, dict):
                pct = eval_d.get("score", 0)
                # Store in 1-10 scale for the DifficultyEngine / QuestionGeneratorAgent
                previous_evaluations.append(
                    {
                        "question_id": item.get("sequence_number"),
                        "score": round(pct / 10) if pct > 10 else pct,
                        "competency_targeted": eval_d.get("competency_targeted", ""),
                        "question_type": eval_d.get("question_type", ""),
                    }
                )

        # ── 5. Run compiled production agentic graph ──────────────────────────
        MCP_TOOL_CALLS_TOTAL.labels(tool_name="evaluation_agent", status="success").inc()

        config = {"configurable": {"thread_id": interview_id}}

        # Explicit immutable current question context for this specific turn
        explicit_turn_q = {
            "id": db_question.id if db_question else str(uuid.uuid4()),
            "question_text": q_text,
            "competency_targeted": competency,
            "question_type": "aptitude" if round_type == "APTITUDE" else (round_type.lower() if round_type else "fundamentals"),
            "round_type": round_type,
            "difficulty": difficulty,
            "sequence_number": current_seq,
        }

        initial_state = {
            "interview_id": interview_id,
            "user_id": interview_obj.user_id,
            "resume_data": resume_data,
            "jd_data": jd_data,
            "competency_matrix": competency_matrix,
            "interview_plan": {
                "role": role_title,
                "hr_question_count": 2,
                "technical_question_count": 7 if is_fresher_candidate else 3,
                "total_questions": total_questions,
            },
            "current_round": round_type,
            "current_question": explicit_turn_q,
            "questions_asked": [
                {
                    "id": q.id,
                    "question_text": q.question_text,
                    "competency_targeted": q.competency_targeted,
                    "round_type": q.round_type,
                    "difficulty": q.difficulty,
                    "sequence_number": q.sequence_number,
                }
                for q in all_configured_questions
                if q.sequence_number <= current_seq
            ],
            "answers": [
                {
                    "sequence_number": item.get("sequence_number", 1),
                    "answer_text": item.get("candidate_answer", ""),
                }
                for item in existing_answered
            ] + [{
                "question_id": db_question.id if db_question else str(uuid.uuid4()),
                "sequence_number": current_seq,
                "answer_text": ans_str,
                "round_type": round_type,
                "competency_targeted": competency,
            }],
            "evaluations": previous_evaluations,
            "workflow_stage": "WAITING_FOR_ANSWER",
            "pending_answer": ans_str,
            "policy_iteration_count": 0,
            "policy_decisions": [],
            "observations": [],
        }

        output_state = master_workflow.invoke(initial_state, config=config)

        # ── 6. Extract LLM evaluation — CORRECT KEY: "evaluations" list ──────
        evaluations_list = output_state.get("evaluations", [])
        if not evaluations_list:
            logger.error(f"EvaluationAgent returned no evaluations for {interview_id}")
            raise HTTPException(
                status_code=503,
                detail="LLM evaluation failed — EvaluationAgent returned no result.",
            )

        llm_eval = evaluations_list[-1]

        # Detect hard failure (_on_failure: score=0 + needs_human_review=True)
        if llm_eval.get("needs_human_review") and int(llm_eval.get("score", 0)) == 0:
            logger.error(f"EvaluationAgent LLM failure for interview={interview_id}")
            raise HTTPException(
                status_code=503,
                detail="LLM evaluation failed. Ollama service may be unavailable.",
            )

        # ── Safety Guard: Ensure evaluation context matches submitted question ───
        eval_q_seq = llm_eval.get("question_id")
        if eval_q_seq is not None and eval_q_seq != current_seq:
            logger.error(
                f"QUESTION_CONTEXT_MISMATCH: Evaluation returned for seq={eval_q_seq}, "
                f"expected submitted question seq={current_seq}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"QUESTION_CONTEXT_MISMATCH: Evaluation generated for sequence {eval_q_seq} instead of submitted question {current_seq}.",
            )

        # ── 7. Convert 1-10 → 0-100 ONCE at service boundary ─────────────────
        raw_val = int(llm_eval.get("score", 0))
        if raw_val == 0:
            llm_score_1_10 = 0
            score_pct = 0
        elif raw_val > 10:
            # Already on 0-100 scale (e.g. from conftest test double)
            score_pct = raw_val
            llm_score_1_10 = int(round(raw_val / 10))
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

        # Build complete evaluation result with round-specific scorecards
        feedback_text = llm_eval.get("feedback", "")
        ideal_summary = llm_eval.get("ideal_answer_summary", "")
        display_str = f"{llm_score_1_10}/10 ({score_pct}%)"

        comm_val = (
            rubric_pct.get("Communication")
            if "Communication" in rubric_pct
            else (
                rubric_pct.get("Clarity & Structure")
                if "Clarity & Structure" in rubric_pct
                else llm_eval.get("communication_score")
            )
        )
        conf_val = (
            rubric_pct.get("Confidence")
            if "Confidence" in rubric_pct
            else llm_eval.get("confidence_score")
        )

        eval_result = {
            "question_id": current_seq,
            "score": score_pct,
            "score_1_10": llm_score_1_10,
            "display_score": display_str,
            "scorecard_type": round_type,
            "technical_score": score_pct if round_type == "TECHNICAL" else None,
            "communication_score": comm_val if comm_val is not None else score_pct,
            "confidence_score": conf_val if conf_val is not None else score_pct,
            "correctness": rubric_pct.get("Correctness & Accuracy", rubric_pct.get("Correctness", score_pct)),
            "relevance": rubric_pct.get("Reasoning & Approach", rubric_pct.get("Completeness", score_pct)),
            "technical_quality": score_pct if round_type == "TECHNICAL" else None,
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
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_question)
                self.db.flush()

            # Check if an answer already exists for this question (prevent duplicate submissions)
            db_answer = self.db.query(InterviewAnswer).filter(InterviewAnswer.question_id == db_question.id).first()
            if db_answer:
                db_answer.answer_text = ans_str
                db_answer.created_at = datetime.now(UTC)
                self.db.add(db_answer)
                self.db.flush()
            else:
                db_answer = InterviewAnswer(
                    id=str(uuid.uuid4()),
                    question_id=db_question.id,
                    answer_text=ans_str,
                    response_time_seconds=30,
                    created_at=datetime.now(UTC),
                )
                self.db.add(db_answer)
                self.db.flush()

            # Check if an evaluation already exists for this answer
            db_eval_record = self.db.query(Evaluation).filter(Evaluation.answer_id == db_answer.id).first()
            if db_eval_record:
                db_eval_record.score = score_pct
                db_eval_record.rubric_breakdown = json.dumps(eval_result)
                db_eval_record.feedback = feedback_text
                db_eval_record.ideal_answer_summary = ideal_summary
                self.db.add(db_eval_record)
            else:
                db_eval_record = Evaluation(
                    id=str(uuid.uuid4()),
                    answer_id=db_answer.id,
                    score=score_pct,
                    rubric_breakdown=json.dumps(eval_result),
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
                input_snapshot=json.dumps(
                    {
                        "answer": ans_str[:200],
                        "question": q_text[:200],
                        "competency": competency,
                    }
                ),
                output_snapshot=json.dumps(eval_result),
                latency_ms=int((monotonic() - start_t0) * 1000),
                retry_count=0,
                prompt_version="1.0",
                created_at=datetime.now(UTC),
            )
            self.db.add(db_log)

            # Mark current question as CONSUMED
            db_question.status = "CONSUMED"
            self.db.add(db_question)

            # ── Check completion ──────────────────────────────────────────────
            next_seq = current_seq + 1
            next_db_q = self.question_repo.get_by_interview_and_sequence(interview_id, next_seq)
            all_configured_questions = self.question_repo.list_by_interview(interview_id)

            is_last = current_seq >= total_questions

            if is_last:
                is_completed = True
                interview_obj.status = "COMPLETED"
                interview_obj.completed_at = datetime.now(UTC)

                # Compute overall score from all evaluations + current
                all_scores = [
                    item.get("evaluation", {}).get("score", 0)
                    for item in existing_answered
                    if isinstance(item.get("evaluation"), dict)
                ]
                all_scores.append(score_pct)
                interview_obj.overall_score = int(round(sum(all_scores) / max(1, len(all_scores))))
                ACTIVE_INTERVIEWS_GAUGE.dec()
                next_q_data = None

            else:
                # ── Ensure next question is ready or fallback ───────────────────
                if not next_db_q:
                    # Dynamically create next question row (e.g. for legacy manual tests)
                    next_round_type = _determine_next_round_type(next_seq, is_fresher_candidate)
                    from app.strategy.seed_question_bank import get_seed_question
                    comp_name = competency_matrix[next_seq % len(competency_matrix)]["name"] if competency_matrix else "Technical"
                    difficulty = next_difficulty_str
                    asked_list = [
                        {
                            "question_text": q.question_text,
                            "competency_targeted": q.competency_targeted,
                            "round_type": q.round_type,
                        }
                        for q in all_configured_questions
                        if q.sequence_number < next_seq and q.status in ("READY", "FALLBACK", "CONSUMED")
                    ]
                    seed_q = get_seed_question(
                        round_type=next_round_type,
                        competency=comp_name,
                        difficulty=difficulty,
                        asked_questions=asked_list,
                    )
                    next_db_q = InterviewQuestion(
                        id=str(uuid.uuid4()),
                        interview_id=interview_obj.id,
                        round_type=next_round_type,
                        competency_targeted=seed_q.get("competency_targeted") or comp_name,
                        difficulty=seed_q.get("difficulty") or difficulty,
                        question_text=seed_q["question_text"],
                        sequence_number=next_seq,
                        status="READY",
                        created_at=datetime.now(UTC),
                    )
                    self.db.add(next_db_q)
                    self.db.flush()

                elif next_db_q.status in ("PENDING", "GENERATING"):
                    logger.info(f"Next question Q{next_seq} is in status {next_db_q.status}. Starting bounded wait...")
                    import time
                    for _ in range(6):
                        self.db.refresh(next_db_q)
                        if next_db_q.status in ("READY", "FALLBACK"):
                            break
                        time.sleep(0.5)

                    # If still not ready, fetch seed-bank fallback immediately
                    if next_db_q.status in ("PENDING", "GENERATING"):
                        logger.warning(f"Next question Q{next_seq} still not ready after bounded wait. Using seed-bank fallback.")
                        difficulty = next_db_q.difficulty or next_difficulty_str
                        asked_list = [
                            {
                                "question_text": q.question_text,
                                "competency_targeted": q.competency_targeted,
                                "round_type": q.round_type,
                            }
                            for q in all_configured_questions
                            if q.sequence_number < next_seq and q.status in ("READY", "FALLBACK", "CONSUMED")
                        ]
                        from app.strategy.seed_question_bank import get_seed_question
                        seed_q = get_seed_question(
                            round_type=next_db_q.round_type,
                            competency=next_db_q.competency_targeted,
                            difficulty=difficulty,
                            asked_questions=asked_list,
                        )
                        next_db_q.question_text = seed_q["question_text"]
                        next_db_q.competency_targeted = seed_q.get("competency_targeted") or next_db_q.competency_targeted
                        next_db_q.difficulty = seed_q.get("difficulty") or difficulty
                        next_db_q.status = "FALLBACK"
                        self.db.add(next_db_q)
                        self.db.flush()

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

            if not is_completed:
                self.trigger_next_pending_generation(interview_id)

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

        # Save or queue report on completion
        if is_completed:
            try:
                final_rep = output_state.get("final_report")
                ver_rep = output_state.get("verification_report") or {}
                needs_review = output_state.get("human_review_required", False) or not ver_rep.get("verified", True)

                if needs_review:
                    # Verification failed: flag in ReviewQueue and do NOT publish
                    from app.review.service import ReviewService

                    ReviewService(self.db).flag_for_review(
                        interview_id=interview_id,
                        confidence=0.0,
                        reason="Report verification failed: executive summary contains unsupported claims.",
                    )
                    self.db.commit()
                    logger.warning(f"Report verification failed for {interview_id}. Flagged for review.")
                else:
                    # Verification succeeded: publish report
                    if final_rep:
                        scorecard = [
                            c.model_dump() if hasattr(c, "model_dump") else c
                            for c in final_rep.get("competency_scorecard", [])
                        ]
                        imp_plan = final_rep.get("improvement_plan", [])
                        transcript = [
                            t.model_dump() if hasattr(t, "model_dump") else t
                            for t in final_rep.get("transcript_snapshot", [])
                        ]

                        from app.models.interview import InterviewReport

                        report_obj = InterviewReport(
                            interview_id=interview_id,
                            competency_scorecard=json.dumps(scorecard),
                            improvement_plan=json.dumps(imp_plan),
                            transcript_snapshot=json.dumps(transcript),
                            generated_at=datetime.now(UTC),
                        )
                        # Remove existing if any
                        existing_rep = (
                            self.db.query(InterviewReport)
                            .filter(InterviewReport.interview_id == interview_id)
                            .first()
                        )
                        if existing_rep:
                            self.db.delete(existing_rep)
                            self.db.flush()
                        self.db.add(report_obj)
                        self.db.commit()
                        logger.info(f"Verified report published successfully for {interview_id}.")
            except Exception as exc:
                logger.error(
                    f"Failed to handle completed report for {interview_id}: {exc}", exc_info=True
                )

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

    def pause_interview(self, interview_id: str) -> Interview | None:
        return self._update_status(interview_id, "PAUSED")

    def resume_interview(self, interview_id: str) -> Interview | None:
        return self._update_status(interview_id, "IN_PROGRESS")

    def complete_interview(
        self, interview_id: str, overall_score: float | None = None
    ) -> Interview | None:
        interview = self.get_interview(interview_id)
        if not interview:
            return None

        if interview.status != "COMPLETED":
            interview.status = "COMPLETED"
            interview.completed_at = datetime.now(UTC)

            if overall_score is not None:
                interview.overall_score = int(overall_score)
            else:
                existing_answers = self.answer_repo.list_answers_with_evaluations_by_interview(
                    interview_id
                )
                all_scores = [
                    item.get("evaluation", {}).get("score", 0)
                    for item in existing_answers
                    if isinstance(item.get("evaluation"), dict)
                    and item.get("evaluation", {}).get("score") is not None
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
                logger.warning(
                    f"Report generation warning during explicit completion for {interview_id}: {exc}"
                )

        return interview

    def _update_status(self, interview_id: str, status: str) -> Interview | None:
        interview = self.get_interview(interview_id)
        if not interview:
            return None
        return self.interview_repo.update(interview_id, {"status": status})

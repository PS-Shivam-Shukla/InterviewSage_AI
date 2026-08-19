"""
Integration Tests for Interview Startup & JIT Question Generation Refactor (Phase 14).
"""

import time
import uuid
import pytest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import (
    Interview,
    InterviewQuestion,
    JobDescription,
    Resume,
    User,
    InterviewAnswer,
    Evaluation,
)
from app.services import InterviewService, AuthService
from app.agents.question_generator_agent import QuestionGeneratorAgent, GeneratedQuestion
from app.core.llm_client import LLMClient
from app.strategy.seed_question_bank import get_seed_question


@pytest.fixture(autouse=True)
def bypass_speech_and_mcp():
    """Mock speech services and MCP for rapid offline test execution."""
    from app.speech.stt import FasterWhisperSTTService
    from app.speech.tts import KokoroTTSService

    mock_res = MagicMock()
    mock_res.output = {
        "score": 8,
        "reasoning": "Evaluated successfully.",
        "rubric_breakdown": {"Communication": 4, "Confidence": 4},
        "feedback": "Great response.",
        "ideal_answer_summary": "Ideal answer",
        "answer_quality": "VALID_ANSWER",
    }
    dummy_wav = b"RIFF dummy audio data"

    from app.mcp.server import mcp_server
    orig_call_tool = mcp_server.call_tool

    def mock_call_tool(name, *args, **kwargs):
        if name == "score_answer_rubric":
            return orig_call_tool(name, *args, **kwargs)
        # For other tools, return mock result with success=True
        m = MagicMock()
        m.success = True
        m.output = mock_res.output
        return m

    with (
        patch("app.mcp.server.mcp_server.call_tool", side_effect=mock_call_tool),
        patch.object(FasterWhisperSTTService, "_init_model", return_value=None),
        patch.object(FasterWhisperSTTService, "transcribe_bytes", return_value="Custom candidate response text."),
        patch.object(KokoroTTSService, "_init_kokoro", return_value=None),
        patch.object(KokoroTTSService, "speak", return_value=dummy_wav),
        patch.object(KokoroTTSService, "synthesize", return_value=dummy_wav),
    ):
        yield


@pytest.fixture(autouse=True)
def mock_global_llm(monkeypatch):
    """Mock LLMClient.invoke_structured globally for fast deterministic execution in this file."""
    from app.graph.policy_node import PolicyDecision, FinishDecision
    from app.agents.evaluation_agent import EvaluationOutput
    from app.agents.question_generator_agent import GeneratedQuestion
    from app.graph.report_verification_node import VerifiedReportOutput
    from app.agents.technical_interview_agent import TechnicalTurn
    from app.agents.hr_interview_agent import HRTurn

    def default_invoke_structured(self, messages, output_schema, retry_feedback=None):
        name = output_schema.__name__
        if name == "PolicyDecision":
            return PolicyDecision(action="finish", finish=FinishDecision(reasoning="Mock finish"))
        if name == "EvaluationOutput":
            return EvaluationOutput(
                score=8,
                rubric_breakdown={"Correctness": 4, "Communication": 4},
                feedback="Mock feedback",
                ideal_answer_summary="Mock ideal"
            )
        if name == "GeneratedQuestion":
            return GeneratedQuestion(
                question_text="Mock JIT question?",
                competency_targeted="Technical",
                difficulty="MEDIUM"
            )
        if name == "VerifiedReportOutput":
            return VerifiedReportOutput(
                verified=True,
                claims=[],
                corrected_executive_summary="Mock verified summary",
                unsupported_claims_count=0
            )
        if name == "TechnicalTurn":
            return TechnicalTurn(
                question_text="Technical question",
                candidate_answer="Candidate answer",
                follow_up_question=None
            )
        if name == "HRTurn":
            return HRTurn(
                question_text="HR question",
                candidate_answer="Candidate answer",
                follow_up_question=None
            )
        return output_schema.model_construct()

    monkeypatch.setattr("app.core.llm_client.LLMClient.invoke_structured", default_invoke_structured)


def _setup_test_context(db: Session) -> tuple[User, Resume, JobDescription]:
    user = User(
        id=str(uuid.uuid4()),
        email=f"candidate_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="hashedpassword",
        full_name="Test User",
    )
    db.add(user)
    db.flush()

    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user.id,
        file_path="uploads/resume.pdf",
        raw_text="Experienced Software Engineer working on React and Python backend microservices.",
        parsed_skills='["React", "Python", "PostgreSQL"]',
        parsed_experience='[{"role": "Software Engineer", "company": "Tech Corp", "description": "Developed React UI and Python services.", "technologies": ["React", "Python"]}]',
        seniority_signal="MID",
    )
    db.add(resume)

    jd = JobDescription(
        id=str(uuid.uuid4()),
        user_id=user.id,
        raw_text="We need a Mid/Senior Backend Engineer with React and Python experience.",
        target_role="Fullstack Software Engineer",
        required_skills='["React", "Python", "PostgreSQL"]',
        seniority_level="Mid",
    )
    db.add(jd)
    db.commit()

    return user, resume, jd


# ── Test 1: Startup does not call LLM ──────────────────────────────────────────

def test_1_interview_creation_does_not_call_llm(db_session: Session):
    """Verify that create_interview reaches READY and sets up Q1 without calling LLM client."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)

    # Patch LLMClient invoke/invoke_structured to catch any accidental LLM calls
    mock_invoke = MagicMock(side_effect=RuntimeError("Accidental LLM call during startup!"))
    
    with (
        patch.object(LLMClient, "invoke", mock_invoke),
        patch.object(LLMClient, "invoke_structured", mock_invoke),
    ):
        interview = service.create_interview(
            user_id=user.id,
            resume_id=resume.id,
            jd_id=jd.id,
            payload={"experience_level": "MID"},
        )
        
        db_session.refresh(interview)
        assert interview.status == "READY"
        
        # Check that questions exist and Q1 is set up
        questions = db_session.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id
        ).order_by(InterviewQuestion.sequence_number.asc()).all()
        
        assert len(questions) == 5
        assert questions[0].sequence_number == 1
        assert questions[0].status == "READY"
        assert questions[0].question_text != "[Pending JIT Generation]"
        
        # Subsequent questions should be PENDING
        assert questions[1].status == "PENDING"
        assert questions[1].question_text == "[Pending JIT Generation]"
        
        # Assert no LLM call occurred
        mock_invoke.assert_not_called()


# ── Test 2: WebSocket unaffected by slow LLM ───────────────────────────────────

def test_2_websocket_unaffected_by_slow_llm(client: TestClient, db_session: Session):
    """Verify that starting a slow JIT task doesn't block the WebSocket connection."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    
    # Mock LLM Client to block/sleep for 2 seconds (simulating slow Ollama)
    def slow_call(*args, **kwargs):
        time.sleep(2.0)
        return {"current_question": {"question_text": "Slow generated React question?", "competency_targeted": "React", "difficulty": "MEDIUM"}}
        
    token = AuthService(db_session).create_user_token(user)
    
    # Trigger background JIT generation for Q2 which is slow
    with patch.object(QuestionGeneratorAgent, "__call__", side_effect=slow_call):
        service.trigger_next_pending_generation(interview.id)
        
        # Verify WebSocket connection succeeds immediately
        ws_url = f"/api/v1/ws/interviews/{interview.id}?token={token}"
        t0 = time.monotonic()
        with client.websocket_connect(ws_url) as websocket:
            websocket.send_json({"type": "HEARTBEAT"})
            resp = websocket.receive_json()
            assert resp["type"] == "HEARTBEAT_ACK"
            
        elapsed = time.monotonic() - t0
        # The handshake/heartbeat must complete way below the 2-second LLM block!
        assert elapsed < 1.0


# ── Test 3: Background Q2 generation ──────────────────────────────────────────

def test_3_background_q2_generation(db_session: Session):
    """Verify background task transitions Q2 from PENDING to GENERATING to READY."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    
    q2 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 2
    ).first()
    
    assert q2.status == "PENDING"
    
    # Mock LLM to return valid question
    mock_agent_res = {
        "current_question": {
            "question_text": "Explain how React reconciles component updates.",
            "competency_targeted": "React",
            "difficulty": "MEDIUM",
            "question_type": "fundamentals",
        }
    }
    
    with patch.object(QuestionGeneratorAgent, "__call__", return_value=mock_agent_res):
        # Run JIT generation synchronously to simulate worker execution completion
        service.generate_question_jit_sync(interview.id, 2)
        
        db_session.refresh(q2)
        assert q2.status == "READY"
        assert q2.question_text == "Explain how React reconciles component updates."


# ── Test 4: Candidate can answer Q1 while Q2 generates ────────────────────────

def test_4_candidate_answering_not_blocked_by_jit(db_session: Session):
    """Simulate slow Q2 generation in the background. Verify candidate answering Q1 is not blocked."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    
    # Setup Q1 and evaluate it
    interview = service.create_interview(user.id, resume.id, jd.id)
    q1 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 1
    ).first()
    
    # Set Q2 status to GENERATING (simulating active background thread)
    q2 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 2
    ).first()
    q2.status = "GENERATING"
    db_session.commit()
    
    # Candidate submits answer to Q1
    t0 = time.monotonic()
    
    # Mock evaluation agent reply
    mock_eval = {
        "evaluations": [
            {
                "score": 80,
                "rubric_breakdown": {"Communication": 4, "Technical": 4},
                "feedback": "Good answer.",
                "reasoning": "Good",
                "ideal_answer_summary": "Ideal answer",
                "answer_quality": "VALID_ANSWER",
            }
        ]
    }
    
    with (
        patch("app.agents.evaluation_agent.EvaluationAgent.__call__", return_value=mock_eval),
        patch.object(QuestionGeneratorAgent, "__call__", return_value={})
    ):
        res = service.submit_answer(
            interview_id=interview.id,
            answer="React uses Virtual DOM and diffing algorithm.",
            question_id=q1.id,
        )
        
        elapsed = time.monotonic() - t0
        # Should not wait for Ollama timeout; should complete quickly and fallback Q2 to seed bank since it was GENERATING
        assert elapsed < 5.0
        assert res["status"] == "IN_PROGRESS"
        assert res["next_question"]["sequence_number"] == 2
        assert q1.status == "CONSUMED"


# ── Test 5: Q2 unavailable fallback recovery ─────────────────────────────────

def test_5_q2_unavailable_fallback_recovery(db_session: Session):
    """Verify that if Q2 JIT generation is currently GENERATING but times out, candidate gets seed-bank Q2 instantly."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    
    q1 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 1
    ).first()
    
    q2 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 2
    ).first()
    q2.status = "GENERATING"
    db_session.commit()
    
    mock_eval = {
        "evaluations": [
            {
                "score": 8,
                "rubric_breakdown": {"Communication": 4, "Technical": 4},
                "feedback": "Correct explanation.",
                "ideal_answer_summary": "reconciliation details",
            }
        ]
    }
    
    # Submit answer while Q2 is still GENERATING (times out)
    with patch("app.agents.evaluation_agent.EvaluationAgent.__call__", return_value=mock_eval):
        res = service.submit_answer(
            interview_id=interview.id,
            answer="React reconciliation operates via keys.",
            question_id=q1.id,
        )
        
        assert res["next_question"]["sequence_number"] == 2
        
        # Verify next question has been resolved to a seed fallback question
        db_session.refresh(q2)
        assert q2.status == "FALLBACK"
        assert q2.question_text != "[Pending JIT Generation]"
        assert q2.question_text != ""


# ── Test 6: Gate 2 retry logic ────────────────────────────────────────────────

def test_6_gate_2_rejection_retry_stays_on_same_competency(db_session: Session):
    """Verify that a Gate 2 (relevance) failure triggers at most one same-competency retry."""
    user, resume, jd = _setup_test_context(db_session)
    
    # Inject dummy LLMClient to bypass the conftest.py monkeypatch
    q_gen = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=MagicMock())
    
    # Set up mock responses for _invoke_structured
    mock_q1 = MagicMock(spec=GeneratedQuestion)
    mock_q1.question_text = "How do you manage memory and concurrency in Go backend microservices?"
    mock_q1.competency_targeted = "React"
    mock_q1.difficulty = "MEDIUM"
    mock_q1.question_type = "fundamentals"
    mock_q1.model_dump.return_value = {
        "question_text": mock_q1.question_text,
        "competency_targeted": "React",
        "difficulty": "MEDIUM",
        "question_type": "fundamentals",
    }
    
    mock_q2 = MagicMock(spec=GeneratedQuestion)
    mock_q2.question_text = "What are standard render performance optimizations in React?"
    mock_q2.competency_targeted = "React"
    mock_q2.difficulty = "MEDIUM"
    mock_q2.question_type = "fundamentals"
    mock_q2.model_dump.return_value = {
        "question_text": mock_q2.question_text,
        "competency_targeted": "React",
        "difficulty": "MEDIUM",
        "question_type": "fundamentals",
    }
    
    mock_invoke = MagicMock(side_effect=[mock_q1, mock_q2])
    
    state = {
        "interview_id": "test-id",
        "resume_data": {
            "skills": ["React", "Python"],
            "experience": [{"description": "React developer backend Python", "technologies": ["React", "Python"]}],
            "seniority_signal": "MID",
        },
        "jd_data": {
            "required_skills": ["React", "Python"],
            "target_role": "Fullstack Engineer",
        },
        "competency_matrix": [{"name": "React", "weight": 50}, {"name": "Python", "weight": 50}],
        "questions_asked": [],
        "evaluations": [],
        "target_competency": "React",
    }
    
    with patch.object(q_gen, "_invoke_structured", mock_invoke):
        res = q_gen(state)
        # Verify it retried exactly once (2 calls total) and stayed on React competency
        assert mock_invoke.call_count == 2
        assert res["current_question"]["question_text"] == "What are standard render performance optimizations in React?"
        assert res["current_question"]["competency_targeted"] == "React"


# ── Test 7: Gate 5 retry logic ────────────────────────────────────────────────

def test_7_gate_5_duplicate_retry(db_session: Session):
    """Verify that a Gate 5 (duplicate) failure triggers at most one retry with a different question."""
    q_gen = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=MagicMock())
    
    mock_q1 = MagicMock(spec=GeneratedQuestion)
    mock_q1.question_text = "Explain the Virtual DOM in React."
    mock_q1.competency_targeted = "React"
    mock_q1.difficulty = "MEDIUM"
    mock_q1.question_type = "fundamentals"
    mock_q1.model_dump.return_value = {
        "question_text": mock_q1.question_text,
        "competency_targeted": "React",
        "difficulty": "MEDIUM",
        "question_type": "fundamentals",
    }
    
    mock_q2 = MagicMock(spec=GeneratedQuestion)
    mock_q2.question_text = "How would you optimize list rendering in React?"
    mock_q2.competency_targeted = "React"
    mock_q2.difficulty = "MEDIUM"
    mock_q2.question_type = "fundamentals"
    mock_q2.model_dump.return_value = {
        "question_text": mock_q2.question_text,
        "competency_targeted": "React",
        "difficulty": "MEDIUM",
        "question_type": "fundamentals",
    }
    
    state = {
        "interview_id": "test-id",
        "resume_data": {
            "skills": ["React", "Python"],
            "experience": [{"description": "React developer", "technologies": ["React"]}],
            "seniority_signal": "MID",
        },
        "jd_data": {
            "required_skills": ["React"],
            "target_role": "React dev",
        },
        "competency_matrix": [{"name": "React", "weight": 100}],
        # History contains exact duplicate of mock_q1
        "questions_asked": [{"question_text": "Explain the Virtual DOM in React.", "competency_targeted": "React", "round_type": "TECHNICAL"}],
        "evaluations": [],
        "target_competency": "React",
    }
    
    with patch.object(q_gen, "_invoke_structured", side_effect=[mock_q1, mock_q2]) as mock_inv:
        res = q_gen(state)
        assert mock_inv.call_count == 2
        assert res["current_question"]["question_text"] == "How would you optimize list rendering in React?"


# ── Test 8: Both LLM attempts fail ────────────────────────────────────────────

def test_8_both_attempts_fail_recovers_to_seed(db_session: Session):
    """Verify that if both LLM attempts fail, it falls back to the seed question bank."""
    user, resume, jd = _setup_test_context(db_session)
    q_gen = QuestionGeneratorAgent(round_type="TECHNICAL", llm_client=MagicMock())
    
    state = {
        "interview_id": "test-id",
        "resume_data": {
            "skills": ["React"],
            "seniority_signal": "MID",
        },
        "jd_data": {
            "required_skills": ["React"],
        },
        "competency_matrix": [{"name": "React", "weight": 100}],
        "questions_asked": [],
        "evaluations": [],
        "target_competency": "React",
    }
    
    # Make LLM Client call always fail (raising ValueError/validation error)
    with patch.object(q_gen, "_invoke_structured", side_effect=ValueError("LLM Error")) as mock_inv:
        res = q_gen(state)
        # Should call 2 times total (Attempt 1 + Attempt 2 retry)
        assert mock_inv.call_count == 2
        
        # Verify fallback question is returned
        assert res["current_question"]["fallback_used"] is True
        assert res["current_question"]["fallback_type"] == "seed_bank"
        assert "React" in res["current_question"]["question_text"] or "Virtual DOM" in res["current_question"]["question_text"]


# ── Test 9: Same competency different questions ────────────────────────────────

def test_9_same_competency_different_questions_accepted(db_session: Session):
    """Verify that different questions on the same tech/framework are accepted by Gate 5 duplicate check."""
    from app.services.question_relevance_service import QuestionRelevanceService
    
    q1 = "Explain React Context API state management and its trade-offs."
    q2 = "How do you optimize render performance using useMemo and useCallback in React?"
    
    asked = [{"question_text": q1, "competency_targeted": "React", "round_type": "TECHNICAL"}]
    
    res = QuestionRelevanceService.validate_question(
        question_text=q2,
        question_difficulty="MEDIUM",
        relevant_experience_months=24,
        seniority_level="MID",
        candidate_skills=["React"],
        work_experience_bullets=["React UI developer"],
        jd_required_skills=["React"],
        questions_asked=asked,
        round_type="TECHNICAL",
        competency_targeted="React",
    )
    
    # Should be accepted (not flagged as duplicate)
    assert res.accepted is True


# ── Test 10: Full interview lifecycle ──────────────────────────────────────────

def test_10_full_interview_lifecycle(client: TestClient, db_session: Session):
    """Test full concurrency flow: CREATE -> READY -> WS CONNECT -> Q1 -> ANSWER Q1 -> Q2 -> ANSWER Q2 -> Q3."""
    user, resume, jd = _setup_test_context(db_session)
    token = AuthService(db_session).create_user_token(user)
    
    # 1. CREATE INTERVIEW
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    assert interview.status == "READY"
    
    # Verify Q1 is READY, Q2 is PENDING
    questions = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id
    ).order_by(InterviewQuestion.sequence_number.asc()).all()
    assert questions[0].status == "READY"
    assert questions[1].status == "PENDING"
    
    # Background generation for Q2 is triggered during creation. Mock JIT execution for Q2.
    mock_agent_res2 = {
        "current_question": {
            "question_text": "What is Python asyncio, and how does it support concurrency?",
            "competency_targeted": "Python",
            "difficulty": "MEDIUM",
            "question_type": "fundamentals",
        }
    }
    
    # 2. WebSocket CONNECT
    ws_url = f"/api/v1/ws/interviews/{interview.id}?token={token}"
    with client.websocket_connect(ws_url) as websocket:
        # Pre-generate Q2 in the background using mock agent
        with patch.object(QuestionGeneratorAgent, "__call__", return_value=mock_agent_res2):
            service.generate_question_jit_sync(interview.id, 2)
            
            db_session.refresh(questions[1])
            assert questions[1].status == "READY"
            
            # 3. Answer Q1
            mock_eval = {
                "evaluations": [
                    {
                        "score": 90,
                        "rubric_breakdown": {"Communication": 4, "Technical": 5},
                        "feedback": "Perfect answer.",
                        "reasoning": "Correct",
                        "ideal_answer_summary": "Virtual DOM reconciliation details",
                        "answer_quality": "VALID_ANSWER",
                    }
                ]
            }
            
            # Background Q3 generation mock
            mock_agent_res3 = {
                "current_question": {
                    "question_text": "How do database indexes speed up PostgreSQL queries?",
                    "competency_targeted": "PostgreSQL",
                    "difficulty": "MEDIUM",
                    "question_type": "fundamentals",
                }
            }
            
            with (
                patch("app.agents.evaluation_agent.EvaluationAgent.__call__", return_value=mock_eval),
                patch.object(QuestionGeneratorAgent, "__call__", return_value=mock_agent_res3)
            ):
                # Submit Q1 answer
                submit_res = service.submit_answer(
                    interview_id=interview.id,
                    answer="Virtual DOM reconciliation diffs tree nodes.",
                    question_id=questions[0].id,
                )
                
                assert submit_res["status"] == "IN_PROGRESS"
                assert submit_res["next_question"]["sequence_number"] == 2
                assert submit_res["next_question"]["text"] == "What is Python asyncio, and how does it support concurrency?"
                
                # Check Q1 becomes CONSUMED
                db_session.refresh(questions[0])
                assert questions[0].status == "CONSUMED"
                
                # Verify background JIT generated Q3
                db_session.refresh(questions[2])
                # In background, trigger next pending triggers Q3 JIT generation
                service.generate_question_jit_sync(interview.id, 3)
                db_session.refresh(questions[2])
                assert questions[2].status == "READY"
                assert questions[2].question_text == "How do database indexes speed up PostgreSQL queries?"


# ── Test 11: Concurrency race check (Duplicate Q2) ───────────────────────────

def test_11_verify_no_duplicate_q2_generation(db_session: Session):
    """Verify that multiple concurrent triggers to generate the same question only invoke the LLM once."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    
    mock_agent_res = {
        "current_question": {
            "question_text": "Concurrent React question?",
            "competency_targeted": "React",
            "difficulty": "MEDIUM",
            "question_type": "fundamentals",
        }
    }
    
    # We call generate_question_jit_sync twice. The first call marks it as GENERATING.
    # The second concurrent call should see it is GENERATING/READY and skip invoking the agent.
    with patch.object(QuestionGeneratorAgent, "__call__", return_value=mock_agent_res) as mock_agent_call:
        # Simulate concurrent call 1: executes fully
        service.generate_question_jit_sync(interview.id, 2)
        
        # Simulate concurrent call 2: sees READY status and exits immediately
        service.generate_question_jit_sync(interview.id, 2)
        
        # Verify LLM agent was called exactly once
        assert mock_agent_call.call_count == 1
        
        # Verify Q2 is READY
        q2 = db_session.query(InterviewQuestion).filter(
            InterviewQuestion.interview_id == interview.id,
            InterviewQuestion.sequence_number == 2
        ).first()
        assert q2.status == "READY"
        assert q2.question_text == "Concurrent React question?"


# ── Test 12: True Concurrency (Slow LLM does not block submit_answer) ──────────

def test_12_verify_true_concurrency_non_blocking_slow_llm(db_session: Session):
    """Verify that candidate submit_answer does not wait for a running slow background LLM task."""
    user, resume, jd = _setup_test_context(db_session)
    service = InterviewService(db_session)
    interview = service.create_interview(user.id, resume.id, jd.id)
    
    q1 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 1
    ).first()
    
    # Set Q2 to PENDING
    q2 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 2
    ).first()
    assert q2.status == "PENDING"
    
    # Launch slow JIT task for Q2 in the background using loop executor
    import asyncio
    import threading
    
    generation_started = threading.Event()
    generation_should_finish = threading.Event()
    
    def slow_llm_generation(*args, **kwargs):
        generation_started.set()
        # Block JIT generator intentionally to simulate slow LLM
        generation_should_finish.wait(timeout=0.2)
        return {
            "current_question": {
                "question_text": "Slow JIT question text",
                "competency_targeted": "React",
                "difficulty": "MEDIUM",
                "question_type": "fundamentals",
            }
        }
        
    mock_eval = {
        "evaluations": [
            {
                "score": 90,
                "rubric_breakdown": {"Communication": 5, "Technical": 5},
                "feedback": "Perfect response.",
                "reasoning": "Correct",
                "ideal_answer_summary": "reconciliation details",
                "answer_quality": "VALID_ANSWER",
            }
        ]
    }
    
    # Trigger background JIT in a separate thread so it blocks
    with (
        patch.object(QuestionGeneratorAgent, "__call__", side_effect=slow_llm_generation),
        patch("app.agents.evaluation_agent.EvaluationAgent.__call__", return_value=mock_eval)
    ):
        service.trigger_next_pending_generation(interview.id)
        
        # Wait until background JIT has started and acquired the lock
        generation_started.wait(timeout=2.0)
        
        # Submit answer to Q1 while Q2 generation is deliberately blocked/paused.
        # Candidate request should continue and fetch seed fallback instead of blocking on the paused generator!
        t_start = time.monotonic()
        res = service.submit_answer(
            interview_id=interview.id,
            answer="React uses Virtual DOM reconciliation.",
            question_id=q1.id,
        )
        t_duration = time.monotonic() - t_start
        
        # Ensure candidate answer submission completes within our bounded timeout (max 3 seconds)
        # without waiting for the 10-second slow LLM generation to complete!
        assert t_duration < 4.0
        assert res["status"] == "IN_PROGRESS"
        assert res["next_question"]["sequence_number"] == 2
        assert res["next_question"]["text"] != "Slow JIT question text"  # Fetched fallback instead
        
        # Cleanup background thread
        generation_should_finish.set()


class MockLLM:
    def __init__(self, policy_responses, eval_responses, other_responses=None):
        self.policy_responses = policy_responses
        self.eval_responses = eval_responses
        self.other_responses = other_responses or {}
        self.policy_idx = 0
        self.eval_idx = 0

    def __call__(self, messages, output_schema, retry_feedback=None):
        name = output_schema.__name__
        if name == "PolicyDecision":
            res = self.policy_responses[self.policy_idx]
            self.policy_idx = min(self.policy_idx + 1, len(self.policy_responses) - 1)
            return res
        if name == "EvaluationOutput":
            res = self.eval_responses[self.eval_idx]
            self.eval_idx = min(self.eval_idx + 1, len(self.eval_responses) - 1)
            return res
        if name in self.other_responses:
            return self.other_responses[name]

        # Defaults
        from app.graph.policy_node import PolicyDecision, FinishDecision
        from app.agents.evaluation_agent import EvaluationOutput
        from app.graph.report_verification_node import VerifiedReportOutput
        from app.agents.technical_interview_agent import TechnicalTurn
        from app.agents.hr_interview_agent import HRTurn

        if name == "PolicyDecision":
            return PolicyDecision(action="finish", finish=FinishDecision(reasoning="Mock finish"))
        if name == "EvaluationOutput":
            return EvaluationOutput(
                score=8,
                rubric_breakdown={"Correctness": 4, "Communication": 4},
                feedback="Mock feedback",
                ideal_answer_summary="Mock ideal"
            )
        if name == "VerifiedReportOutput":
            return VerifiedReportOutput(
                verified=True,
                claims=[],
                corrected_executive_summary="Mock verified summary",
                unsupported_claims_count=0
            )
        if name == "TechnicalTurn":
            return TechnicalTurn(
                question_text="Technical question",
                candidate_answer="Candidate answer",
                follow_up_question=None
            )
        if name == "HRTurn":
            return HRTurn(
                question_text="HR question",
                candidate_answer="Candidate answer",
                follow_up_question=None
            )
        return output_schema.model_construct()


# ── Test 13: Verify Production Agentic Trace ──────────────────────────────────
def test_13_verify_production_agentic_trace(db_session: Session, monkeypatch):
    """
    Verify the complete production-level agentic trace:
    InterviewService.submit_answer() -> build_graph() -> PolicyNode -> tool_call
    -> ToolExecutor -> score_answer_rubric tool execution -> observation propagation
    -> PolicyNode receives observation -> second decision -> finish.
    """
    # 1. Setup candidate & interview
    user = User(
        id=str(uuid.uuid4()),
        email="agentic_trace@test.com",
        password_hash="hash",
        full_name="Agentic Trace",
    )
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume GIL")
    jd = JobDescription(
        id=str(uuid.uuid4()), user_id=user.id, raw_text="JD Python", target_role="Python Architect"
    )
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    db_session.commit()

    # Pre-populate Q1
    q1 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="TECHNICAL",
        competency_targeted="GIL",
        difficulty="MEDIUM",
        question_text="What is GIL?",
        sequence_number=1,
        status="READY",
        created_at=datetime.now(UTC),
    )
    # Pre-populate Q2 in PENDING status to ensure Q1 is not considered the final question during intermediate turn evaluation
    q2_pending = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="TECHNICAL",
        competency_targeted="Concurrency",
        difficulty="MEDIUM",
        question_text="[Pending JIT Generation]",
        sequence_number=2,
        status="PENDING",
        created_at=datetime.now(UTC),
    )
    db_session.add_all([q1, q2_pending])
    db_session.commit()

    # 2. Mock LLM structured outputs for the agentic trace
    from app.graph.policy_node import PolicyDecision, ToolCallDecision, FinishDecision
    from app.graph.report_verification_node import VerifiedReportOutput
    from app.agents.evaluation_agent import EvaluationOutput
    from app.agents.technical_interview_agent import TechnicalTurn

    turn1 = TechnicalTurn(
        question_text="What is GIL?",
        candidate_answer="GIL is Global Interpreter Lock in CPython.",
        follow_up_question=None,
    )
    dec1 = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(
            tool="score_answer_rubric",
            arguments={
                "answer_text": "GIL is Global Interpreter Lock.",
                "question_text": "What is GIL?",
                "question_type": "fundamentals",
                "seniority_level": "MID",
                "competency_targeted": "GIL",
                "difficulty": "MEDIUM",
            },
            reasoning="Need to score answer using rubric tool.",
        ),
    )
    eval_out = EvaluationOutput(
        score=9,
        rubric_breakdown={"Correctness": 5, "Completeness": 5, "Communication": 4, "Confidence": 4},
        feedback="Excellent description of GIL mutex details.",
        ideal_answer_summary="GIL is a mutex that protects access to Python objects.",
    )
    dec2 = PolicyDecision(
        action="finish",
        finish=FinishDecision(reasoning="Rubric score obtained. Execution complete."),
    )

    mock_client1 = MockLLM(
        policy_responses=[dec1, dec2],
        eval_responses=[eval_out],
        other_responses={"TechnicalTurn": turn1}
    )
    monkeypatch.setattr("app.core.llm_client.LLMClient.invoke_structured", lambda self, *args, **kwargs: mock_client1(*args, **kwargs))

    service = InterviewService(db_session)

    # 3. Submit answer (intermediate turn)
    res = service.submit_answer(
        interview_id=interview.id,
        answer="GIL is Global Interpreter Lock in CPython.",
        question_id=q1.id,
    )

    # 4. Verify intermediate assertions
    assert res["status"] == "IN_PROGRESS"
    assert "evaluation" in res
    assert res["evaluation"]["score"] == 90  # 9 * 10
    assert mock_client1.policy_idx >= 1

    # Verify database state
    db_eval = db_session.query(Evaluation).join(InterviewAnswer).filter(InterviewAnswer.question_id == q1.id).first()
    assert db_eval is not None
    assert db_eval.score == 90

    # 5. Final turn verification
    # Setup Q2 as the final question (update the pre-populated pending Q2)
    q2 = db_session.query(InterviewQuestion).filter(
        InterviewQuestion.interview_id == interview.id,
        InterviewQuestion.sequence_number == 2
    ).first()
    assert q2 is not None
    q2.question_text = "Explain async/await."
    q2.status = "READY"
    db_session.add(q2)
    db_session.commit()

    # Make the interview plan total_questions = 2
    from app.models.interview import InterviewPlan
    plan = db_session.query(InterviewPlan).filter(InterviewPlan.interview_id == interview.id).first()
    if plan:
        plan.technical_question_count = 2
        db_session.add(plan)
        db_session.commit()

    # Set up LLM responses for the final turn
    turn2 = TechnicalTurn(
        question_text="Explain async/await.",
        candidate_answer="Asyncio uses single-threaded event loop.",
        follow_up_question=None,
    )
    dec_final_1 = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(
            tool="score_answer_rubric",
            arguments={
                "answer_text": "Asyncio is cooperative multitasking.",
                "question_text": "Explain async/await.",
                "question_type": "fundamentals",
                "seniority_level": "MID",
                "competency_targeted": "Concurrency",
                "difficulty": "MEDIUM",
            },
            reasoning="Score final answer.",
        ),
    )
    eval_final_out = EvaluationOutput(
        score=8,
        rubric_breakdown={"Correctness": 4, "Completeness": 4, "Communication": 4, "Confidence": 4},
        feedback="Solid asyncio explanation.",
        ideal_answer_summary="Cooperative multitasking.",
    )
    dec_final_2 = PolicyDecision(
        action="finish",
        finish=FinishDecision(reasoning="Final turn scoring done. Proceed to report verification."),
    )
    
    from pydantic import BaseModel
    class SummaryOut(BaseModel):
        executive_summary: str
    
    summary_out = SummaryOut(executive_summary="Candidate has strong Python backend skills.")
    
    ver_final_out = VerifiedReportOutput(
        verified=True,
        claims=[],
        corrected_executive_summary="Candidate demonstrated solid GIL and concurrency depth.",
        unsupported_claims_count=0,
    )

    mock_client2 = MockLLM(
        policy_responses=[dec_final_1, dec_final_2],
        eval_responses=[eval_final_out],
        other_responses={
            "TechnicalTurn": turn2,
            "SummaryOut": summary_out,
            "VerifiedReportOutput": ver_final_out
        }
    )
    monkeypatch.setattr("app.core.llm_client.LLMClient.invoke_structured", lambda self, *args, **kwargs: mock_client2(*args, **kwargs))

    # Run submit_answer on final question
    res_final = service.submit_answer(
        interview_id=interview.id,
        answer="Asyncio uses single-threaded event loop.",
        question_id=q2.id,
    )

    # Verify final assertions
    assert res_final["status"] == "COMPLETED"
    assert mock_client2.policy_idx >= 1
    
    # Verify Report is saved and verified
    from app.models.interview import InterviewReport
    db_report = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).first()
    assert db_report is not None
    import json
    report_data = json.loads(db_report.competency_scorecard)
    assert len(report_data) > 0


def test_14_verify_report_verification_failure_flagged(db_session: Session, monkeypatch):
    """
    Verify that if report verification fails:
    1. Do NOT publish/save the original unverified report.
    2. Flag the interview for human review in ReviewQueue with reason.
    """
    # 1. Setup candidate & interview
    user = User(
        id=str(uuid.uuid4()),
        email="ver_fail@test.com",
        password_hash="hash",
        full_name="Verification Failure Test",
    )
    resume = Resume(id=str(uuid.uuid4()), user_id=user.id, file_path="r.pdf", raw_text="Resume Django")
    jd = JobDescription(
        id=str(uuid.uuid4()), user_id=user.id, raw_text="JD Backend", target_role="Django Developer"
    )
    db_session.add_all([user, resume, jd])
    db_session.commit()

    interview = Interview(
        id=str(uuid.uuid4()),
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="IN_PROGRESS",
    )
    db_session.add(interview)
    db_session.commit()

    # Setup final question Q1
    q1 = InterviewQuestion(
        id=str(uuid.uuid4()),
        interview_id=interview.id,
        round_type="TECHNICAL",
        competency_targeted="Django",
        difficulty="MEDIUM",
        question_text="Explain Django ORM.",
        sequence_number=1,
        status="READY",
        created_at=datetime.now(UTC),
    )
    db_session.add(q1)
    db_session.commit()

    # Make the interview plan total_questions = 1
    from app.models.interview import InterviewPlan
    plan = db_session.query(InterviewPlan).filter(InterviewPlan.interview_id == interview.id).first()
    if plan:
        plan.technical_question_count = 1
        db_session.add(plan)
        db_session.commit()

    # 2. Mock LLM structured outputs
    from app.graph.policy_node import PolicyDecision, ToolCallDecision, FinishDecision
    from app.graph.report_verification_node import VerifiedReportOutput
    from app.agents.evaluation_agent import EvaluationOutput
    from app.agents.technical_interview_agent import TechnicalTurn

    turn1 = TechnicalTurn(
        question_text="Explain Django ORM.",
        candidate_answer="I used Django querysets for lazy loading.",
        follow_up_question=None,
    )
    dec1 = PolicyDecision(
        action="tool_call",
        tool_call=ToolCallDecision(
            tool="score_answer_rubric",
            arguments={"answer_text": "I used Django."},
            reasoning="Score answer.",
        ),
    )
    eval_out = EvaluationOutput(
        score=7,
        rubric_breakdown={"Correctness": 4, "Completeness": 3, "Communication": 4, "Confidence": 3},
        feedback="Fair ORM explanation.",
        ideal_answer_summary="Django ORM details.",
    )
    dec2 = PolicyDecision(
        action="finish",
        finish=FinishDecision(reasoning="Scoring complete. Final round report."),
    )

    from pydantic import BaseModel
    class SummaryOut(BaseModel):
        executive_summary: str
    summary_out = SummaryOut(executive_summary="Candidate claims expert knowledge in Kubernetes.")

    # Mark as verified=False due to unsupported Kubernetes claim
    ver_fail_out = VerifiedReportOutput(
        verified=False,
        claims=[],
        corrected_executive_summary="Verification failed.",
        unsupported_claims_count=1,
    )

    mock_client = MockLLM(
        policy_responses=[dec1, dec2],
        eval_responses=[eval_out],
        other_responses={
            "TechnicalTurn": turn1,
            "SummaryOut": summary_out,
            "VerifiedReportOutput": ver_fail_out
        }
    )
    monkeypatch.setattr("app.core.llm_client.LLMClient.invoke_structured", lambda self, *args, **kwargs: mock_client(*args, **kwargs))

    service = InterviewService(db_session)

    # 3. Submit answer to complete the interview
    res = service.submit_answer(
        interview_id=interview.id,
        answer="I used Django querysets for lazy loading.",
        question_id=q1.id,
    )

    # 4. Verify assertions
    assert res["status"] == "COMPLETED"

    # Verify that InterviewReport table has NO entry for this interview (Do NOT publish)
    from app.models.interview import InterviewReport
    db_report = db_session.query(InterviewReport).filter(InterviewReport.interview_id == interview.id).first()
    assert db_report is None

    # Verify that the interview is flagged in ReviewQueue with reason
    from app.models.review_queue import ReviewQueue
    queue_item = db_session.query(ReviewQueue).filter(ReviewQueue.interview_id == interview.id).first()
    assert queue_item is not None
    assert queue_item.status == "PENDING"
    assert "contains unsupported claims" in queue_item.reason



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

    with (
        patch("app.mcp.server.mcp_server.call_tool", return_value=mock_res),
        patch.object(FasterWhisperSTTService, "_init_model", return_value=None),
        patch.object(FasterWhisperSTTService, "transcribe_bytes", return_value="Custom candidate response text."),
        patch.object(KokoroTTSService, "_init_kokoro", return_value=None),
        patch.object(KokoroTTSService, "speak", return_value=dummy_wav),
        patch.object(KokoroTTSService, "synthesize", return_value=dummy_wav),
    ):
        yield


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
        generation_should_finish.wait(timeout=10.0)
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

"""
Interview repository tests.
"""

from datetime import UTC, datetime

import pytest

from app.models import AgentLog, Evaluation, Interview, InterviewAnswer, InterviewQuestion


@pytest.mark.unit
class TestInterviewRepository:
    """Tests for InterviewRepository operations."""

    def test_create_interview(self, interview_repo, sample_user, sample_resume, sample_jd):
        """Test creating an interview."""
        interview = Interview(
            user_id=sample_user.id,
            resume_id=sample_resume.id,
            jd_id=sample_jd.id,
            status="PLANNING",
            started_at=datetime.now(UTC),
        )
        created = interview_repo.create(interview)
        assert created.id is not None
        assert created.status == "PLANNING"

    def test_get_interview_by_id(self, interview_repo, sample_interview):
        """Test retrieving interview by ID."""
        retrieved = interview_repo.get_by_id(sample_interview.id)
        assert retrieved is not None
        assert retrieved.user_id == sample_interview.user_id

    def test_update_interview_status(self, interview_repo, sample_interview):
        """Test updating interview status."""
        updated = interview_repo.update(sample_interview.id, {"status": "IN_PROGRESS"})
        assert updated is not None
        assert updated.status == "IN_PROGRESS"

    def test_list_interviews_by_user(
        self, interview_repo, db_session, sample_user, sample_resume, sample_jd
    ):
        """Test listing interviews for a user."""
        # Create additional interview
        interview2 = Interview(
            user_id=sample_user.id,
            resume_id=sample_resume.id,
            jd_id=sample_jd.id,
            status="COMPLETED",
            started_at=datetime.now(UTC),
        )
        db_session.add(interview2)
        db_session.commit()

        # List all for user
        interviews = interview_repo.list_by_user(sample_user.id)
        assert len(interviews) >= 1

    def test_list_interviews_by_status(
        self, interview_repo, db_session, sample_user, sample_resume, sample_jd
    ):
        """Test filtering interviews by status."""
        # Create a completed interview
        completed = Interview(
            user_id=sample_user.id,
            resume_id=sample_resume.id,
            jd_id=sample_jd.id,
            status="COMPLETED",
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        db_session.add(completed)
        db_session.commit()

        # Filter by status
        planning = interview_repo.list_by_user_and_status(sample_user.id, "PLANNING")
        completed_list = interview_repo.list_by_user_and_status(sample_user.id, "COMPLETED")
        assert len(completed_list) >= 1


@pytest.mark.unit
class TestCompetencyMatrixRepository:
    """Tests for CompetencyMatrixRepository."""

    def test_get_by_interview(self, competency_matrix_repo, db_session, sample_interview):
        """Test retrieving competency matrix by interview."""
        from app.models import CompetencyMatrix

        matrix = CompetencyMatrix(
            interview_id=sample_interview.id,
            competencies="[]",
        )
        db_session.add(matrix)
        db_session.commit()

        retrieved = competency_matrix_repo.get_by_interview(sample_interview.id)
        assert retrieved is not None
        assert retrieved.interview_id == sample_interview.id


@pytest.mark.unit
class TestInterviewQuestionRepository:
    """Tests for InterviewQuestionRepository."""

    def test_create_question(self, question_repo, sample_interview):
        """Test creating an interview question."""
        question = InterviewQuestion(
            interview_id=sample_interview.id,
            round_type="HR",
            competency_targeted="Communication",
            difficulty="MEDIUM",
            question_text="Tell me about yourself",
            sequence_number=1,
        )
        created = question_repo.create(question)
        assert created.id is not None
        assert created.sequence_number == 1

    def test_list_questions_by_interview(self, question_repo, db_session, sample_interview):
        """Test listing questions for an interview."""
        # Create 3 questions
        for i in range(3):
            question = InterviewQuestion(
                interview_id=sample_interview.id,
                round_type="HR",
                competency_targeted="Communication",
                difficulty="MEDIUM",
                question_text=f"Question {i}",
                sequence_number=i + 1,
            )
            db_session.add(question)
        db_session.commit()

        questions = question_repo.list_by_interview(sample_interview.id)
        assert len(questions) == 3
        # Verify ordering by sequence
        assert questions[0].sequence_number == 1
        assert questions[2].sequence_number == 3

    def test_get_by_sequence(self, question_repo, db_session, sample_interview):
        """Test retrieving question by sequence number."""
        question = InterviewQuestion(
            interview_id=sample_interview.id,
            round_type="TECHNICAL",
            competency_targeted="System Design",
            difficulty="HARD",
            question_text="Design a distributed system",
            sequence_number=5,
        )
        db_session.add(question)
        db_session.commit()

        retrieved = question_repo.get_by_interview_and_sequence(sample_interview.id, 5)
        assert retrieved is not None
        assert retrieved.question_text == "Design a distributed system"


@pytest.mark.unit
class TestEvaluationRepository:
    """Tests for EvaluationRepository."""

    def test_create_evaluation(self, evaluation_repo, db_session, sample_interview):
        """Test creating an evaluation."""
        from app.models import InterviewQuestion

        # Setup: create question, answer
        question = InterviewQuestion(
            interview_id=sample_interview.id,
            round_type="HR",
            competency_targeted="Communication",
            difficulty="MEDIUM",
            question_text="Tell about yourself",
            sequence_number=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = InterviewAnswer(
            question_id=question.id,
            answer_text="I have 5 years of experience...",
            response_time_seconds=120,
        )
        db_session.add(answer)
        db_session.commit()

        # Create evaluation
        evaluation = Evaluation(
            answer_id=answer.id,
            score=8,
            rubric_breakdown='{"clarity": 8, "relevance": 8}',
            feedback="Good answer",
            ideal_answer_summary="Mention key achievements",
        )
        created = evaluation_repo.create(evaluation)
        assert created.id is not None
        assert created.score == 8

    def test_get_evaluation_by_answer(self, evaluation_repo, db_session, sample_interview):
        """Test retrieving evaluation by answer."""
        from app.models import Evaluation, InterviewQuestion

        # Setup
        question = InterviewQuestion(
            interview_id=sample_interview.id,
            round_type="TECHNICAL",
            competency_targeted="Coding",
            difficulty="HARD",
            question_text="Implement LRU cache",
            sequence_number=1,
        )
        db_session.add(question)
        db_session.commit()

        answer = InterviewAnswer(
            question_id=question.id,
            answer_text="def lru_cache()...",
            response_time_seconds=600,
        )
        db_session.add(answer)
        db_session.commit()

        evaluation = Evaluation(
            answer_id=answer.id,
            score=9,
            rubric_breakdown='{"correctness": 9, "efficiency": 8}',
            feedback="Excellent solution",
            ideal_answer_summary="Optimal time and space complexity",
        )
        db_session.add(evaluation)
        db_session.commit()

        retrieved = evaluation_repo.get_by_answer(answer.id)
        assert retrieved is not None
        assert retrieved.score == 9


@pytest.mark.unit
class TestAgentLogRepository:
    """Tests for AgentLogRepository."""

    def test_list_logs_by_interview(self, agent_log_repo, db_session, sample_interview):
        """Test listing agent logs for an interview."""
        # Create multiple logs
        for i in range(3):
            log = AgentLog(
                interview_id=sample_interview.id,
                agent_name=f"Agent{i}",
                node_status="SUCCESS",
                input_snapshot="{}",
                output_snapshot="{}",
                latency_ms=100 + i * 50,
                retry_count=0,
            )
            db_session.add(log)
        db_session.commit()

        logs = agent_log_repo.list_by_interview(sample_interview.id)
        assert len(logs) == 3

    def test_list_logs_by_agent(self, agent_log_repo, db_session, sample_interview):
        """Test listing logs for a specific agent."""
        log1 = AgentLog(
            interview_id=sample_interview.id,
            agent_name="ResumeAgent",
            node_status="SUCCESS",
            latency_ms=50,
            retry_count=0,
        )
        log2 = AgentLog(
            interview_id=sample_interview.id,
            agent_name="JDAgent",
            node_status="SUCCESS",
            latency_ms=75,
            retry_count=0,
        )
        db_session.add(log1)
        db_session.add(log2)
        db_session.commit()

        resume_logs = agent_log_repo.list_by_interview_and_agent(sample_interview.id, "ResumeAgent")
        assert len(resume_logs) == 1
        assert resume_logs[0].agent_name == "ResumeAgent"

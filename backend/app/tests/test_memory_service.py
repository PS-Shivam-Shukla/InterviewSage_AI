"""
Unit and Integration Tests for MemoryService, MemoryRepository, & MemorySummarizer.
"""

from sqlalchemy.orm import Session

from app.memory.schemas import CandidateMemoryCreate
from app.memory.service import MemoryService
from app.models import Interview, User


def test_memory_service_profile_creation_and_update(db_session: Session, sample_user: User):
    """Verify CandidateProfile auto-creation and updates."""
    service = MemoryService(db_session)
    profile = service.get_candidate_memory(sample_user.id)

    assert profile.candidate_id == sample_user.id
    assert profile.experience_years == 0
    assert profile.current_level == "MID"

    # Update profile
    updated = service.manager.repo.update_profile(
        candidate_id=sample_user.id,
        experience_years=5,
        skills=["Python", "FastAPI", "PostgreSQL"],
        level="SENIOR",
        strengths=["Backend Architecture"],
        weaknesses=["Kubernetes Operator Tuning"],
        summary="Senior Backend Architect candidate.",
    )

    assert updated.experience_years == 5
    assert updated.current_level == "SENIOR"
    assert "Python" in updated.get_skills()
    assert "Backend Architecture" in updated.get_strengths()


def test_memory_service_save_and_retrieve_memories(
    db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify saving and listing candidate memories."""
    service = MemoryService(db_session)
    payload = CandidateMemoryCreate(
        interview_id=sample_interview.id,
        memory_type="EPISODIC",
        summary="Candidate demonstrated strong knowledge of FastAPI dependency injection.",
        key_topics=["FastAPI", "Dependency Injection", "Python"],
    )

    mem = service.save_memory(sample_user.id, payload)
    assert mem.id is not None
    assert mem.candidate_id == sample_user.id
    assert mem.interview_id == sample_interview.id
    assert "FastAPI" in mem.key_topics

    timeline = service.get_timeline(sample_user.id)
    assert len(timeline) >= 1
    assert timeline[0].interview_id == sample_interview.id


def test_memory_service_compress_memories(
    db_session: Session, sample_user: User, sample_interview: Interview
):
    """Verify MemorySummarizer compresses candidate memories into a MemorySummary."""
    service = MemoryService(db_session)

    # Save multiple memories
    for i in range(3):
        service.save_memory(
            sample_user.id,
            CandidateMemoryCreate(
                interview_id=sample_interview.id,
                memory_type="EPISODIC",
                summary=f"Interview {i+1}: Evaluated distributed systems & concurrency.",
                key_topics=["Distributed Systems", "Concurrency"],
            ),
        )

    summary = service.compress_memories(sample_user.id)
    assert summary.candidate_id == sample_user.id
    assert summary.interview_count_covered >= 3
    assert "Distributed Systems" in summary.compressed_summary

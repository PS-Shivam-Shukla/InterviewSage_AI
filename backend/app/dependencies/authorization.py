"""
Centralized Resource Ownership Authorization Layer.
Enforces multi-tenant isolation and prevents horizontal privilege escalation (Audit C-6).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Interview, JobDescription, Resume
from app.repositories import (
    InterviewRepository,
    JobDescriptionRepository,
    ResumeRepository,
)


def verify_ownership(owner_id: str, current_user_id: str, resource_name: str = "resource") -> None:
    """
    Verify that current_user_id matches the owner_id of the resource.
    Raises HTTP 403 Forbidden if ownership validation fails.
    """
    if owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You do not have permission to access this {resource_name}.",
        )


def check_interview_ownership(interview_id: str, user_id: str, db: Session) -> Interview:
    """
    Fetch interview and verify ownership by user_id.
    Returns Interview object if valid.
    Raises HTTP 404 if not found, HTTP 403 if user does not own it.
    """
    repo = InterviewRepository(db)
    interview = repo.get_by_id(interview_id)
    if not interview:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found")
    verify_ownership(interview.user_id, user_id, "interview")
    return interview


def check_resume_ownership(resume_id: str, user_id: str, db: Session) -> Resume:
    """
    Fetch resume and verify ownership by user_id.
    Returns Resume object if valid.
    Raises HTTP 404 if not found, HTTP 403 if user does not own it.
    """
    repo = ResumeRepository(db)
    resume = repo.get_by_id(resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    verify_ownership(resume.user_id, user_id, "resume")
    return resume


def check_job_description_ownership(jd_id: str, user_id: str, db: Session) -> JobDescription:
    """
    Fetch job description and verify ownership by user_id.
    Returns JobDescription object if valid.
    Raises HTTP 404 if not found, HTTP 403 if user does not own it.
    """
    repo = JobDescriptionRepository(db)
    jd = repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    verify_ownership(jd.user_id, user_id, "job description")
    return jd

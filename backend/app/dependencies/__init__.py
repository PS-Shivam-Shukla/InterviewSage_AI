"""
FastAPI dependency providers.
"""

from app.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
)
from app.dependencies.authorization import (
    check_interview_ownership,
    check_job_description_ownership,
    check_resume_ownership,
    verify_ownership,
)

__all__ = [
    "check_interview_ownership",
    "check_job_description_ownership",
    "check_resume_ownership",
    "get_current_user",
    "get_current_user_optional",
    "verify_ownership",
]

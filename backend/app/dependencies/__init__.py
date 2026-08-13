"""
FastAPI dependency providers.
"""

from app.dependencies.auth import (
    get_current_user,
    get_current_user_optional,
)
from app.dependencies.authorization import (
    verify_ownership,
    check_interview_ownership,
    check_resume_ownership,
    check_job_description_ownership,
)

__all__ = [
    "get_current_user",
    "get_current_user_optional",
    "verify_ownership",
    "check_interview_ownership",
    "check_resume_ownership",
    "check_job_description_ownership",
]

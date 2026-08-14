"""User management service skeleton."""

from sqlalchemy.orm import Session

from app.repositories import (
    InterviewRepository,
    JobDescriptionRepository,
    ResumeRepository,
    UserRepository,
)


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.resume_repo = ResumeRepository(db)
        self.jd_repo = JobDescriptionRepository(db)
        self.interview_repo = InterviewRepository(db)

    def update_user(self, user_id: str, full_name: str) -> dict:
        user = self.user_repo.update(user_id, {"full_name": full_name})
        if not user:
            return {"error": "User not found"}
        return {"user_id": user.id, "full_name": user.full_name}

    def export_user_data(self, user_id: str) -> dict:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return {"error": "User not found"}
        resumes = self.resume_repo.list_by_user(user_id)
        job_descriptions = self.jd_repo.list_by_user(user_id)
        interviews = self.interview_repo.list_by_user(user_id)
        return {
            "user_id": user_id,
            "email": user.email,
            "full_name": user.full_name,
            "resumes": ["resume_id:" + resume.id for resume in resumes],
            "job_descriptions": ["jd_id:" + jd.id for jd in job_descriptions],
            "interviews": ["interview_id:" + interview.id for interview in interviews],
        }

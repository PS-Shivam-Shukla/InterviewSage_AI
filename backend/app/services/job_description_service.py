"""Job description service implementation."""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import JobDescription, Resume
from app.repositories import JobDescriptionRepository, ResumeRepository
from app.agents.jd_agent import JDAgent
from app.mcp.tools.compute_ats_score import compute_ats_score

logger = logging.getLogger(__name__)


class JobDescriptionService:
    def __init__(self, db: Session):
        self.db = db
        self.jd_repo = JobDescriptionRepository(db)
        self.resume_repo = ResumeRepository(db)

    def create_job_description(self, jd_data: dict) -> dict:
        """Create JobDescription record, execute JDAgent for structured skill/seniority analysis, and persist."""
        t_start = time.monotonic()
        raw_text = (jd_data.get("jd_text") or "").replace("\x00", "")
        target_role = (jd_data.get("target_role") or "").replace("\x00", "")
        company_name = (jd_data.get("company_name") or "").replace("\x00", "") if jd_data.get("company_name") else None
        industry = (jd_data.get("industry") or "").replace("\x00", "") if jd_data.get("industry") else None
        user_id = jd_data["user_id"]

        logger.info(f"INFO JobDescription creation started for role '{target_role}' by user {user_id}")

        # 1. Execute JDAgent LLM analysis if text is present
        required_skills = []
        seniority_level = "MID"
        jd_analysis_dict = {}

        jd_status = "PROCESSING"
        if raw_text:
            try:
                agent = JDAgent()
                state = {"jd_raw_text": raw_text, "_db_session": None}
                logger.info("INFO JDAgent LLM request sent")
                agent_output = agent(state)
                jd_analysis_dict = agent_output.get("jd_data", {})
                required_skills = jd_analysis_dict.get("required_skills", [])
                seniority_level = jd_analysis_dict.get("seniority_level", "MID")
                if not target_role and jd_analysis_dict.get("target_role"):
                    target_role = jd_analysis_dict.get("target_role")
                if not industry and jd_analysis_dict.get("industry") != "NOT_SPECIFIED":
                    industry = jd_analysis_dict.get("industry")
                jd_status = "COMPLETED"
                logger.info(f"INFO JDAgent analysis complete: {len(required_skills)} skills extracted, seniority={seniority_level}")
            except Exception as exc:
                jd_status = "FAILED"
                logger.warning(f"JDAgent LLM analysis fallback due to error: {exc}")

        jd = JobDescription(
            user_id=user_id,
            raw_text=raw_text[:8000],
            target_role=target_role or "Software Engineer",
            company_name=company_name,
            industry=industry,
            required_skills=json.dumps(required_skills),
            seniority_level=seniority_level,
            status=jd_status,
        )
        created = self.jd_repo.create(jd)
        elapsed_ms = int((time.monotonic() - t_start) * 1000)
        logger.info(f"INFO JobDescription persisted: id={created.id} in {elapsed_ms}ms")

        return self._format_jd(created, extra_analysis=jd_analysis_dict)

    def get_job_description(self, jd_id: str) -> dict | None:
        jd = self.jd_repo.get_by_id(jd_id)
        if not jd:
            return None
        return self._format_jd(jd)

    def list_job_descriptions(self, user_id: str) -> List[dict]:
        jds = self.jd_repo.list_by_user(user_id)
        return [self._format_jd(jd) for jd in jds]

    def match_resume_with_jd(self, jd_id: str, resume_id: str) -> dict:
        """Compute ATS keyword/skill overlap score between a resume and job description."""
        jd = self.jd_repo.get_by_id(jd_id)
        if not jd:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

        resume = self.resume_repo.get_by_id(resume_id)
        if not resume:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

        try:
            resume_skills = json.loads(resume.parsed_skills or "[]")
        except Exception:
            resume_skills = []

        try:
            jd_required_skills = json.loads(jd.required_skills or "[]")
        except Exception:
            jd_required_skills = []

        match_metrics = compute_ats_score(
            resume_skills=resume_skills,
            jd_required_skills=jd_required_skills,
            resume_text=resume.raw_text or "",
            jd_text=jd.raw_text or "",
        )

        # Include detailed breakdown
        return {
            "jd_id": jd.id,
            "resume_id": resume.id,
            "target_role": jd.target_role,
            "company_name": jd.company_name,
            "candidate_seniority": resume.seniority_signal or "MID",
            "required_seniority": jd.seniority_level or "MID",
            "ats_score": match_metrics.get("overlap_score", 0),
            "matched_skills": match_metrics.get("matched_keywords", []),
            "missing_skills": match_metrics.get("missing_keywords", []),
            "resume_skill_count": match_metrics.get("resume_skill_count", len(resume_skills)),
            "jd_skill_count": match_metrics.get("jd_skill_count", len(jd_required_skills)),
        }

    def _format_jd(self, jd: JobDescription, extra_analysis: Optional[dict] = None) -> dict:
        try:
            skills = json.loads(jd.required_skills or "[]")
        except Exception:
            skills = []

        formatted = {
            "id": jd.id,
            "user_id": jd.user_id,
            "raw_text": jd.raw_text,
            "target_role": jd.target_role,
            "company_name": jd.company_name,
            "industry": jd.industry,
            "required_skills": skills,
            "seniority_level": jd.seniority_level,
            "status": getattr(jd, "status", "COMPLETED") or "COMPLETED",
            "created_at": jd.created_at,
        }
        if extra_analysis:
            formatted["analysis"] = extra_analysis
        return formatted

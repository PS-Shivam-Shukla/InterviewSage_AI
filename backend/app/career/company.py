"""
Company Interview Profiles Engine.
Stores and retrieves company-specific interview weightings (Amazon, Google, Microsoft, Meta, Netflix).
"""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.career.schemas import CompanyProfileResponse
from app.models.career import CompanyProfile


class CompanyProfileEngine:
    """Manages company interview weightings and principles."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self._seed_default_companies()

    def _seed_default_companies(self) -> None:
        defaults = [
            (
                "Amazon",
                "Amazon leadership principles & system scaling emphasis",
                0.35,
                0.25,
                0.40,
                ["Customer Obsession", "Ownership", "Dive Deep", "Deliver Results"],
            ),
            (
                "Google",
                "Google data structures, algorithms & system architecture",
                0.50,
                0.30,
                0.20,
                ["Googliness", "Algorithm Complexity", "System Design"],
            ),
            (
                "Microsoft",
                "Microsoft software engineering design & problem solving",
                0.30,
                0.40,
                0.30,
                ["Growth Mindset", "Collaborative Design", "Quality"],
            ),
            (
                "Meta",
                "Meta fast-paced coding, system design & product orientation",
                0.45,
                0.35,
                0.20,
                ["Move Fast", "Focus on Impact", "Build Awesome Things"],
            ),
        ]
        for name, desc, c_w, s_w, b_w, princ in defaults:
            existing = (
                self.db.query(CompanyProfile).filter(CompanyProfile.company_name == name).first()
            )
            if not existing:
                cp = CompanyProfile(
                    company_name=name,
                    description=desc,
                    coding_weight=c_w,
                    system_design_weight=s_w,
                    behavioral_weight=b_w,
                    key_principles=json.dumps(princ),
                )
                self.db.add(cp)
        self.db.commit()

    def get_company_profile(self, company_name: str) -> CompanyProfileResponse:
        comp = (
            self.db.query(CompanyProfile)
            .filter(CompanyProfile.company_name.ilike(company_name))
            .first()
        )
        if not comp:
            comp = (
                self.db.query(CompanyProfile)
                .filter(CompanyProfile.company_name == "Amazon")
                .first()
            )

        principles = (
            json.loads(comp.key_principles)
            if comp and comp.key_principles
            else ["Leadership", "Coding"]
        )
        return CompanyProfileResponse(
            company_name=comp.company_name if comp else company_name,
            description=comp.description if comp else "General Enterprise Tech",
            coding_weight=comp.coding_weight if comp else 0.35,
            system_design_weight=comp.system_design_weight if comp else 0.35,
            behavioral_weight=comp.behavioral_weight if comp else 0.30,
            key_principles=principles,
        )

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview import Interview
    from app.models.user import User


class JobDescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_descriptions"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # JSON stored as TEXT
    required_skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    seniority_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="NOT_SPECIFIED"
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROCESSING")

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="job_descriptions")
    interviews: Mapped[list[Interview]] = relationship(
        "Interview", back_populates="job_description"
    )

    def __repr__(self) -> str:
        return f"<JobDescription id={self.id!r} target_role={self.target_role!r}>"

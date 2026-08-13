from __future__ import annotations

from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.interview import Interview


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # JSON stored as TEXT; validated by Pydantic on read/write
    parsed_skills: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    parsed_experience: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    seniority_signal: Mapped[str] = mapped_column(String(50), nullable=False, default="UNKNOWN")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PROCESSING")
    seniority_score: Mapped[int] = mapped_column(nullable=False, default=0)
    total_experience_months: Mapped[int] = mapped_column(nullable=False, default=0)
    relevant_experience_months: Mapped[int] = mapped_column(nullable=False, default=0)
    seniority_breakdown: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="resumes")  # noqa: F821
    interviews: Mapped[list["Interview"]] = relationship(  # noqa: F821
        "Interview", back_populates="resume"
    )

    def __repr__(self) -> str:
        return f"<Resume id={self.id!r} user_id={self.user_id!r}>"

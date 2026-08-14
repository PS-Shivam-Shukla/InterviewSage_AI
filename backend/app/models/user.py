from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.interview import Interview
    from app.models.job_description import JobDescription
    from app.models.resume import Resume


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    resumes: Mapped[list[Resume]] = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan"
    )
    job_descriptions: Mapped[list[JobDescription]] = relationship(
        "JobDescription", back_populates="user", cascade="all, delete-orphan"
    )
    interviews: Mapped[list[Interview]] = relationship(
        "Interview", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id!r} email={self.email!r}>"

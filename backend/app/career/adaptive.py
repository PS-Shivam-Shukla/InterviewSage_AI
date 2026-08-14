"""
Adaptive Interview Difficulty Engine.
Dynamically adjusts question difficulty on a 1.0 - 10.0 scale based on performance,
response latency, consecutive streaks, and candidate background.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.career import AdaptiveSession, DifficultyHistory


class AdaptiveDifficultyEngine:
    """Computes dynamic question difficulty adjustments during live interviews."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def start_session(
        self, interview_id: str, candidate_id: str, initial_difficulty: float = 5.0
    ) -> AdaptiveSession:
        session = AdaptiveSession(
            interview_id=interview_id,
            candidate_id=candidate_id,
            current_difficulty=initial_difficulty,
            target_difficulty=initial_difficulty,
            consecutive_correct=0,
            consecutive_incorrect=0,
            status="ACTIVE",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def process_answer_and_adjust(
        self, session_id: str, performance_score: float, response_latency_seconds: float = 0.0
    ) -> dict[str, Any]:
        session = self.db.query(AdaptiveSession).filter(AdaptiveSession.id == session_id).first()
        if not session:
            raise ValueError(f"Adaptive session {session_id} not found.")

        prev_diff = session.current_difficulty
        question_count = len(session.history) + 1

        if performance_score >= 80.0:
            session.consecutive_correct += 1
            session.consecutive_incorrect = 0
            delta = 0.5 + (0.3 if session.consecutive_correct >= 2 else 0.0)
            reason = "High performance score (>80%). Escalating question complexity."
        elif performance_score < 60.0:
            session.consecutive_incorrect += 1
            session.consecutive_correct = 0
            delta = -0.6 - (0.3 if session.consecutive_incorrect >= 2 else 0.0)
            reason = "Low performance score (<60%). Decreasing question complexity."
        else:
            session.consecutive_correct = 0
            session.consecutive_incorrect = 0
            delta = 0.1
            reason = "Moderate performance. Maintaining difficulty level."

        # Factor latency
        if response_latency_seconds > 45.0 and delta > 0:
            delta -= 0.2
            reason += " (Latency penalty applied)"

        new_diff = min(10.0, max(1.0, round(prev_diff + delta, 1)))
        session.current_difficulty = new_diff
        session.target_difficulty = new_diff

        hist = DifficultyHistory(
            session_id=session_id,
            question_number=question_count,
            difficulty_assigned=prev_diff,
            performance_score=performance_score,
            response_latency_seconds=response_latency_seconds,
            adjustment_reason=reason,
        )
        self.db.add(hist)
        self.db.commit()
        self.db.refresh(session)

        suggested_focus = (
            "Advanced System Architecture & Optimization"
            if new_diff >= 7.5
            else (
                "Core Algorithmic Implementation"
                if new_diff >= 5.0
                else "Fundamental Data Structures"
            )
        )

        return {
            "session_id": session_id,
            "previous_difficulty": prev_diff,
            "new_difficulty": new_diff,
            "adjustment_reason": reason,
            "suggested_focus": suggested_focus,
        }

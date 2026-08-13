from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass(frozen=True)
class AdaptationDecision:
    next_difficulty: int
    adaptation_reason: str
    trigger_follow_up: bool
    follow_up_topic: str | None


class DifficultyEngine:
    """
    Real-Time Difficulty Progression & Adaptation Engine (DISE Module).
    Adapts question difficulty dynamically based on real-time candidate scores
    and triggers experience-first follow-up questions.
    """

    SUPPORTED_TECH_TRIGGERS = [
        "redis", "kafka", "kubernetes", "k8s", "docker", "postgres", "mongodb",
        "graphql", "grpc", "aws", "jwt", "oauth", "microservices", "rabbitmq", "asyncio"
    ]

    def adapt_difficulty(
        self,
        current_difficulty: int,
        latest_score: float,  # 0.0 to 100.0
        candidate_answer: str,
    ) -> AdaptationDecision:
        """
        Compute difficulty adaptation decision based on latest score and answer content.
        """
        # Determine follow-up technology triggers from candidate's answer
        follow_up_topic = self._detect_tech_trigger(candidate_answer)
        trigger_follow_up = follow_up_topic is not None

        # Adaptation rules
        if latest_score >= 80.0:
            next_diff = min(5, current_difficulty + 1)
            reason = f"Excellent response ({latest_score}%). Increased difficulty to level {next_diff}."
        elif latest_score <= 45.0:
            next_diff = max(1, current_difficulty - 1)
            reason = f"Candidate struggled ({latest_score}%). Reduced difficulty to level {next_diff}."
        else:
            next_diff = current_difficulty
            reason = f"Solid response ({latest_score}%). Maintained difficulty at level {next_diff}."

        return AdaptationDecision(
            next_difficulty=next_diff,
            adaptation_reason=reason,
            trigger_follow_up=trigger_follow_up,
            follow_up_topic=follow_up_topic,
        )

    def _detect_tech_trigger(self, answer_text: str) -> str | None:
        """Identify if candidate answer explicitly mentions key architectural technologies."""
        if not answer_text:
            return None
        text_lower = answer_text.lower()
        for tech in self.SUPPORTED_TECH_TRIGGERS:
            if tech in text_lower:
                return tech
        return None

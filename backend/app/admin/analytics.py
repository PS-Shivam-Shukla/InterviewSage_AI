"""
Admin Analytics Subsystem Wrapper.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.analytics.service import AnalyticsService


class AdminAnalyticsManager:
    """Wrapper providing Admin Analytics endpoints integration."""

    def __init__(self, db: Session) -> None:
        self.service = AnalyticsService(db)

    def get_overview(self) -> dict[str, Any]:
        return self.service.get_admin_overview()

    def get_models(self) -> Any:
        return self.service.get_model_analytics()

    def get_costs(self) -> dict[str, Any]:
        return self.service.get_cost_analytics()

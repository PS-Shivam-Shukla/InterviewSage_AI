"""
Analytics Service — Powers cross-interview, model, evaluation, cost, and admin dashboard queries.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.analytics_service import AnalyticsService

def __getattr__(name: str):
    if name == "AnalyticsService":
        from app.services.analytics_service import AnalyticsService
        return AnalyticsService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["AnalyticsService"]

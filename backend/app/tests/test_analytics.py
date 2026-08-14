"""
Phase 11 — Analytics Service tests.
Uses in-memory SQLite + seeded fixture data to validate
aggregation logic without touching the real database.
"""

import json
from datetime import datetime

from app.models import Interview
from app.models.interview import AgentLog, InterviewReport
from app.services.analytics_service import AnalyticsService

# ── Helpers ───────────────────────────────────────────────────

def _seed_completed_interview(db_session, user, resume, jd, score: int, scorecard: list) -> Interview:
    """Create a completed interview with a persisted report."""
    iv = Interview(
        user_id=user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        status="COMPLETED",
        overall_score=score,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
    )
    db_session.add(iv)
    db_session.flush()

    report = InterviewReport(
        interview_id=iv.id,
        competency_scorecard=json.dumps(scorecard),
        improvement_plan="[]",
        transcript_snapshot="[]",
        generated_at=datetime.utcnow(),
    )
    db_session.add(report)
    db_session.commit()
    return iv


# ── Summary ───────────────────────────────────────────────────

class TestAnalyticsSummary:
    def test_empty_user_returns_zeros(self, db_session, sample_user):
        svc = AnalyticsService(db_session)
        result = svc.get_summary(sample_user.id)
        assert result["total_interviews"] == 0
        assert result["average_score"] is None
        assert result["completion_rate"] == 0.0
        assert result["weak_competencies"] == []

    def test_counts_correctly(self, db_session, sample_user, sample_resume, sample_jd):
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=8,
            scorecard=[{"competency": "Coding", "score": 8}],
        )
        svc = AnalyticsService(db_session)
        result = svc.get_summary(sample_user.id)
        assert result["total_interviews"] == 1
        assert result["average_score"] == 8.0
        assert result["completion_rate"] == 1.0

    def test_weak_competency_flagged(self, db_session, sample_user, sample_resume, sample_jd):
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=4,
            scorecard=[
                {"competency": "Coding",      "score": 4},
                {"competency": "Communication","score": 8},
            ],
        )
        svc = AnalyticsService(db_session)
        result = svc.get_summary(sample_user.id)
        assert "Coding" in result["weak_competencies"]
        assert "Communication" not in result["weak_competencies"]

    def test_average_score_across_multiple(
        self, db_session, sample_user, sample_resume, sample_jd
    ):
        for score in [6, 8, 10]:
            _seed_completed_interview(
                db_session, sample_user, sample_resume, sample_jd,
                score=score,
                scorecard=[{"competency": "Coding", "score": score}],
            )
        svc = AnalyticsService(db_session)
        result = svc.get_summary(sample_user.id)
        assert result["average_score"] == 8.0   # (6+8+10)/3


# ── Trends ────────────────────────────────────────────────────

class TestAnalyticsTrends:
    def test_empty_returns_empty_list(self, db_session, sample_user):
        svc = AnalyticsService(db_session)
        assert svc.get_trends(sample_user.id) == []

    def test_returns_completed_only(self, db_session, sample_user, sample_resume, sample_jd):
        # One completed, one in-progress
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=7, scorecard=[],
        )
        in_prog = Interview(
            user_id=sample_user.id, resume_id=sample_resume.id, jd_id=sample_jd.id,
            status="IN_PROGRESS", overall_score=None, started_at=datetime.utcnow(),
        )
        db_session.add(in_prog)
        db_session.commit()

        svc = AnalyticsService(db_session)
        trends = svc.get_trends(sample_user.id)
        assert len(trends) == 1
        assert trends[0]["score"] == 7

    def test_trend_shape(self, db_session, sample_user, sample_resume, sample_jd):
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=9, scorecard=[],
        )
        svc = AnalyticsService(db_session)
        trends = svc.get_trends(sample_user.id)
        assert "date" in trends[0]
        assert "score" in trends[0]
        assert "interview_id" in trends[0]


# ── Competencies ──────────────────────────────────────────────

class TestAnalyticsCompetencies:
    def test_empty_returns_empty_list(self, db_session, sample_user):
        svc = AnalyticsService(db_session)
        assert svc.get_competencies(sample_user.id) == []

    def test_averages_across_interviews(
        self, db_session, sample_user, sample_resume, sample_jd
    ):
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=6,
            scorecard=[{"competency": "Coding", "score": 6}],
        )
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=8,
            scorecard=[{"competency": "Coding", "score": 8}],
        )
        svc = AnalyticsService(db_session)
        comps = svc.get_competencies(sample_user.id)
        coding = next(c for c in comps if c["competency"] == "Coding")
        assert coding["avg_score"] == 7.0
        assert coding["interview_count"] == 2

    def test_multiple_competencies(self, db_session, sample_user, sample_resume, sample_jd):
        _seed_completed_interview(
            db_session, sample_user, sample_resume, sample_jd,
            score=7,
            scorecard=[
                {"competency": "Coding",       "score": 8},
                {"competency": "System Design", "score": 6},
            ],
        )
        svc = AnalyticsService(db_session)
        comps = svc.get_competencies(sample_user.id)
        names = [c["competency"] for c in comps]
        assert "Coding" in names
        assert "System Design" in names


# ── Agent Metrics ─────────────────────────────────────────────

class TestAgentMetrics:
    def test_empty_logs_returns_empty(self, db_session):
        svc = AnalyticsService(db_session)
        assert svc.get_agent_metrics() == []

    def test_computes_success_rate(self, db_session, sample_interview):
        for status in ["SUCCESS", "SUCCESS", "FAILED"]:
            log = AgentLog(
                interview_id=sample_interview.id,
                agent_name="ResumeAgent",
                node_status=status,
                latency_ms=100,
                retry_count=0,
            )
            db_session.add(log)
        db_session.commit()

        svc = AnalyticsService(db_session)
        metrics = svc.get_agent_metrics()
        resume = next(m for m in metrics if m["agent_name"] == "ResumeAgent")
        assert round(resume["success_rate"], 2) == round(2 / 3, 2)

    def test_computes_avg_latency(self, db_session, sample_interview):
        for latency in [100, 200, 300]:
            log = AgentLog(
                interview_id=sample_interview.id,
                agent_name="EvaluationAgent",
                node_status="SUCCESS",
                latency_ms=latency,
                retry_count=0,
            )
            db_session.add(log)
        db_session.commit()

        svc = AnalyticsService(db_session)
        metrics = svc.get_agent_metrics()
        eval_m = next(m for m in metrics if m["agent_name"] == "EvaluationAgent")
        assert eval_m["avg_latency_ms"] == 200

    def test_multiple_agents(self, db_session, sample_interview):
        for agent in ["ResumeAgent", "JDAgent", "ATSAgent"]:
            db_session.add(AgentLog(
                interview_id=sample_interview.id,
                agent_name=agent,
                node_status="SUCCESS",
                latency_ms=50, retry_count=0,
            ))
        db_session.commit()

        svc = AnalyticsService(db_session)
        names = [m["agent_name"] for m in svc.get_agent_metrics()]
        assert "ResumeAgent" in names
        assert "JDAgent" in names
        assert "ATSAgent" in names

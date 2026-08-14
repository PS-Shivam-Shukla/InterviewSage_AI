"""
Unit and Integration Tests for CompanyProfileEngine & IndustryBenchmarkEngine.
"""

from sqlalchemy.orm import Session

from app.career.benchmark import IndustryBenchmarkEngine
from app.career.company import CompanyProfileEngine
from app.models import User


def test_company_profile_engine(db_session: Session):
    """Verify CompanyProfileEngine returns company weightings."""
    engine = CompanyProfileEngine(db_session)

    amazon = engine.get_company_profile("Amazon")
    assert amazon.company_name == "Amazon"
    assert amazon.behavioral_weight == 0.40
    assert "Customer Obsession" in amazon.key_principles

    google = engine.get_company_profile("Google")
    assert google.company_name == "Google"
    assert google.coding_weight == 0.50


def test_industry_benchmark_engine(db_session: Session, sample_user: User):
    """Verify IndustryBenchmarkEngine calculates percentiles across category benchmarks."""
    engine = IndustryBenchmarkEngine(db_session)

    res = engine.get_candidate_benchmark(sample_user.id)
    assert res.candidate_id == sample_user.id
    assert res.overall_percentile > 0.0
    assert len(res.categories) >= 5

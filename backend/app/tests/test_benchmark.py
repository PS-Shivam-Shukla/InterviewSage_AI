"""
Unit Tests for BenchmarkRunner Subsystem.
Verifies model benchmarking comparison runs and BenchmarkResult DB persistence.
"""

from sqlalchemy.orm import Session

from app.evaluation.benchmark import BenchmarkRunner
from app.models.evaluation import BenchmarkResult, ModelScore


def test_benchmark_runner_multi_model_execution(db_session: Session):
    """Verify BenchmarkRunner executes multi-model comparison suite and updates ModelScore DB records."""
    runner = BenchmarkRunner()
    targets = [("ollama", "qwen2.5:7b"), ("openai", "gpt-4o")]

    reports = runner.benchmark_models(
        benchmark_name="test_benchmark_run",
        prompt_version="v1",
        providers_and_models=targets,
        db=db_session,
    )

    assert len(reports) == 2
    assert reports[0]["model_name"] == "qwen2.5:7b"
    assert reports[1]["model_name"] == "gpt-4o"

    # Verify DB persistence
    bm_recs = (
        db_session.query(BenchmarkResult)
        .filter(BenchmarkResult.benchmark_name == "test_benchmark_run")
        .all()
    )
    assert len(bm_recs) == 2

    model_score = db_session.query(ModelScore).filter(ModelScore.model_name == "gpt-4o").first()
    assert model_score is not None
    assert model_score.provider_name == "openai"

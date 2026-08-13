"""
Unit and Integration Tests for AIEvaluator Subsystem.
Verifies evaluation suite execution, DB persistence, and sample scoring.
"""

import pytest
from sqlalchemy.orm import Session

from app.evaluation.evaluator import AIEvaluator
from app.evaluation.datasets import EvaluationSample
from app.models.evaluation import EvaluationRun, EvaluationResult


def test_evaluator_evaluate_single_sample():
    """Verify single sample evaluation produces valid metrics result."""
    evaluator = AIEvaluator()
    sample = EvaluationSample(
        id="sample_test_1",
        question="How do you configure connection pooling in PostgreSQL?",
        expected_answer="Use HikariCP or SQLAlchemy SessionLocal connection pool.",
    )

    res = evaluator.evaluate_sample(sample, prompt_version="v1")
    assert res["sample_id"] == "sample_test_1"
    assert res["metrics"].correctness > 0.0
    assert res["metrics"].faithfulness > 0.0
    assert res["metrics"].hallucination_score >= 0.0


def test_evaluator_run_suite_with_db(db_session: Session):
    """Verify full evaluation suite execution persists EvaluationRun and EvaluationResult DB records."""
    evaluator = AIEvaluator()
    eval_summary = evaluator.run_eval_suite(
        run_name="unit_test_suite_run",
        prompt_version="v1",
        model_name="qwen2.5:7b",
        db=db_session,
    )

    assert eval_summary["run_id"] is not None
    assert eval_summary["total_samples"] > 0
    assert eval_summary["pass_rate"] >= 0.0

    # Verify DB records
    run_rec = db_session.query(EvaluationRun).filter(EvaluationRun.run_name == "unit_test_suite_run").first()
    assert run_rec is not None
    assert run_rec.total_samples > 0

    results = db_session.query(EvaluationResult).filter(EvaluationResult.run_id == run_rec.id).all()
    assert len(results) > 0

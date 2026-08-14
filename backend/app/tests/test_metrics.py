"""
Unit Tests for EvaluationMetrics & Rubric Subsystems.
Verifies correctness, faithfulness, hallucination, relevancy, toxicity, and rubric scoring.
"""

from app.evaluation.metrics import EvaluationMetrics
from app.evaluation.rubric import TECHNICAL_RUBRIC


def test_metrics_correctness_and_faithfulness():
    """Verify correctness and faithfulness scoring logic."""
    expected = "Use HikariCP for connection pooling with max overflow."
    candidate = "HikariCP handles connection pooling with max overflow."

    correctness = EvaluationMetrics.calculate_correctness(candidate, expected)
    assert correctness > 70.0

    faithfulness = EvaluationMetrics.calculate_faithfulness(candidate, expected)
    assert faithfulness > 70.0

    hallucination = EvaluationMetrics.calculate_hallucination_score(candidate, expected)
    assert hallucination < 30.0


def test_metrics_relevancy_and_toxicity():
    """Verify question relevancy and toxicity detection."""
    question = "How do you optimize SQL queries?"
    answer = "Optimize SQL queries using indexes, execution plans, and query cache."

    relevancy = EvaluationMetrics.calculate_relevancy(question, answer)
    assert relevancy > 50.0

    toxic, bias = EvaluationMetrics.calculate_toxicity_and_bias(answer)
    assert toxic == 0.0
    assert bias == 0.0

    toxic_sample, _ = EvaluationMetrics.calculate_toxicity_and_bias("This candidate is dumb and stupid.")
    assert toxic_sample > 0.0


def test_technical_rubric_composite_score():
    """Verify weighted composite scoring using TECHNICAL_RUBRIC."""
    scores = {
        "correctness": 90.0,
        "faithfulness": 85.0,
        "relevancy": 95.0,
        "clarity": 80.0,
    }

    score = TECHNICAL_RUBRIC.score(scores)
    assert 80.0 <= score <= 95.0

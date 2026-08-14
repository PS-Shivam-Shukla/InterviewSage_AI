"""
Unit Tests for RegressionTester Subsystem.
Verifies prompt regression detection, comparison metrics, and failure reason assertions.
"""

from app.evaluation.regression import RegressionComparisonResult, RegressionTester


def test_regression_tester_no_regression():
    """Verify RegressionTester approves comparison when target run improves over baseline."""
    tester = RegressionTester()

    baseline = {
        "run_name": "prompt_v1",
        "pass_rate": 80.0,
        "avg_hallucination": 10.0,
        "avg_latency_ms": 1200.0,
        "avg_cost_usd": 0.002,
    }

    target = {
        "run_name": "prompt_v2",
        "pass_rate": 85.0,
        "avg_hallucination": 8.0,
        "avg_latency_ms": 1100.0,
        "avg_cost_usd": 0.002,
    }

    res: RegressionComparisonResult = tester.compare_runs(baseline, target)
    assert res.is_regression is False
    assert res.status == "PASSED"
    assert res.accuracy_delta == 5.0


def test_regression_tester_detects_accuracy_drop():
    """Verify RegressionTester flags regression when accuracy drops beyond threshold."""
    tester = RegressionTester(max_accuracy_drop=5.0)

    baseline = {
        "run_name": "v1",
        "pass_rate": 85.0,
        "avg_hallucination": 5.0,
        "avg_latency_ms": 1000.0,
        "avg_cost_usd": 0.001,
    }
    target = {
        "run_name": "v2",
        "pass_rate": 70.0,
        "avg_hallucination": 5.0,
        "avg_latency_ms": 1000.0,
        "avg_cost_usd": 0.001,
    }

    res = tester.compare_runs(baseline, target)
    assert res.is_regression is True
    assert res.status == "REGRESSION_DETECTED"
    assert any("Accuracy dropped" in reason for reason in res.failure_reasons)


def test_regression_tester_detects_hallucination_spike():
    """Verify RegressionTester flags regression when hallucination rate spikes."""
    tester = RegressionTester(max_hallucination_increase=5.0)

    baseline = {
        "run_name": "v1",
        "pass_rate": 85.0,
        "avg_hallucination": 5.0,
        "avg_latency_ms": 1000.0,
        "avg_cost_usd": 0.001,
    }
    target = {
        "run_name": "v2",
        "pass_rate": 85.0,
        "avg_hallucination": 20.0,
        "avg_latency_ms": 1000.0,
        "avg_cost_usd": 0.001,
    }

    res = tester.compare_runs(baseline, target)
    assert res.is_regression is True
    assert any("Hallucination rate increased" in reason for reason in res.failure_reasons)

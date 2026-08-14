"""
Regression Testing Engine for AI Evaluation Framework.
Compares two evaluation runs (baseline vs target) to detect prompt, model, or quality regressions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.logging import get_logger
from app.evaluation.evaluator import AIEvaluator

logger = get_logger(__name__)


@dataclass
class RegressionComparisonResult:
    baseline_run_name: str
    target_run_name: str
    accuracy_delta: float  # positive = improvement, negative = regression
    hallucination_delta: float  # positive = worse hallucination, negative = lower hallucination
    latency_delta_ms: float  # positive = slower, negative = faster
    cost_delta_usd: float  # positive = more expensive, negative = cheaper
    is_regression: bool
    status: str  # "PASSED" | "REGRESSION_DETECTED"
    failure_reasons: list[str]


class RegressionTester:
    """
    Executes automated regression testing comparing baseline prompt/model vs new candidate prompt/model.
    """

    def __init__(
        self,
        evaluator: AIEvaluator | None = None,
        max_accuracy_drop: float = 5.0,  # Max allowed accuracy drop in %
        max_hallucination_increase: float = 5.0,  # Max allowed hallucination increase in %
        max_latency_increase_ms: float = 1000.0,  # Max allowed latency increase in ms
    ) -> None:
        self.evaluator = evaluator or AIEvaluator()
        self.max_accuracy_drop = max_accuracy_drop
        self.max_hallucination_increase = max_hallucination_increase
        self.max_latency_increase_ms = max_latency_increase_ms

    def compare_runs(
        self,
        baseline_summary: dict[str, Any],
        target_summary: dict[str, Any],
    ) -> RegressionComparisonResult:
        """
        Compare two evaluation run summaries and assert regression criteria.
        """
        accuracy_delta = round(target_summary["pass_rate"] - baseline_summary["pass_rate"], 2)
        hallucination_delta = round(
            target_summary["avg_hallucination"] - baseline_summary["avg_hallucination"], 2
        )
        latency_delta = round(
            target_summary["avg_latency_ms"] - baseline_summary["avg_latency_ms"], 2
        )
        cost_delta = round(target_summary["avg_cost_usd"] - baseline_summary["avg_cost_usd"], 6)

        reasons = []
        is_regression = False

        if accuracy_delta < -self.max_accuracy_drop:
            is_regression = True
            reasons.append(
                f"Accuracy dropped by {abs(accuracy_delta)}% (max allowed drop: {self.max_accuracy_drop}%)"
            )

        if hallucination_delta > self.max_hallucination_increase:
            is_regression = True
            reasons.append(
                f"Hallucination rate increased by {hallucination_delta}% (max allowed: {self.max_hallucination_increase}%)"
            )

        if latency_delta > self.max_latency_increase_ms:
            is_regression = True
            reasons.append(
                f"Latency increased by {latency_delta}ms (max allowed: {self.max_latency_increase_ms}ms)"
            )

        status = "REGRESSION_DETECTED" if is_regression else "PASSED"

        return RegressionComparisonResult(
            baseline_run_name=baseline_summary.get("run_name", "baseline"),
            target_run_name=target_summary.get("run_name", "target"),
            accuracy_delta=accuracy_delta,
            hallucination_delta=hallucination_delta,
            latency_delta_ms=latency_delta,
            cost_delta_usd=cost_delta,
            is_regression=is_regression,
            status=status,
            failure_reasons=reasons,
        )

    def run_prompt_regression_test(
        self,
        prompt_version_baseline: str = "v1",
        prompt_version_candidate: str = "v2",
        model_name: str | None = None,
    ) -> RegressionComparisonResult:
        """
        Run side-by-side prompt regression test (e.g. Prompt v1 vs Prompt v2).
        """
        logger.info(
            f"Running prompt regression test: {prompt_version_baseline} vs {prompt_version_candidate}"
        )

        baseline_summary = self.evaluator.run_eval_suite(
            run_name=f"prompt_{prompt_version_baseline}",
            prompt_version=prompt_version_baseline,
            model_name=model_name,
        )

        candidate_summary = self.evaluator.run_eval_suite(
            run_name=f"prompt_{prompt_version_candidate}",
            prompt_version=prompt_version_candidate,
            model_name=model_name,
        )

        return self.compare_runs(baseline_summary, candidate_summary)

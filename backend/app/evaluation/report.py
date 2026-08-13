"""
Evaluation Report Generator.
Produces formatted Markdown scorecards and regression summary reports.
"""

from __future__ import annotations

from typing import Any, Dict
from app.evaluation.regression import RegressionComparisonResult


class EvaluationReportGenerator:
    """Generates human-readable evaluation scorecards and regression comparison reports."""

    @staticmethod
    def generate_markdown_scorecard(eval_summary: Dict[str, Any]) -> str:
        """Generate a formatted Markdown evaluation scorecard."""
        md = f"""# AI Evaluation Scorecard — {eval_summary.get('run_name', 'Run')}

**Model**: `{eval_summary.get('model_name', 'N/A')}`  
**Prompt Version**: `{eval_summary.get('prompt_version', 'v1')}`  
**Pass Rate**: **{eval_summary.get('pass_rate', 0.0)}%**  

---

### Core Performance Metrics

| Metric | Score / Value | Target Benchmark |
|---|:---:|:---:|
| **Correctness** | {eval_summary.get('avg_correctness', 0.0)}% | >= 80.0% |
| **Faithfulness** | {eval_summary.get('avg_faithfulness', 0.0)}% | >= 85.0% |
| **Hallucination Rate** | {eval_summary.get('avg_hallucination', 0.0)}% | <= 15.0% |
| **Response Relevancy** | {eval_summary.get('avg_relevancy', 0.0)}% | >= 85.0% |
| **Avg Latency** | {eval_summary.get('avg_latency_ms', 0.0)} ms | <= 2000 ms |
| **Avg Cost / Req** | ${eval_summary.get('avg_cost_usd', 0.0):.6f} | <= $0.005 |

---

### Sample Results Summary
- **Total Samples Evaluated**: {eval_summary.get('total_samples', 0)}
- **Passed**: {eval_summary.get('passed_samples', 0)}
- **Failed**: {eval_summary.get('failed_samples', 0)}
"""
        return md

    @staticmethod
    def generate_regression_report(comparison: RegressionComparisonResult) -> str:
        """Generate a formatted Markdown regression report."""
        status_badge = "✅ PASSED (NO REGRESSION)" if not comparison.is_regression else "❌ REGRESSION DETECTED"
        reasons_text = "\n".join([f"- {r}" for r in comparison.failure_reasons]) if comparison.failure_reasons else "- None"

        md = f"""# AI Prompt Regression Test Report

**Baseline Run**: `{comparison.baseline_run_name}`  
**Candidate Run**: `{comparison.target_run_name}`  
**Status**: **{status_badge}**

---

### Delta Summary

| Metric | Baseline -> Target Delta | Evaluation Status |
|---|:---:|:---:|
| **Accuracy / Pass Rate** | {comparison.accuracy_delta:+.2f}% | {"FAIL" if comparison.accuracy_delta < -5 else "PASS"} |
| **Hallucination Rate** | {comparison.hallucination_delta:+.2f}% | {"FAIL" if comparison.hallucination_delta > 5 else "PASS"} |
| **Average Latency** | {comparison.latency_delta_ms:+.2f} ms | {"FAIL" if comparison.latency_delta_ms > 1000 else "PASS"} |
| **Average Cost** | ${comparison.cost_delta_usd:+.6f} | PASS |

---

### Regression Failure Reasons
{reasons_text}
"""
        return md

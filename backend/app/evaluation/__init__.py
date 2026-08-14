"""
AI Evaluation Framework Package.
Exposes AIEvaluator, EvaluationMetrics, GoldenDatasetManager, BenchmarkRunner, RegressionTester, and EvaluationReportGenerator.
"""

from app.evaluation.benchmark import BenchmarkRunner
from app.evaluation.datasets import EvaluationSample, GoldenDatasetManager
from app.evaluation.evaluator import AIEvaluator
from app.evaluation.metrics import EvaluationMetrics, EvaluationMetricsResult
from app.evaluation.regression import RegressionComparisonResult, RegressionTester
from app.evaluation.report import EvaluationReportGenerator
from app.evaluation.rubric import (
    BEHAVIORAL_RUBRIC,
    EXECUTIVE_RUBRIC,
    TECHNICAL_RUBRIC,
    EvaluationRubric,
)

__all__ = [
    "BEHAVIORAL_RUBRIC",
    "EXECUTIVE_RUBRIC",
    "TECHNICAL_RUBRIC",
    "AIEvaluator",
    "BenchmarkRunner",
    "EvaluationMetrics",
    "EvaluationMetricsResult",
    "EvaluationReportGenerator",
    "EvaluationRubric",
    "EvaluationSample",
    "GoldenDatasetManager",
    "RegressionComparisonResult",
    "RegressionTester",
]

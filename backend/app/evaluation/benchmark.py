"""
Automated Model Benchmark Runner.
Executes benchmarking suites across multiple model providers and prompt versions, persisting BenchmarkResult summaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.evaluation.evaluator import AIEvaluator
from app.models.evaluation import BenchmarkResult, ModelScore, PromptScore

logger = get_logger(__name__)


class BenchmarkRunner:
    """
    Executes automated model benchmarking and prompt comparison runs.
    """

    def __init__(self, evaluator: Optional[AIEvaluator] = None) -> None:
        self.evaluator = evaluator or AIEvaluator()

    def benchmark_models(
        self,
        benchmark_name: str = "model_benchmark",
        prompt_version: str = "v1",
        providers_and_models: Optional[List[tuple[str, str]]] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Benchmark multiple model providers/models against the golden dataset.
        """
        targets = providers_and_models or [
            ("ollama", "qwen2.5:7b"),
            ("openai", "gpt-4o"),
            ("claude", "claude-3-5-sonnet"),
        ]

        reports = []
        for provider, model_name in targets:
            run_title = f"{benchmark_name}_{provider}_{model_name}"
            eval_summary = self.evaluator.run_eval_suite(
                run_name=run_title,
                prompt_version=prompt_version,
                model_name=model_name,
                provider=provider,
                db=db,
            )

            reports.append(eval_summary)

            # Persist BenchmarkResult and update ModelScore/PromptScore in DB
            if db is not None:
                try:
                    bm_rec = BenchmarkResult(
                        id=str(uuid.uuid4()),
                        benchmark_name=benchmark_name,
                        model_name=model_name,
                        prompt_version=prompt_version,
                        overall_score=eval_summary["pass_rate"],
                        latency_p95_ms=eval_summary["avg_latency_ms"],
                        total_cost_usd=eval_summary["avg_cost_usd"],
                        timestamp=datetime.now(timezone.utc),
                    )
                    db.add(bm_rec)

                    # Update or insert ModelScore aggregate
                    model_score = db.query(ModelScore).filter(ModelScore.model_name == model_name).first()
                    if not model_score:
                        model_score = ModelScore(
                            id=str(uuid.uuid4()),
                            provider_name=provider,
                            model_name=model_name,
                            accuracy_score=eval_summary["pass_rate"],
                            latency_p95_ms=eval_summary["avg_latency_ms"],
                            cost_per_1k_tokens=eval_summary["avg_cost_usd"],
                            quality_rating="STRONG" if eval_summary["pass_rate"] >= 80 else "MODERATE",
                            updated_at=datetime.now(timezone.utc),
                        )
                        db.add(model_score)
                    else:
                        model_score.accuracy_score = eval_summary["pass_rate"]
                        model_score.latency_p95_ms = eval_summary["avg_latency_ms"]
                        model_score.updated_at = datetime.now(timezone.utc)

                    db.commit()
                except Exception as exc:
                    db.rollback()
                    logger.error(f"Failed to persist BenchmarkResult: {exc}", exc_info=True)

        return reports

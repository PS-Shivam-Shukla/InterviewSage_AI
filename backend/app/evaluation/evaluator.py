"""
Core AI Evaluator Engine.
Executes evaluation runs across golden datasets, scoring outputs with EvaluationMetrics and persisting results.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.ai.gateway import AIGateway, ai_gateway
from app.ai.request import AIGatewayRequest
from app.core.logging import get_logger
from app.evaluation.datasets import EvaluationSample, GoldenDatasetManager
from app.evaluation.metrics import EvaluationMetrics, EvaluationMetricsResult
from app.models.evaluation import EvaluationResult, EvaluationRun

logger = get_logger(__name__)


class AIEvaluator:
    """
    Evaluates LLM performance across golden datasets and persists EvaluationRun audit records.
    """

    def __init__(
        self,
        gateway: Optional[AIGateway] = None,
        dataset_manager: Optional[GoldenDatasetManager] = None,
    ) -> None:
        self.gateway = gateway or ai_gateway
        self.dataset_manager = dataset_manager or GoldenDatasetManager()

    def evaluate_sample(
        self,
        sample: EvaluationSample,
        prompt_version: str = "v1",
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate a single evaluation sample using AIGateway."""
        start_t = time.perf_counter()

        # Construct AIGateway Request
        req = AIGatewayRequest(
            task_type="personalize_question",
            prompt_key="prompt:question_personalizer",
            prompt_version=prompt_version,
            provider_override=provider,
            model_override=model_name,
            variables={
                "seniority_level": sample.seniority,
                "target_competency": sample.domain,
                "project_context": "Production enterprise application",
                "baseline_question": sample.question,
            },
        )

        resp = self.gateway.execute(req)
        duration_ms = int((time.perf_counter() - start_t) * 1000)

        # Run metrics evaluation
        candidate_ans = resp.raw_content
        metrics_res: EvaluationMetricsResult = EvaluationMetrics.evaluate_sample(
            question=sample.question,
            answer=candidate_ans,
            expected_answer=sample.expected_answer,
            context=sample.question,
        )

        return {
            "sample_id": sample.id,
            "question": sample.question,
            "answer": candidate_ans,
            "expected": sample.expected_answer,
            "metrics": metrics_res,
            "cost_usd": resp.cost_usd,
            "latency_ms": duration_ms,
            "provider": resp.provider,
            "model_name": resp.model_name,
        }

    def run_eval_suite(
        self,
        run_name: str = "suite_run",
        prompt_version: str = "v1",
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Execute full evaluation suite across golden dataset and record summary run.
        """
        samples = self.dataset_manager.load_full_benchmark_dataset()
        if not samples:
            samples = [
                EvaluationSample(
                    id="sample_fallback_1",
                    question="Discuss database connection pooling strategies.",
                    expected_answer="Use HikariCP with max pool size configuration.",
                    domain="Database",
                    seniority="Senior",
                )
            ]

        results = []
        tot_correctness = 0.0
        tot_faithfulness = 0.0
        tot_hallucination = 0.0
        tot_relevancy = 0.0
        tot_cost = 0.0
        tot_latency = 0.0
        passed_count = 0

        for sample in samples:
            res = self.evaluate_sample(sample, prompt_version=prompt_version, model_name=model_name, provider=provider)
            results.append(res)

            m: EvaluationMetricsResult = res["metrics"]
            tot_correctness += m.correctness
            tot_faithfulness += m.faithfulness
            tot_hallucination += m.hallucination_score
            tot_relevancy += m.relevancy
            tot_cost += res["cost_usd"]
            tot_latency += res["latency_ms"]

            if m.passed:
                passed_count += 1

        total = len(samples)
        avg_correctness = round(tot_correctness / total, 2) if total > 0 else 0.0
        avg_faithfulness = round(tot_faithfulness / total, 2) if total > 0 else 0.0
        avg_hallucination = round(tot_hallucination / total, 2) if total > 0 else 0.0
        avg_relevancy = round(tot_relevancy / total, 2) if total > 0 else 0.0
        avg_cost = round(tot_cost / total, 6) if total > 0 else 0.0
        avg_latency = round(tot_latency / total, 2) if total > 0 else 0.0
        pass_rate = round((passed_count / total) * 100.0, 2) if total > 0 else 0.0

        run_id = str(uuid.uuid4())
        model_used = model_name or "qwen2.5:7b"

        # Persist into DB if session provided
        if db is not None:
            try:
                run_record = EvaluationRun(
                    id=run_id,
                    run_name=run_name,
                    prompt_version=prompt_version,
                    model_name=model_used,
                    dataset_name="golden_dataset",
                    total_samples=total,
                    passed_samples=passed_count,
                    failed_samples=total - passed_count,
                    avg_correctness=avg_correctness,
                    avg_faithfulness=avg_faithfulness,
                    avg_hallucination=avg_hallucination,
                    avg_relevancy=avg_relevancy,
                    avg_cost_usd=avg_cost,
                    avg_latency_ms=avg_latency,
                    pass_rate=pass_rate,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(run_record)
                db.flush()

                for r in results:
                    m = r["metrics"]
                    res_record = EvaluationResult(
                        id=str(uuid.uuid4()),
                        run_id=run_id,
                        sample_id=r["sample_id"],
                        question_text=r["question"],
                        candidate_answer=r["answer"],
                        expected_answer=r["expected"],
                        correctness_score=m.correctness,
                        faithfulness_score=m.faithfulness,
                        hallucination_score=m.hallucination_score,
                        relevancy_score=m.relevancy,
                        passed=m.passed,
                        created_at=datetime.now(timezone.utc),
                    )
                    db.add(res_record)

                db.commit()
            except Exception as exc:
                db.rollback()
                logger.error(f"Failed to persist EvaluationRun DB records: {exc}", exc_info=True)

        return {
            "run_id": run_id,
            "run_name": run_name,
            "prompt_version": prompt_version,
            "model_name": model_used,
            "total_samples": total,
            "passed_samples": passed_count,
            "failed_samples": total - passed_count,
            "pass_rate": pass_rate,
            "avg_correctness": avg_correctness,
            "avg_faithfulness": avg_faithfulness,
            "avg_hallucination": avg_hallucination,
            "avg_relevancy": avg_relevancy,
            "avg_cost_usd": avg_cost,
            "avg_latency_ms": avg_latency,
            "results": results,
        }

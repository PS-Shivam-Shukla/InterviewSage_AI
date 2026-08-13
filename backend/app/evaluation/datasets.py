"""
Golden Dataset Loader & Manager for AI Evaluation Framework.
Loads, validates, and manages interview questions, expected answers, edge cases, and prompt benchmarks.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)

GOLDEN_DATASET_DIR = os.path.join(os.path.dirname(__file__), "golden_dataset")


@dataclass
class EvaluationSample:
    id: str
    question: str
    expected_answer: Optional[str] = None
    target_concepts: Optional[List[str]] = None
    domain: str = "General"
    seniority: str = "Mid"
    sample_type: str = "standard"


class GoldenDatasetManager:
    """Manages golden evaluation datasets stored in golden_dataset/ directory."""

    def __init__(self, dataset_dir: Optional[str] = None) -> None:
        self.dataset_dir = dataset_dir or GOLDEN_DATASET_DIR

    def _read_json(self, filename: str) -> List[Dict[str, Any]]:
        file_path = os.path.join(self.dataset_dir, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Golden dataset file not found: {file_path}")
            return []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"Failed to load golden dataset {filename}: {exc}", exc_info=True)
            return []

    def get_interview_questions(self) -> List[EvaluationSample]:
        """Load baseline interview questions and expected concepts."""
        raw_questions = self._read_json("interview_questions.json")
        raw_answers = {item["id"]: item.get("expected_answer") for item in self._read_json("expected_answers.json")}

        samples = []
        for q in raw_questions:
            sample_id = q.get("id", "q_unknown")
            samples.append(
                EvaluationSample(
                    id=sample_id,
                    question=q.get("question", ""),
                    expected_answer=raw_answers.get(sample_id),
                    target_concepts=q.get("target_concepts", []),
                    domain=q.get("domain", "General"),
                    seniority=q.get("seniority", "Mid"),
                    sample_type="standard",
                )
            )
        return samples

    def get_edge_cases(self) -> List[EvaluationSample]:
        """Load edge cases (short answers, hallucinated claims, prompt injections)."""
        raw_cases = self._read_json("edge_cases.json")
        samples = []
        for c in raw_cases:
            samples.append(
                EvaluationSample(
                    id=c.get("id", "edge_unknown"),
                    question=c.get("question", ""),
                    expected_answer=c.get("expected_evaluation"),
                    sample_type=c.get("type", "edge_case"),
                )
            )
        return samples

    def load_full_benchmark_dataset(self) -> List[EvaluationSample]:
        """Combine standard questions and edge cases into complete evaluation suite."""
        return self.get_interview_questions() + self.get_edge_cases()
